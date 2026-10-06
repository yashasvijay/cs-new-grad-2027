# Pages deployment

In repository Settings → Pages, select **GitHub Actions** as the source. After merging the Pages workflow, run **GitHub Pages** manually for the first deployment. The workflow never commits or pushes to the repository.

The build uses Python 3.12, generates `site/data.json`, checks relative site URLs and nonzero matching record counts, and packages the site with the original `data/listings.json` available as `listings.json`. Generated files are not committed.

## Triggers

- Successful completion of **Update job listings** on main: checkout the current remote main, including any commit pushed during that run. Compare the SHA-256 of the input listings with the public `version.txt`. Matching versions skip deployment. Missing versions, access errors, and mismatches allow deployment. The version lookup has a ten-second timeout and uses no credentials.
- Push to main affecting `site/**`, `tracker/site_data.py`, or the Pages workflow: build and deploy regardless of the data hash.
- Manual dispatch on main: build and deploy regardless of the data hash. Dispatches on other branches only build.
- Pull requests affecting the same paths: build and upload an artifact, never deploy.

Changing the artifact helper alone requires manual dispatch; it is outside the requested push path filters. Failed updater runs do not build or deploy Pages. Pages runs use shared concurrency with cancellation disabled. GitHub may coalesce pending runs; a later successful updater run catches current main.

The updater schedules every five minutes at minutes 2, 7, …, 57. Its default `GITHUB_TOKEN` pushes cannot trigger the Pages push workflow. `workflow_run` handles that case. Actual scheduled execution is best-effort. Each successful updater run builds; only a changed listings hash deploys. Human site edits and manual dispatch bypass that optimization.

## Local verification

From the repository root:

```sh
python3 -m unittest discover -s tests
node tests/site_dates.cjs
python3 -m tracker.site_data
python3 -m tracker.pages --output /tmp/pages-preview/cs-new-grad-2027
python3 -m http.server 8002 --bind 127.0.0.1 --directory /tmp/pages-preview
```

Open `http://127.0.0.1:8002/cs-new-grad-2027/`. The Node test is an additional local date check; the Python suite needs only the standard library.

## After merging

1. Set the Pages source to GitHub Actions and check any github-pages environment approval rules.
2. Dispatch GitHub Pages on main. Confirm build and deployment succeed.
3. Open the project subpath and verify assets, data, filters, `listings.json`, and `version.txt`.
4. Confirm a successful updater run launches Pages and skips deployment when the published data hash matches.
5. Confirm changed listings deploy and a PR runs only the build job.

GitHub deployment permissions, environment rules, and workflow_run delivery cannot be validated locally.
