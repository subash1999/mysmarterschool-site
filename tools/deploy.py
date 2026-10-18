#!/usr/bin/env python3
"""Publish the static site to the owner's pinned cPanel root with backups."""
import datetime
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

DOMAIN = 'mysmarterschool.com'
CPANEL_ROOT = '/home/subashnc/public_html'
ALLOWED_TOP = {'index.html', '404.html', 'about', 'guide', 'assets', 'favicon.svg', 'favicon.png', 'robots.txt', 'sitemap.xml'}
ALLOWED_SUFFIXES = {'.html', '.css', '.webp', '.png', '.svg', '.json', '.txt', '.xml'}


def configured_root(config):
    if config.get('domain') != DOMAIN or config.get('document_root') != CPANEL_ROOT:
        raise ValueError('Deployment root differs from the owner-approved mysmarterschool.com root.')
    return Path(CPANEL_ROOT)


def no_symlinks(path):
    if not path.is_absolute() or any(item.is_symlink() for item in [path, *path.parents]):
        raise ValueError('Absolute, non-symlinked paths are required.')


def configured_files(config):
    files = config.get('files')
    if not isinstance(files, list) or not files or any(not isinstance(name, str) for name in files):
        raise ValueError('An explicit deployment file list is required.')
    if len(set(files)) != len(files) or 'index.html' not in files:
        raise ValueError('The deployment file list must be unique and include index.html.')
    for name in files:
        path = Path(name)
        if path.is_absolute() or path.as_posix() != name or any(part.startswith('.') for part in path.parts) or path.parts[0] not in ALLOWED_TOP or path.suffix not in ALLOWED_SUFFIXES:
            raise ValueError('Only normalized, relative static paths may be listed for deployment.')
    return set(files)


def publication_plan(source, target, allowed_files):
    source, target = Path(source), Path(target)
    for path in [source, target]:
        no_symlinks(path)
    if not target.is_dir() or source == target or source in target.parents or target in source.parents:
        raise ValueError('Refusing a missing destination or source/destination overlap.')
    files = []
    for path in source.rglob('*'):
        relative = path.relative_to(source)
        if path.is_symlink() or relative.parts[0] not in ALLOWED_TOP or any(part.startswith('.') for part in relative.parts):
            raise ValueError('Unexpected or symlinked static input.')
        if path.is_dir():
            continue
        if not path.is_file() or path.suffix not in ALLOWED_SUFFIXES or relative.as_posix() not in allowed_files:
            raise ValueError('A build file is outside the reviewed deployment file list.')
        destination = target / relative
        no_symlinks(destination)
        if destination.exists() and not destination.is_file():
            raise ValueError('A destination file is occupied by a directory.')
        if any(parent.exists() and not parent.is_dir() for parent in destination.parents):
            raise ValueError('A destination parent is not a directory.')
        files.append((path, destination, relative))
    if {relative.as_posix() for _, _, relative in files} != allowed_files or 'index.html' not in allowed_files:
        raise ValueError('The static build differs from the reviewed deployment file list.')
    return files


def publish(source, target, backup_base, allowed_files):
    source, target, backup_base = Path(source), Path(target), Path(backup_base)
    no_symlinks(backup_base)
    files = publication_plan(source, target, allowed_files)
    if backup_base == target or target in backup_base.parents or backup_base == source or source in backup_base.parents:
        raise ValueError('Backups must be outside the source and document root.')
    backup_base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ-')
    backup = Path(tempfile.mkdtemp(prefix=stamp, dir=backup_base))
    # Finish every backup before changing any destination file.
    for _, destination, relative in files:
        if destination.exists():
            previous = backup / relative
            previous.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination, previous)
    print('Backup complete:', backup, flush=True)
    # Assets first, HTML last. Each individual file is replaced atomically.
    for path, destination, _ in sorted(files, key=lambda entry: entry[0].suffix == '.html'):
        destination.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(prefix='.smart-school-', dir=destination.parent)
        os.close(descriptor)
        try:
            shutil.copy2(path, temporary)
            os.replace(temporary, destination)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return backup


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Build and print the complete write plan without publishing')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / 'deployment.json').read_text())
    target, allowed_files = configured_root(config), configured_files(config)
    subprocess.run([sys.executable, str(root / 'tools/build.py')], check=True)
    plan = publication_plan(root / 'dist', target, allowed_files)
    print('Using the owner-audited cPanel root. Re-audit Domains after any mapping change.', flush=True)
    for _, destination, _ in sorted(plan, key=lambda entry: str(entry[2])):
        print('WRITE', destination, flush=True)
    if args.check:
        print('Write plan validated. No published files changed.')
        return
    backup = publish(root / 'dist', target, Path('/home/subashnc/backups/mysmarterschool-site'), allowed_files)
    print('Published Smart School. Backup:', backup)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        sys.exit(str(error))
