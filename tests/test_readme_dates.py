import unittest
from tracker.readme import date_cell


class ReadmeDateTests(unittest.TestCase):
    def test_release_and_exact_tooltip(self):
        self.assertEqual(date_cell({'employer_posted_at': '2026-10-04'}, '2026-10-06'), '<span title="Released: 2026-10-04">Released 2 days ago</span>')

    def test_first_seen_and_today(self):
        self.assertIn('First seen today', date_cell({'first_seen_at': '2026-10-06'}, '2026-10-06'))
        self.assertIn('First seen 1 day ago', date_cell({'first_seen_at': '2026-10-05'}, '2026-10-06'))

    def test_unknown_and_future(self):
        self.assertEqual(date_cell({}, '2026-10-06'), 'Date unknown')
        self.assertIn('Released 2026-10-07', date_cell({'employer_posted_at': '2026-10-07'}, '2026-10-06'))
