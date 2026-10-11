"""Load the local Command W module without moving existing code or strings."""
import struct


def add_shortcuts(original):
    binary = bytearray(original)
    dependency = b'@executable_path/../Frameworks/NDMWindowShortcuts.dylib\0'
    size = (24+len(dependency)+7)//8*8
    command = struct.pack('<IIIIII', 0xc, size, 24, 0, 0x10000, 0x10000) + dependency
    command += b'\0' * (size-len(command))
    report = []
    for i in range(struct.unpack_from('>I', binary, 4)[0]):
        cpu, _, base, slice_size, _ = struct.unpack_from('>IIIII', binary, 8+i*20)
        count, command_size = struct.unpack_from('<II', binary, base+16)
        end = base+32+command_size
        assert end+size <= base+0x1100, 'Must not overlap the sidebar display hook'
        assert not any(binary[end:end+size])
        binary[end:end+size] = command
        struct.pack_into('<II', binary, base+16, count+1, command_size+size)
        report.append({'architecture': {0x1000007:'x86_64',0x100000c:'arm64'}[cpu],
            'new_load_command_offset': end, 'command_size': size})
    assert len(binary) == len(original)
    return bytes(binary), report
