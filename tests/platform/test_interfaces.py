"""Tests for listing adapters. psutil is replaced with fake data."""

import socket
from ipaddress import IPv4Interface
from types import SimpleNamespace

import psutil
import pytest

from kyn.platform.interfaces import interface_addresses


def address(family: int, value: str, netmask: str | None) -> SimpleNamespace:
    return SimpleNamespace(family=family, address=value, netmask=netmask)


def test_lists_valid_ipv4_addresses_of_adapters_that_are_up(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_addresses = {
        "wlan0": [
            address(socket.AF_INET, "192.168.1.23", "255.255.255.0"),
            address(socket.AF_INET6, "fe80::1", "ffff:ffff:ffff:ffff::"),  # IPv6.
            address(socket.AF_INET, "192.168.1.99", None),  # No mask.
            address(socket.AF_INET, "not-an-address", "255.255.255.0"),
        ],
        "eth1": [address(socket.AF_INET, "10.0.0.5", "255.255.255.0")],  # Down.
        "ghost": [address(socket.AF_INET, "10.9.9.9", "255.255.255.0")],  # No stats.
    }
    fake_stats = {
        "wlan0": SimpleNamespace(isup=True),
        "eth1": SimpleNamespace(isup=False),
    }
    monkeypatch.setattr(psutil, "net_if_addrs", lambda: fake_addresses)
    monkeypatch.setattr(psutil, "net_if_stats", lambda: fake_stats)

    assert interface_addresses() == {"wlan0": [IPv4Interface("192.168.1.23/24")]}
