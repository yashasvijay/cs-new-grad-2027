from tracker.run import cell
from tracker.sections import annotate
from html import escape
import re


STATES = dict(zip(
    'Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|District of Columbia'.split('|'),
    'AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY DC'.split()))


def normalize_location(location):
    original = location.strip()
    campus = re.match(r'^US-([A-Z]{2})-([A-Z][A-Z -]+)-[A-Z]+\d+(?:\s*~|$)', original)
    if campus and campus[1] in STATES.values():
        return f'{campus[2].title()}, {campus[1]}'
    parts = [part.strip() for part in original.split(',')]
    if parts[-1].lower() in ('us', 'usa', 'united states', 'united states of america'):
        parts = parts[:-1]
    if len(parts) >= 2:
        city, state = parts[-2:]
        state = STATES.get(state, state)
        if state in STATES.values() and re.fullmatch(r"[A-Za-z][A-Za-z .'-]*", city):
            return f'{city}, {state}'
    return original


def location_cell(location):
    locations = [normalize_location(part) for part in (location or '').split(';') if part.strip()]
    locations = [escape(part, quote=False).replace('|', '&#124;').replace('\r', ' ').replace('\n', ' ') for part in locations]
    if len(locations) < 3:
        return '; '.join(locations)
    return f'<details><summary>{len(locations)} locations</summary>' + '<br>'.join(locations) + '</details>'


