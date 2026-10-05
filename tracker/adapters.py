import html
import json
import re
import subprocess
import time


def fetch(url):
    error = None
    for delay in (0, 1, 3):
        time.sleep(delay)
        result = subprocess.run(['curl', '--fail', '--silent', '--show-error', '--location',
                                 '--max-time', '40', '--max-filesize', '50000000', url],
                                capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        error = result.stderr[-500:]
    raise RuntimeError(error)


def plain(value):
    return re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', html.unescape(html.unescape(value or '')))).strip()


def endpoint(source):
    board = source['board']
    if not re.fullmatch(r'[A-Za-z0-9_-]+', board):
        raise ValueError('Invalid board slug')
    return {'greenhouse': f'https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true',
            'lever': f'https://api.lever.co/v0/postings/{board}?mode=json',
            'ashby': f'https://api.ashbyhq.com/posting-api/job-board/{board}'}[source['adapter']]


def normalize(source, payload):
    kind = source['adapter']
    rows = payload if kind == 'lever' else payload['jobs']
    if not isinstance(rows, list):
        raise ValueError('Source jobs must be a list')
    jobs = []
    for row in rows:
        if kind == 'greenhouse':
            job = dict(id=str(row['id']), requisition_id=row.get('requisition_id'),
                       title=row['title'], location=row['location']['name'], countries=[],
                       description=plain(row.get('content')), employment_type='unknown',
                       url=row['absolute_url'], employer_posted_at=None,
                       employer_published_at=row.get('first_published'),
                       employer_updated_at=row.get('updated_at'))
        elif kind == 'lever':
            categories = row.get('categories', {})
            job = dict(id=str(row['id']), requisition_id=None, title=row['text'],
                       location='; '.join(categories.get('allLocations') or [categories.get('location', '')]),
                       countries=[row.get('country', '')],
                       description=plain(row.get('descriptionPlain', '') + ' ' + ' '.join(
                           plain(x.get('content', '')) for x in row.get('lists', []))),
                       employment_type=categories.get('commitment', 'unknown'), url=row['hostedUrl'],
                       employer_posted_at=None, employer_published_at=None, employer_updated_at=None)
        else:
            if not row.get('isListed', True):
                continue
            places = [row] + row.get('secondaryLocations', [])
            countries = []
            for place in places:
                address = place.get('address') or {}
                countries.append(address.get('postalAddress', address).get('addressCountry', ''))
            job = dict(id=str(row['id']), requisition_id=None, title=row['title'],
                       location='; '.join(p.get('location', '') for p in places), countries=countries,
                       description=plain(row.get('descriptionPlain') or row.get('descriptionHtml')),
                       employment_type=row.get('employmentType', 'unknown'), url=row['jobUrl'],
                       employer_posted_at=None, employer_published_at=row.get('publishedAt'),
                       employer_updated_at=None)
        if not job['url'].startswith('https://') or not job['id']:
            raise ValueError('Missing job identity or HTTPS source link')
        job['source'] = kind
        jobs.append(job)
    if len({j['id'] for j in jobs}) != len(jobs):
        raise ValueError('Duplicate source identifiers')
    return jobs


def fetch_source(source):
    if source['adapter'] != 'smartrecruiters':
        return normalize(source, fetch(endpoint(source)))
    board = source['board']
    if not re.fullmatch(r'[A-Za-z0-9_-]+', board):
        raise ValueError('Invalid company slug')
    rows = []
    expected = None
    for offset in range(0, 3000, 100):
        page = fetch(f'https://api.smartrecruiters.com/v1/companies/{board}/postings?limit=100&offset={offset}')
        expected = page['totalFound'] if expected is None else expected
        batch = page['content']
        if not isinstance(batch, list):
            raise ValueError('Invalid postings response')
        rows.extend(batch)
        if len(rows) >= expected:
            break
        if not batch:
            raise ValueError('Incomplete pagination')
    if len(rows) < expected or len({row['id'] for row in rows}) != len(rows):
        raise ValueError('Incomplete or inconsistent pagination')
    jobs = []
    for row in rows:
        title = row['name']
        if not re.search(r'new.?grad|graduate|early.?career|entry.?level|engineer[ ,]+i\b|2027', title, re.I):
            continue
        detail = fetch(f"https://api.smartrecruiters.com/v1/companies/{board}/postings/{row['id']}")
        location = detail['location']
        description = ' '.join(plain(v.get('text', '')) for v in detail['jobAd']['sections'].values() if isinstance(v, dict))
        jobs.append(dict(id=str(row['id']), requisition_id=row.get('refNumber'), title=title,
                         location=location.get('fullLocation') or ', '.join(location.get(k, '') for k in ('city', 'region', 'country')),
                         countries=[location.get('country', '')], description=description,
                         employment_type=detail.get('typeOfEmployment', {}).get('label', 'unknown'),
                         url=detail['applyUrl'], source='smartrecruiters', employer_posted_at=None,
                         employer_published_at=detail.get('releasedDate'), employer_updated_at=None))
    return jobs
