#!/usr/bin/env python3
"""Build the complete patch from an exact, user-supplied original app."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import plistlib
import subprocess
import tempfile
from ndm_patch.localize import translate_nibs, translate_constants
from ndm_patch.sidebar import patch_sidebar
from ndm_patch.shortcuts import add_shortcuts
from install import fingerprint

ROOT = Path(__file__).resolve().parent
ARCHES = ('arm64', 'x86_64')


def run(*args):
    subprocess.run([str(a) for a in args], check=True)


def validate_source(app):
    expected = json.loads((ROOT / 'data/compatibility.json').read_text())
    info = plistlib.loads((app / 'Contents/Info.plist').read_bytes())
    if str(info.get('CFBundleShortVersionString')) != expected['version'] or str(info.get('CFBundleVersion')) != expected['build']:
        raise ValueError('仅支持原版 1.3 (Build 24)，通常称为 1.3.24')
    executable = app / 'Contents/MacOS/NeatDownloadManager'
    if hashlib.sha256(executable.read_bytes()).hexdigest() != expected['original_executable_sha256']:
        raise ValueError('主程序指纹不匹配：请选择未经汉化的原版备份，不能在已打补丁的应用上重复运行')
    nibs = {str(p.relative_to(app)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (app / 'Contents/Resources').rglob('*.nib') if p.is_file()}
    if nibs != expected['nibs']:
        raise ValueError('NIB 资源指纹不匹配，停止构建')


def compile_assembly(directory):
    for arch in ARCHES:
        run('xcrun', 'clang', '-arch', arch, '-c', ROOT / f'src/asm/sidebar-{arch}.s', '-o', directory / f'sidebar-{arch}.o')


def build(source, output):
    if __debug__ is False:
        raise RuntimeError('不能使用 python -O：补丁依赖结构断言进行安全校验')
    source, output = source.resolve(), output.resolve()
    if output == source or source in output.parents or output in source.parents:
        raise ValueError('构建目录不能覆盖或包含原应用')
    if output.exists():
        raise FileExistsError(f'输出已存在，请换一个路径或手动保留后移走：{output}')
    validate_source(source)
    run('codesign', '--verify', '--deep', '--strict', source)
    official_plugins = fingerprint(source / 'Contents/PlugIns')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='ndm-build-', dir=output.parent) as temporary:
        directory = Path(temporary)
        app = directory / 'NeatDownloadManager.app'
        run('ditto', source, app)
        compile_assembly(directory)
        translations = json.loads((ROOT / 'data/translations.json').read_text())
        report = {'version': '1.3.24', 'minimum_macos': '11.0'}
        report['nibs'] = translate_nibs(source, app, translations)
        executable = app / 'Contents/MacOS/NeatDownloadManager'
        binary, report['constants'] = translate_constants(executable.read_bytes(), translations)
        binary, report['sidebar'] = patch_sidebar(binary, directory)
        binary, report['shortcuts'] = add_shortcuts(binary)
        # Replace the staged inode: never modify a signed executable in place.
        executable.unlink()
        executable.write_bytes(binary)
        executable.chmod(0o755)
        library = app / 'Contents/Frameworks/NDMWindowShortcuts.dylib'
        library.parent.mkdir(exist_ok=True)
        slices = []
        for arch in ARCHES:
            thin = directory / f'NDMWindowShortcuts-{arch}.dylib'
            run('xcrun', 'clang', '-arch', arch, '-mmacosx-version-min=11.0', '-fobjc-arc', '-dynamiclib',
                '-framework', 'Cocoa', ROOT / 'src/NDMWindowShortcuts.m', '-o', thin,
                '-Wl,-install_name,@executable_path/../Frameworks/NDMWindowShortcuts.dylib')
            slices.append(thin)
        run('xcrun', 'lipo', '-create', *slices, '-output', library)
        run('codesign', '--force', '--sign', '-', library)
        # Do not re-sign the official Safari extension or strip its sandbox entitlements.
        run('codesign', '--force', '--sign', '-', app)
        run('codesign', '--verify', '--deep', '--strict', app)
        assert fingerprint(app / 'Contents/PlugIns') == official_plugins
        report['official_plugins_preserved'] = True
        report['display_reference_count'] = sum(len(n['changes']) for n in report['nibs'])
        report['signed_executable_sha256'] = hashlib.sha256(executable.read_bytes()).hexdigest()
        os.rename(app, output)
        (output.parent / (output.name + '.build-report.json')).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(f'构建成功：{output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, type=Path, help='未经修改的原版 1.3.24 .app')
    parser.add_argument('--output', type=Path, default=ROOT / 'build/NeatDownloadManager.app')
    args = parser.parse_args()
    try:
        build(args.source, args.output)
    except (ValueError, FileExistsError, FileNotFoundError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'构建失败：{error}\n')
