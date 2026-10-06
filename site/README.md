# Local preview

From the repository root:

```sh
python3 -m tracker.site_data
python3 -m http.server 8000 --bind 127.0.0.1 --directory site
```

Open http://127.0.0.1:8000. Regenerate the data after updating `data/listings.json`.

`site/data.json` is generated and ignored by Git. The build preserves every record and uses the README location normalizer; ambiguous locations remain unchanged. Missing fields stay null. Dates use the employer release date, falling back to a clearly labeled first-seen date.

The default list includes main 2027 and general early-career roles. The low-confidence toggle includes secondary records. Role-type filters use approximate title keywords; titles matching no category remain visible under every role-type filter. “New this week” uses the last seven days at the time the filters run.

All assets and data load locally. There are no accounts, analytics, application tracking, or deployment settings.
