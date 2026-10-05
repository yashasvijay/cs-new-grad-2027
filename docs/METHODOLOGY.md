# How the tracker works

The starter polls public Greenhouse, Lever, Ashby, and SmartRecruiters employer feeds. A listing must have a U.S. location signal, a CS role title, and a new-grad/early-career or 2027 graduation signal. Explicit internships, part-time/contract jobs, senior titles, incompatible graduation windows, and detected minimum experience above two years are excluded. Ambiguous remote geography is excluded. Unknown full-time status is flagged for review. These rules are conservative heuristics, not an eligibility determination; omissions and false positives remain possible.

## Identity and history

Jobs are keyed by employer and requisition ID where available, otherwise by employer and provider posting ID. Separate location-specific provider IDs remain separate postings. Source links are preserved. Returning jobs retain their original first-seen time.

- `employer_posted_at`: original posting time, null unless explicitly supplied. Current adapters do not assume it.
- `employer_published_at`: employer feed publication/republication time when provided. Ashby's `publishedAt` is the last publication time; Greenhouse `first_published` is distinct from `updated_at`.
- `employer_updated_at`: feed update timestamp, never used as original posting time.
- `first_seen_at`: our first successful detection, including initial backfill; never inferred from a discovery list's date.
- `tracker_published_at`: first generation into the public listing snapshot. Git commit time is the actual repository delivery time and can follow generation.
- `last_checked_at`, `last_seen_at`, `last_attempt_at`, `last_success_at`: full per-check values live in state/health artifacts. Public JSON omits routine check timestamps to avoid commits on every poll.

Descriptions are inspected locally, not republished. Every candidate is labeled for human review. The list preserves closed postings in JOBS.md and JSON; the README shows open candidates.

## Source failures and closure

Malformed responses and HTTP errors are failed checks, never an empty successful board. Jobs remain unchanged during failures. Omission marks a job pending verification; closure requires at least three successful omissions over at least 30 minutes. Reappearance reopens the job. A source is overdue after 30 minutes without success. The coverage page shows status at its snapshot; use the latest Actions run and its `source-health` artifact for current checks. If the scheduler stops entirely, the public page cannot autonomously update its overdue label; assess snapshot/run age.

## Zero-budget persistence and scheduling

GitHub Actions requests a run every five minutes at minutes 2, 7, 12, and so on. GitHub may delay, drop, or disable schedules (including inactive public repositories); this is best-effort, not a delivery guarantee. Runs serialize through a concurrency group; pending runs can be replaced. SmartRecruiters uses validated pagination (up to 3,000 postings) and fetches details for early-career title candidates; an incomplete page set fails rather than closing jobs. Direct feeds have bounded retries/timeouts and four concurrent checks. No paid services or API keys are required.

Full polling state is stored in Actions cache. Cache entries can be evicted, so this is not durable database storage. Published candidate identities, first-seen and publication timestamps are rebuilt from committed JSON if the cache disappears. Closure counters restart conservatively. Noncandidate detection history can be lost on eviction. The public listing/history in Git is durable; source-health artifacts retain per-run check details for two days. Cache capacity is limited and older snapshots are evicted. Only semantic listing/status changes create public commits.

## Development

Python 3.12 and a trusted system `curl` are sufficient; no Python dependencies. TLS verification stays enabled.

```sh
python3 -m unittest discover -s tests -v
python3 -m tracker.bootstrap
python3 -m tracker.run
```

`--fixtures DIRECTORY` loads `<employer-id>.json` responses for offline replay. `--state PATH` and `--output DIRECTORY` support isolated validation. Employer inventory configuration is in `data/employers.json`. Add only verified direct board slugs; do not label configured or planned employers as monitored before success.

## Manual employer-page backfill

`data/manual-backfill.json` contains public job facts independently checked on official employer pages when an API cannot be verified. These rows carry a manual marker and verification time; they do not increase monitored-employer coverage. After 48 hours they become overdue and leave the open README tables until reverified. Source failures do not extend their freshness. Whatnot’s current official 2027 role was checked on 2026-10-05, while its attempted Ashby API remains failed.

## Company events and social discovery

`data/events.json` contains manually verified organizer pages, event dates, format, cost notes, and verification timestamps. EVENTS.md moves completed events to its history on the next successful run. Event discovery is incomplete and is not a five-minute feed. Confirm the organizer schedule before registering.

Public Instagram stories are discovery leads reviewed in local scheduled checks when browser access is available. Direct employer or organizer pages are required before publication. Expired stories and missed checks cannot be recovered reliably. Local reminders require an awake Mac and running Codex. No inbox contents, application outcomes, personal registration links, or story screenshots are published.

For reused requisitions, `employer_original_posted_at` preserves the old date independently of the current cycle release. Verified employer cohort guidance is recorded in `current_cycle` and `cycle_source`; an old requisition date does not establish when it reopened. Current-cycle release dates remain unknown without dated evidence.

Every live tracker run checks eligible posting URLs, including closed roles, with bounded parallel HTTP GET requests. HTTP 404 closes a listing immediately. A subsequent successful 2xx response containing the role title moves it to verification pending and requires review. Access denials (401/403), throttling, timeouts, and server errors retain the prior link state. Browser-only error screens may require manual confirmation. Link transitions are cached and published; unchanged checks do not create timestamp-only commits.
