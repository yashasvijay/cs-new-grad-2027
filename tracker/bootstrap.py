import json
from pathlib import Path
from tracker.run import save


def main():
    target = Path('.state/state.json')
    published = Path('data/listings.json')
    if target.exists() or not published.exists():
        return
    view = json.loads(published.read_text())
    state = {'jobs': {}, 'health': {}}
    for job in view['jobs']:
        identity = str(job.get('requisition_id') or job['id'])
        state['jobs'][job['employer_id'] + ':' + identity] = dict(job, description='', countries=[],
            employment_type='unknown', _recovered=True, missing_checks=0, last_seen_at=job['first_seen_at'])
    save(target, state)
    print('State cache unavailable; preserved published identities and first-seen timestamps. Source checks will rebuild metadata.')


if __name__ == '__main__':
    main()
