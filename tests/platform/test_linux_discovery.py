"""Tests for nudging and discovery. No real packets: sending and waiting are faked."""

from ipaddress import IPv4Address, IPv4Interface

import pytest

from kyn.core.devices import Device
from kyn.core.mac import MacAddress
from kyn.core.scope import ScanScope, ScopeError
from kyn.platform.linux.discovery import SETTLE_SECONDS, discover
from kyn.platform.linux.nudge import send_nudges

SCOPE = ScanScope.from_interface(IPv4Interface("192.168.1.23/24"))


def no_wait(_seconds: float) -> None:
    pass


def test_nudges_every_target_once() -> None:
    sent: list[IPv4Address] = []
    send_nudges(SCOPE, SCOPE.targets(), send=sent.append, pause=no_wait)

    assert len(sent) == 253
    assert IPv4Address("192.168.1.23") not in sent


def test_refuses_an_out_of_scope_target_before_sending_to_it() -> None:
    sent: list[IPv4Address] = []
    targets = [IPv4Address("192.168.1.50"), IPv4Address("8.8.8.8")]

    with pytest.raises(ScopeError):
        send_nudges(SCOPE, targets, send=sent.append, pause=no_wait)

    assert sent == [IPv4Address("192.168.1.50")]


def test_a_failed_send_is_skipped() -> None:
    sent: list[IPv4Address] = []

    def flaky(address: IPv4Address) -> None:
        if address == IPv4Address("192.168.1.2"):
            raise OSError("No buffer space available")
        sent.append(address)

    send_nudges(SCOPE, SCOPE.targets(), send=flaky, pause=no_wait)
    assert len(sent) == 252


def test_discover_nudges_waits_then_reads_in_scope_devices() -> None:
    waits: list[float] = []
    router = Device(IPv4Address("192.168.1.1"), MacAddress.parse("AA:BB:CC:DD:EE:FF"))
    elsewhere = Device(IPv4Address("10.0.0.1"), MacAddress.parse("11:22:33:44:55:66"))

    def read(interface_name: str) -> list[Device]:
        assert interface_name == "wlan0"
        return [elsewhere, router]

    found = discover(SCOPE, "wlan0", send=lambda _: None, read=read, wait=waits.append)

    assert found == [router]
    assert waits[-1] == SETTLE_SECONDS
