#!/usr/bin/env python3
"""Copy an explicit allowlist of static files; no server or dependencies required."""
from pathlib import Path
import shutil
import json
from deploy import configured_files

root = Path(__file__).resolve().parents[1]
output = root / 'dist'
if output.is_symlink():
    raise SystemExit('Refusing a symlinked build directory.')
if output.exists():
    shutil.rmtree(output)
output.mkdir()
for name in ['index.html', '404.html', 'about', 'guide', 'assets', 'favicon.svg', 'favicon.png', 'robots.txt', 'sitemap.xml']:
    source = root / name
    paths = [source, *source.rglob('*')] if source.is_dir() else [source]
    for path in paths:
        if path.is_symlink() or not path.exists():
            raise SystemExit(f'Missing or symlinked build input: {path}')
        if path.is_file() and path.suffix not in {'.html', '.css', '.webp', '.png', '.svg', '.json', '.txt', '.xml'}:
            raise SystemExit(f'Unexpected static file: {path}')
    if source.is_dir():
        shutil.copytree(source, output / name)
    else:
        shutil.copy2(source, output / name)
actual = {path.relative_to(output).as_posix() for path in output.rglob('*') if path.is_file()}
if actual != configured_files(json.loads((root / 'deployment.json').read_text())):
    raise SystemExit('Build differs from deployment.json files. Review and update the explicit list.')
print(f'Built {len(list(output.rglob("*")))} static entries in {output}')
