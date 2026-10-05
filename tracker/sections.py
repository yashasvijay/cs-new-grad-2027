import re


def classify_section(job):
    reasons = []
    if job['status'] == 'closed':
        reasons.append('closed')
    elif not job['status'].startswith('open'):
        reasons.append('verification_pending')
    title = job.get('title', '')
    notes = job.get('eligibility_note') or ''
    phd = r'ph\.?d\.?|doctorate|doctoral'
    phd_title = re.search(phd, title, re.I)
    alternatives = re.search(r'bachelor|master|\b(?:bs|bsc|ms|msc)\b', title, re.I)
    phd_required = re.search(rf'(?:{phd})(?: degree)?\s+(?:required|only)\b|requires? (?:a )?(?:{phd})\b', notes, re.I)
    if (phd_title and not alternatives) or phd_required:
        reasons.append('phd_only')
    reused = job.get('employer_original_posted_at') or re.search(r'reused requisition|original requisition', notes + ' ' + (job.get('date_kind') or ''), re.I)
    release = job.get('employer_published_at') or job.get('employer_posted_at')
    if reused and not release:
        reasons.append('reused_release_unverified')
    section = 'secondary' if reasons else ('new_grad_2027' if job['eligibility'].startswith('2027') else 'general_early_career')
    return {'listing_section': section, 'secondary_reasons': reasons}


def annotate(jobs):
    return [dict(job, **classify_section(job)) for job in jobs]
