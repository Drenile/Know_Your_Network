"""Find the default router on Linux by reading the kernel's routing table.

/proc/net/route is a plain-text file that any normal user can read, so no program is
launched and no admin rights are needed. Each line looks like:

    Iface  Destination  Gateway   Flags  RefCnt  Use  Metric  Mask      ...
    eth0   00000000     0101A8C0  0003   0       0    100     00000000  ...

Addresses are hexadecimal in the machine's own byte order (little-endian on x86
and ARM), so 0101A8C0 is 192.168.1.1.
"""

import sys
from ipaddress import IPv4Address
from pathlib import Path
from typing import Final

ROUTE_TABLE: Final = Path("/proc/net/route")

_RTF_UP: Final = 0x1  # Route is usable.
_RTF_GATEWAY: Final = 0x2  # Route goes through a router.
_MIN_COLUMNS: Final = 8


def default_gateway() -> IPv4Address | None:
    """Return the router address, or None if this computer has no default route."""
    return parse_route_table(ROUTE_TABLE.read_text(encoding="ascii"))


def parse_route_table(text: str) -> IPv4Address | None:
    """Return the gateway of the best (lowest metric) usable default route."""
    lines = text.splitlines()[1:]  # The first line is the header.
    default_routes = [r for line in lines if (r := _parse_default_route(line))]
    return min(default_routes)[1] if default_routes else None


def _parse_default_route(line: str) -> tuple[int, IPv4Address] | None:
    """Return (metric, gateway) if the line is a usable default route, else None."""
    columns = line.split()
    if len(columns) < _MIN_COLUMNS:
        return None
    try:
        destination = int(columns[1], 16)
        gateway = int(columns[2], 16)
        flags = int(columns[3], 16)
        metric = int(columns[6])
        mask = int(columns[7], 16)
    except ValueError:
        return None

    wanted = _RTF_UP | _RTF_GATEWAY
    if destination != 0 or mask != 0 or flags & wanted != wanted:
        return None
    if not 0 < gateway < 1 << 32:
        return None
    return metric, IPv4Address(gateway.to_bytes(4, sys.byteorder))
