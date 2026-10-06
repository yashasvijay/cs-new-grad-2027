import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from tracker.pages import assemble, already_published, check_paths


class PagesTests(unittest.TestCase):
    def test_site_urls_are_subpath_safe(self):
        check_paths(Path('site'))

    def test_root_absolute_urls_fail(self):
        for suffix, content in [('html', '<script src="/app.js">'), ('css', 'background: url(/asset.svg)'), ('js', 'fetch("/data.json")')]:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / ('bad.' + suffix)).write_text(content)
                with self.assertRaises(ValueError):
                    check_paths(root)

    def test_artifact_and_sanity_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            site = root / 'site'
            site.mkdir()
            listings = root / 'listings.json'
            listings.write_text(json.dumps({'jobs':[{'id':'1'}]}))
            output = root / 'artifact'
            with self.assertRaises(ValueError):
                assemble(site, listings, output)
            for jobs in [[], [{'id':'1'}, {'id':'2'}]]:
                (site / 'data.json').write_text(json.dumps({'jobs':jobs}))
                with self.assertRaises(ValueError):
                    assemble(site, listings, output)
            (site / 'data.json').write_text(listings.read_text())
            (site / 'index.html').write_text('<script src="app.js"></script>')
            version = assemble(site, listings, output)
            self.assertEqual((output / 'listings.json').read_bytes(), listings.read_bytes())
            self.assertEqual((output / 'data.json').read_bytes(), (site / 'data.json').read_bytes())
            self.assertEqual((output / 'version.txt').read_text().strip(), version)

    def test_version_match_and_first_deploy(self):
        with patch('tracker.pages.urlopen') as request:
            request.return_value.__enter__.return_value.read.return_value = b'abc\n'
            self.assertTrue(already_published('https://example.com/version.txt', 'abc'))
            self.assertFalse(already_published('https://example.com/version.txt', 'changed'))
        with patch('tracker.pages.urlopen', side_effect=HTTPError('url', 404, 'Missing', {}, None)):
            self.assertFalse(already_published('https://example.com/version.txt', 'abc'))
