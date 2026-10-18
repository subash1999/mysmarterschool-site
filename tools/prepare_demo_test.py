from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid
import shutil


class PreparationTests(unittest.TestCase):
    def make_source(self, directory):
        source = Path(directory).resolve()
        for name in ['app', 'config', 'database/seeders', 'resources', 'routes', 'vendor', 'bootstrap', 'public']:
            (source / name).mkdir(parents=True, exist_ok=True)
        for name in ['vendor/autoload.php', 'bootstrap/app.php', 'artisan', 'composer.json', 'composer.lock', 'public/index.php', 'public/favicon.ico', 'public/.htaccess', 'database/seeders/DatabaseSeeder.php']:
            (source / name).write_text('synthetic fixture')
        return source

    def runtime(self):
        runtime = Path('/private/tmp' if Path('/private/tmp').is_dir() else '/tmp') / ('smart-school-demo-preflight-' + uuid.uuid4().hex)
        self.addCleanup(lambda: shutil.rmtree(runtime) if runtime.exists() else None)
        return runtime

    def prepare(self, source, runtime):
        return subprocess.run([sys.executable, str(Path(__file__).resolve().with_name('prepare-demo.py')), '--source', str(source), '--runtime', str(runtime)], capture_output=True, text=True)

    def test_external_symlink_is_rejected_before_runtime_creation(self):
        with tempfile.TemporaryDirectory(prefix='smart-school-source-fixture-') as directory:
            source = self.make_source(directory)
            outside = source / 'synthetic-upload.txt'
            outside.write_text('synthetic private upload fixture')
            (source / 'app/linked-upload.txt').symlink_to(outside)
            runtime = self.runtime()
            result = self.prepare(source, runtime)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(runtime.exists(), result.stdout + result.stderr)
            self.assertEqual(outside.read_text(), 'synthetic private upload fixture')

    def test_compressed_dumps_and_local_databases_are_excluded(self):
        with tempfile.TemporaryDirectory(prefix='smart-school-source-fixture-') as directory:
            source = self.make_source(directory)
            names = ['synthetic.sql.gz', 'synthetic.sqlite', 'synthetic.db']
            for name in names:
                (source / 'database' / name).write_text('synthetic forbidden database fixture')
            runtime = self.runtime()
            result = self.prepare(source, runtime)
            self.assertEqual(result.returncode, 0, result.stderr)
            for name in names:
                self.assertFalse((runtime / 'database' / name).exists(), name)

    def test_symlinked_input_ancestors_are_rejected_before_runtime_creation(self):
        for ancestor in ['public/images', 'public', 'bootstrap']:
            with self.subTest(ancestor=ancestor), tempfile.TemporaryDirectory(prefix='smart-school-source-fixture-') as directory, tempfile.TemporaryDirectory(prefix='smart-school-outside-fixture-') as outside_directory:
                source = self.make_source(directory)
                outside = Path(outside_directory)
                linked_path = source / ancestor
                if linked_path.exists():
                    shutil.copytree(linked_path, outside, dirs_exist_ok=True)
                    shutil.rmtree(linked_path)
                (outside / 'login-background.jpg').write_text('synthetic outside image')
                linked_path.symlink_to(outside, target_is_directory=True)
                runtime = self.runtime()
                result = self.prepare(source, runtime)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertFalse(runtime.exists(), result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
