from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from quick_install import run_install


class QuickInstallTests(unittest.TestCase):
    def test_missing_original_stops_before_build_or_install(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'original/NeatDownloadManager.app'
            with patch('quick_install.build') as build, patch('quick_install.install_main') as install:
                with self.assertRaisesRegex(RuntimeError, 'original'):
                    run_install(source)
                build.assert_not_called()
                install.assert_not_called()

    def test_running_app_stops_before_build(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'original/NeatDownloadManager.app'
            target = Path(directory) / 'Applications/NeatDownloadManager.app'
            (source / 'Contents/MacOS').mkdir(parents=True)
            (source / 'Contents/MacOS/NeatDownloadManager').touch()
            target.mkdir(parents=True)
            with patch('quick_install.check_tools'), patch('quick_install.validate_source'), \
                    patch('quick_install.ensure_stopped', side_effect=RuntimeError('NDM 仍在运行')), \
                    patch('quick_install.build') as build, patch('quick_install.install_main') as install:
                with self.assertRaisesRegex(RuntimeError, '仍在运行'):
                    run_install(source, target)
                build.assert_not_called()
                install.assert_not_called()

    def test_failed_build_never_installs(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / 'original/NeatDownloadManager.app'
            target = Path(directory) / 'Applications/NeatDownloadManager.app'
            (source / 'Contents/MacOS').mkdir(parents=True)
            (source / 'Contents/MacOS/NeatDownloadManager').touch()
            target.mkdir(parents=True)
            with patch('quick_install.check_tools'), patch('quick_install.validate_source'), \
                    patch('quick_install.ensure_stopped'), \
                    patch('quick_install.build', side_effect=RuntimeError('签名验证失败')), \
                    patch('quick_install.install_main') as install:
                with self.assertRaisesRegex(RuntimeError, '签名验证失败'):
                    run_install(source, target)
                install.assert_not_called()
