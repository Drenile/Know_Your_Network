"""OS-specific code. This is the only module that checks which OS is running (D-006).

Each OS gets its own subpackage. The rest of the app calls the functions here and
never needs to know which one is in use.
"""

import sys
from ipaddress import IPv4Address

from kyn.core.devices import Device
from kyn.core.scope import ScanScope


class UnsupportedPlatformError(RuntimeError):
    """The app doesn't support this operating system yet (D-002)."""


def default_gateway() -> IPv4Address | None:
    """Return this computer's router address, or None if it has no default route."""
    if sys.platform == "win32":
        from kyn.platform.windows.routes import default_gateway as read_gateway
    elif sys.platform == "linux":
        from kyn.platform.linux.routes import default_gateway as read_gateway
    else:
        raise UnsupportedPlatformError(f"{sys.platform} is not supported yet.")
    return read_gateway()


def discover_devices(scope: ScanScope, interface_name: str) -> list[Device]:
    """Find the devices on the scanned network. Takes about 10 seconds."""
    if sys.platform == "linux":
        from kyn.platform.linux.discovery import discover

        return discover(scope, interface_name)
    else:
        raise UnsupportedPlatformError(
            f"Finding devices on {sys.platform} is not supported yet."
        )
