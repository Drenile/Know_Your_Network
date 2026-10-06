"""Find devices on Linux without admin rights: nudge every address, wait, read the
neighbour table (D-004, D-022)."""

import time
from collections.abc import Callable
from typing import Final

from kyn.core.devices import Device, keep_in_scope
from kyn.core.scope import ScanScope
from kyn.platform.linux.neighbours import read_neighbours
from kyn.platform.linux.nudge import Sender, send_nudges

# Linux keeps old neighbour entries for a while. When our nudge reaches one, the
# kernel waits 5 s, then checks 3 times, 1 s apart, and drops it if the device has
# gone. Waiting 9 s means every entry we read has been confirmed recently.
SETTLE_SECONDS: Final = 9.0


def discover(
    scope: ScanScope,
    interface_name: str,
    *,
    send: Sender | None = None,
    read: Callable[[str], list[Device]] = read_neighbours,
    wait: Callable[[float], None] = time.sleep,
) -> list[Device]:
    """Return the devices currently on the scanned network, sorted by IP."""
    send_nudges(scope, scope.targets(), send=send, pause=wait)
    wait(SETTLE_SECONDS)
    return keep_in_scope(scope, read(interface_name))
