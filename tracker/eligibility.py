import re

US = re.compile(r'\b(?:united states|usa|u\.s\.|san francisco|new york|seattle|boston|austin|palo alto|mountain view|menlo park|sunnyvale|san jose|los angeles|chicago|washington,? dc)\b|,\s*(?:AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b', re.I)
CS = re.compile(r'\b(?:software|firmware|ai engineer|ai research scientist|machine learning|data scien|data engineer|computer|cyber|security engineer|cloud engineer|systems engineer|research engineer|applied scientist|developer)')
ENTRY = re.compile(r'\b(?:new (?:college )?grad(?:uate)?|recent grad(?:uate)?|university grad(?:uate)?|entry[ -]level|early career|graduate engineer|engineer i)\b')


def classify(job):
    if job.get('_recovered'):
        return {k: job[k] for k in ('eligibility', 'employment', 'evidence', 'review_required')}
    title = job['title'].lower()
    text = title + ' ' + job['description'].lower()
    countries = [c.lower() for c in job.get('countries', []) if c]
    if countries:
        domestic = any(c in ('us', 'usa', 'united states', 'united states of america') for c in countries)
    else:
        domestic = bool(US.search(job['location']))
    domestic = domestic or (not countries and bool(re.search(r',\s*(?:Virginia|California|New York|Washington|Massachusetts|Texas|Illinois|Maryland|Florida|Colorado|North Carolina|Georgia|Pennsylvania|Michigan|Ohio|Utah|Oregon)\b', job['location'], re.I)))
    cs_role = bool(CS.search(title)) or (bool(re.search(r'\b(?:associate|application) engineer\b', title)) and bool(re.search(r'computer science|software engineering', text)))
    if not domestic or not cs_role:
        return None
    employment = job['employment_type'].lower().replace('-', '').replace(' ', '')
    if employment not in ('fulltime', 'unknown'):
        return None
    if re.search(r'\b(intern(?:ship)?|co[ -]?op|contract(?:or)?|part[ -]time|temporary)\b', title):
        return None
    if re.search(r'\b(senior|sr\.?|staff|principal|director|manager|lead)\b', title):
        return None
    experience = re.findall(r'\b(\d+)\s*(?:\+|(?:-|–|to)\s*\d+)?\s*years? (?:of )?(?:relevant |professional |industry |software |engineering |work )?experience', text)
    if any(int(n) > 2 for n in experience):
        return None
    graduation = re.search(r'(?:graduat\w*(?:(?!start|join|begin|full.time by)[^.;]){0,100}2027|2027[^.;]{0,60}graduat\w*)', text)
    if re.search(r'\b202[4-6]\b', title) and '2027' not in title and not graduation:
        return None
    if '2027' in title and ENTRY.search(title):
        graduation = re.search(r'.+', title)
    other_window = re.search(r'graduat\w*[^.;]{0,80}20(?:2[4-689]|3\d)', text)
    if other_window and not graduation:
        return None
    if not graduation and not ENTRY.search(text):
        return None
    fulltime = employment == 'fulltime' or bool(re.search(r'\bfull[ -]time\b', text))
    evidence = graduation.group(0) if graduation else ENTRY.search(text).group(0)
    return {'eligibility': '2027 mentioned — review requirements' if graduation else 'general entry-level — review 2027 eligibility',
            'employment': 'full-time' if fulltime else 'full-time unverified — review',
            'evidence': evidence[:180], 'review_required': True}
