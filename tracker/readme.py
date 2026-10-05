from tracker.run import cell


def render(view, now):
    open_jobs = [j for j in view['jobs'] if j['status'].startswith('open')]
    monitored = sum(e['coverage'] == 'monitored' for e in view['coverage'])
    confirmed = [j for j in open_jobs if j['eligibility'].startswith('2027')]
    general = [j for j in open_jobs if j not in confirmed]
    lines = ['<div align="center">', '', '# yashasvijay - C.S. New Grad', '',
             '**U.S. new-grad roles and company events. Direct links. Clear status.**', '',
             '[![Update jobs](https://github.com/yashasvijay/cs-new-grad-2027/actions/workflows/update.yml/badge.svg)](https://github.com/yashasvijay/cs-new-grad-2027/actions/workflows/update.yml)', '',
             f'**{len(open_jobs)} open candidates** · **{len(confirmed)} mention 2027** · **{monitored} employers checked successfully**', '',
             '[2027 roles](#2027-new-grad-roles) · [General early career](#general-early-career--swe--sde-i) · [Closed roles](#closed-roles) · [Company events](EVENTS.md) · [Coverage](COVERAGE.md) · [How it works](docs/METHODOLOGY.md)', '',
             '</div>', '', '---', '',
             'A public tracker for full-time U.S. CS new-grad jobs in the 2027 cycle, plus virtual and in-person company events. Jobs come from employer career pages and refresh on a best-effort five-minute schedule; events are manually curated.', '',
             '**Read before applying:** “2027 mentioned” is a screening signal, not a guarantee of eligibility. Check graduation dates, experience, sponsorship, citizenship, and start dates on the employer page. General new-grad roles may not accept 2027 graduates.', '',
             f'Listing snapshot: **{now[:10]} {now[11:16]} UTC**. [Latest source checks](https://github.com/yashasvijay/cs-new-grad-2027/actions/workflows/update.yml) are recorded per run; this date changes only when the public list or source status changes.', '']
    from tracker.presentation import release_order, button
    groups = [('2027 new-grad roles', confirmed), ('General early career · SWE / SDE I', general), ('Verification pending', [j for j in view['jobs'] if not j['status'].startswith('open') and j['status'] != 'closed']), ('Closed roles', [j for j in view['jobs'] if j['status'] == 'closed'])]
    lines += ['**Order:** open roles first, then verification pending, then 🔒 closed roles. Each group is newest employer release first; unknown release dates follow dated postings. Publication dates can reflect republication.', '']
    lines += ['## Open roles', '', '### 2027 new-grad roles', '', 'These postings mention 2027 graduation or start dates. Review the employer’s exact requirements.', '']
    for heading, jobs in groups:
        level = '###' if heading in ('2027 new-grad roles', 'General early career · SWE / SDE I') else '##'
        heading_lines = [] if heading == '2027 new-grad roles' else [f'{level} {heading}', '']
        if heading == 'General early career · SWE / SDE I':
            heading_lines += ['General new-grad and early-career postings; 2027 eligibility is unconfirmed.', '']
        lines += heading_lines + ['<table>', '<thead><tr><th>Company</th><th>Role</th><th>Location</th><th>Notes</th><th width="100">Apply</th><th>Released</th></tr></thead>', '<tbody>']
        for j in release_order(jobs):
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
            notes = cell(note)
            marker = '🔒 ' if j['status'] == 'closed' else ''
            lines.append(f"<tr><td><strong>{cell(j['employer'])}</strong></td><td>{marker}{cell(j['title'])}{' ⚠️' if j['employment'].startswith('full-time unverified') else ''}{' 📝' if j.get('verification_mode') == 'manual' else ''} </td><td>{cell(j['location'])}</td><td>{notes}</td><td width=100 nowrap>{button(j)}</td><td>{date}</td></tr>")
        lines += ['</tbody></table>', '']
        if not jobs:
            lines += ['', 'No listings in this group yet.']
        lines += ['']
    lines += ['## Coverage, without the guesswork', '',
              f'{len(view["coverage"])} employers in the inventory; {monitored} have had a successful source check. Most S&P 500 candidates are **planned**, including several major technology employers. An employer in the inventory does not mean its jobs are monitored.', '',
              '🟢 **Open** — present in a successful employer feed. 📝 marks a manual employer-page check that expires after 48 hours.<br>',
              '🟡 **Review** — eligibility needs confirmation. ⚠️ marks full-time status unverified.<br>',
              '🔒 **Closed** — missing in at least three successful checks over at least 30 minutes.', '',
              '[Full listing history and timestamps](JOBS.md) · [Employer coverage and failures](COVERAGE.md) · [Machine-readable listings](data/listings.json)', '',
              '## Contribute', '',
              'Found a role or missing employer? [Open an issue](https://github.com/yashasvijay/cs-new-grad-2027/issues/new) with the direct employer link. Please keep personal application statuses private. See [contributing](CONTRIBUTING.md).', '',
              '## About', '',
              '**Job Application Tracker Platform** is built at a $0 hosting budget using public GitHub Actions. Schedules can be delayed or skipped; coverage is incomplete. Employer publication dates may describe republication, and are unknown when the feed does not provide them.', '',
              'Visual structure inspired by [Simplify](https://github.com/SimplifyJobs/New-Grad-Positions) and [Vansh](https://github.com/vanshb03/New-Grad-2027). Job records are verified against employer feeds. [Sources and attribution](docs/SOURCES.md).', '']
    from tracker.events import upcoming_rows
    lines += ['## Company events', '', 'Virtual, in-person, and hybrid events from company organizers. Event dates are separate from job release dates. Check registration, cost, and eligibility before attending.', '', '| Company | Event | Dates | Format | Location | Cost | Link |', '|---|---|---|---|---|---|:---:|']
    lines += upcoming_rows(now)
    lines += ['', '[Full event list and history](EVENTS.md) · [Event data](data/events.json)', '']
    from tracker.presentation import decorate_links
    return decorate_links('\n'.join(lines))
