"""Tests for reading /proc/net/route text. Runs on every OS: it's just text parsing."""

from ipaddress import IPv4Address

import pytest

from kyn.platform.linux.routes import parse_route_table

HEADER = "\t".join(
    ["Iface", "Destination", "Gateway ", "Flags", "RefCnt", "Use", "Metric", "Mask"]
)


def table(*rows: str) -> str:
    return "\n".join([HEADER, *rows]) + "\n"


def test_finds_the_default_router() -> None:
    text = table(
        "eth0\t00000000\t0101A8C0\t0003\t0\t0\t100\t00000000\t0\t0\t0",
        "eth0\t0001A8C0\t00000000\t0001\t0\t0\t100\t00FFFFFF\t0\t0\t0",
    )
    assert parse_route_table(text) == IPv4Address("192.168.1.1")


def test_lowest_metric_wins() -> None:
    text = table(
        "wlan0\t00000000\t0101A8C0\t0003\t0\t0\t600\t00000000\t0\t0\t0",
        "eth0\t00000000\t0100000A\t0003\t0\t0\t100\t00000000\t0\t0\t0",
    )
    assert parse_route_table(text) == IPv4Address("10.0.0.1")


@pytest.mark.parametrize(
    "row",
    [
        "eth0\t00000000\t0101A8C0\t0002\t0\t0\t100\t00000000",  # Not up.
        "eth0\t00000000\t0101A8C0\t0001\t0\t0\t100\t00000000",  # No router flag.
        "eth0\t0001A8C0\t0101A8C0\t0003\t0\t0\t100\t00FFFFFF",  # Not a default route.
        "eth0\t00000000\t00000000\t0003\t0\t0\t100\t00000000",  # Router is 0.0.0.0.
        "eth0\t00000000\t-1\t0003\t0\t0\t100\t00000000",  # Negative number.
        "eth0\t00000000\t1FFFFFFFF\t0003\t0\t0\t100\t00000000",  # Over 32 bits.
        "eth0\t00000000\tZZZZZZZZ\t0003\t0\t0\t100\t00000000",  # Not hex.
        "eth0\t00000000\t0101A8C0",  # Too few columns.
        "",
    ],
)
def test_ignores_rows_that_are_not_usable_default_routes(row: str) -> None:
    assert parse_route_table(table(row)) is None


def test_header_only_means_no_router() -> None:
    assert parse_route_table(table()) is None
