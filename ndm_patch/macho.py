"""Small parsers and relative instruction encoders for the supported Mach-O."""
import struct

def macho(data, base=0):
    assert data[base:base+4] == b'\xcf\xfa\xed\xfe'
    count, command_size = struct.unpack_from('<II', data, base+16)
    pos = base+32
    sections = {}
    symtab = None
    for _ in range(count):
        cmd, size = struct.unpack_from('<II', data, pos)
        if cmd == 0x19:
            segment = data[pos+8:pos+24].split(b'\0')[0].decode()
            vmaddr, vmsize, fileoff, filesize = struct.unpack_from('<QQQQ', data, pos+24)
            nsections = struct.unpack_from('<I', data, pos+64)[0]
            for j in range(nsections):
                q = pos+72+j*80
                name = data[q:q+16].split(b'\0')[0].decode()
                section_segment = data[q+16:q+32].split(b'\0')[0].decode()
                address, length, offset = struct.unpack_from('<QQI', data, q+32)
                relocoff, nreloc = struct.unpack_from('<II', data, q+56)
                sections[(section_segment, name)] = {'address': address, 'length': length, 'offset': base+offset,
                    'relocoff': base+relocoff, 'nreloc': nreloc}
        elif cmd == 0x2:
            symtab = struct.unpack_from('<IIII', data, pos+8)
        pos += size
    return sections, symtab, command_size

def object_code(arch, object_dir):
    data = (object_dir / f'sidebar-{arch}.o').read_bytes()
    sections, symtab, _ = macho(data)
    section = sections[('__TEXT', '__text')]
    code = bytearray(data[section['offset']:section['offset']+section['length']])
    symoff, nsyms, stroff, strsize = symtab
    symbols = []
    names = {}
    for i in range(nsyms):
        string, typ, sec, desc, value = struct.unpack_from('<IBBHQ', data, symoff+i*16)
        end = data.index(0, stroff+string)
        name = data[stroff+string:end].decode()
        symbols.append((name, value))
        names[name] = value
    for j in range(section['nreloc']):
        location, info = struct.unpack_from('<II', data, section['relocoff']+j*8)
        index = info & 0xffffff
        pcrel = (info >> 24) & 1
        length = (info >> 25) & 3
        external = (info >> 27) & 1
        kind = info >> 28
        assert arch == 'x86_64' and pcrel == 1 and length == 2 and external == 1 and kind in [1, 2]
        addend = struct.unpack_from('<i', code, location)[0]
        struct.pack_into('<i', code, location, addend + symbols[index][1] - (location+4))
    return code, names

def arm_instruction(kind, pc, target, reg=0):
    delta = target-pc
    if kind in ['bl', 'b']:
        assert delta % 4 == 0 and -(1 << 27) <= delta < (1 << 27)
        return (0x94000000 if kind == 'bl' else 0x14000000) | ((delta//4) & 0x3ffffff)
    if kind == 'ldr':
        assert delta % 4 == 0 and -(1 << 20) <= delta < (1 << 20)
        return 0x58000000 | (((delta//4) & 0x7ffff) << 5) | reg
    assert kind == 'adr' and -(1 << 20) <= delta < (1 << 20)
    return 0x10000000 | ((delta & 3) << 29) | (((delta >> 2) & 0x7ffff) << 5) | reg

def bind(code, names, arch, address, refs):
    changes = {'_load_nsstring': ('nsstring', 'ldr', 0), '_load_utf8': ('utf8', 'ldr', 1),
               '_call_make': ('send', 'bl', 0), '_tail_send': ('send', 'b', 0)}
    for i, key in enumerate(['complete', 'incomplete', 'all', 'video', 'audio', 'compressed', 'document', 'misc'], 1):
        changes[f'_load_eq{i}'] = ('eq', 'ldr', 1)
        changes['_' + key] = (key, 'adr', 2)
        changes[f'_call_eq{i}'] = ('send', 'bl', 0)
    for name, (ref, kind, reg) in changes.items():
        offset = names[name]
        if arch == 'arm64':
            struct.pack_into('<I', code, offset, arm_instruction(kind, address+offset, refs[ref], reg))
        else:
            size = 6 if kind in ['bl', 'b'] else 7
            struct.pack_into('<i', code, offset+size-4, refs[ref]-(address+offset+size))
    return code

