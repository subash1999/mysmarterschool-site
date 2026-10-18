#!/usr/bin/env python3
"""Prepare a disposable runtime without copying tenant config, dumps or uploads."""
import argparse
import base64
from pathlib import Path
import re
import secrets
import shutil
import os
import stat

parser = argparse.ArgumentParser()
parser.add_argument('--source', required=True, help='Absolute path to the read-only application checkout')
parser.add_argument('--runtime', required=True, help='New /private/tmp/smart-school-demo-… directory')
args = parser.parse_args()
source, runtime = Path(args.source), Path(args.runtime)
if not source.is_absolute() or not runtime.is_absolute() or not re.fullmatch(r'/(?:private/)?tmp/smart-school-demo-[a-z0-9-]+', str(runtime)):
    raise SystemExit('Absolute source and disposable runtime paths required.')
source = source.resolve(strict=True)
if runtime.exists() or runtime.is_symlink() or source == runtime or source in runtime.parents:
    raise SystemExit('Runtime must be new and separate from the source.')
if not (source / 'vendor/autoload.php').is_file():
    raise SystemExit('Source dependencies must already be installed.')

def excluded(name):
    lower = name.lower()
    return lower.startswith('.env') or lower in {'.git', '.ds_store', 'desktop.ini', 'uploads', 'storage'} or lower.endswith(('.sql', '.sqlite', '.sqlite3', '.db', '.dump', '.bak', '.backup', '.gz', '.bz2', '.xz', '.zst', '.zip', '.tar'))


def exclude(directory, names):
    return [name for name in names if excluded(name)]


def validate(path, boundary=source):
    # A regular file can still be reached through a symlinked parent directory.
    current = boundary
    for component in path.relative_to(boundary).parts:
        current = current / component
        if current.is_symlink():
            raise SystemExit('Symlinks are not permitted in demo runtime inputs.')
    mode = path.lstat().st_mode
    if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
        raise SystemExit('Special files are not permitted in demo runtime inputs.')
    if path.is_dir():
        for directory, directories, files in os.walk(path, followlinks=False):
            directories[:] = [name for name in directories if not excluded(name)]
            for name in directories + [name for name in files if not excluded(name)]:
                item = Path(directory) / name
                if item.is_symlink() or not (stat.S_ISREG(item.lstat().st_mode) or stat.S_ISDIR(item.lstat().st_mode)):
                    raise SystemExit('Symlinks and special files are not permitted in demo runtime inputs.')


# Validate every selected input before creating or copying anything.
for name in ['app', 'config', 'database', 'resources', 'routes', 'vendor', 'bootstrap/app.php', 'artisan', 'composer.json', 'composer.lock', 'public/index.php', 'public/favicon.ico', 'public/.htaccess']:
    validate(source / name)
for name in ['vendors', 'vendors_compressed', 'css', 'js', 'build', 'fonts', 'webfonts', 'favicon']:
    path = source / 'public' / name
    if path.exists() or path.is_symlink():
        validate(path)
for name in ['image_loading.png', 'male-icon.jpg', 'female-icon.jpg', 'other-gender-icon.png', 'login-background.jpg', 'mountain.jpg']:
    path = source / 'public/images' / name
    if path.exists() or path.is_symlink():
        validate(path)
runtime.mkdir(mode=0o700)
for name in ['app', 'config', 'database', 'resources', 'routes', 'vendor']:
    shutil.copytree(source / name, runtime / name, ignore=exclude, symlinks=True)
(runtime / 'bootstrap/cache').mkdir(parents=True)
shutil.copy2(source / 'bootstrap/app.php', runtime / 'bootstrap/app.php', follow_symlinks=False)
(runtime / 'public').mkdir()
for name in ['vendors', 'vendors_compressed', 'css', 'js', 'build', 'fonts', 'webfonts', 'favicon']:
    if (source / 'public' / name).is_dir():
        shutil.copytree(source / 'public' / name, runtime / 'public' / name, ignore=exclude, symlinks=True)
for name in ['artisan', 'composer.json', 'composer.lock']:
    shutil.copy2(source / name, runtime / name, follow_symlinks=False)
for name in ['index.php', 'favicon.ico', '.htaccess']:
    shutil.copy2(source / 'public' / name, runtime / 'public' / name, follow_symlinks=False)
(runtime / 'public/images').mkdir()
for name in ['image_loading.png', 'male-icon.jpg', 'female-icon.jpg', 'other-gender-icon.png', 'login-background.jpg', 'mountain.jpg']:
    if (source / 'public/images' / name).is_file():
        shutil.copy2(source / 'public/images' / name, runtime / 'public/images' / name, follow_symlinks=False)
validate(runtime, boundary=runtime)
for name in ['framework/cache/data', 'framework/sessions', 'framework/views', 'logs', 'app/private/avatars', 'app/private/logos', 'app/private/passport_photos']:
    (runtime / 'storage' / name).mkdir(parents=True, exist_ok=True)
key = base64.b64encode(secrets.token_bytes(32)).decode()
(runtime / '.env').write_text('APP_NAME="Smart School"\nAPP_ENV=local\nAPP_DEBUG=false\nAPP_KEY=base64:' + key + '\nAPP_URL=http://127.0.0.1:8025\nDB_CONNECTION=mysql\nDB_HOST=127.0.0.1\nDB_PORT=33318\nDB_DATABASE=smart_school_capture_demo\nDB_USERNAME=root\nDB_PASSWORD=\nCACHE_DRIVER=file\nSESSION_DRIVER=file\nQUEUE_CONNECTION=sync\nFILESYSTEM_DISK=local\nMAIL_MAILER=log\nBROADCAST_DRIVER=log\nLOG_CHANNEL=single\nIS_DEMO=true\nIS_NEPALI_DATE=false\nAPP_UNDER_MAINTENANCE=false\nBCRYPT_ROUNDS=4\n')
(runtime / '.env').chmod(0o600)
seeder = runtime / 'database/seeders/DatabaseSeeder.php'
text = seeder.read_text()
text = re.sub(r'\$user->email\s*=\s*"[^"]+";', '$user->email = "operator@demo.example.test";', text, count=1)
text = re.sub(r"'name'\s*=>\s*'[^']+'", "'name' => 'Demo Operator'", text, count=1)
text = re.sub(r'\$user->avatar\s*=\s*"[^"]+";', '$user->avatar = "http://127.0.0.1:8025/images/demo-avatar.svg";', text, count=1)
seeder.write_text(text)
(runtime / 'public/images/demo-academy.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 120"><rect width="120" height="120" rx="20" fill="#133842"/><path d="M20 76 45 33l15 26 14-19 26 36M32 88h56" fill="none" stroke="white" stroke-width="5"/><text x="60" y="107" font-size="11" font-family="sans-serif" text-anchor="middle" fill="white">DEMO ACADEMY</text></svg>')
(runtime / 'public/images/demo-avatar.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 160 160"><rect width="160" height="160" fill="#e6eff0"/><circle cx="80" cy="58" r="28" fill="#668b91"/><path d="M25 145a55 55 0 0 1 110 0" fill="#668b91"/><text x="80" y="154" text-anchor="middle" font-family="sans-serif" font-size="14" fill="#133842">DEMO</text></svg>')
print('Prepared isolated runtime:', runtime)
print('No environment files, SQL dumps, uploads, source Git data or cached config copied.')
