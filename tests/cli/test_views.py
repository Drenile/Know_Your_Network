"""Tests for how the permission screen and device table read."""

import io
from ipaddress import IPv4Address, IPv4Interface

from rich.console import Console, RenderableType

from kyn.cli.views import device_table, permission_screen
from kyn.core.connection import Connection
from kyn.core.devices import Device
from kyn.core.identify import IdentifiedDevice
from kyn.core.mac import MacAddress
from kyn.core.scope import ScanScope
from kyn.core.vendors import Vendor

CONNECTION = Connection(
    "Wi-Fi\x1b[2J", IPv4Interface("10.0.0.5/24"), IPv4Address("10.0.0.1")
)


def rendered(renderable: RenderableType) -> str:
    buffer = io.StringIO()
    Console(file=buffer, color_system=None, width=120).print(renderable)
    return buffer.getvalue()


def item(mac: str, vendor: Vendor | None = None, *, router: bool = False) -> str:
    device = Device(IPv4Address("10.0.0.9"), MacAddress.parse(mac))
    return rendered(device_table([IdentifiedDevice(device, vendor, router)]))


def test_permission_screen_explains_the_scan() -> None:
    output = rendered(
        permission_screen(CONNECTION, ScanScope.from_interface(CONNECTION.address))
    )

    assert "10.0.0.0/24 (253 addresses)" in output
    assert "10.0.0.1" in output
    assert "will not contact anything outside this network" in output


def test_permission_screen_cleans_the_adapter_name() -> None:
    output = rendered(
        permission_screen(CONNECTION, ScanScope.from_interface(CONNECTION.address))
    )

    assert "\x1b" not in output
    assert "Wi-Fi?[2J" in output


def test_known_maker_shows_its_full_name() -> None:
    output = item("3C:2D:9E:49:1B:15", Vendor("Vantiva", "Vantiva USA LLC"))
    assert "Vantiva USA LLC" in output


def test_unknown_maker() -> None:
    assert "Unknown" in item("D0:C9:07:0D:B7:EA")


def test_maker_registered_as_private_is_not_confused_with_private_address() -> None:
    output = item("00:01:01:12:34:56", Vendor("Private", "Private"))

    assert "Maker not disclosed" in output
    assert "Private address" not in output


def test_private_address_is_labelled() -> None:
    assert "Private address (privacy feature)" in item("C2:68:FD:A0:2E:97")


def test_router_is_labelled() -> None:
    assert "Router" in item("3C:2D:9E:49:1B:15", router=True)


def test_hostile_maker_name_is_cleaned() -> None:
    output = item("3C:2D:9E:49:1B:15", Vendor("x", "[bold]Evil\x1b[31m"))

    assert "\x1b" not in output
    assert "[bold]Evil?[31m" in output
