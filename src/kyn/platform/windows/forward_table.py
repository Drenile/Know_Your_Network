"""Decode the bytes Windows returns from GetIpForwardTable (its IPv4 routing table).

This is plain Python with no Windows calls, so it can be tested on any OS. Layout,
from the MIB_IPFORWARDTABLE documentation:

    DWORD dwNumEntries                      4 bytes
    MIB_IPFORWARDROW table[dwNumEntries]    56 bytes each:
        dest, mask, policy, next_hop, if_index, type, proto, age, next_hop_as,
        metric1, metric2, metric3, metric4, metric5      (14 x 4 bytes)

Addresses are stored in network byte order, so they are read as raw 4-byte strings
and handed straight to IPv4Address.
"""

import struct
from ipaddress import IPv4Address
from typing import Final

_COUNT: Final = struct.Struct("<I")
# dest, mask, policy, next_hop, then 10 numbers starting with if_index.
_ROW: Final = struct.Struct("<4s4sI4s10I")
_METRIC1_INDEX: Final = 5  # Position of metric1 within the 10 numbers.
_ANY: Final = bytes(4)  # 0.0.0.0


def parse_forward_table(buffer: bytes) -> IPv4Address | None:
    """Return the gateway of the best (lowest metric1) default route.

    Returns None if there is no default route, or if the buffer is shorter than the
    entry count claims, because a damaged table must not be half-trusted.
    """
    if len(buffer) < _COUNT.size:
        return None
    (count,) = _COUNT.unpack_from(buffer, 0)
    if _COUNT.size + count * _ROW.size > len(buffer):
        return None

    default_routes = []
    for row in range(count):
        dest, mask, _policy, next_hop, *numbers = _ROW.unpack_from(
            buffer, _COUNT.size + row * _ROW.size
        )
        if dest == _ANY and mask == _ANY and next_hop != _ANY:
            default_routes.append((numbers[_METRIC1_INDEX], IPv4Address(next_hop)))
    return min(default_routes)[1] if default_routes else None
