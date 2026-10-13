"""The `kyn scan` command: read the connection, ask permission, find devices, show them.

The OS functions arrive as `ScanServices`, so this module never imports platform code
and tests can pass fakes instead of touching a real network (dependency inversion).
"""

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Interface

from rich.console import Console
from rich.prompt import Confirm

from kyn.cli.safe_text import safe_text
from kyn.cli.views import device_table, permission_screen
from kyn.core.connection import NoConnectionError, pick_connection
from kyn.core.devices import Device
from kyn.core.identify import VendorLookup, identify
from kyn.core.scope import ScanScope, ScopeError
from kyn.core.vendors import VendorDataError

EXIT_OK = 0
EXIT_FAILED = 1

Ask = Callable[[Console], bool]


@dataclass(frozen=True, slots=True)
class ScanServices:
    """What the scan needs from the operating system."""

    read_gateway: Callable[[], IPv4Address | None]
    read_interfaces: Callable[[], Mapping[str, Iterable[IPv4Interface]]]
    discover: Callable[[ScanScope, str], list[Device]]
    load_vendors: Callable[[], VendorLookup]


def ask_to_start(console: Console) -> bool:
    """Ask "Start the scan?". No answer (e.g. input closed) counts as no."""
    try:
        return Confirm.ask("Start the scan?", console=console, default=False)
    except EOFError:
        return False


def run_scan(
    console: Console,
    services: ScanServices,
    *,
    assume_yes: bool = False,
    ask: Ask = ask_to_start,
) -> int:
    """Run one scan and return the process exit code."""
    try:
        connection = pick_connection(
            services.read_gateway(), services.read_interfaces()
        )
        scope = ScanScope.from_interface(connection.address)
        vendors = services.load_vendors()
    except (NoConnectionError, ScopeError, VendorDataError) as error:
        return _fail(console, error)

    console.print(permission_screen(connection, scope))
    if not assume_yes and not ask(console):
        console.print("Nothing was scanned.")
        return EXIT_FAILED

    try:
        with console.status("Scanning your network. This takes about 10 seconds..."):
            devices = services.discover(scope, connection.interface_name)
    except OSError as error:
        return _fail(console, error)

    console.print(device_table(identify(devices, connection.gateway, vendors)))
    console.print(
        "Devices that are asleep, such as phones with the screen off, may not answer.\n"
        "Nothing was saved."
    )
    return EXIT_OK


def _fail(console: Console, error: Exception) -> int:
    # OS error text can include adapter names, so it's cleaned like any outside text.
    console.print(safe_text(f"Can't scan: {error}", style="red"))
    return EXIT_FAILED
