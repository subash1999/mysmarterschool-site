import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
from io import StringIO

script = Path(__file__).resolve().with_name('deploy.py')
deploy = None
if script.exists():
    spec = importlib.util.spec_from_file_location('deploy', script)
    deploy = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(deploy)


class DeploymentTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(deploy, 'The guarded deployment implementation is missing')
        self.temporary = tempfile.TemporaryDirectory(prefix='smart-school-deploy-test-')
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name).resolve()
        self.source = self.base / 'dist'
        self.target = self.base / 'marketing'
        self.backups = self.base / 'backups'
        self.source.mkdir()
        self.target.mkdir()
        (self.source / 'index.html').write_text('<title>Smart School</title>')
        (self.source / 'assets').mkdir()
        (self.source / 'assets/site.css').write_text('body{color:#133842}')
        (self.target / 'index.html').write_text('old blank index')
        self.sentinel = self.base / 'other-site.html'
        self.sentinel.write_text('leave untouched')

    def publish(self, allowed=None):
        return deploy.publish(self.source, self.target, self.backups,
                              allowed if allowed is not None else {'index.html', 'assets/site.css'})

    def assert_unchanged(self):
        self.assertEqual((self.target / 'index.html').read_text(), 'old blank index')
        self.assertEqual(self.sentinel.read_text(), 'leave untouched')
        self.assertFalse(self.backups.exists())

    def test_unplanned_static_file_causes_zero_writes(self):
        (self.source / 'assets/unrelated.html').write_text('unreviewed file')
        with self.assertRaises(ValueError):
            self.publish()
        self.assert_unchanged()

    def test_missing_planned_file_causes_zero_writes(self):
        with self.assertRaises(ValueError):
            self.publish({'index.html', 'assets/site.css', 'about/index.html'})
        self.assert_unchanged()

    def test_destination_directory_collision_causes_zero_writes(self):
        (self.target / 'assets').write_text('preserve unrelated file')
        with self.assertRaises(ValueError):
            self.publish()
        self.assert_unchanged()

    def test_approved_public_html_publish_preserves_server_configuration(self):
        self.target = self.base / 'public_html'
        self.target.mkdir()
        (self.target / 'index.html').write_text('old blank index')
        (self.target / '.htaccess').write_text('existing server configuration')
        backup = self.publish()
        self.assertEqual((backup / 'index.html').read_text(), 'old blank index')
        self.assertEqual((self.target / 'index.html').read_text(), '<title>Smart School</title>')
        self.assertEqual((self.target / '.htaccess').read_text(), 'existing server configuration')

    def test_backup_failure_causes_zero_destination_writes(self):
        (self.target / 'assets').mkdir()
        (self.target / 'assets/site.css').write_text('old stylesheet')
        real_copy = deploy.shutil.copy2
        count = 0
        def fail_second_backup(source, destination):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError('synthetic backup failure')
            return real_copy(source, destination)
        with patch.object(deploy.shutil, 'copy2', side_effect=fail_second_backup), self.assertRaises(OSError):
            self.publish()
        self.assertEqual((self.target / 'index.html').read_text(), 'old blank index')
        self.assertEqual((self.target / 'assets/site.css').read_text(), 'old stylesheet')

    def test_partial_publication_failure_reports_the_completed_backup(self):
        (self.target / 'assets').mkdir()
        (self.target / 'assets/site.css').write_text('old stylesheet')
        real_replace = deploy.os.replace
        count = 0
        def fail_second_replace(source, destination):
            nonlocal count
            count += 1
            if count == 2:
                raise OSError('synthetic publication failure')
            return real_replace(source, destination)
        output = StringIO()
        with redirect_stdout(output), patch.object(deploy.os, 'replace', side_effect=fail_second_replace), self.assertRaises(OSError):
            self.publish()
        backups = list(self.backups.iterdir())
        self.assertEqual(len(backups), 1)
        self.assertIn(str(backups[0]), output.getvalue())
        self.assertEqual((backups[0] / 'index.html').read_text(), 'old blank index')
        self.assertEqual((backups[0] / 'assets/site.css').read_text(), 'old stylesheet')
        self.assertEqual((self.target / 'assets/site.css').read_text(), 'body{color:#133842}')

    def test_server_configuration_is_never_published(self):
        (self.source / '.htaccess').write_text('synthetic server configuration')
        with self.assertRaises(ValueError):
            self.publish()
        self.assert_unchanged()

    def test_symlinked_destination_cannot_write_outside_target(self):
        outside = self.base / 'unrelated'
        outside.mkdir()
        (self.target / 'assets').symlink_to(outside, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.publish()
        self.assert_unchanged()
        self.assertEqual(list(outside.iterdir()), [])

    def test_unexpected_source_file_causes_zero_writes(self):
        (self.source / '.env').write_text('synthetic forbidden fixture')
        with self.assertRaises(ValueError):
            self.publish()
        self.assert_unchanged()

    def test_source_symlink_causes_zero_writes(self):
        (self.source / 'assets/leak.txt').symlink_to(self.sentinel)
        with self.assertRaises(ValueError):
            self.publish()
        self.assert_unchanged()

    def test_valid_publish_backs_up_before_overwriting_and_preserves_other_files(self):
        (self.target / 'keep.txt').write_text('preserve')
        backup = self.publish()
        self.assertEqual((backup / 'index.html').read_text(), 'old blank index')
        self.assertEqual((self.target / 'index.html').read_text(), '<title>Smart School</title>')
        self.assertTrue((self.target / 'assets/site.css').exists())
        self.assertEqual((self.target / 'keep.txt').read_text(), 'preserve')
        self.assertEqual(self.sentinel.read_text(), 'leave untouched')

    def test_missing_or_unconfigured_document_root_is_refused(self):
        for value in [None, '', '/home/subashnc/mysmarterschool.com', '/home/subashnc/some-other-domain']:
            with self.assertRaises(ValueError):
                deploy.configured_root({'domain': 'mysmarterschool.com', 'document_root': value})

    def test_only_owner_approved_root_can_be_configured(self):
        self.assertEqual(deploy.configured_root({'domain': 'mysmarterschool.com', 'document_root': '/home/subashnc/public_html'}), Path('/home/subashnc/public_html'))

    def test_only_normalized_static_paths_can_be_configured(self):
        for name in ['/index.html', '../index.html', './index.html', 'assets/../index.html', 'assets//file.webp', '.htaccess', 'assets/private.php', 'assets/.private.json']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                deploy.configured_files({'files': ['index.html', name]})

    def test_missing_or_duplicate_file_lists_are_refused(self):
        for files in [None, [], ['index.html', 'index.html'], ['assets/site.css']]:
            with self.subTest(files=files), self.assertRaises(ValueError):
                deploy.configured_files({'files': files})

    def test_valid_file_list_is_accepted(self):
        self.assertEqual(deploy.configured_files({'files': ['index.html', 'assets/site.css']}), {'index.html', 'assets/site.css'})


if __name__ == '__main__':
    unittest.main()
