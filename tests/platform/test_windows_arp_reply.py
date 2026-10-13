"""Tests for decoding SendARP's reply buffer, using hand-built bytes on any OS."""

import pytest

from kyn.platform.windows.arp_reply import parse_arp_reply

# SendARP's buffer is two ULONGs (8 bytes); the address fills the first 6.
REPLY = bytes([0x3C, 0x22, 0xFB, 0x1A, 0x2B, 0x3C, 0xFF, 0xFF])


def test_reads_the_first_six_bytes() -> None:
    mac = parse_arp_reply(REPLY, 6)
    assert str(mac) == "3C:22:FB:1A:2B:3C"


@pytest.mark.parametrize(
    ("buffer", "length"),
    [
        (REPLY, 0),  # Nothing written.
        (REPLY, 4),  # Not an Ethernet address.
        (REPLY, 8),
        (REPLY[:5], 6),  # Buffer shorter than the length claimed.
        (bytes(8), 6),  # All zeros: no real answer.
    ],
)
def test_refuses_unusable_replies(buffer: bytes, length: int) -> None:
    assert parse_arp_reply(buffer, length) is None
