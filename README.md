# Daily Ops

A small installable web app for DevOps: one newer tool spotlighted each day (what it is, the problem it solves, link to the official site), plus a "new this week" feed of headlines and releases that a GitHub Action refreshes every Monday. No API keys.

## Files

- `index.html`: the app (the daily spotlight list lives in the `LIB` array near the top of the script)
- `feed.json`: the weekly feed, written by the Action
- `scripts/update_feed.py`: fetches the feeds (edit the `SOURCES` list to add or remove sources)
- `.github/workflows/update-feed.yml`: runs the script weekly
- `manifest.json`, `sw.js`, `icon-*.png`: make it installable and available offline

## Set up on GitHub

1. Create a new repo, e.g. `daily-ops`, and upload everything in this folder, keeping the structure.
   - Dragging the `.github` folder into the web uploader can be fiddly because it is hidden on some systems. If it doesn't upload, use git instead:
     ```bash
     git init && git add -A && git commit -m "Daily Ops"
     git branch -M main
     git remote add origin https://github.com/<you>/daily-ops.git
     git push -u origin main
     ```
2. **Settings → Actions → General → Workflow permissions**: choose **Read and write permissions**, then Save. (Without this the Action cannot commit the feed.)
3. **Settings → Pages**: Source "Deploy from a branch", branch `main`, folder `/ (root)`.
4. **Actions** tab → "Update feed" → **Run workflow**, to fill the feed now instead of waiting until Monday.
5. Your site will be at `https://<you>.github.io/daily-ops/`.

## Install on your phone

Open the URL in Chrome, then ⋮ → **Install app**. It is a separate app from your other GitHub Pages sites because each has its own path and app ID.

## Notes

- The weekly feed gives headlines and links only, from the sources listed in `scripts/update_feed.py`. Release feeds skip pre-releases (rc, alpha, beta).
- If a source ever changes its URL, the script skips it and carries on with the rest. The Action log shows which ones failed.
- The daily spotlight entries are fixed text. To add newer tools, add entries to `LIB` (or ask me to).
