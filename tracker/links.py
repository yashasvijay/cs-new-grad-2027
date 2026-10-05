from concurrent.futures import ThreadPoolExecutor
import subprocess
from tracker.adapters import plain


def response_code(url, title):
    result = subprocess.run(['curl', '--silent', '--location', '--max-time', '20',
                             '--max-redirs', '5', '--max-filesize', '5000000',
                             '--write-out', '\n%{http_code}', url], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    body, _, status = result.stdout.rpartition('\n')
    if not status.isdigit():
        return None
    code = int(status)
    if 200 <= code < 300 and plain(title).lower() not in plain(body).lower():
        return None
    return code


def apply_result(job, code):
    if code == 404:
        job['link_closed'] = True
        job['link_review_required'] = False
        job['closure_reason'] = 'Posting link returns HTTP 404'
    elif code is not None and 200 <= code < 300 and job.get('link_closed'):
        job['link_closed'] = False
        job['link_review_required'] = True
        job.pop('closure_reason', None)


def check(state, classify, probe=None):
    candidates = [job for job in state.get('jobs', {}).values() if classify(job)]
    with ThreadPoolExecutor(max_workers=8) as pool:
        for job, code in zip(candidates, pool.map(lambda job: probe(job['url']) if probe else response_code(job['url'], job['title']), candidates)):
            apply_result(job, code)
    return len(candidates)
