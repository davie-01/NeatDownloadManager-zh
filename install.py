#!/usr/bin/env python3
"""Install or restore a whole bundle, retaining the replaced bundle as a backup."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent


def fingerprint(app):
    return {str(p.relative_to(app)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(app.rglob('*')) if p.is_file()}


def verify(app):
    subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)


def ensure_stopped():
    result = subprocess.run(['pgrep', '-x', 'NeatDownloadManager'], capture_output=True)
    if result.returncode == 0:
        raise RuntimeError('NDM 仍在运行。请等待下载完成并使用“完全退出”后再安装/恢复')
    if result.returncode != 1:
        raise RuntimeError('无法检查 NDM 运行状态，停止操作')


def swap_bundle(source, target, verifier=verify, backup_dir=None):
    source, target = source.resolve(), target.resolve()
    backup_dir = (Path(backup_dir) if backup_dir is not None else ROOT / 'backup').resolve()
    if source == target or source in target.parents or target in source.parents:
        raise ValueError('来源与目标必须是不同的独立应用目录')
    if source == backup_dir or target == backup_dir or source in backup_dir.parents or target in backup_dir.parents:
        raise ValueError('备份目录不能位于来源或目标应用内部')
    if target.name != 'NeatDownloadManager.app' or not target.is_dir():
        raise ValueError('目标必须是已存在的 NeatDownloadManager.app')
    if not (source / 'Contents/MacOS/NeatDownloadManager').is_file():
        raise ValueError('来源不是完整的 NDM 应用')
    old_manifest = fingerprint(target)
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    backup_dir.mkdir(parents=True, exist_ok=True)
    backup = backup_dir / f'NeatDownloadManager.backup-{stamp}.app'
    record_path = backup.with_suffix('.json')
    with tempfile.TemporaryDirectory(prefix='.ndm-stage-', dir=target.parent) as temporary:
        staged = Path(temporary) / target.name
        subprocess.run(['ditto', str(source), str(staged)], check=True)
        if fingerprint(staged) != fingerprint(source):
            raise RuntimeError('复制校验失败，未更改当前应用')
        verifier(staged)
        # Copy, rather than rename, because the project may be on a different volume.
        with tempfile.TemporaryDirectory(prefix='.ndm-backup-', dir=backup_dir) as saved:
            copied = Path(saved) / target.name
            subprocess.run(['ditto', str(target), str(copied)], check=True)
            if fingerprint(copied) != old_manifest:
                raise RuntimeError('备份校验失败，未更改当前应用')
            os.rename(copied, backup)
            record = Path(saved) / 'record.json'
            record.write_text(json.dumps({'backup': str(backup), 'files': old_manifest}, ensure_ascii=False, indent=2) + '\n')
            os.rename(record, record_path)
        # Keep the original inode locally only during replacement, for reliable rollback.
        previous = Path(temporary) / 'previous.app'
        os.rename(target, previous)
        try:
            os.rename(staged, target)
            verifier(target)
        except BaseException:
            failed = Path(temporary) / 'failed.app'
            if target.exists():
                os.rename(target, failed)
            os.rename(previous, target)
            if failed.exists():
                subprocess.run(['ditto', str(failed), str(backup_dir / f'NeatDownloadManager.failed-{stamp}.app')], check=True)
            raise
    return backup, old_manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    install = sub.add_parser('install', help='安装已经构建并签名的完整应用')
    install.add_argument('--app', type=Path, default=ROOT / 'build/NeatDownloadManager.app')
    restore = sub.add_parser('restore', help='从安装时的记录恢复；会保留当前应用')
    restore.add_argument('--record', required=True, type=Path)
    parser.add_argument('--target', type=Path, default=Path('/Applications/NeatDownloadManager.app'))
    args = parser.parse_args(argv)
    ensure_stopped()
    if args.command == 'install':
        source, verifier = args.app, verify
    else:
        record = json.loads(args.record.read_text())
        source = Path(record['backup'])
        if fingerprint(source) != record['files']:
            raise ValueError('备份内容与记录不一致，停止恢复')
        # Restore the exact captured bundle, including its original signature.
        def verifier(app):
            if fingerprint(app) != record['files']:
                raise ValueError('恢复副本与备份不一致')
    backup, files = swap_bundle(source, args.target, verifier)
    record_path = backup.with_suffix('.json')
    print(f'完成：{args.target}\n保留的完整备份：{backup}\n恢复记录：{record_path}')
    print('请手动启动 NDM。安装不会自动中断下载或启动应用。')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        raise SystemExit(f'操作失败：{error}')
