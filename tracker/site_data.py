import argparse
import json
from pathlib import Path

from tracker.readme import normalize_location


def display_data(view):
    jobs = []
    for job in view['jobs']:
        released = job.get('employer_published_at') or job.get('employer_posted_at')
        jobs.append({
            'id': job.get('employer_id', '') + ':' + str(job.get('id', '')),
            'company': job.get('employer') or None,
            'title': job.get('title') or None,
            'locations': [normalize_location(part) for part in (job.get('location') or '').split(';') if part.strip()] or None,
            'notes': job.get('eligibility_note') or None,
            'apply_url': job.get('url') or None,
            'date': released or job.get('first_seen_at') or None,
            'date_kind': 'Released' if released else ('First seen' if job.get('first_seen_at') else None),
            'section': job.get('listing_section') or None,
            'status': job.get('status') or None,
            'full_time_unverified': (job.get('employment') or '').startswith('full-time unverified'),
            'manual_check': job.get('verification_mode') == 'manual',
            'deadline': job.get('deadline') or None,
            'sponsorship': job.get('sponsorship') or None,
            'citizenship': job.get('citizenship') or None,
            'degree_level': job.get('degree_level') or None,
        })
    return {'snapshot_at': view.get('snapshot_at'), 'jobs': jobs}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=Path('data/listings.json'))
    parser.add_argument('--output', type=Path, default=Path('site/data.json'))
    args = parser.parse_args()
    data = display_data(json.loads(args.input.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')


if __name__ == '__main__':
    main()
