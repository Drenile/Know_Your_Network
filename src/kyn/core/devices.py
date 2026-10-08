"""Devices found on the network, and the rule for which results we keep (A2)."""

from collections.abc import Iterable
from dataclasses import dataclass
from ipaddress import IPv4Address

from kyn.core.mac import MacAddress
from kyn.core.scope import ScanScope


@dataclass(frozen=True, slots=True, order=True)
class Device:
    """One device that answered on the network. Sorts by IP address."""

    ip: IPv4Address
    mac: MacAddress


def keep_in_scope(scope: ScanScope, found: Iterable[Device]) -> list[Device]:
    """Keep only devices inside the scanned network, one per IP, sorted by IP.

    The OS may also remember devices from other networks or from earlier traffic;
    those are dropped here so results never show anything outside the scope.
    """
    by_ip = {device.ip: device for device in found if scope.allows(device.ip)}
    return sorted(by_ip.values())
