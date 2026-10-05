from tracker.run import cell


def render(view, now):
    open_jobs = [j for j in view['jobs'] if j['status'].startswith('open')]
    monitored = sum(e['coverage'] == 'monitored' for e in view['coverage'])
    confirmed = [j for j in open_jobs if j['eligibility'].startswith('2027')]
    general = [j for j in open_jobs if j not in confirmed]
    lines = ['<div align="center">', '', '# CS New Grad · 2027', '',
             '**U.S. roles. Direct employer links. A clearer view of what’s open.**', '',
             '[![Update jobs](https://github.com/yashasvijay/cs-new-grad-2027/actions/workflows/update.yml/badge.svg)](https://github.com/yashasvijay/cs-new-grad-2027/actions/workflows/update.yml)', '',
             f'**{len(open_jobs)} open candidates** · **{len(confirmed)} mention 2027** · **{monitored} employers checked successfully**', '',
             '[2027 roles](#2027-mentioned) · [Other new-grad roles](#general-new-grad--early-career) · [Company events](EVENTS.md) · [Coverage](COVERAGE.md) · [How it works](docs/METHODOLOGY.md)', '',
             '</div>', '', '---', '',
             'A public list of full-time CS roles for the 2027 graduating class. Sourced from employer job boards and refreshed on a best-effort five-minute schedule.', '',
             '**Read before applying:** “2027 mentioned” is a screening signal, not a guarantee of eligibility. Check graduation dates, experience, sponsorship, citizenship, and start dates on the employer page. General new-grad roles may not accept 2027 graduates.', '',
             f'Listing snapshot: **{now[:10]} {now[11:16]} UTC**. [Latest source checks](https://github.com/yashasvijay/cs-new-grad-2027/actions/workflows/update.yml) are recorded per run; this date changes only when the public list or source status changes.', '']
    for heading, jobs in [('2027 mentioned', confirmed), ('General new-grad / early career', general)]:
        lines += [f'## {heading}', '', '| Company | Role | Location | Apply | Employer published |', '|---|---|---|:---:|---|']
        for j in sorted(jobs, key=lambda j:(j['employer'].lower(), j['title'], j['location'])):
            date = (j.get('employer_published_at') or '')[:10] or '—'
            lines.append(f"| **{cell(j['employer'])}** | {cell(j['title'])}{' ⚠️' if j['employment'].startswith('full-time unverified') else ''}{' 📝' if j.get('verification_mode') == 'manual' else ''} | {cell(j['location'])} | [Apply ↗]({j['url']}) | {date} |")
        if not jobs:
            lines += ['', 'No verified candidates in this group yet.']
        lines += ['']
    lines += ['## Company events', '',
              '[Browse virtual and in-person company events →](EVENTS.md)', '',
              'Public conferences, recruiting sessions, workshops, and hackathons when independently verified. Events are manually curated; registration, pricing, and student eligibility vary. An event listing does not imply a job opening.', '',
              '## Coverage, without the guesswork', '',
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
    return '\n'.join(lines)
