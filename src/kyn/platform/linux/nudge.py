"""Send the "nudge": one empty UDP packet to port 9 of each address (D-004, D-022).

Before Linux can deliver any packet on the local network, it must learn the target's
hardware (MAC) address, so it asks "who has 192.168.1.50?" (an ARP request). Every
device must answer ARP to use the network, even behind a firewall. The answers land
in the kernel's neighbour table, which neighbours.py reads.

Port 9 is the "discard" service and is closed on almost every device. That is the
point: no program on the device ever handles the packet. It is dropped, or answered
with a harmless "port unreachable" that we never read.
"""

import socket
import time
from collections.abc import Callable, Iterable
from ipaddress import IPv4Address
from typing import Final

from kyn.core.scope import ScanScope

DISCARD_PORT: Final = 9
# A short pause between packets, so a whole /24 takes about half a second and
# cheap routers aren't flooded with ARP requests.
NUDGE_INTERVAL_SECONDS: Final = 0.002

Sender = Callable[[IPv4Address], None]


def send_nudges(
    scope: ScanScope,
    targets: Iterable[object],
    send: Sender | None = None,
    pause: Callable[[float], None] = time.sleep,
) -> None:
    """Nudge each target. Every target passes the scope guard just before sending.

    Raises ScopeError, before sending anything to it, if a target is outside the
    scope. A failed send to one address is skipped: that device just won't be found.
    """
    if send is not None:
        _send_all(scope, targets, send, pause)
        return
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        _send_all(scope, targets, _udp_sender(sock), pause)


def _send_all(
    scope: ScanScope,
    targets: Iterable[object],
    send: Sender,
    pause: Callable[[float], None],
) -> None:
    for target in targets:
        address = scope.require(target)
        try:
            send(address)
        except OSError:
            continue
        pause(NUDGE_INTERVAL_SECONDS)


def _udp_sender(sock: socket.socket) -> Sender:
    def send(address: IPv4Address) -> None:
        sock.sendto(b"", (str(address), DISCARD_PORT))

    return send
