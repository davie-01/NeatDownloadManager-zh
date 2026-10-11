#!/usr/bin/env python3
"""Portable structure tests and native harnesses; no original app is required."""
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build import compile_assembly
from ndm_patch.macho import object_code


def run(*args):
    subprocess.run([str(a) for a in args], check=True, cwd=ROOT)


if __name__ == '__main__':
    run(sys.executable, '-m', 'unittest', 'discover', '-s', ROOT / 'tests', '-v')
    with tempfile.TemporaryDirectory(prefix='ndm-tests-') as temporary:
        directory = Path(temporary)
        compile_assembly(directory)
        keys = ['complete', 'incomplete', 'all', 'video', 'audio', 'compressed', 'document', 'misc']
        names_in_order = []
        targets, kinds, registers = [], [], []
        for i, key in enumerate(keys, 1):
            names_in_order.extend([f'_load_eq{i}', '_' + key, f'_call_eq{i}'])
            targets.extend([2048, 2112 + (i-1)*32, 2080])
            kinds.extend([0, 1, 2])
            registers.extend([1, 2, 0])
        names_in_order.extend(['_load_nsstring', '_load_utf8', '_call_make', '_tail_send'])
        targets.extend([2064, 2056, 2080, 2080])
        kinds.extend([0, 0, 2, 3])
        registers.extend([0, 1, 0, 0])
        header = []
        for index, arch in enumerate(('arm64', 'x86_64')):
            code, names = object_code(arch, directory)
            (directory / f'template-{arch}.bin').write_bytes(code)
            header.append('#if defined(__aarch64__)' if index == 0 else '#else')
            header.append('static const int offsets[] = {' + ','.join(str(names[n]) for n in names_in_order) + '};')
        header.append('#endif')
        for name, values in [('targets', targets), ('kinds', kinds), ('registers', registers)]:
            header.append('static const int ' + name + '[] = {' + ','.join(map(str, values)) + '};')
        (directory / 'hook-offsets.h').write_text('\n'.join(header) + '\n')
        for arch in ('arm64', 'x86_64'):
            for name, framework in [('sidebar', 'Foundation'), ('window_shortcuts', 'Cocoa')]:
                executable = directory / f'test-{name}-{arch}'
                run('xcrun', 'clang', '-arch', arch, '-mmacosx-version-min=11.0', '-fobjc-arc',
                    '-framework', framework, '-I', directory, ROOT / f'tests/test_{name}.m', '-o', executable)
                # Intel Macs cannot run arm64. Apple Silicon needs Rosetta for x86_64.
                if platform.machine() == 'x86_64' and arch == 'arm64':
                    print('SKIP arm64 execution on Intel; compilation passed')
                    continue
                arguments = [str(executable)]
                if name == 'sidebar':
                    arguments.append(str(directory / f'template-{arch}.bin'))
                run('arch', '-' + arch, *arguments)
    print('全部可执行检查通过')
