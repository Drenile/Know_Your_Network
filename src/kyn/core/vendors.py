"""Offline manufacturer lookup using the bundled Wireshark `manuf` list (A3, D-016).

The list is treated as untrusted input: each line must match the expected format
exactly, and names must be plain printable text. Anything else is skipped.
"""

import re
from collections.abc import Iterable
from dataclasses import dataclass
from importlib.resources import files
from typing import Final

from kyn.core.mac import MacAddress

# Checked longest first, so a small maker's block inside a bigger one wins.
PREFIX_SIZES: Final = (36, 28, 24)

# Bytes written in the prefix column for each block size, e.g. "00:1B:C5:00:10/36".
_OCTETS_FOR_BITS: Final = {24: 3, 28: 4, 36: 5}

# "<prefix>[/<bits>]  <TAB> <short name>  <TAB> <full name>", padded with spaces.
_LINE: Final = re.compile(
    r"(?P<prefix>[0-9A-F]{2}(?::[0-9A-F]{2}){2,4})(?:/(?P<bits>28|36))? *"
    r"\t(?P<short>[^\t]+?) *\t(?P<name>[^\t]+)"
)

MAX_FILE_BYTES: Final = 10 * 1024 * 1024
MAX_NAME_LENGTH: Final = 120


class VendorDataError(ValueError):
    """The bundled manufacturer list is missing, too large or not valid UTF-8."""


@dataclass(frozen=True, slots=True)
class Vendor:
    short_name: str
    name: str


@dataclass(frozen=True, slots=True)
class _Entry:
    bits: int
    prefix: int
    vendor: Vendor


class VendorDirectory:
    """Maps MAC address prefixes to manufacturers."""

    def __init__(self, entries: Iterable[_Entry], skipped_lines: int = 0) -> None:
        self._tables: dict[int, dict[int, Vendor]] = {bits: {} for bits in PREFIX_SIZES}
        for entry in entries:
            self._tables[entry.bits].setdefault(entry.prefix, entry.vendor)
        self.skipped_lines = skipped_lines

    @classmethod
    def from_lines(cls, lines: Iterable[str]) -> VendorDirectory:
        """Build a directory from `manuf` lines, skipping any line that isn't valid."""
        entries: list[_Entry] = []
        skipped = 0
        for raw_line in lines:
            line = raw_line.rstrip("\r\n")
            if not line or line.startswith("#"):
                continue
            entry = _parse_line(line)
            if entry is None:
                skipped += 1
            else:
                entries.append(entry)
        return cls(entries, skipped)

    def lookup(self, mac: MacAddress) -> Vendor | None:
        """Return the maker, or None if unknown or the address isn't a maker's.

        Private (locally administered) and multicast addresses are never looked up,
        because their prefix doesn't identify a manufacturer.
        """
        if mac.is_locally_administered or mac.is_multicast:
            return None
        for bits in PREFIX_SIZES:
            vendor = self._tables[bits].get(mac.prefix(bits))
            if vendor is not None:
                return vendor
        return None

    def __len__(self) -> int:
        return sum(len(table) for table in self._tables.values())


def load_bundled() -> VendorDirectory:
    """Load the manufacturer list shipped inside the app. Never downloads anything."""
    data = files("kyn").joinpath("data", "manuf").read_bytes()
    if len(data) > MAX_FILE_BYTES:
        raise VendorDataError(f"Manufacturer list is too large ({len(data):,} bytes).")
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise VendorDataError("Manufacturer list is not valid UTF-8.") from error
    return VendorDirectory.from_lines(text.splitlines())


def _parse_line(line: str) -> _Entry | None:
    match = _LINE.fullmatch(line)
    if match is None:
        return None

    bits = int(match["bits"] or 24)
    octets = match["prefix"].split(":")
    if len(octets) != _OCTETS_FOR_BITS[bits]:
        return None

    unused_bits = len(octets) * 8 - bits
    value = int("".join(octets), 16)
    if value & ((1 << unused_bits) - 1):
        return None  # e.g. "00:55:DA:15/28": the last 4 bits should be zero.

    short_name, name = match["short"], match["name"]
    if not (_is_safe_name(short_name) and _is_safe_name(name)):
        return None
    return _Entry(bits, value >> unused_bits, Vendor(short_name, name))


def _is_safe_name(text: str) -> bool:
    """Plain, visible text only. `isprintable()` rejects control characters and
    invisible formatting characters such as zero-width spaces and direction marks."""
    return 0 < len(text) <= MAX_NAME_LENGTH and text.isprintable()
