"""Translate display references without rewriting images, actions or identities."""
import copy
import html
import plistlib
import re
import struct


def normalized(text):
    return re.sub(r'\s+', ' ', html.unescape(text)).strip()

UI_KEYS = {'NSContents', 'NSDev', 'NSWindowTitle', 'NSTitle', 'NSSegmentItemLabel',
           'NSToolbarItemLabel', 'NSToolbarItemPaletteLabel', 'NSToolbarItemToolTip'}


def translate_nibs(source_app, output_app, translations):
    mapping = {normalized(k): v for k, v in translations.items()}
    results = []
    for source in sorted((source_app / 'Contents/Resources').rglob('*.nib')):
        if not source.is_file():
            continue
        relative = source.relative_to(source_app)
        old = plistlib.loads(source.read_bytes())
        new = copy.deepcopy(old)
        objects = new['$objects']
        count = len(objects)
        replacements = {}
        changes = []
        for index in range(count):
            obj = objects[index]
            if not isinstance(obj, dict):
                continue
            class_ref = obj.get('$class')
            class_name = objects[class_ref.data].get('$classname', '') if isinstance(class_ref, plistlib.UID) else ''
            for key, value in list(obj.items()):
                if (key not in UI_KEYS and not (key == 'NSLabel' and class_name == 'NSTabViewItem')) or not isinstance(value, plistlib.UID):
                    continue
                english = objects[value.data]
                if not isinstance(english, str):
                    continue
                chinese = mapping.get(normalized(english))
                if chinese is None or chinese == english:
                    continue
                if chinese not in replacements:
                    replacements[chinese] = plistlib.UID(len(objects))
                    objects.append(chinese)
                obj[key] = replacements[chinese]
                changes.append({'object': index, 'key': key, 'from': english, 'to': chinese})
        encoded = plistlib.dumps(new, fmt=plistlib.FMT_BINARY, sort_keys=False)
        new = plistlib.loads(encoded)
        # Every original object is unchanged, except explicitly selected UI references.
        permitted = {(c['object'], c['key']) for c in changes}
        for i, obj in enumerate(old['$objects']):
            actual = new['$objects'][i]
            if isinstance(obj, dict):
                assert obj.keys() == actual.keys()
                for key, value in obj.items():
                    if (i, key) in permitted:
                        assert isinstance(actual[key], plistlib.UID)
                        assert actual[key].data >= count
                    else:
                        assert value == actual[key], (relative, i, key)
            else:
                assert obj == actual, (relative, i)
        for key in old.keys() - {'$objects'}:
            assert old[key] == new[key]
        (output_app / relative).write_bytes(encoded)
        results.append({'file': str(relative), 'changes': changes, 'original_objects': count})

    return results


def translate_constants(original_bytes, translations):
    mapping = {normalized(k): v for k, v in translations.items()}
    report = {'binary': []}
    binary = bytearray(original_bytes)
    assert binary[:4] == b'\xca\xfe\xba\xbe'
    categories = {name: mapping[normalized(name)] for name in ['New URL', 'Browsers', 'Settings', 'About', 'Total Quit', 'Resume', 'Stop', 'Delete', 'Redownload', 'Open', 'Open Folder', 'Show Window', 'Properties']}
    allowed_ranges = []
    fat_count = struct.unpack_from('>I', binary, 4)[0]
    assert fat_count == 2
    for architecture in range(fat_count):
        cpu, _, base, slice_size, _ = struct.unpack_from('>IIIII', binary, 8 + architecture * 20)
        assert binary[base:base+4] == b'\xcf\xfa\xed\xfe'
        command_count = struct.unpack_from('<I', binary, base + 16)[0]
        pos = base + 32
        sections = []
        for _ in range(command_count):
            cmd, size = struct.unpack_from('<II', binary, pos)
            if cmd == 0x19:
                section_count = struct.unpack_from('<I', binary, pos + 64)[0]
                for j in range(section_count):
                    q = pos + 72 + j * 80
                    name = binary[q:q+16].split(b'\0')[0].decode()
                    address, length, offset = struct.unpack_from('<QQI', binary, q + 32)
                    sections.append((name, address, length, base + offset))
            pos += size
        cstrings = next(s for s in sections if s[0] == '__cstring')
        cfstrings = next(s for s in sections if s[0] == '__cfstring')
        records = []
        for q in range(cfstrings[3], cfstrings[3] + cfstrings[2], 32):
            isa, flags, pointer, length = struct.unpack_from('<QQQQ', binary, q)
            if cstrings[1] <= pointer < cstrings[1] + cstrings[2]:
                offset = cstrings[3] + pointer - cstrings[1]
                text = original_bytes[offset:offset+length]
                records.append((q, flags, pointer, length, offset, text))
        found = set()
        storage_cursor = base + 0x1800
        storage_limit = next(s for s in sections if s[0] == "__text")[3]
        for q, flags, pointer, length, offset, text in records:
            try:
                english = text.decode('ascii')
            except UnicodeDecodeError:
                continue
            if english not in categories:
                continue
            assert english not in found
            found.add(english)
            assert flags == 0x7c8 and original_bytes[offset+length] == 0
            assert sum(p == pointer for _, _, p, _, _, _ in records) == 1
            chinese = categories[english]
            utf16 = chinese.encode('utf-16-le')
            # The same ASCII storage is referenced directly by C++ code. Keep it intact.
            assert storage_cursor % 2 == 0
            end = storage_cursor + len(utf16) + 2
            assert end <= storage_limit and not any(binary[storage_cursor:end])
            binary[storage_cursor:end] = utf16 + b'\0\0'
            new_pointer = 0x100000000 + storage_cursor - base
            struct.pack_into('<QQQ', binary, q+8, 0x7d0, new_pointer, len(utf16)//2)
            allowed_ranges.extend([(storage_cursor, end), (q+8, q+32)])
            assert binary[offset:offset+length+1] == original_bytes[offset:offset+length+1]
            storage_cursor = end
            report['binary'].append({'architecture': hex(cpu), 'from': english, 'to': chinese,
                                     'constant_offset': q, 'original_storage_offset': offset, 'storage_offset': base + new_pointer - 0x100000000, 'original_length': length})
        assert found == categories.keys()
        start, size = cstrings[3], cstrings[2]
        assert binary[start:start+size] == original_bytes[start:start+size]
    assert len(binary) == len(original_bytes)
    for i, (before, after) in enumerate(zip(original_bytes, binary)):
        if before != after:
            assert any(start <= i < end for start, end in allowed_ranges), i
    return bytes(binary), report['binary']
