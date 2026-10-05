import copy
from collections import Counter
import json
import re
from pathlib import Path
import unittest

from tracker.eligibility import classify
from tracker.engine import public_view, reconcile
from tracker.readme import render
from tracker.sections import annotate, classify_section
from test_tracker import job


class SectionTests(unittest.TestCase):
    def test_secondary_classification(self):
        base = dict(status='open', title='2027 New Grad Software Engineer', eligibility='2027 mentioned — review requirements')
        cases = [
            (dict(base, employer_original_posted_at='2020-10-27'), ['reused_release_unverified']),
            (dict(base, eligibility_note='Reused requisition; current-cycle release date unverified.'), ['reused_release_unverified']),
            (dict(base, date_kind='Original requisition date; current-cycle release unverified'), ['reused_release_unverified']),
            (dict(base, title='PhD University Grad Machine Learning Engineer'), ['phd_only']),
            (dict(base, eligibility_note='PhD required; 2027 full-time start.'), ['phd_only']),
            (dict(base, status='closed'), ['closed']),
            (dict(base, status='reopened — verification pending'), ['verification_pending']),
            (dict(base, status='closed', title='Ph.D. Software Engineer', employer_original_posted_at='2020-10-27'), ['closed', 'phd_only', 'reused_release_unverified']),
        ]
        for row, reasons in cases:
            with self.subTest(row=row):
                self.assertEqual(classify_section(row), {'listing_section':'secondary', 'secondary_reasons':reasons})

    def test_main_sections_and_ambiguous_degrees(self):
        base = dict(status='open', title='2027 New Grad Software Engineer', eligibility='2027 mentioned — review requirements')
        for changes in [dict(), dict(employer_published_at=None),
                        dict(employer_original_posted_at='2020-10-27', employer_published_at='2026-10-05'),
                        dict(title='AI Research Scientist - Early Career (PHD/MS)'),
                        dict(title='2027 Software Engineer', eligibility_note='PhD preferred')]:
            self.assertEqual(classify_section(dict(base, **changes))['listing_section'], 'new_grad_2027')
        self.assertEqual(classify_section(dict(base, eligibility='general entry-level — review 2027 eligibility'))['listing_section'], 'general_early_career')

    def test_classification_is_independent_of_company(self):
        base = dict(status='open', title='Software Engineer, PhD, 2027', eligibility='2027 mentioned — review requirements')
        expected = classify_section(base)
        for employer in ['Example Company', 'Unlisted Employer', None]:
            self.assertEqual(classify_section(dict(base, employer=employer, employer_id='any-id')), expected)

    def test_no_records_or_existing_fields_lost(self):
        snapshot = json.loads(Path('data/listings.json').read_text())
        original = [{k:v for k,v in row.items() if k not in ('listing_section', 'secondary_reasons')} for row in snapshot['jobs']]
        before = copy.deepcopy(original)
        result = annotate(original)
        self.assertEqual(original, before)
        self.assertEqual(len(result), len(original))
        self.assertEqual([{k:v for k,v in row.items() if k not in ('listing_section', 'secondary_reasons')} for row in result], original)
        identities = lambda rows: Counter((row['employer_id'], row.get('requisition_id') or row['id']) for row in rows)
        self.assertEqual(identities(result), identities(original))
        self.assertEqual(sum(sum(row['listing_section'] == section for row in result) for section in ('new_grad_2027', 'general_early_career', 'secondary')), len(original))

    def test_generation_and_recovery_recompute_sections(self):
        state = {}; employer = {'id':'e', 'name':'Employer'}
        reconcile(state, employer, [job()], '2026-10-05T10:00:00+00:00')
        state['jobs']['e:1'].update(_recovered=True, eligibility='2027 mentioned — review requirements', employment='full-time', evidence='2027 graduates', review_required=True, listing_section='secondary', secondary_reasons=['closed'])
        view = public_view(state, [employer], '2026-10-05T10:00:00+00:00', classify)
        self.assertEqual(len(view['jobs']), 1)
        self.assertEqual(view['jobs'][0]['listing_section'], 'new_grad_2027')
        state['jobs']['e:1']['status'] = 'closed'
        closed = public_view(state, [employer], '2026-10-05T10:00:00+00:00', classify)
        self.assertEqual(len(closed['jobs']), 1)
        self.assertEqual(closed['jobs'][0]['secondary_reasons'], ['closed'])

    def test_readme_placement_and_full_record_visibility(self):
        view = json.loads(Path('data/listings.json').read_text())
        text = render(view, view['snapshot_at'])
        main = text.split('### 2027 new-grad roles', 1)[1].split('### General early career', 1)[0]
        general = text.split('### General early career', 1)[1].split('## Secondary listings', 1)[0]
        secondary = text.split('## Secondary listings', 1)[1].split('## Company events', 1)[0]
        for row in annotate(view['jobs']):
            if row['listing_section'] == 'secondary':
                self.assertNotIn('href="' + row['url'] + '"', main)
                self.assertNotIn('href="' + row['url'] + '"', general)
                self.assertIn('href="' + row['url'] + '"', secondary)
        self.assertEqual(text.count('<tr><td><strong>'), len(view['jobs']))
        self.assertIn('<details><summary>Show ', secondary)
        self.assertRegex(secondary, r'</summary>\n\n<table>')
        self.assertIn('</tbody></table>\n\n</details>', secondary)
        self.assertIn('# yashasvijay - 2027 CS New Grad Tracker', text)
        self.assertIn('width="100" height="32"', text)
        self.assertLess(text.index('## Company events'), text.index('## Coverage'))
        intro = text.split('# yashasvijay - 2027 CS New Grad Tracker', 1)[1].split('</div>', 1)[0]
        self.assertIn('<!-- SCREENSHOT:', intro)
        self.assertIn('<!-- SITE LINK:', intro)
        self.assertNotIn('> Screenshot placeholder', text)
        self.assertNotIn('> Site link placeholder', text)
        self.assertNotIn('badge.svg', intro)
        self.assertNotIn('Read before applying', intro)
        self.assertIn("Listings are sourced from public employer career pages and remain the property of their respective employers. The MIT license covers this repository's code, not the listings.", text)

    def test_navigation_and_prominent_eligibility_warning(self):
        view = json.loads(Path('data/listings.json').read_text())
        text = render(view, view['snapshot_at'])
        nav = next(line for line in text.splitlines() if 'alt="2027 roles"' in line)
        links = re.findall(r'href="([^"]+)"', nav)
        self.assertEqual(len(links), 6)
        self.assertNotIn(' · ', nav)
        for link in links:
            path, anchor = link.split('#', 1)
            target = Path(path).read_text() if path else text
            headings = re.findall(r'^#{1,6} (.+)$', target, re.MULTILINE)
            slugs = [re.sub(r'[^\w -]', '', heading.lower()).replace(' ', '-') for heading in headings]
            self.assertIn(anchor, slugs, link)
        warning = '**“2027 mentioned” is a screening signal, not a guarantee of eligibility.**'
        self.assertIn(warning, text)
        self.assertLess(text.index('</div>'), text.index(warning))
        self.assertLess(text.index(warning), text.index('## Open roles'))

    def test_legend_placement_and_row_symbols(self):
        view = json.loads(Path('data/listings.json').read_text())
        text = render(view, view['snapshot_at'])
        legend = '⚠️ full-time status unverified · 📝 manual employer-page check (expires after 48 hours)'
        self.assertIn(legend + '\n\n<table>', text)
        coverage = text.split('## Coverage', 1)[1].split('## Contribute', 1)[0]
        self.assertIn(legend, coverage)
        for employment, mode in [('full-time', None), ('full-time unverified', None), ('full-time', 'manual'), ('full-time unverified', 'manual')]:
            row = dict(view['jobs'][0], title='Legend test role', employment=employment, verification_mode=mode)
            rendered = render(dict(view, jobs=[row]), view['snapshot_at'])
            title_cell = rendered.split('Legend test role', 1)[1].split('</td>', 1)[0]
            self.assertEqual('⚠️' in title_cell, employment.startswith('full-time unverified'))
            self.assertEqual('📝' in title_cell, mode == 'manual')


if __name__ == '__main__':
    unittest.main()
