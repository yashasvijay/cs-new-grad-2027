from datetime import datetime, timezone
from html import escape
import re
from urllib.parse import quote


def release_order(jobs):
    def key(job):
        value = job.get('employer_published_at') or job.get('employer_posted_at')
        try:
            date = datetime.fromisoformat(value.replace('Z', '+00:00'))
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            timestamp = date.timestamp()
        except (AttributeError, TypeError, ValueError):
            timestamp = None
        return (timestamp is None, -(timestamp or 0), job['employer'].lower(), job['title'], job.get('location', ''))
    return sorted(jobs, key=key)


def listing_order(jobs):
    return [job for group in (
        [j for j in jobs if j['status'].startswith('open')],
        [j for j in jobs if not j['status'].startswith('open') and j['status'] != 'closed'],
        [j for j in jobs if j['status'] == 'closed']) for job in release_order(group)]


def button(job):
    closed = job['status'] == 'closed'
    label = '🔒 Closed — original posting' if closed else ('Apply' if job['status'].startswith('open') else 'Review original posting')
    asset = 'closed.svg' if closed else ('apply.svg' if job['status'].startswith('open') else 'review.svg')
    return f'<a href="{escape(job["url"], quote=True)}"><img src="assets/{asset}" width="118" alt="{label}"></a>'


def decorate_links(text):
    def replace(match):
        label, url = match.groups()
        image = 'https://img.shields.io/badge/' + quote(label, safe='') + '-334155?style=for-the-badge'
        return f'<a href="{escape(url, quote=True)}"><img src="{image}" alt="{escape(label, quote=True)}"></a>'
    return re.sub(r'(?<!!)\[([^\[\]]+)\]\(([^()\s]+)\)', replace, text)
