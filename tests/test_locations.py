import copy
import json
from pathlib import Path
import unittest

from tracker.readme import location_cell, normalize_location, render


class LocationTests(unittest.TestCase):
    def test_one_location(self):
        self.assertEqual(location_cell('Costa Mesa, California, United States'), 'Costa Mesa, CA')

    def test_two_locations_inline(self):
        self.assertEqual(location_cell('Costa Mesa, California, United States; Seattle, Washington, United States'), 'Costa Mesa, CA; Seattle, WA')

    def test_nine_locations_single_line_dropdown(self):
        value = '; '.join(['Atlanta, Georgia, United States', 'Boston, Massachusetts, United States',
                           'Broomfield, Colorado, United States', 'Colorado Springs, Colorado, United States',
                           'Costa Mesa, California, United States', 'Fort Collins, Colorado, United States',
                           'Irvine, California, United States', 'Reston, Virginia, United States',
                           'Seattle, Washington, United States'])
        result = location_cell(value)
        self.assertTrue(result.startswith('<details><summary>9 locations</summary>'))
        self.assertEqual(result.count('<br>'), 8)
        self.assertTrue(result.endswith('</details>'))
        self.assertNotIn('\n', result)
        self.assertIn('Costa Mesa, CA', result)

    def test_street_addresses(self):
        self.assertEqual(normalize_location('US-MA-TEWKSBURY-TB3 ~ 50 Apple Hill Dr ~ CONCORD BLDG, Tewksbury Tb3 300 Concord'), 'Tewksbury, MA')
        self.assertEqual(normalize_location('US-MA-WOBURN-WB1 ~ 235 Presidential Way ~ SPENCER BLDG'), 'Woburn, MA')
        self.assertEqual(normalize_location('235 Presidential Way, Woburn, Massachusetts, United States'), 'Woburn, MA')

    def test_unknown_location_and_pipe(self):
        self.assertEqual(normalize_location('Campus 3 | North Building'), 'Campus 3 | North Building')
        self.assertEqual(location_cell('Campus 3 | North Building'), 'Campus 3 &#124; North Building')
        self.assertEqual(normalize_location('50 Unknown Road'), '50 Unknown Road')
        self.assertEqual(normalize_location('Vancouver, Canada'), 'Vancouver, Canada')
        self.assertIn('&lt;script&gt;', location_cell('<script>'))

    def test_render_is_display_only_in_all_sections(self):
        path = Path('data/listings.json')
        before = path.read_bytes()
        view = json.loads(before)
        original = copy.deepcopy(view)
        base = dict(view['jobs'][0], title='Software Engineer, 2027 New Grad', eligibility='2027 mentioned — review requirements',
                    location='Costa Mesa, California, United States; Seattle, Washington, United States; Austin, Texas, United States')
        view['jobs'] = [dict(base, id='open', status='open'), dict(base, id='closed', status='closed')]
        fixture = copy.deepcopy(view)
        result = render(view, view['snapshot_at'])
        primary, secondary = result.split('## Secondary listings', 1)
        self.assertIn('<details><summary>3 locations</summary>Costa Mesa, CA<br>Seattle, WA<br>Austin, TX</details>', primary)
        self.assertIn('<details><summary>3 locations</summary>Costa Mesa, CA<br>Seattle, WA<br>Austin, TX</details>', secondary)
        self.assertEqual(view, fixture)
        render(original, original['snapshot_at'])
        self.assertEqual(path.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()
