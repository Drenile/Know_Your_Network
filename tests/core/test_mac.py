"""Tests for MAC address parsing and flags."""

import pytest

from kyn.core.mac import MacAddress, MacAddressError


@pytest.mark.parametrize(
    "text",
    [
        "3c:22:fb:1a:2b:3c",  # Linux style.
        "3C-22-FB-1A-2B-3C",  # Windows style.
        "3C:22:fb:1A:2b:3c",  # Mixed case.
    ],
)
def test_parses_common_formats_to_the_same_address(text: str) -> None:
    mac = MacAddress.parse(text)
    assert mac.value == 0x3C22FB1A2B3C
    assert str(mac) == "3C:22:FB:1A:2B:3C"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "3c:22:fb:1a:2b",  # Too short.
        "3c:22:fb:1a:2b:3c:4d",  # Too long.
        "3c:22-fb:1a:2b:3c",  # Mixed separators.
        "3c22fb1a2b3c",  # No separators.
        "3g:22:fb:1a:2b:3c",  # Not hex.
        " 3c:22:fb:1a:2b:3c",  # Leading space.
        "3c:22:fb:1a:2b:3c\n",  # Trailing newline.
        "\N{FULLWIDTH DIGIT THREE}c:22:fb:1a:2b:3c",  # Looks like "3", isn't.
    ],
)
def test_refuses_anything_else(text: str) -> None:
    with pytest.raises(MacAddressError):
        MacAddress.parse(text)


@pytest.mark.parametrize("value", [-1, 1 << 48])
def test_refuses_numbers_outside_48_bits(value: int) -> None:
    with pytest.raises(MacAddressError):
        MacAddress(value)


@pytest.mark.parametrize(
    ("text", "private", "multicast"),
    [
        ("3C:22:FB:1A:2B:3C", False, False),  # Normal device: assigned by its maker.
        ("3E:22:FB:1A:2B:3C", True, False),  # Phone's private Wi-Fi address.
        ("01:00:5E:00:00:01", False, True),  # Multicast group.
    ],
)
def test_flags(text: str, private: bool, multicast: bool) -> None:
    mac = MacAddress.parse(text)
    assert mac.is_locally_administered is private
    assert mac.is_multicast is multicast


def test_prefix() -> None:
    mac = MacAddress.parse("00:1B:C5:00:10:AA")
    assert mac.prefix(24) == 0x001BC5
    assert mac.prefix(36) == 0x001BC5001
