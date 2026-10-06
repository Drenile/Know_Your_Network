"""Developer-only: refresh the bundled manufacturer list (D-016).

The app itself never runs this or downloads anything.

Usage:  uv run python scripts/update_manuf.py

Then update MANUF_SHA256 in tests/core/test_vendors.py with the printed hash, and
review the diff of src/kyn/data/manuf in the pull request before merging.
"""

import hashlib
import sys
import urllib.request
from pathlib import Path
from typing import Final

from kyn.core.vendors import MAX_FILE_BYTES, VendorDirectory

# Fixed HTTPS address. Wireshark asks that this is downloaded at most once a week.
SOURCE_URL: Final = "https://www.wireshark.org/download/automated/data/manuf"
TARGET: Final = Path(__file__).resolve().parents[1] / "src" / "kyn" / "data" / "manuf"

# Sanity floor: the real list has about 58,000 entries.
MIN_ENTRIES: Final = 50_000
MAX_SKIPPED: Final = 50


def download() -> bytes:
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as response:
        if not response.geturl().startswith("https://www.wireshark.org/"):
            sys.exit(f"Refusing: redirected to {response.geturl()}")
        data: bytes = response.read(MAX_FILE_BYTES + 1)
    if len(data) > MAX_FILE_BYTES:
        sys.exit(f"Refusing: download is larger than {MAX_FILE_BYTES:,} bytes.")
    return data


def check(data: bytes) -> VendorDirectory:
    directory = VendorDirectory.from_lines(data.decode("utf-8").splitlines())
    if len(directory) < MIN_ENTRIES or directory.skipped_lines > MAX_SKIPPED:
        sys.exit(
            f"Refusing: {len(directory):,} entries and {directory.skipped_lines} "
            "skipped lines. The format may have changed; inspect it by hand."
        )
    return directory


def main() -> None:
    data = download()
    directory = check(data)
    TARGET.write_bytes(data)
    print(f"Wrote {TARGET} ({len(data):,} bytes)")
    print(f"Entries: {len(directory):,}, skipped lines: {directory.skipped_lines}")
    print(f"SHA-256: {hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
