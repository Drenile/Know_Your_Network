"""Decode the hardware address SendARP writes into its buffer.

This is plain Python with no Windows calls, so it can be tested on any OS. SendARP
fills a buffer and reports how many bytes it wrote. An Ethernet or Wi-Fi address is
exactly 6 bytes; anything else is refused rather than guessed at.
"""

from typing import Final

from kyn.core.mac import MacAddress

_ETHERNET_LENGTH: Final = 6


def parse_arp_reply(buffer: bytes, length: int) -> MacAddress | None:
    """Return the MAC address in the first `length` bytes, or None if unusable.

    An all-zero address means "no real answer", as in the Linux table (D-022).
    """
    if length != _ETHERNET_LENGTH or len(buffer) < length:
        return None
    mac = MacAddress.from_bytes(buffer[:length])
    return mac if mac.value != 0 else None
