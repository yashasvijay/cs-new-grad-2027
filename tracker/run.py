import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
from pathlib import Path

from tracker.adapters import endpoint, fetch, normalize, fetch_source
from tracker.eligibility import classify
from tracker.engine import public_view, reconcile


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)


def cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ').replace('[', '').replace(']', '').replace('<', '&lt;').replace('>', '&gt;')


def render(view, now):
    rows = ['# U.S. CS New-Grad Jobs · 2027', '',
            'Automated candidate listings. Every listing requires review of the employer’s requirements.', '',
            f'Listing snapshot: {now}. See [coverage](COVERAGE.md) and the latest Actions run for live check timestamps.', '',
            '| Employer | Role | Location | Eligibility | Employment | Status | First seen | Employer published | Tracker published | Apply |',
            '|---|---|---|---|---|---|---|---|---|---|']
    from tracker.presentation import listing_order, button, decorate_links
    for job in listing_order(view['jobs']):
        rows.append('| ' + ' | '.join([cell(job['employer']), cell(job['title']), cell(job['location']), cell(job['eligibility']), cell(job['employment']), cell(('🔒 ' if job['status'] == 'closed' else '') + job['status']), job['first_seen_at'], job.get('employer_published_at') or 'unknown', job['tracker_published_at'], button(job)]) + ' |')
    if not view['jobs']:
        rows += ['', 'No candidates passed the current conservative filters. This does not mean no suitable jobs exist.']
    return decorate_links('\n'.join(rows) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--fixtures', type=Path)
    parser.add_argument('--state', type=Path, default=Path('.state/state.json'))
    parser.add_argument('--output', type=Path, default=Path('.'))
    args = parser.parse_args()
    employers = json.loads(Path('data/employers.json').read_text())['employers']
    state = json.loads(args.state.read_text()) if args.state.exists() else {'jobs': {}, 'health': {}}
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    configured = [e for e in employers if e.get('source')]
    def check(employer):
        try:
            jobs = normalize(employer['source'], json.loads((args.fixtures / (employer['id'] + '.json')).read_text())) if args.fixtures else fetch_source(employer['source'])
            return employer, jobs, None
        except Exception as error:
            return employer, [], str(error)
    with ThreadPoolExecutor(max_workers=4) as pool:
        for employer, jobs, error in pool.map(check, configured):
            reconcile(state, employer, jobs, now, error)
            print(f"{employer['name']}: {'FAILED ' + error if error else str(len(jobs)) + ' source jobs'}")
    from tracker.manual import seed
    seed(state)
    dates_path = Path('data/backfill-dates.json')
    if dates_path.exists():
        for key, metadata in json.loads(dates_path.read_text())['jobs'].items():
            if key in state['jobs'] and not state['jobs'][key].get('employer_published_at'):
                state['jobs'][key].update(metadata)
    view = public_view(state, employers, now, classify)
    from tracker.events import render as render_events
    (args.output / 'EVENTS.md').write_text(render_events(Path('data/events.json'), now))
    destination = args.output / 'data/listings.json'
    previous = json.loads(destination.read_text()) if destination.exists() else None
    comparable = {k: v for k, v in (previous or {}).items() if k != 'snapshot_at'}
    changed = view != comparable
    snapshot = now if changed else previous['snapshot_at']
    if changed:
        save(destination, dict(view, snapshot_at=now))
    (args.output / 'JOBS.md').write_text(render(view, snapshot))
    from tracker.readme import render as render_readme
    (args.output / 'README.md').write_text(render_readme(view, snapshot))
    if changed:
        coverage = ['# Employer coverage', '', f'Snapshot: {now}. Planned employers are not monitored. Current check timestamps are in the latest Actions health artifact.', '', '| Employer | Coverage | Source health | Overdue at snapshot |', '|---|---|---|---|']
        coverage += [f"| {cell(e['name'])} | {e['coverage']} | {cell(e['health'])} | {e['verification_overdue']} |" for e in view['coverage']]
        (args.output / 'COVERAGE.md').write_text('\n'.join(coverage) + '\n')
    save(args.state, state)
    save(Path('.state/health.json'), {'checked_at': now, 'sources': state['health']})
    print(f"{len(configured)} configured employers; {len(view['jobs'])} candidate listings")
    if configured and all(state['health'][e['id']]['status'] == 'failed' for e in configured):
        raise SystemExit('All sources failed; existing listings retained')


if __name__ == '__main__':
    main()
