"""Tests for the `kyn scan` flow. The OS is faked, so nothing touches a real network."""

import io
from collections.abc import Iterable, Mapping
from ipaddress import IPv4Address, IPv4Interface

from rich.console import Console

from kyn.cli.scan import EXIT_FAILED, EXIT_OK, ScanServices, run_scan
from kyn.core.devices import Device
from kyn.core.identify import VendorLookup
from kyn.core.mac import MacAddress
from kyn.core.scope import ScanScope
from kyn.core.vendors import VendorDataError, VendorDirectory

GATEWAY = IPv4Address("10.0.0.1")
HOME = {"Wi-Fi": [IPv4Interface("10.0.0.5/24")]}
ROUTER = Device(GATEWAY, MacAddress.parse("3C:2D:9E:49:1B:15"))


class FakeOS:
    """Records what the scan asked for, and returns canned answers."""

    def __init__(
        self,
        interfaces: Mapping[str, Iterable[IPv4Interface]] = HOME,
        discover_error: OSError | None = None,
    ) -> None:
        self.interfaces = interfaces
        self.discover_error = discover_error
        self.scanned: list[tuple[ScanScope, str]] = []

    def discover(self, scope: ScanScope, interface_name: str) -> list[Device]:
        self.scanned.append((scope, interface_name))
        if self.discover_error is not None:
            raise self.discover_error
        return [ROUTER]

    def services(self) -> ScanServices:
        return ScanServices(
            read_gateway=lambda: GATEWAY,
            read_interfaces=lambda: self.interfaces,
            discover=self.discover,
            load_vendors=lambda: VendorDirectory.from_lines([]),
        )


def run(
    fake: FakeOS, *, assume_yes: bool = False, answer: bool = True
) -> tuple[int, str]:
    buffer = io.StringIO()
    console = Console(file=buffer, color_system=None, width=120)
    code = run_scan(
        console, fake.services(), assume_yes=assume_yes, ask=lambda _: answer
    )
    return code, buffer.getvalue()


def test_shows_permission_screen_then_devices() -> None:
    fake = FakeOS()
    code, output = run(fake)

    assert code == EXIT_OK
    assert output.index("Before we scan") < output.index("Devices found: 1")
    assert "10.0.0.0/24 (253 addresses)" in output
    assert fake.scanned[0][1] == "Wi-Fi"
    assert "Nothing was saved." in output


def test_saying_no_scans_nothing() -> None:
    fake = FakeOS()
    code, output = run(fake, answer=False)

    assert code == EXIT_FAILED
    assert fake.scanned == []
    assert "Nothing was scanned." in output


def test_yes_flag_skips_the_question() -> None:
    fake = FakeOS()
    buffer = io.StringIO()

    def must_not_ask(_console: Console) -> bool:
        raise AssertionError("asked despite --yes")

    code = run_scan(
        Console(file=buffer), fake.services(), assume_yes=True, ask=must_not_ask
    )

    assert code == EXIT_OK
    assert len(fake.scanned) == 1


def test_refuses_a_network_too_large_before_asking() -> None:
    fake = FakeOS(interfaces={"eth0": [IPv4Interface("10.0.0.5/16")]})
    code, output = run(fake)

    assert code == EXIT_FAILED
    assert "Before we scan" not in output
    assert "larger than a home network" in output
    assert fake.scanned == []


def test_no_router_is_explained() -> None:
    fake = FakeOS(interfaces={})
    code, output = run(fake)

    assert code == EXIT_FAILED
    assert "Can't scan:" in output


def test_a_failed_discovery_is_explained_not_crashed() -> None:
    fake = FakeOS(discover_error=OSError("The adapter went away"))
    code, output = run(fake)

    assert code == EXIT_FAILED
    assert "Can't scan: The adapter went away" in output


def test_a_broken_manufacturer_list_stops_before_scanning() -> None:
    def broken() -> VendorLookup:
        raise VendorDataError("Manufacturer list is not valid UTF-8.")

    fake = FakeOS()
    services = ScanServices(
        read_gateway=lambda: GATEWAY,
        read_interfaces=lambda: HOME,
        discover=fake.discover,
        load_vendors=broken,
    )
    code = run_scan(Console(file=io.StringIO()), services, ask=lambda _: True)

    assert code == EXIT_FAILED
    assert fake.scanned == []
