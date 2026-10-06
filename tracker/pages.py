import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
from urllib.error import URLError
from urllib.request import Request, urlopen


def check_paths(site):
    patterns = [r'''(?:src|href)\s*=\s*["'](/[^"']*)''',
                r'''\b(?:fetch|url)\s*\(\s*["']?(/[^"')\s]*)''']
    for path in site.rglob('*'):
        if path.suffix not in ('.html', '.css', '.js'):
            continue
        for pattern in patterns:
            if re.search(pattern, path.read_text(), re.I):
                raise ValueError(f'Root-absolute URL in {path}')


def assemble(site, listings, output):
    check_paths(site)
    generated = site / 'data.json'
    if not generated.is_file():
        raise ValueError('site/data.json is missing')
    source = json.loads(listings.read_text())['jobs']
    display = json.loads(generated.read_text())['jobs']
    if not source or not display or len(source) != len(display):
        raise ValueError('Source/display record counts must be equal and nonzero')
    shutil.copytree(site, output, dirs_exist_ok=True)
    shutil.copyfile(listings, output / 'listings.json')
    version = hashlib.sha256(listings.read_bytes()).hexdigest()
    (output / 'version.txt').write_text(version + '\n')
    (output / '.nojekyll').touch()
    return version


def already_published(url, version):
    try:
        request = Request(url, headers={'Cache-Control': 'no-cache'})
        with urlopen(request, timeout=10) as response:
            return response.read(256).decode().strip() == version
    except (URLError, TimeoutError, OSError, UnicodeError):
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--site', type=Path, default=Path('site'))
    parser.add_argument('--listings', type=Path, default=Path('data/listings.json'))
    parser.add_argument('--output', type=Path, default=Path('.pages'))
    parser.add_argument('--live-version')
    parser.add_argument('--github-output', type=Path)
    args = parser.parse_args()
    version = assemble(args.site, args.listings, args.output)
    deploy = not (args.live_version and already_published(args.live_version, version))
    print(f'Artifact assembled; deploy={deploy}; version={version}')
    if args.github_output:
        with args.github_output.open('a') as output:
            output.write(f'deploy={str(deploy).lower()}\n')


if __name__ == '__main__':
    main()
