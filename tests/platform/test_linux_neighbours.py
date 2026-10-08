"""Tests for parsing /proc/net/arp text. Runs on every OS: it's just text parsing."""

from ipaddress import IPv4Address

import pytest

from kyn.core.devices import Device
from kyn.core.mac import MacAddress
from kyn.platform.linux.neighbours import parse_neighbour_table

HEADER = (
    "IP address       HW type     Flags       HW address            Mask     Device"
)
ROUTER = "192.168.1.1      0x1         0x2         aa:bb:cc:dd:ee:ff     *        wlan0"


def table(*rows: str) -> str:
    return "\n".join([HEADER, *rows]) + "\n"


def test_reads_complete_entries_on_the_chosen_adapter() -> None:
    assert parse_neighbour_table(table(ROUTER), "wlan0") == [
        Device(IPv4Address("192.168.1.1"), MacAddress.parse("aa:bb:cc:dd:ee:ff"))
    ]


@pytest.mark.parametrize(
    "row",
    [
        ROUTER.replace("wlan0", "docker0"),  # Another adapter.
        ROUTER.replace("0x2  ", "0x0  "),  # Incomplete: no answer.
        "192.168.1.9      0x1         0x0         00:00:00:00:00:00     *        wlan0",
        ROUTER.replace("0x1 ", "0x20"),  # Not Ethernet (InfiniBand).
        ROUTER.replace("192.168.1.1 ", "192.168.1.999"),  # Bad IP.
        ROUTER.replace("aa:bb:cc:dd:ee:ff", "aa:bb:cc:dd:ee:zz"),  # Bad MAC.
        ROUTER.replace("0x2  ", "zz   "),  # Bad flags.
        ROUTER + " extra",  # Wrong column count.
        "",
    ],
)
def test_skips_anything_else(row: str) -> None:
    assert parse_neighbour_table(table(row), "wlan0") == []
