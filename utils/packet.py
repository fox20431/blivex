__all__ = ['make_packet']

import collections
import struct
import json

header_struct = struct.Struct('>I2H2I')
HeaderTuple = collections.namedtuple('HeaderTuple', ('packet_len', 'header_len', 'ver', 'op', 'seq_id'))

def build(data: dict, operation: int):
    body = json.dumps(data).encode('UTF-8')
    header = header_struct.pack(*HeaderTuple(
        packet_len=header_struct.size + len(body),
        header_len=header_struct.size,
        ver=0,
        op=operation,
        seq_id=0
    ))
    return header + body

def parse_header(data):
    return HeaderTuple(*header_struct.unpack_from(data, 0))