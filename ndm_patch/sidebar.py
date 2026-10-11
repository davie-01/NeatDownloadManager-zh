"""Patch only the sidebar's final text setter; leave status and image names intact."""
import struct
from .macho import macho, object_code, bind, arm_instruction


def patch_sidebar(before, object_dir):
    binary = bytearray(before)
    report = []
    bindings = {
        'arm64': {'eq': 0x1000d4c70, 'utf8': 0x1000d48f0, 'nsstring': 0x1000d5b50,
            'send': 0x100077b88, 'callsite': 0x100044334},
        'x86_64': {'eq': 0x1000dcab0, 'utf8': 0x1000dc730, 'nsstring': 0x1000dda48,
            'send': 0x1000cc128, 'callsite': 0x100046525},
    }
    allowed = []
    for i in range(struct.unpack_from('>I', binary, 4)[0]):
        cpu, _, base, slice_size, _ = struct.unpack_from('>IIIII', binary, 8+i*20)
        arch = {0x1000007: 'x86_64', 0x100000c: 'arm64'}[cpu]
        sections, _, command_size = macho(binary, base)
        cf = next(s for (seg, name), s in sections.items() if name == '__cfstring')
        cs = sections[('__TEXT', '__cstring')]
        refs = dict(bindings[arch])
        constants = {}
        labels = {'Complete': 'complete', 'Incomplete': 'incomplete', 'All Downloads': 'all',
                  'Video': 'video', 'Audio': 'audio', 'Compressed': 'compressed', 'Document': 'document', 'Misc': 'misc'}
        for q in range(cf['offset'], cf['offset']+cf['length'], 32):
            isa, flags, ptr, length = struct.unpack_from('<QQQQ', binary, q)
            if cs['address'] <= ptr < cs['address']+cs['length'] and flags == 0x7c8:
                offset = cs['offset'] + ptr - cs['address']
                text = bytes(binary[offset:offset+length])
                if text.decode('ascii', errors='replace') in labels:
                    constants[text.decode()] = (q, length, offset)
                    refs[labels[text.decode()]] = cf['address'] + q - cf['offset']
        assert constants.keys() == labels.keys()
        text = sections[('__TEXT', '__text')]
        cave_offset = 0x1100
        assert 32+command_size <= cave_offset
        cave_address = 0x100000000+cave_offset
        code, names = object_code(arch, object_dir)
        assert len(code) <= 0x700
        assert base+cave_offset+len(code) < text['offset']
        assert not any(binary[base+cave_offset:base+cave_offset+len(code)])
        bind(code, names, arch, cave_address, refs)
        binary[base+cave_offset:base+cave_offset+len(code)] = code
        allowed.append((base+cave_offset, base+cave_offset+len(code)))
        site = text['offset']+refs['callsite']-text['address']
        if arch == 'arm64':
            assert struct.unpack_from('<I', binary, site)[0] == arm_instruction('bl', refs['callsite'], refs['send'])
            struct.pack_into('<I', binary, site, arm_instruction('bl', refs['callsite'], cave_address))
            allowed.append((site, site+4))
        else:
            assert bytes(binary[site:site+2]) == b'\xff\x15'
            assert refs['callsite']+6+struct.unpack_from('<i', binary, site+2)[0] == refs['send']
            binary[site:site+6] = b'\xe8'+struct.pack('<i', cave_address-(refs['callsite']+5))+b'\x90'
            allowed.append((site, site+6))
        for q, length, offset in constants.values():
            assert binary[q:q+32] == before[q:q+32]
            assert binary[offset:offset+length+1] == before[offset:offset+length+1]
        report.append({'architecture': arch, 'callsite': hex(refs['callsite']), 'hook': hex(cave_address),
            'hook_size': len(code), 'status_constants_unchanged': True})
    assert len(binary) == len(before)
    for i, (old, new) in enumerate(zip(before, binary)):
        if old != new:
            assert any(start <= i < end for start, end in allowed), i
    return bytes(binary), report
