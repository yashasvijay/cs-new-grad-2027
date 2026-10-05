from tracker.run import cell


def render(view, now):
    open_jobs = [j for j in view['jobs'] if j['status'].startswith('open')]
    monitored = sum(e['coverage'] == 'monitored' for e in view['coverage'])
    confirmed = [j for j in open_jobs if j['eligibility'].startswith('2027')]
    general = [j for j in open_jobs if j not in confirmed]
    lines = ['<div align="center">', '', '# yashavijay - CS New Grad', '',
             '**U.S. new-grad roles and company events. Direct links. Clear status.**', '',
             '[![Update jobs](https://github.com/yashasvijay/cs-new-grad-2027/actions/workflows/update.yml/badge.svg)](https://github.com/yashasvijay/cs-new-grad-2027/actions/workflows/update.yml)', '',
             f'**{len(open_jobs)} open candidates** · **{len(confirmed)} mention 2027** · **{monitored} employers checked successfully**', '',
             '[Open roles](#open-roles) · [Closed roles](#closed-roles) · [Company events](EVENTS.md) · [Coverage](COVERAGE.md) · [How it works](docs/METHODOLOGY.md)', '',
             '</div>', '', '---', '',
             'A public tracker for full-time U.S. CS new-grad jobs in the 2027 cycle, plus virtual and in-person company events. Jobs come from employer career pages and refresh on a best-effort five-minute schedule; events are manually curated.', '',
             '**Read before applying:** “2027 mentioned” is a screening signal, not a guarantee of eligibility. Check graduation dates, experience, sponsorship, citizenship, and start dates on the employer page. General new-grad roles may not accept 2027 graduates.', '',
             f'Listing snapshot: **{now[:10]} {now[11:16]} UTC**. [Latest source checks](https://github.com/yashasvijay/cs-new-grad-2027/actions/workflows/update.yml) are recorded per run; this date changes only when the public list or source status changes.', '']
    from tracker.presentation import release_order, button
    groups = [('Open roles', open_jobs), ('Verification pending', [j for j in view['jobs'] if not j['status'].startswith('open') and j['status'] != 'closed']), ('Closed roles', [j for j in view['jobs'] if j['status'] == 'closed'])]
    lines += ['**Order:** open roles first, then verification pending, then 🔒 closed roles. Each group is newest employer release first; unknown release dates follow dated postings. Publication dates can reflect republication.', '']
    for heading, jobs in groups:
        lines += [f'## {heading}', '', '<table>', '<thead><tr><th>Company</th><th>Role</th><th>Location</th><th>Eligibility / notes</th><th width="100">Apply</th><th>Released</th></tr></thead>', '<tbody>']
        for j in release_order(jobs):
            date = (j.get('employer_published_at') or j.get('employer_posted_at') or '')[:10] or ('Release unknown<br>First seen ' + j['first_seen_at'][:10])
            notes = cell(j.get('eligibility_note') or j['eligibility'])
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
