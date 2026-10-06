"""MAC addresses: the hardware ID every network device has, e.g. 3C:22:FB:1A:2B:3C."""

import re
from dataclasses import dataclass
from typing import Final

# Six pairs of hex digits, all separated by ":" or all by "-". Linux prints
# "3c:22:fb:1a:2b:3c" and Windows prints "3C-22-FB-1A-2B-3C".
_MAC_PATTERN: Final = re.compile(
    r"[0-9A-Fa-f]{2}([:-])(?:[0-9A-Fa-f]{2}\1){4}[0-9A-Fa-f]{2}"
)

BITS: Final = 48

# Bits in the first byte. "Locally administered" means the address was made up by
# the device (for example a phone's private Wi-Fi address), not assigned by a maker.
_MULTICAST_BIT: Final = 0x01 << 40
_LOCALLY_ADMINISTERED_BIT: Final = 0x02 << 40


class MacAddressError(ValueError):
    """Text is not a valid MAC address."""


@dataclass(frozen=True, slots=True, order=True)
class MacAddress:
    """A validated 48-bit MAC address, stored as a number."""

    value: int

    def __post_init__(self) -> None:
        if not 0 <= self.value < 1 << BITS:
            raise MacAddressError(f"{self.value} is not a 48-bit number.")

    @classmethod
    def parse(cls, text: str) -> MacAddress:
        """Parse "3c:22:fb:1a:2b:3c" or "3C-22-FB-1A-2B-3C"; refuse anything else."""
        if not _MAC_PATTERN.fullmatch(text):
            raise MacAddressError(f"{text!r} is not a MAC address.")
        return cls(int(text.replace(":", "").replace("-", ""), 16))

    @property
    def is_locally_administered(self) -> bool:
        """True for addresses a device made up itself, e.g. private Wi-Fi addresses."""
        return bool(self.value & _LOCALLY_ADMINISTERED_BIT)

    @property
    def is_multicast(self) -> bool:
        """True for group addresses, which never belong to a single device."""
        return bool(self.value & _MULTICAST_BIT)

    def prefix(self, bits: int) -> int:
        """Return the first `bits` bits, e.g. the 24-bit maker prefix."""
        return self.value >> (BITS - bits)

    def __str__(self) -> str:
        return ":".join(f"{self.value:012X}"[i : i + 2] for i in range(0, 12, 2))
