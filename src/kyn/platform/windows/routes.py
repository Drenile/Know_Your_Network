"""Find the default router on Windows with GetIpForwardTable from iphlpapi.dll.

The function is called directly through ctypes: no program is launched, no text is
parsed, and no admin rights are needed. The same DLL provides SendARP (D-004).
"""

import ctypes
import sys
from ipaddress import IPv4Address
from typing import Final

from kyn.platform.windows.forward_table import parse_forward_table

if sys.platform != "win32":
    raise ImportError("kyn.platform.windows.routes only works on Windows.")

_NO_ERROR: Final = 0
_ERROR_INSUFFICIENT_BUFFER: Final = 122
_ERROR_NO_DATA: Final = 232
# The table can grow between "how big is it?" and "fill this buffer", so retry.
_ATTEMPTS: Final = 3

_get_ip_forward_table = ctypes.WinDLL("iphlpapi.dll").GetIpForwardTable
_get_ip_forward_table.argtypes = (
    ctypes.c_void_p,  # Buffer to fill, or None to ask for the size.
    ctypes.POINTER(ctypes.c_ulong),  # In: buffer size. Out: size needed.
    ctypes.c_int,  # Sort the table? (BOOL)
)
_get_ip_forward_table.restype = ctypes.c_ulong


def default_gateway() -> IPv4Address | None:
    """Return the router address, or None if this computer has no default route."""
    size = ctypes.c_ulong(0)
    buffer: ctypes.Array[ctypes.c_char] | None = None
    for _ in range(_ATTEMPTS):
        result = _get_ip_forward_table(buffer, ctypes.byref(size), 0)
        if result == _NO_ERROR and buffer is not None:
            return parse_forward_table(buffer.raw)
        if result == _ERROR_NO_DATA:
            return None
        if result != _ERROR_INSUFFICIENT_BUFFER:
            raise ctypes.WinError(result)
        buffer = ctypes.create_string_buffer(size.value)
    raise OSError("The routing table kept changing size. Please try again.")
