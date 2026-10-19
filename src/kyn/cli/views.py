"""How a scan looks in the terminal: the permission screen (G2) and the device table.

Every value that comes from outside the app goes through `safe_text`.
"""

from typing import Final

from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from kyn.cli.safe_text import safe_text
from kyn.core.connection import Connection
from kyn.core.identify import IdentifiedDevice
from kyn.core.scope import ScanScope

# Some makers register with the name "Private" to hide who they are. That is not the
# same as our "Private address" note for addresses a device made up itself.
_HIDDEN_MAKER: Final = "Private"


def permission_screen(connection: Connection, scope: ScanScope) -> Panel:
    """Explain what the scan will do before it starts."""
    addresses = sum(1 for _ in scope.targets())
    details = Text.assemble(
        ("Network:      ", "bold"),
        f"{scope.network} ({addresses:,} addresses)\n",
        ("Adapter:      ", "bold"),
        safe_text(connection.interface_name),
        "\n",
        ("Your router:  ", "bold"),
        str(connection.gateway),
    )
    what_happens = Text(
        '\nKnow Your Network will ask each address on this network "who are you?" '
        "(an ARP request). Your computer sends the same message every time it talks "
        "to a device nearby.\n\n"
        "It will not contact anything outside this network, send any data off this "
        "computer, or save anything.\n\n"
        "Only scan a network you own or have permission to scan."
    )
    return Panel(
        Group(details, what_happens), title="Before we scan", title_align="left"
    )


def device_table(devices: list[IdentifiedDevice]) -> Table:
    """One row per device, in the order given."""
    table = Table(title=f"Devices found: {len(devices)}", title_justify="left")
    table.add_column("IP address", no_wrap=True)
    table.add_column("MAC address", no_wrap=True)
    table.add_column("Maker")
    table.add_column("Note")
    for item in devices:
        table.add_row(
            str(item.device.ip),
            str(item.device.mac),
            _maker(item),
            _note(item),
        )
    return table


def _maker(item: IdentifiedDevice) -> Text:
    if item.device.mac.is_locally_administered:
        return Text("-", style="dim")
    if item.vendor is None:
        return Text("Unknown", style="dim")
    if item.vendor.short_name == _HIDDEN_MAKER:
        return Text("Maker not disclosed", style="dim")
    return safe_text(item.vendor.name)


def _note(item: IdentifiedDevice) -> Text:
    if item.is_router:
        return Text("Router", style="bold")
    if item.device.mac.is_locally_administered:
        return Text("Private address (privacy feature)")
    return Text("")
