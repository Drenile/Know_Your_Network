"""Tests for Windows discovery. No real ARP: the SendARP lookup is faked, so these run
on any OS."""

from ipaddress import IPv4Address, IPv4Interface

import pytest

from kyn.core.devices import Device
from kyn.core.mac import MacAddress
from kyn.core.scope import ScanScope, ScopeError
from kyn.platform.windows.discovery import discover, resolve_all

SCOPE = ScanScope.from_interface(IPv4Interface("192.168.1.23/24"))
ROUTER_IP = IPv4Address("192.168.1.1")
ROUTER_MAC = MacAddress.parse("AA:BB:CC:DD:EE:FF")


def nobody_answers(_address: IPv4Address) -> MacAddress | None:
    return None


def test_asks_every_target_once() -> None:
    asked: list[IPv4Address] = []

    def resolve(address: IPv4Address) -> MacAddress | None:
        asked.append(address)
        return None

    resolve_all(SCOPE, SCOPE.targets(), resolve)

    assert sorted(asked) == list(SCOPE.targets())
    assert IPv4Address("192.168.1.23") not in asked


def test_refuses_an_out_of_scope_target_without_contacting_it() -> None:
    asked: list[IPv4Address] = []

    def resolve(address: IPv4Address) -> MacAddress | None:
        asked.append(address)
        return None

    targets = [IPv4Address("192.168.1.50"), IPv4Address("8.8.8.8")]
    with pytest.raises(ScopeError):
        resolve_all(SCOPE, targets, resolve)

    assert IPv4Address("8.8.8.8") not in asked


def test_a_failed_lookup_stops_the_scan() -> None:
    def broken(_address: IPv4Address) -> MacAddress | None:
        raise OSError("The adapter went away")

    with pytest.raises(OSError, match="adapter"):
        resolve_all(SCOPE, SCOPE.targets(), broken)


def test_discover_returns_only_devices_that_answered_sorted_by_ip() -> None:
    phone_ip = IPv4Address("192.168.1.80")
    phone_mac = MacAddress.parse("3E:22:FB:1A:2B:3C")
    answers = {phone_ip: phone_mac, ROUTER_IP: ROUTER_MAC}

    found = discover(SCOPE, resolve=answers.get)

    assert found == [Device(ROUTER_IP, ROUTER_MAC), Device(phone_ip, phone_mac)]


def test_discover_finds_nothing_when_nobody_answers() -> None:
    assert discover(SCOPE, resolve=nobody_answers) == []
