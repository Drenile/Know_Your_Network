"""Add what we know about each device found: its maker and whether it is the router.

This covers A3 and returns plain data. How it is worded and shown is up to the
interface (D-006).
"""

from collections.abc import Iterable
from dataclasses import dataclass
from ipaddress import IPv4Address
from typing import Protocol

from kyn.core.devices import Device
from kyn.core.mac import MacAddress
from kyn.core.vendors import Vendor


class VendorLookup(Protocol):
    """Anything that can name a maker from a MAC address, e.g. `VendorDirectory`."""

    def lookup(self, mac: MacAddress) -> Vendor | None: ...


@dataclass(frozen=True, slots=True)
class IdentifiedDevice:
    device: Device
    vendor: Vendor | None
    is_router: bool


def identify(
    devices: Iterable[Device], gateway: IPv4Address, vendors: VendorLookup
) -> list[IdentifiedDevice]:
    """Return each device with its maker (None if unknown) and router flag."""
    return [
        IdentifiedDevice(device, vendors.lookup(device.mac), device.ip == gateway)
        for device in devices
    ]
