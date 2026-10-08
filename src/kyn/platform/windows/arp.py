"""Ask one address for its hardware (MAC) address with SendARP (D-004).

SendARP needs no admin rights. If Windows already has a saved answer for the address
in its ARP table, it returns that without asking the network again, so a device that
left recently may still be listed (see D-023).

ctypes releases Python's GIL (the lock that lets only one thread run Python at a time)
during the call, so many threads can wait on SendARP at once.
"""

import ctypes
import sys
from ipaddress import IPv4Address
from typing import Final

from kyn.core.mac import MacAddress
from kyn.platform.windows.arp_reply import parse_arp_reply

if sys.platform != "win32":
    raise ImportError("kyn.platform.windows.arp only works on Windows.")

_NO_ERROR: Final = 0
# "No device answered." Windows Vista and later return ERROR_BAD_NET_NAME; older
# versions, and some drivers, return ERROR_GEN_FAILURE.
_NO_ANSWER: Final = frozenset({31, 67})
# The documentation requires room for two ULONGs, even though a MAC is 6 bytes.
_BUFFER_SIZE: Final = 8

_send_arp = ctypes.WinDLL("iphlpapi.dll").SendARP
_send_arp.argtypes = (
    ctypes.c_ulong,  # DestIP (IPAddr: the 4 address bytes in network order).
    ctypes.c_ulong,  # SrcIP: our own address, which picks the adapter to use.
    ctypes.c_void_p,  # Buffer that receives the MAC address.
    ctypes.POINTER(ctypes.c_ulong),  # In: buffer size. Out: bytes written.
)
_send_arp.restype = ctypes.c_ulong


def send_arp(target: IPv4Address, source: IPv4Address) -> MacAddress | None:
    """Return the target's MAC address, or None if nothing answered.

    Raises OSError for any other failure (for example, `source` is no longer this
    computer's address), because that means the whole scan is broken, not just
    that one device is absent.
    """
    buffer = ctypes.create_string_buffer(_BUFFER_SIZE)
    length = ctypes.c_ulong(_BUFFER_SIZE)
    result = _send_arp(_ip_addr(target), _ip_addr(source), buffer, ctypes.byref(length))
    if result in _NO_ANSWER:
        return None
    if result != _NO_ERROR:
        raise ctypes.WinError(result)
    return parse_arp_reply(buffer.raw, length.value)


def _ip_addr(address: IPv4Address) -> int:
    # IPAddr holds the bytes in network order, whatever this CPU's byte order is,
    # so reinterpret the packed bytes rather than converting the number.
    return ctypes.c_ulong.from_buffer_copy(address.packed).value
