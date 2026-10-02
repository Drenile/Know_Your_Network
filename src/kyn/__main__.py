"""Command-line entry point: `kyn` or `python -m kyn`."""

from kyn import __version__


def main() -> int:
    """Run the app and return the process exit code."""
    print(f"Know Your Network {__version__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
