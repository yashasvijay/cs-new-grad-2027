import json
from pathlib import Path

from tracker.run import cell


def upcoming_rows(now, path=Path('data/events.json')):
    events = json.loads(Path(path).read_text())['events']
    return [row(event) for event in sorted(events, key=lambda e: (e['start_date'], e['company'])) if event['end_date'] >= now[:10]]


def row(event):
    from html import escape
    link = f'<a href="{escape(event["url"], quote=True)}"><img src="assets/event.svg" width="118" alt="View event / registration"></a>'
    return '| ' + ' | '.join([cell(event['company']), cell(event['name']), f"{event['start_date']} – {event['end_date']}", cell(event['format']), cell(event['location']), cell(event['cost']), link]) + ' |'


def render(path, now):
    events = json.loads(Path(path).read_text())['events']
    lines = ['# Company events', '',
             'Public virtual and in-person events for companies in the tracker. Manually curated, with organizer links. Dates do not imply recruiting availability or 2027 eligibility. Confirm registration, cost, accessibility, and the organizer’s detailed schedule.', '',
             '[Jobs](README.md) · [Event data](data/events.json)', '']
    for heading, ended in [('Upcoming events', False), ('Past events', True)]:
        lines += [f'## {heading}', '', '| Company | Event | Dates | Format | Location | Cost | Link |', '|---|---|---|---|---|---|:---:|']
        for event in sorted(events, key=lambda e: (e['start_date'], e['company'])):
            if (event['end_date'] < now[:10]) != ended:
                continue
            lines.append(row(event))
        lines += ['']
    lines += ['## Add an event', '', 'Suggest a direct organizer page with company, dates, format, location, registration requirements, and cost. Social stories and email confirmations are discovery leads; private invitations and personal registration links are never published.', '']
    from tracker.presentation import decorate_links
    return decorate_links('\n'.join(lines))
