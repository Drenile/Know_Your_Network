"""Tests for decoding GetIpForwardTable bytes, using hand-built bytes on any OS."""

import struct
from ipaddress import IPv4Address

from kyn.platform.windows.forward_table import parse_forward_table


def row(dest: str, mask: str, next_hop: str, metric: int) -> bytes:
    numbers = [7, 4, 3, 0, 0, metric, 0, 0, 0, 0]  # if_index, type, proto, ...
    return struct.pack(
        "<4s4sI4s10I",
        IPv4Address(dest).packed,
        IPv4Address(mask).packed,
        0,
        IPv4Address(next_hop).packed,
        *numbers,
    )


# "Any address" (0.0.0.0) in a route. Built from a number because the literal
# string looks like a server listening on every network, which Ruff (S104) flags.
ANY = str(IPv4Address(0))


def table(*rows: bytes) -> bytes:
    return struct.pack("<I", len(rows)) + b"".join(rows)


DEFAULT = row(ANY, ANY, "192.168.1.1", 25)
LOCAL = row("192.168.1.0", "255.255.255.0", "192.168.1.23", 281)


def test_finds_the_default_router() -> None:
    assert parse_forward_table(table(LOCAL, DEFAULT)) == IPv4Address("192.168.1.1")


def test_lowest_metric_wins() -> None:
    vpn = row(ANY, ANY, "10.8.0.1", 5)
    assert parse_forward_table(table(DEFAULT, vpn)) == IPv4Address("10.8.0.1")


def test_no_default_route() -> None:
    assert parse_forward_table(table(LOCAL)) is None
    assert parse_forward_table(table()) is None


def test_on_link_default_route_without_router_is_ignored() -> None:
    assert parse_forward_table(table(row(ANY, ANY, ANY, 1))) is None


def test_damaged_buffer_is_not_trusted() -> None:
    claims_two_rows = struct.pack("<I", 2) + DEFAULT  # Only one row present.
    assert parse_forward_table(claims_two_rows) is None
    assert parse_forward_table(b"") is None
    assert parse_forward_table(b"\x01\x00") is None
