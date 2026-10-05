"""Tests for the scan scope guard. No network is touched."""

import dataclasses
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address

import pytest

from kyn.core.scope import ScanScope, ScopeError


def scope(interface: str) -> ScanScope:
    return ScanScope.from_interface(IPv4Interface(interface))


# ------------------------------------------------------------ which networks


@pytest.mark.parametrize(
    "interface",
    [
        "192.168.1.23/24",  # The most common home setup.
        "10.0.0.5/24",
        "172.16.5.4/22",  # Largest allowed size.
        "172.31.255.1/24",  # Top edge of 172.16.0.0/12.
        "192.168.0.1/30",  # Smallest allowed size.
    ],
)
def test_accepts_private_home_networks(interface: str) -> None:
    assert scope(interface).network == IPv4Interface(interface).network


@pytest.mark.parametrize(
    ("interface", "reason"),
    [
        ("8.8.8.8/24", "not a private home network"),  # Public internet.
        ("100.64.1.2/24", "not a private home network"),  # Carrier-grade NAT.
        ("169.254.3.4/24", "not a private home network"),  # Link-local.
        ("127.0.0.1/24", "not a private home network"),  # Loopback.
        ("172.32.0.1/24", "not a private home network"),  # Just past 172.16.0.0/12.
        ("192.0.2.1/24", "not a private home network"),  # Documentation range.
        ("10.0.0.5/21", "larger than a home network"),  # One step too big.
        ("10.0.0.5/8", "larger than a home network"),
        ("192.168.1.1/31", "no other devices"),
        ("192.168.1.1/32", "no other devices"),
    ],
)
def test_refuses_networks_outside_scope(interface: str, reason: str) -> None:
    with pytest.raises(ScopeError, match=reason):
        scope(interface)


def test_refuses_own_address_outside_network() -> None:
    with pytest.raises(ScopeError, match="not inside"):
        ScanScope(
            network=IPv4Network("192.168.1.0/24"),
            own_address=IPv4Address("192.168.2.5"),
        )


def test_scope_cannot_be_changed_after_creation() -> None:
    home = scope("192.168.1.23/24")
    with pytest.raises(dataclasses.FrozenInstanceError):
        home.network = IPv4Network("8.8.8.0/24")  # type: ignore[misc]


# ------------------------------------------------------------ which addresses

HOME = "192.168.1.23/24"


def test_allows_another_device_on_the_network() -> None:
    assert scope(HOME).allows(IPv4Address("192.168.1.50"))


@pytest.mark.parametrize(
    "address",
    [
        IPv4Address("192.168.1.23"),  # This computer.
        IPv4Address("192.168.1.0"),  # Network address.
        IPv4Address("192.168.1.255"),  # Broadcast address.
        IPv4Address("192.168.2.50"),  # Neighbouring network.
        IPv4Address("8.8.8.8"),  # Public internet.
        IPv6Address("fe80::1"),  # Wrong IP version.
        "192.168.1.50",  # A string, not a parsed address.
        None,
    ],
)
def test_refuses_everything_else(address: object) -> None:
    home = scope(HOME)
    assert not home.allows(address)
    with pytest.raises(ScopeError, match="Refusing to contact"):
        home.require(address)


def test_require_returns_allowed_address() -> None:
    address = IPv4Address("192.168.1.50")
    assert scope(HOME).require(address) == address


def test_targets_are_every_other_host() -> None:
    home = scope(HOME)
    targets = list(home.targets())

    assert len(targets) == 253  # 254 hosts in a /24, minus this computer.
    assert IPv4Address("192.168.1.23") not in targets
    assert all(home.allows(address) for address in targets)
