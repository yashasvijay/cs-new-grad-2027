import html
import json
import re
import subprocess
import time


def fetch(url, body=None, raw=False):
    error = None
    for delay in (0, 1, 3):
        time.sleep(delay)
        command = ['curl', '--fail', '--silent', '--show-error', '--location',
                   '--max-time', '40', '--max-filesize', '50000000', url]
        if body is not None:
            command += ['-H', 'Content-Type: application/json', '--data', json.dumps(body)]
        result = subprocess.run(command,
                                capture_output=True, text=True)
        if result.returncode == 0:
            return result.stdout if raw else json.loads(result.stdout)
        error = result.stderr[-500:]
    raise RuntimeError(error)


def plain(value):
    return re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', html.unescape(html.unescape(value or '')))).strip()


def endpoint(source):
    board = source['board']
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', board):
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
    if source['adapter'] == 'multi':
        jobs = [job for board in source['boards'] for job in fetch_source(board)]
        return list({str(j.get('requisition_id') or j['id']):j for j in jobs}.values())
    if source['adapter'] == 'jsonld':
        return [jsonld_job(entry, fetch(entry['url'], raw=True)) for entry in source['postings']]
    if source['adapter'] == 'workday':
        return fetch_workday(source)
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


def jsonld_job(entry, page):
    matches = re.findall(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', page, re.S | re.I)
    records = [json.loads(value) for value in matches]
    rows = [item for record in records for item in (record if isinstance(record, list) else record.get('@graph', [record])) if item.get('@type') == 'JobPosting']
    if len(rows) != 1:
        raise ValueError('Expected one public JobPosting record')
    row = rows[0]
    places = row.get('jobLocation', [])
    if isinstance(places, dict):
        places = [places]
    addresses = [p.get('address', {}) for p in places]
    countries = [a.get('addressCountry', '') for a in addresses]
    countries = [c.get('name', '') if isinstance(c, dict) else c for c in countries]
    employment = row.get('employmentType', 'unknown')
    if isinstance(employment, list):
        employment = employment[0] if len(employment) == 1 else 'unknown'
    return dict(id=entry['id'], requisition_id=entry.get('requisition_id'), title=row['title'],
                location='; '.join(', '.join(a.get(k, '') for k in ('addressLocality', 'addressRegion')) for a in addresses),
                countries=countries, description=plain(row['description']),
                employment_type=employment.replace('_', ''), url=entry['url'], source='employer JSON-LD',
                employer_posted_at=None, employer_published_at=row.get('datePosted'), employer_updated_at=None,
                entry_role_verified=entry.get('entry_role_verified', False), eligibility_note=entry.get('eligibility_note'))


def workday_job(row):
    info = row['jobPostingInfo']
    if info.get('posted') is False:
        return None
    return dict(id=info['id'], requisition_id=info['jobReqId'], title=info['title'],
                location='; '.join([info.get('location', '')] + info.get('additionalLocations', [])),
                countries=[info.get('country', {}).get('descriptor', '')],
                description=plain(info['jobDescription']), employment_type=info.get('timeType', 'unknown'),
                url=info['externalUrl'], source='workday', employer_posted_at=None,
                employer_published_at=info.get('startDate'), employer_updated_at=None)


def fetch_workday(source):
    host, tenant, board = source['host'], source['tenant'], source['board']
    if not re.fullmatch(r'[a-z0-9-]+\.wd\d+\.myworkdayjobs\.com', host) or not all(re.fullmatch(r'[A-Za-z0-9_-]+', value) for value in (tenant, board)):
        raise ValueError('Invalid Workday source')
    base = f'https://{host}/wday/cxs/{tenant}/{board}'
    rows = {}
    for query in source.get('queries', ['2027', 'new grad', 'early career']):
        total = None
        collected = []
        for offset in range(0, 3000, 20):
            page = fetch(base + '/jobs', {'appliedFacets':{}, 'limit':20, 'offset':offset, 'searchText':query})
            total = page['total'] if total is None else total
            batch = page['jobPostings']
            if not isinstance(batch, list):
                raise ValueError('Invalid Workday postings response')
            collected.extend(batch)
            if len(collected) >= total:
                break
            if not batch:
                raise ValueError('Incomplete Workday pagination')
        if len(collected) < total or len({r.get('externalPath') or tuple(r['bulletFields']) for r in collected}) != len(collected):
            raise ValueError('Incomplete or inconsistent Workday pagination')
        rows.update({r.get('externalPath') or r['bulletFields'][0]:r for r in collected})
    jobs = []
    for path, row in rows.items():
        if not row.get('externalPath'):
            jobs.append(dict(id=row['bulletFields'][0], requisition_id=row['bulletFields'][0], _unavailable=True))
            continue
        if not path.startswith('/job/') or '?' in path or '..' in path:
            raise ValueError('Invalid Workday posting path')
        title = row['title']
        if re.search(r'\bintern|\bco[ -]?op|\bsenior|\bstaff|\bprincipal|\bmanager', title, re.I):
            continue
        if not re.search(r'software|firmware|data engineer|machine learning|security engineer|site reliability|technology development', title, re.I):
            continue
        detail = workday_job(fetch(base + path))
        if detail:
            jobs.append(detail)
    return jobs
