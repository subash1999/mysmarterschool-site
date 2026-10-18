#!/usr/bin/env python3
"""Offline checks for the public static site; never requests a tenant or service."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

root = Path(__file__).resolve().parents[1]
pages = [root / 'index.html', root / '404.html', *(root / 'about').rglob('*.html'), *(root / 'guide').rglob('*.html')]


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.references = []
        self.h1 = 0
        self.scripts = 0
        self.images = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        self.h1 += tag == 'h1'
        self.scripts += tag in {'script', 'iframe'}
        if tag == 'img':
            self.images.append(attrs)
        for name in ['href', 'src']:
            if attrs.get(name):
                self.references.append(attrs[name])


parsed = {}
for path in pages:
    page = Page()
    text = path.read_text()
    page.feed(text)
    assert page.h1 == 1 and page.scripts == 0, path
    assert len(page.ids) == len(set(page.ids)), path
    assert not re.search(r'[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}', text, re.I), path
    assert '<title>' in text and 'name="description"' in text and 'rel="canonical"' in text, path
    assert all(image.get('alt', '').strip() and image.get('width') and image.get('height') for image in page.images), path
    parsed[path] = page

for path, page in parsed.items():
    for reference in page.references:
        url = urlsplit(reference)
        if url.netloc and url.netloc != 'mysmarterschool.com':
            assert url.scheme == 'https' and url.netloc in {'www.linkedin.com', 'subashn.com.np'}, (path, reference)
            continue
        target = path if not url.path else root / unquote(url.path).lstrip('/')
        assert not url.path or url.path.startswith('/'), (path, 'Use site-root absolute URLs', reference)
        if target.is_dir():
            target = target / 'index.html'
        assert target.exists() and target.resolve().is_relative_to(root), (path, reference)
        if url.fragment:
            assert target in parsed and unquote(url.fragment) in parsed[target].ids, (path, reference)

manifest = json.loads((root / 'assets/screens/manifest.json').read_text())
assert manifest['school'] == 'Demo Academy'
assert len(manifest['screens']) == 32
assert len({screen['screen'] for screen in manifest['screens']}) == 16
assert all((root / 'assets/screens' / screen['file']).is_file() for screen in manifest['screens'])
print(f'Passed {len(pages)} static pages and the 32-image synthetic screenshot manifest.')
