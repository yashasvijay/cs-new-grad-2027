import json
from pathlib import Path

from tracker.run import cell


def render(path, now):
    events = json.loads(Path(path).read_text())['events']
    lines = ['# Company events', '',
             'Public virtual and in-person events for companies in the tracker. Manually curated, with organizer links. Dates do not imply recruiting availability or 2027 eligibility. Confirm registration, cost, accessibility, and the organizer’s detailed schedule.', '',
             '[Jobs](README.md) · [Event data](data/events.json)', '']
    for heading, ended in [('Upcoming events', False), ('Past events', True)]:
        lines += [f'## {heading}', '', '| Company | Event | Dates | Format / location | Cost | Last verified |', '|---|---|---|---|---|---|']
        for event in sorted(events, key=lambda e: (e['start_date'], e['company'])):
            if (event['end_date'] < now[:10]) != ended:
                continue
            lines.append('| ' + ' | '.join([cell(event['company']), f"[{cell(event['name'])}]({event['url']})", f"{event['start_date']} – {event['end_date']}", cell(event['format'] + ' · ' + event['location']), cell(event['cost']), event['verified_at'][:10]]) + ' |')
        lines += ['']
    lines += ['## Add an event', '', 'Suggest a direct organizer page with company, dates, format, location, registration requirements, and cost. Social stories and email confirmations are discovery leads; private invitations and personal registration links are never published.', '']
    return '\n'.join(lines)
