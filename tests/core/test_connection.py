"""Tests for choosing this computer's home connection. No OS calls."""

from ipaddress import IPv4Address, IPv4Interface

import pytest

from kyn.core.connection import Connection, NoConnectionError, pick_connection

ROUTER = IPv4Address("192.168.1.1")


def test_picks_the_adapter_on_the_routers_network() -> None:
    interfaces = {
        "docker0": [IPv4Interface("172.17.0.1/16")],
        "lo": [IPv4Interface("127.0.0.1/8")],
        "vboxnet0": [IPv4Interface("192.168.56.1/24")],
        "wlan0": [IPv4Interface("192.168.1.23/24")],
    }
    assert pick_connection(ROUTER, interfaces) == Connection(
        "wlan0", IPv4Interface("192.168.1.23/24"), ROUTER
    )


def test_two_adapters_on_the_same_network_gives_a_stable_choice() -> None:
    interfaces = {
        "wlan0": [IPv4Interface("192.168.1.23/24")],
        "eth0": [IPv4Interface("192.168.1.24/24")],
    }
    assert pick_connection(ROUTER, interfaces).interface_name == "eth0"


def test_no_router_means_no_connection() -> None:
    with pytest.raises(NoConnectionError, match="No router found"):
        pick_connection(None, {"wlan0": [IPv4Interface("192.168.1.23/24")]})


def test_no_adapter_on_the_routers_network() -> None:
    with pytest.raises(NoConnectionError, match=r"same network as 192\.168\.1\.1"):
        pick_connection(ROUTER, {"eth0": [IPv4Interface("10.0.0.5/24")]})


def test_the_router_itself_is_not_this_computer() -> None:
    with pytest.raises(NoConnectionError):
        pick_connection(ROUTER, {"eth0": [IPv4Interface("192.168.1.1/24")]})
