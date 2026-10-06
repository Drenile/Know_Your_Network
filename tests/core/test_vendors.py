"""Tests for the offline manufacturer lookup. No network is touched."""

import hashlib
from importlib.resources import files

import pytest

from kyn.core.mac import MacAddress
from kyn.core.vendors import Vendor, VendorDirectory, load_bundled

# Fingerprint of src/kyn/data/manuf. Changing the file means updating this on
# purpose, so a refresh can't slip in unreviewed (D-016).
MANUF_SHA256 = "9b2c3db4b9be4bdd6a398ad719112d6a65f5e09c8cb2f498145adbb5208fd281"

SAMPLE = [
    "# A comment",
    "",
    "00:55:DA         \tBigMaker    \tBig Maker Ltd",
    "00:55:DA:10/28   \tMidMaker    \tMid Maker Inc.",
    "00:55:DA:10:20/36\tTinyMaker   \tTiny Maker GmbH",
    "3C:22:FB         \tPrüftechnik \tPrüftechnik AG",  # Accented letters are fine.
]


def lookup(directory: VendorDirectory, mac: str) -> str | None:
    vendor = directory.lookup(MacAddress.parse(mac))
    return vendor.short_name if vendor else None


# ------------------------------------------------------------ lookup


@pytest.mark.parametrize(
    ("mac", "expected"),
    [
        ("00:55:DA:00:00:01", "BigMaker"),  # Only the 24-bit block matches.
        ("00:55:DA:1F:00:01", "MidMaker"),  # 28-bit block wins over 24-bit.
        ("00:55:DA:10:20:01", "TinyMaker"),  # 36-bit block wins over both.
        ("3C:22:FB:1A:2B:3C", "Prüftechnik"),
        ("AA:BB:CC:00:00:01", None),  # Unknown maker.
    ],
)
def test_longest_prefix_wins(mac: str, expected: str | None) -> None:
    assert lookup(VendorDirectory.from_lines(SAMPLE), mac) == expected


@pytest.mark.parametrize(
    "mac",
    [
        "3E:22:FB:1A:2B:3C",  # Private address: same as 3C:22:FB with the "local" bit.
        "01:55:DA:00:00:01",  # Multicast.
    ],
)
def test_never_looks_up_private_or_multicast_addresses(mac: str) -> None:
    directory = VendorDirectory.from_lines([*SAMPLE, "3E:22:FB\tFake\tFake Ltd"])
    assert lookup(directory, mac) is None


# ------------------------------------------------------------ strict parsing


@pytest.mark.parametrize(
    "line",
    [
        "00:55:DA\tNoFullName",  # Missing column.
        "00:55:DA\tA\tB\tC",  # Extra column.
        "00:55:da\tLower\tLower case prefix",
        "00:55:DA:10\tNoSize\tBlock size missing",
        "00:55:DA/28\tWrongSize\tToo few bytes for /28",
        "00:55:DA:15/28\tHostBits\tLast 4 bits must be zero",
        "00:55:DA\t​Hidden\tZero-width space",
        "00:55:DA\tBidi\tRight-to-left ‮ override",
        "00:55:DA\tBell\tControl \x07 character",
        "00:55:DA\tLong\t" + "x" * 121,
    ],
)
def test_skips_invalid_lines(line: str) -> None:
    directory = VendorDirectory.from_lines([line])
    assert len(directory) == 0
    assert directory.skipped_lines == 1


# ------------------------------------------------------------ bundled file


def test_bundled_file_is_the_reviewed_version() -> None:
    data = files("kyn").joinpath("data", "manuf").read_bytes()
    assert hashlib.sha256(data).hexdigest() == MANUF_SHA256


def test_bundled_file_loads() -> None:
    directory = load_bundled()
    assert len(directory) > 50_000
    assert directory.skipped_lines == 3  # The lines with invisible characters.
    assert directory.lookup(MacAddress.parse("00:00:0C:12:34:56")) == Vendor(
        "Cisco", "Cisco Systems, Inc"
    )
