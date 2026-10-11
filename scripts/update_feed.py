#!/usr/bin/env python3
"""Fetch DevOps news/release feeds and write feed.json. Standard library only, no API keys."""
import json, re, sys, urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

MAX_AGE_DAYS = 45
MAX_PER_SOURCE = 3
MAX_TOTAL = 120
PRE = re.compile(r"(?i)(^|[^a-z])(rc|alpha|beta|nightly|snapshot|dev|next|pre|preview)([^a-z]|\d|$)"
                 r"|chart|apis/|bump|\bstable\b|\bbranch\b")

# (name, url, category, kind, include_regex)
# kind "release" = GitHub releases atom (stable releases only); "news" = blog / announcement feed
SOURCES = [
    ("Kubernetes Blog", "https://kubernetes.io/feed.xml", "k8s", "news", None),
    ("CNCF Blog", "https://www.cncf.io/feed/", "k8s", "news", None),
    ("Karpenter", "https://github.com/kubernetes-sigs/karpenter/releases.atom", "k8s", "release", None),
    ("HashiCorp Blog", "https://www.hashicorp.com/blog/feed.xml", "iac", "news", r"(?i)terraform|packer|vault|nomad|opentofu"),
    ("OpenTofu", "https://github.com/opentofu/opentofu/releases.atom", "iac", "release", None),
    ("Crossplane", "https://github.com/crossplane/crossplane/releases.atom", "iac", "release", None),
    ("GitHub Changelog", "https://github.blog/changelog/feed/", "cicd", "news", r"(?i)actions|workflow|runner|dependabot|packages|artifact"),
    ("Argo CD", "https://github.com/argoproj/argo-cd/releases.atom", "cicd", "release", None),
    ("Argo Rollouts", "https://github.com/argoproj/argo-rollouts/releases.atom", "cicd", "release", None),
    ("Flux", "https://github.com/fluxcd/flux2/releases.atom", "cicd", "release", None),
    ("AWS Security Blog", "https://aws.amazon.com/blogs/security/feed/", "aws", "news", None),
    ("AWS What's New", "https://aws.amazon.com/about-aws/whats-new/recent/feed/", "aws", "news",
     r"(?i)\biam\b|\bkms\b|guardduty|cloudtrail|cloudwatch|security hub|detective|inspector|access analyzer|identity center"),
    ("Backstage", "https://github.com/backstage/backstage/releases.atom", "platform", "release", None),
    ("Cilium", "https://github.com/cilium/cilium/releases.atom", "sec", "release", None),
    ("Falco", "https://github.com/falcosecurity/falco/releases.atom", "sec", "release", None),
    ("Trivy", "https://github.com/aquasecurity/trivy/releases.atom", "sec", "release", None),
    ("Kyverno", "https://github.com/kyverno/kyverno/releases.atom", "sec", "release", None),
    ("Cosign", "https://github.com/sigstore/cosign/releases.atom", "sec", "release", None),
    ("K8sGPT", "https://github.com/k8sgpt-ai/k8sgpt/releases.atom", "ai", "release", None),
]

def local(tag):
    return tag.rsplit("}", 1)[-1]

def parse_date(text):
    if not text:
        return None
    text = text.strip()
    try:
        d = parsedate_to_datetime(text)
    except Exception:
        try:
            d = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except Exception:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "daily-ops-feed/1.0 (+github actions)"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()

def entries(xml_bytes):
    root = ET.fromstring(xml_bytes)
    for el in root.iter():
        t = local(el.tag)
        if t not in ("item", "entry"):
            continue
        title = link = date = None
        for c in el:
            ct = local(c.tag)
            if ct == "title":
                title = (c.text or "").strip()
            elif ct == "link":
                link = c.attrib.get("href") or (c.text or "").strip()
            elif ct in ("pubDate", "updated", "published", "date") and not date:
                date = c.text
        if title and link and link.startswith(("http://", "https://")):
            yield title, link, parse_date(date)

def main():
    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)
    items, ok, failed = [], 0, []
    for name, url, cat, kind, inc in SOURCES:
        try:
            raw = fetch(url)
            found = []
            for title, link, d in entries(raw):
                if d is None or d < cutoff:
                    continue
                if kind == "release" and PRE.search(title):
                    continue
                if inc and not re.search(inc, title):
                    continue
                if kind == "release":
                    title = f"{name} {title}" if name.lower() not in title.lower() else title
                found.append({"title": re.sub(r"\s+", " ", title)[:200], "url": link, "source": name,
                              "category": cat, "kind": kind, "date": d.strftime("%Y-%m-%d")})
            found.sort(key=lambda x: x["date"], reverse=True)
            items.extend(found[:MAX_PER_SOURCE])
            ok += 1
            print(f"ok    {name}: {len(found[:MAX_PER_SOURCE])} items")
        except Exception as e:
            failed.append(name)
            print(f"FAIL  {name}: {e}", file=sys.stderr)
    seen, out = set(), []
    for it in sorted(items, key=lambda x: x["date"], reverse=True):
        if it["url"] in seen:
            continue
        seen.add(it["url"])
        out.append(it)
    out = out[:MAX_TOTAL]
    if ok == 0:
        print("All feeds failed; keeping existing feed.json", file=sys.stderr)
        return
    with open("feed.json", "w", encoding="utf-8") as f:
        json.dump({"updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"), "items": out}, f, ensure_ascii=False, indent=1)
    print(f"wrote {len(out)} items from {ok} sources; failed: {failed or 'none'}")

if __name__ == "__main__":
    main()
