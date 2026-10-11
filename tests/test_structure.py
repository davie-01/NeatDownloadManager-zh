from pathlib import Path
import plistlib
import struct
import tempfile
import unittest

from build import validate_source
from ndm_patch.localize import translate_nibs
from ndm_patch.shortcuts import add_shortcuts
from install import fingerprint, swap_bundle


class StructureTests(unittest.TestCase):
    def test_shared_resource_string_is_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / 'source.app'
            dest = Path(temporary) / 'output.app'
            for app in (source, dest):
                (app / 'Contents/Resources').mkdir(parents=True)
            nib = {'$objects': ['$null', {'NSTitle': plistlib.UID(2), 'NSResourceName': plistlib.UID(2),
                                        'NSAction': plistlib.UID(3)}, 'Resume', 'resume:'], '$top': {'root': plistlib.UID(1)}}
            path = 'Contents/Resources/Test.nib'
            (source / path).write_bytes(plistlib.dumps(nib, fmt=plistlib.FMT_BINARY))
            report = translate_nibs(source, dest, {'Resume': '继续'})
            result = plistlib.loads((dest / path).read_bytes())['$objects']
            self.assertEqual(result[1]['NSResourceName'], plistlib.UID(2))
            self.assertEqual(result[2], 'Resume')
            self.assertEqual(result[1]['NSAction'], plistlib.UID(3))
            self.assertEqual(result[result[1]['NSTitle'].data], '继续')
            self.assertEqual(len(report[0]['changes']), 1)

    def test_shortcut_command_cannot_overlap_sidebar(self):
        data = bytearray(0x2000)
        struct.pack_into('>II', data, 0, 0xcafebabe, 1)
        struct.pack_into('>IIIII', data, 8, 0x100000c, 0, 0x100, 0x1800, 0)
        struct.pack_into('<II', data, 0x110, 1, 0x10e0)
        with self.assertRaises(AssertionError):
            add_shortcuts(bytes(data))

    def test_version_gate_rejects_other_builds(self):
        with tempfile.TemporaryDirectory() as temporary:
            app = Path(temporary)
            (app / 'Contents').mkdir()
            (app / 'Contents/Info.plist').write_bytes(plistlib.dumps({'CFBundleShortVersionString': '1.3', 'CFBundleVersion': '25'}))
            with self.assertRaises(ValueError):
                validate_source(app)

    def test_failed_install_restores_original_bundle(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / 'NeatDownloadManager.app'
            source = root / 'built.app'
            for app, content in ((target, b'original'), (source, b'patched')):
                (app / 'Contents/MacOS').mkdir(parents=True)
                (app / 'Contents/MacOS/NeatDownloadManager').write_bytes(content)
            original = fingerprint(target)
            def verifier(app):
                if app == target.resolve():
                    raise RuntimeError('simulated installed verification failure')
            with self.assertRaises(RuntimeError):
                swap_bundle(source, target, verifier, backup_dir=root / 'project/backup')
            self.assertEqual(fingerprint(target), original)
            self.assertTrue(list((root / 'project/backup').glob('NeatDownloadManager.failed-*.app')))

    def test_install_retains_exact_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target, source = root / 'NeatDownloadManager.app', root / 'built.app'
            for app, content in ((target, b'old'), (source, b'new')):
                (app / 'Contents/MacOS').mkdir(parents=True)
                (app / 'Contents/MacOS/NeatDownloadManager').write_bytes(content)
            old = fingerprint(target)
            backup, manifest = swap_bundle(source, target, lambda app: None, backup_dir=root / 'project/backup')
            self.assertEqual(backup.parent, (root / 'project/backup').resolve())
            self.assertFalse(list(root.glob('NeatDownloadManager.backup-*.app')))
            self.assertTrue(backup.with_suffix('.json').is_file())
            self.assertEqual(manifest, old)
            self.assertEqual(fingerprint(backup), old)
            self.assertEqual(fingerprint(target), fingerprint(source))

    def test_backup_copy_failure_leaves_installed_app_untouched(self):
        from unittest.mock import patch
        import subprocess
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target, source = root / 'NeatDownloadManager.app', root / 'built.app'
            for app, content in ((target, b'old'), (source, b'new')):
                (app / 'Contents/MacOS').mkdir(parents=True)
                (app / 'Contents/MacOS/NeatDownloadManager').write_bytes(content)
            old = fingerprint(target)
            actual_run = subprocess.run
            def fail_backup(command, **kwargs):
                if command[:2] == ['ditto', str(target.resolve())]:
                    raise OSError('backup volume full')
                return actual_run(command, **kwargs)
            with patch('install.subprocess.run', side_effect=fail_backup):
                with self.assertRaisesRegex(OSError, 'volume full'):
                    swap_bundle(source, target, lambda app: None, backup_dir=root / 'project/backup')
            self.assertEqual(fingerprint(target), old)
            self.assertFalse(list(root.glob('.ndm-stage-*')))

    def test_restore_record_in_project_backup_restores_original(self):
        import json
        from unittest.mock import patch
        from install import main
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / 'project'
            project.mkdir()
            target, source = root / 'NeatDownloadManager.app', root / 'built.app'
            for app, content in ((target, b'old'), (source, b'new')):
                (app / 'Contents/MacOS').mkdir(parents=True)
                (app / 'Contents/MacOS/NeatDownloadManager').write_bytes(content)
            old = fingerprint(target)
            with patch('install.ROOT', project), patch('install.ensure_stopped'), patch('install.verify'):
                main(['--target', str(target), 'install', '--app', str(source)])
                record = next((project / 'backup').glob('*.json'))
                saved = json.loads(record.read_text())
                self.assertEqual(Path(saved['backup']).parent, (project / 'backup').resolve())
                main(['--target', str(target), 'restore', '--record', str(record)])
            self.assertEqual(fingerprint(target), old)
            self.assertEqual(len(list((project / 'backup').glob('*.app'))), 2)
            self.assertFalse(list(root.glob('NeatDownloadManager.backup-*.app')))
