#!/usr/bin/env python3
"""Validate, build and install from original/ with one command."""
import argparse
from datetime import datetime
import os
from pathlib import Path
import shutil
import subprocess
import sys

from build import build, validate_source
from install import ROOT, ensure_stopped, main as install_main

ORIGINAL = ROOT / 'original/NeatDownloadManager.app'
TARGET = Path('/Applications/NeatDownloadManager.app')


def check_tools():
    if sys.platform != 'darwin':
        raise RuntimeError('此安装脚本仅支持 macOS')
    if sys.version_info < (3, 9):
        raise RuntimeError('需要 Python 3.9 或更新版本')
    for name in ('xcrun', 'codesign', 'ditto'):
        if shutil.which(name) is None:
            raise RuntimeError(f'未找到 {name}。请先运行 xcode-select --install 安装命令行工具')
    for name in ('clang', 'lipo'):
        result = subprocess.run(['xcrun', '--find', name], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(f'编译工具 {name} 不可用。请先完成 xcode-select --install')


def run_install(source=ORIGINAL, target=TARGET, build_only=False):
    if not (source / 'Contents/MacOS/NeatDownloadManager').is_file():
        raise RuntimeError(
            f'未找到官方原版应用：\n{source}\n'
            '请打开官方 NeatDMInstaller.dmg，将其中的 NeatDownloadManager.app 完整复制到本项目 original 文件夹，'
            '然后重新运行 ./install.sh。不要放入 DMG 文件或已汉化的 App。')
    check_tools()
    print('正在校验原版 1.3 (Build 24)…', flush=True)
    validate_source(source)
    if not build_only:
        if target.name != 'NeatDownloadManager.app' or not target.is_dir():
            raise RuntimeError(f'未找到已安装的 NDM：{target}\n请先将官方应用安装到“应用程序”，再运行 ./install.sh')
        ensure_stopped()
        if not os.access(target.parent, os.W_OK | os.X_OK):
            raise RuntimeError(f'没有替换应用的权限：{target.parent}\n请使用有写权限的账户运行，或用 --build-only 构建后通过 Finder 安装')
    # Each run gets a fresh output; earlier builds and backups remain available.
    stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
    output = ROOT / 'build' / ('install-' + stamp) / 'NeatDownloadManager.app'
    print('正在构建中文界面及 Command-W 模块，并验证签名…', flush=True)
    build(source, output)
    if build_only:
        print(f'仅构建完成：{output}\n本次未替换已安装的应用。')
        return output
    print('正在备份并安装…', flush=True)
    # Reuse the installer, including its second process check immediately before replacement.
    install_main(['--target', str(target), 'install', '--app', str(output)])
    return output


def main():
    parser = argparse.ArgumentParser(description='把官方原版 App 放入 original/ 后，一条命令完成汉化安装')
    parser.add_argument('--build-only', action='store_true', help='只构建，保留当前已安装应用')
    parser.add_argument('--target', type=Path, default=TARGET, help='已安装的 NDM 路径，默认 /Applications/NeatDownloadManager.app')
    args = parser.parse_args()
    try:
        run_install(target=args.target, build_only=args.build_only)
    except (OSError, ValueError, RuntimeError, AssertionError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'安装失败：{error}\n')


if __name__ == '__main__':
    main()
