"""Regression checks against a user-supplied original; no vendor binary is bundled."""
import json
import os
from pathlib import Path
import struct
import unittest

from build import ROOT, validate_source
from ndm_patch.localize import translate_constants
from ndm_patch.macho import macho


@unittest.skipUnless(os.environ.get('NDM_ORIGINAL_APP'), 'set NDM_ORIGINAL_APP to test the exact original binary')
class BinaryRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = Path(os.environ['NDM_ORIGINAL_APP'])
        validate_source(source)
        cls.original = (source / 'Contents/MacOS/NeatDownloadManager').read_bytes()
        cls.patched, cls.report = translate_constants(cls.original, json.loads((ROOT / 'data/translations.json').read_text()))
        cls.slices = []
        for i in range(struct.unpack_from('>I', cls.original, 4)[0]):
            _, _, base, _, _ = struct.unpack_from('>IIIII', cls.original, 8+i*20)
            sections, _, _ = macho(cls.original, base)
            cls.slices.append(sections)

    def test_cpp_ascii_storage_is_unchanged(self):
        for sections in self.slices:
            section = sections[('__TEXT', '__cstring')]
            start, length = section['offset'], section['length']
            self.assertEqual(self.original[start:start+length], self.patched[start:start+length])
        self.assertEqual(len(self.report), 26)

    def test_internal_category_and_status_objects_are_unchanged(self):
        expected = {b'Complete', b'Incomplete', b'All Downloads', b'Video', b'Audio', b'Compressed', b'Document', b'Misc'}
        for sections in self.slices:
            cs = sections[('__TEXT', '__cstring')]
            cf = next(s for (_, name), s in sections.items() if name == '__cfstring')
            found = set()
            for offset in range(cf['offset'], cf['offset']+cf['length'], 32):
                _, flags, pointer, length = struct.unpack_from('<QQQQ', self.original, offset)
                if flags != 0x7c8 or not cs['address'] <= pointer < cs['address']+cs['length']:
                    continue
                start = cs['offset'] + pointer - cs['address']
                value = self.original[start:start+length]
                if value in expected:
                    found.add(value)
                    self.assertEqual(self.original[offset:offset+32], self.patched[offset:offset+32])
            self.assertEqual(found, expected)
