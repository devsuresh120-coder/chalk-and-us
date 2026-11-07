# chalk-and-us-publish

Code only for the Chalk & Us video series: the workflow that copies finished videos to Cloudflare R2.

This repo is public so GitHub Actions is free. It holds **no data**: the episodes' scripts, renderer, schedule, links and logs live in a private repository. `r2.yml` (every 10 minutes, or run by hand) looks for `upload/*` branches in that private repo, copies the files to R2 `chalk-and-us/`, records the links there and deletes the branch. Public logs show only counts. `keepalive.yml` makes one empty commit a month so GitHub does not switch the schedule off.

Secrets: `HUB_TOKEN` (fine-grained token, private data repo only, Contents read/write), `R2_*`.
