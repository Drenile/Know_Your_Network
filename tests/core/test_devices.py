"""Tests for keeping only in-scope devices."""

from ipaddress import IPv4Address, IPv4Interface

from kyn.core.devices import Device, keep_in_scope
from kyn.core.mac import MacAddress
from kyn.core.scope import ScanScope

SCOPE = ScanScope.from_interface(IPv4Interface("192.168.1.23/24"))


def device(ip: str, mac: str = "3C:22:FB:1A:2B:3C") -> Device:
    return Device(IPv4Address(ip), MacAddress.parse(mac))


def test_keeps_in_scope_devices_sorted_by_ip() -> None:
    found = [device("192.168.1.100"), device("192.168.1.9"), device("192.168.1.1")]
    assert [str(d.ip) for d in keep_in_scope(SCOPE, found)] == [
        "192.168.1.1",
        "192.168.1.9",
        "192.168.1.100",
    ]


def test_drops_anything_outside_the_scope() -> None:
    found = [
        device("192.168.1.50"),
        device("192.168.2.50"),  # Another network the OS remembers.
        device("192.168.1.23"),  # This computer.
        device("192.168.1.255"),  # Broadcast.
        device("172.17.0.2"),  # Docker container.
    ]
    assert keep_in_scope(SCOPE, found) == [device("192.168.1.50")]


def test_one_entry_per_ip() -> None:
    found = [device("192.168.1.50", "AA:AA:AA:AA:AA:AA"), device("192.168.1.50")]
    assert len(keep_in_scope(SCOPE, found)) == 1
