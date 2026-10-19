"""Tests for adding maker and router details to found devices."""

from ipaddress import IPv4Address

from kyn.core.devices import Device
from kyn.core.identify import identify
from kyn.core.mac import MacAddress
from kyn.core.vendors import VendorDirectory

VENDORS = VendorDirectory.from_lines(["3C:2D:9E\tVantiva\tVantiva USA LLC"])
ROUTER = Device(IPv4Address("10.0.0.1"), MacAddress.parse("3C:2D:9E:49:1B:15"))
UNKNOWN = Device(IPv4Address("10.0.0.12"), MacAddress.parse("D0:C9:07:0D:B7:EA"))


def test_marks_the_router_and_names_known_makers() -> None:
    router, unknown = identify([ROUTER, UNKNOWN], IPv4Address("10.0.0.1"), VENDORS)

    assert router.is_router
    assert router.vendor is not None
    assert router.vendor.short_name == "Vantiva"
    assert not unknown.is_router
    assert unknown.vendor is None


def test_keeps_the_order_it_was_given() -> None:
    found = identify([UNKNOWN, ROUTER], IPv4Address("10.0.0.1"), VENDORS)
    assert [item.device for item in found] == [UNKNOWN, ROUTER]
