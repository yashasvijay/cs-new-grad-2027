import json
from pathlib import Path


def seed(state, path=Path('data/manual-backfill.json')):
    if not path.exists():
        return
    for job in json.loads(path.read_text())['jobs']:
        key = job['employer_id'] + ':' + str(job.get('requisition_id') or job['id'])
        old = state['jobs'].get(key, {})
        if old and (old.get('verification_mode') != 'manual' or old.get('manual_verified_at', '') >= job['manual_verified_at']):
            continue
        state['jobs'][key] = dict(job, first_seen_at=old.get('first_seen_at', job['manual_verified_at']),
            tracker_published_at=old.get('tracker_published_at'), last_seen_at=job['manual_verified_at'],
            last_checked_at=job['manual_verified_at'], missing_checks=0, status='open — manually verified',
            verification_mode='manual', source_links=[job['url']])
