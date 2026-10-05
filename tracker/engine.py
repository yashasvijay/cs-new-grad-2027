import copy
from datetime import datetime, timedelta, timezone


def overdue(health, now):
    last = health.get('last_success_at')
    return not last or datetime.fromisoformat(now) - datetime.fromisoformat(last) > timedelta(minutes=30)


def reconcile(state, employer, jobs, now, error=None):
    state.setdefault('jobs', {})
    health = state.setdefault('health', {}).setdefault(employer['id'], {})
    health['last_attempt_at'] = now
    if error is not None:
        health.update(status='failed', error=str(error)[:500])
        return
    health.update(status='healthy', error=None, last_success_at=now, source_job_count=len(jobs))
    seen = set()
    for job in jobs:
        identity = str(job.get('requisition_id') or job['id'])
        key = employer['id'] + ':' + identity
        seen.add(key)
        if job.get('_unavailable'):
            continue
        old = state['jobs'].get(key, {})
        job = dict(job, source_links=sorted(set(old.get('source_links', []) + [job['url']])))
        state['jobs'][key] = dict(job, employer=employer['name'], employer_id=employer['id'],
                                 first_seen_at=old.get('first_seen_at', now),
                                 tracker_published_at=old.get('tracker_published_at'),
                                 last_seen_at=now, last_checked_at=now, missing_checks=0, status='open')
    for key, job in state['jobs'].items():
        if job['employer_id'] != employer['id'] or key in seen:
            continue
        job['last_checked_at'] = now
        if job['status'] == 'closed':
            continue
        job['missing_checks'] += 1
        job.setdefault('first_missing_at', now)
        if job['missing_checks'] >= 3 and datetime.fromisoformat(now) - datetime.fromisoformat(job['first_missing_at']) >= timedelta(minutes=30):
            job['status'] = 'closed'
        else:
            job['status'] = 'missing — verification pending'
    for key in seen:
        if key in state['jobs']:
            state['jobs'][key].pop('first_missing_at', None)


def public_view(state, employers, now, classify):
    listings = []
    for key, job in sorted(state.get('jobs', {}).items()):
        if job.get('verification_mode') == 'manual' and job['status'] != 'closed':
            expired = datetime.fromisoformat(now) - datetime.fromisoformat(job['manual_verified_at']) > timedelta(hours=48)
            job['status'] = 'verification overdue — manually checked' if expired else job.get('manual_status', 'open — manually verified')
        eligibility = classify(job)
        if not eligibility:
            continue
        if not job.get('tracker_published_at'):
            job['tracker_published_at'] = now
        item = {k: v for k, v in job.items() if k not in ('_recovered', 'description', 'countries', 'missing_checks', 'first_missing_at', 'last_seen_at', 'last_checked_at')}
        item.update(eligibility)
        listings.append(item)
    coverage = []
    for employer in employers:
        health = state.get('health', {}).get(employer['id'], {})
        coverage.append(dict(id=employer['id'], name=employer['name'],
                             coverage='monitored' if health.get('last_success_at') else ('configured' if employer.get('source') else 'planned'),
                             health=health.get('status', 'not checked'), verification_overdue=overdue(health, now),
                             source=employer.get('source'), error=health.get('error')))
    from tracker.presentation import listing_order
    return {'jobs': listing_order(listings), 'coverage': coverage}
