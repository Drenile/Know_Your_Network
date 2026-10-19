"""Command-line entry point: `kyn` or `python -m kyn`.

This is the one place that connects the interface to the real OS functions.
"""

import argparse
from collections.abc import Sequence

from rich.console import Console

from kyn import __version__
from kyn.cli.scan import EXIT_FAILED, ScanServices, run_scan
from kyn.core.vendors import load_bundled
from kyn.platform import UnsupportedPlatformError, default_gateway, discover_devices
from kyn.platform.interfaces import interface_addresses

# The usual exit code for a program stopped with Ctrl+C.
EXIT_CANCELLED = 130


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kyn",
        description="See what's on your home network. Works offline; "
        "nothing leaves this computer.",
    )
    parser.add_argument(
        "--version", action="version", version=f"Know Your Network {__version__}"
    )
    commands = parser.add_subparsers(dest="command", metavar="command")
    scan = commands.add_parser("scan", help="find the devices on your home network")
    scan.add_argument(
        "-y", "--yes", action="store_true", help="start without asking first"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the app and return the process exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 0

    console = Console()
    services = ScanServices(
        read_gateway=default_gateway,
        read_interfaces=interface_addresses,
        discover=discover_devices,
        load_vendors=load_bundled,
    )
    try:
        return run_scan(console, services, assume_yes=args.yes)
    except UnsupportedPlatformError as error:
        console.print(f"Can't scan: {error}", markup=False)
        return EXIT_FAILED
    except KeyboardInterrupt:
        console.print("\nScan cancelled. Nothing was saved.")
        return EXIT_CANCELLED


if __name__ == "__main__":
    raise SystemExit(main())
