import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tracker.readme import normalize_location
from tracker.site_data import display_data, main


class SiteDataTests(unittest.TestCase):
    def test_records_and_source_preserved(self):
        path = Path('data/listings.json')
        before = path.read_bytes()
        source = json.loads(before)
        original = copy.deepcopy(source)
        result = display_data(source)
        self.assertEqual(len(result['jobs']), len(source['jobs']))
        self.assertEqual(len({job['id'] for job in result['jobs']}), len(source['jobs']))
        for raw, display in zip(source['jobs'], result['jobs']):
            self.assertEqual(display['company'], raw['employer'])
            self.assertEqual(display['title'], raw['title'])
            self.assertEqual(display['apply_url'], raw['url'])
            self.assertEqual(display['section'], raw['listing_section'])
            self.assertEqual(display['notes'], raw.get('eligibility_note') or None)
            self.assertEqual(display['locations'], [normalize_location(part) for part in (raw.get('location') or '').split(';') if part.strip()] or None)
        self.assertEqual(source, original)
        self.assertEqual(path.read_bytes(), before)

    def test_nulls_not_invented(self):
        row = display_data({'jobs': [{}]})['jobs'][0]
        for key in ['company', 'title', 'locations', 'notes', 'apply_url', 'date', 'date_kind', 'section', 'status', 'deadline', 'sponsorship', 'citizenship', 'degree_level']:
            self.assertIsNone(row[key], key)
        self.assertFalse(row['manual_check'])
        self.assertFalse(row['full_time_unverified'])

    def test_dates_and_flags(self):
        base = {'first_seen_at':'2026-10-05T10:00:00Z', 'employment':'full-time unverified', 'verification_mode':'manual'}
        row = display_data({'jobs':[base]})['jobs'][0]
        self.assertEqual((row['date'], row['date_kind']), (base['first_seen_at'], 'First seen'))
        self.assertTrue(row['full_time_unverified'])
        self.assertTrue(row['manual_check'])
        base.update(employer_published_at='2026-10-01', employer_posted_at='2026-09-30', sponsorship='No sponsorship', degree_level='PhD')
        row = display_data({'jobs':[base]})['jobs'][0]
        self.assertEqual((row['date'], row['date_kind']), ('2026-10-01', 'Released'))
        self.assertEqual(row['sponsorship'], 'No sponsorship')
        self.assertEqual(row['degree_level'], 'PhD')

    def test_locations_use_readme_normalizer(self):
        values = ['Costa Mesa, California, United States', '235 Presidential Way, Woburn, Massachusetts, United States', 'Campus 3 | North Building']
        row = display_data({'jobs':[{'location':'; '.join(values)}]})['jobs'][0]
        self.assertEqual(row['locations'], [normalize_location(value) for value in values])
        self.assertEqual(row['locations'], ['Costa Mesa, CA', 'Woburn, MA', 'Campus 3 | North Building'])

    def test_build_is_deterministic_and_does_not_write_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'listings.json'
            output = Path(directory) / 'site/data.json'
            source.write_text(json.dumps({'jobs':[{'id':'1', 'employer_id':'e', 'location':None}]}))
            before = source.read_bytes()
            with patch('sys.argv', ['site_data', '--input', str(source), '--output', str(output)]):
                main()
                first = output.read_bytes()
                main()
            self.assertEqual(output.read_bytes(), first)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(len(json.loads(first)['jobs']), 1)