def render(view, now):
    jobs = annotate(view['jobs'])
    monitored = sum(e['coverage'] == 'monitored' for e in view['coverage'])
    confirmed = [j for j in jobs if j['listing_section'] == 'new_grad_2027']
    general = [j for j in jobs if j['listing_section'] == 'general_early_career']
    secondary = [j for j in jobs if j['listing_section'] == 'secondary']
    lines = ['<div align="center">', '', '# yashasvijay - C.S. New Grad', '',
             'Full-time U.S. CS roles for the 2027 graduating class.<br>',
             'Jobs are sourced from public employer career pages.<br>',
             'Company events include virtual, in-person, and hybrid formats.', '',
             '> Screenshot placeholder — a preview will be added after the site is built.', '',
             '> Site link placeholder — the tracker link will be added after Phase 2.', '',
             '</div>', '', '---', '']
    from tracker.presentation import release_order, listing_order, button
    groups = [('2027 new-grad roles', confirmed), ('General early career · SWE / SDE I', general), ('Secondary listings', secondary)]
    lines += ['## Open roles', '', '### 2027 new-grad roles', '', 'These postings mention 2027 graduation or start dates. Review the employer’s exact requirements.', '']
    for heading, jobs in groups:
        level = '##' if heading == 'Secondary listings' else '###'
        heading_lines = [] if heading == '2027 new-grad roles' else [f'{level} {heading}', '']
        if heading == 'General early career · SWE / SDE I':
            heading_lines += ['General new-grad and early-career postings; 2027 eligibility is unconfirmed.', '']
        if heading == 'Secondary listings':
            heading_lines += ['Reused requisitions with unverified release dates, PhD-only roles, verification-pending roles, and closed postings are retained here and in the full listing file.', '',
                              f'<details><summary>Show {len(jobs)} secondary listings</summary>', '']
        lines += heading_lines + ['<table>', '<thead><tr><th>Company</th><th>Role</th><th>Location</th><th>Notes</th><th width="100">Apply</th><th>Released</th></tr></thead>', '<tbody>']
        ordered = listing_order(jobs) if heading == 'Secondary listings' else release_order(jobs)
        for j in ordered:
            date = (j.get('employer_published_at') or j.get('employer_posted_at') or '')[:10] or ('Release unknown<br>First seen ' + j['first_seen_at'][:10])
            note = j.get('eligibility_note', '')
            note = {
                'Entry-level requirements reviewed; 2027 eligibility unconfirmed': '',
                'Degree by August 2027; Seattle; no sponsorship.': 'Degree by August 2027; no sponsorship.',
                'PhD required; 2027 full-time start.': 'PhD required.',
                '2027 new college graduate; historical posting, current availability unverified.': 'Historical posting; availability unverified.',
                '2027 start; degree by December 2026. Included by explicit request.': 'February start; degree by December 2026.',
                'August 2027 start; review degree and work authorization requirements.': 'August 2027 start.',
            }.get(note, note)
            if heading == 'Secondary listings':
                reasons = {'closed': 'Closed', 'verification_pending': 'Verification pending',
                           'phd_only': 'PhD-only', 'reused_release_unverified': 'Reused requisition; release unverified'}
                reason_notes = [reasons[r] for r in j['secondary_reasons']]
                duplicate_reuse_note = note == 'Reused requisition; current-cycle release date unverified.'
                note = '; '.join(reason_notes + ([note] if note and not duplicate_reuse_note else []))
            notes = cell(note)
            marker = '🔒 ' if j['status'] == 'closed' else ''
            lines.append(f"<tr><td><strong>{cell(j['employer'])}</strong></td><td>{marker}{cell(j['title'])}{' ⚠️' if j['employment'].startswith('full-time unverified') else ''}{' 📝' if j.get('verification_mode') == 'manual' else ''} </td><td>{location_cell(j['location'])}</td><td>{notes}</td><td width=100 nowrap>{button(j)}</td><td>{date}</td></tr>")
        lines += ['</tbody></table>', '']
        if not jobs:
            lines += ['', 'No listings in this group yet.']
        if heading == 'Secondary listings':
            lines += ['</details>', '', '[Full listing history and timestamps](JOBS.md) · [Machine-readable listings](data/listings.json)', '']
        lines += ['']
    from tracker.events import upcoming_rows
    lines += ['## Company events', '', 'Virtual, in-person, and hybrid events from company organizers. Event dates are separate from job release dates. Check registration, cost, and eligibility before attending.', '', '| Company | Event | Dates | Format | Location | Cost | Link |', '|---|---|---|---|---|---|:---:|']
    lines += upcoming_rows(now)
    lines += ['', '[Full event list and history](EVENTS.md) · [Event data](data/events.json)', '']
    lines += ['## Coverage', '',
              f'{len(view["coverage"])} employers in the inventory; {monitored} have had a successful source check. Inventory entries do not imply complete monitoring.', '',
              '[Employer coverage and failures](COVERAGE.md) · [Methodology and status definitions](docs/METHODOLOGY.md)', '',
              '## Contribute', '',
              '[Contributing guidelines](CONTRIBUTING.md) · [Suggest a posting](https://github.com/yashasvijay/cs-new-grad-2027/issues/new)', '',
              '## About', '',
              'Jobs refresh on a best-effort five-minute GitHub Actions schedule; events are manually curated. Eligibility and release dates require review. Each section is newest release first, with unknown dates last and closed secondary listings at the bottom.', '',
              '📝 Manual checks expire after 48 hours. ⚠️ Full-time status is unverified. See the methodology for closure and eligibility rules.', '',
              f'Listing snapshot: **{now[:10]} {now[11:16]} UTC**. [Latest source checks](https://github.com/yashasvijay/cs-new-grad-2027/actions/workflows/update.yml).', '',
              '[![Update jobs](https://github.com/yashasvijay/cs-new-grad-2027/actions/workflows/update.yml/badge.svg)](https://github.com/yashasvijay/cs-new-grad-2027/actions/workflows/update.yml)', '',
              'Visual structure inspired by [Simplify](https://github.com/SimplifyJobs/New-Grad-Positions) and [Vansh](https://github.com/vanshb03/New-Grad-2027). [Sources and attribution](docs/SOURCES.md).', '',
              'Listings are sourced from public employer career pages and remain the property of their respective employers. The MIT license covers this repository\'s code, not the listings.', '',
              '[MIT license](LICENSE)', '']
    from tracker.presentation import decorate_links
    return decorate_links('\n'.join(lines))
