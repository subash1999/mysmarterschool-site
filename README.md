# Smart School product site

Plain HTML and CSS for the Smart School marketing site and role guides. No framework, application server, analytics, tracking scripts, remote fonts or paid services. The chosen theme is Himalayan Ink: navy, pine, white and Georgia headings. Demo requests go directly to LinkedIn.

## Preview and build

Run from this checkout:

```sh
python3 -m http.server 8035 --bind 127.0.0.1 --directory "$PWD"
python3 "$PWD/tools/build.py"
```

The build copies only the static site allowlist to `dist` and checks it against the exact file list in `deployment.json`. New public paths require a reviewed update to that list. cPanel builds with Python’s standard library; no Node runtime is needed on the host. See [DEPLOY.md](DEPLOY.md) before any deployment.

## Screenshots

There are 16 application screens at 1440×900 and 390×844: 32 optimized WebPs under `assets/screens`. [The manifest](assets/screens/manifest.json) records each screen, role, caption, viewport and app route. All data is synthetic. Demo Academy is fictional; fees and marks are illustrative.

### Reproduce the local demo

Prerequisites: the authorized private app checkout with its Composer dependencies installed, PHP, MySQL, Node, `cwebp`, and Chromium. The source checkout is read-only: the preparation script copies an explicit runtime allowlist, excluding every `.env*`, SQL dump, upload and cached config. Only the disposable copy is seeded and served.

1. Choose a new absolute runtime path matching `/private/tmp/smart-school-demo-…`. Set `APP_SOURCE` to the absolute source checkout and `DEMO_APP` to the new runtime path. Set `SITE_ROOT` to this checkout’s absolute path.

```sh
export SITE_ROOT="$PWD"
export DEMO_APP=/private/tmp/smart-school-demo-capture
python3 "$SITE_ROOT/tools/prepare-demo.py" --source "$APP_SOURCE" --runtime "$DEMO_APP"
```

2. Initialize a **new disposable** MySQL data directory. Do not use an existing database or MySQL configuration. These commands bind only loopback, disable MySQL X and use a separate socket and port. Leave the server running in its own terminal.

```sh
export DEMO_MYSQL=/private/tmp/smart-school-demo-capture-mysql
mysqld --no-defaults --initialize-insecure --datadir="$DEMO_MYSQL"
mysqld --no-defaults --datadir="$DEMO_MYSQL" --socket=/private/tmp/smart-school-demo-capture.sock --port=33318 --bind-address=127.0.0.1 --mysqlx=OFF --skip-log-bin
```

3. Create only the dedicated empty demo database. Run the app’s complete `DatabaseSeeder`, wait for success, then apply the synthetic supplement. Do not run those steps concurrently. No school environment file or SQL import is used.

```sh
mysql --no-defaults --socket=/private/tmp/smart-school-demo-capture.sock --user=root -e 'CREATE DATABASE smart_school_capture_demo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'
php "$DEMO_APP/artisan" migrate --seed --force
php "$SITE_ROOT/tools/seed-demo.php" "$DEMO_APP"
```

The supplement refuses any host, port or database other than this local demo configuration. It replaces all identities and contacts with generated demo records, creates sample marks/attendance/bills and writes an untracked runtime capture context. The demo-only password and reduced hashing cost are for this isolated runtime.

4. Serve the disposable app. Run this in a separate terminal from its public directory; Laravel’s development router uses that working directory.

```sh
cd "$DEMO_APP/public"
php -S 127.0.0.1:8025 -t "$DEMO_APP/public" "$DEMO_APP/vendor/laravel/framework/src/Illuminate/Foundation/resources/server.php"
```

5. In this site checkout, install the pinned capture-only tooling, then capture. The script logs in through the real login/role-selection routes. It permits only the dedicated loopback app and named static asset CDNs; tenant hosts are blocked.

```sh
cd "$SITE_ROOT"
npm ci
npx playwright install chromium
node "$SITE_ROOT/tools/capture.mjs"
```

If Chromium is already installed, `CHROMIUM_EXECUTABLE` may point to its absolute executable path. `PLAYWRIGHT_MODULE` may point to an already-installed Playwright module’s absolute entrypoint instead of installing another copy. `CAPTURE_ONLY=guardian-results,accountant-monthly-bills` refreshes selected screens in an existing manifest. Do not use these tools with production data.

### Verify

```sh
node --test "$PWD/tools/safety.test.mjs"
python3 -m unittest discover -s "$PWD/tools" -p '*_test.py'
python3 "$PWD/tools/check-static.py"
node "$PWD/tools/check-site.mjs"
```

The browser check uses the local server on port 8035. Reports are in `reports`. Lighthouse results are local measurements; recheck the public site after deployment. Existing server configuration is preserved; no `.htaccess` is published. Host Python and the complete Domains UI were checked; SSH host identity is verified, but the existing Actions deployment key still needs configuring in the new repo.
