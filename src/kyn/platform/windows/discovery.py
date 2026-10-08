"""Find devices on Windows without admin rights: ask every address with SendARP
(D-004, D-023).

Each SendARP call blocks until the device answers, or for about 3 seconds if nothing
is there, so many addresses are checked at once in worker threads.
"""

from collections.abc import Callable, Iterable
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from ipaddress import IPv4Address
from typing import Final

from kyn.core.devices import Device, keep_in_scope
from kyn.core.mac import MacAddress
from kyn.core.scope import ScanScope

# About 6 s for a /24 and 24 s for a /22. ARP requests are tiny, but higher numbers
# send bursts that cheap routers may struggle with.
WORKERS: Final = 128

Resolver = Callable[[IPv4Address], MacAddress | None]


def discover(scope: ScanScope, *, resolve: Resolver | None = None) -> list[Device]:
    """Return the devices currently on the scanned network, sorted by IP."""
    if resolve is None:
        from kyn.platform.windows.arp import send_arp

        resolve = partial(send_arp, source=scope.own_address)
    return keep_in_scope(scope, resolve_all(scope, scope.targets(), resolve))


def resolve_all(
    scope: ScanScope,
    targets: Iterable[object],
    resolve: Resolver,
    workers: int = WORKERS,
) -> list[Device]:
    """Ask every target for its MAC address, many at once.

    Raises ScopeError, before contacting it, if a target is outside the scope, and
    OSError if a lookup fails for any reason other than "no answer". Either error
    cancels the lookups that haven't started yet.
    """
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_resolve_one, scope, t, resolve) for t in targets]
        try:
            return [d for f in futures if (d := f.result()) is not None]
        except BaseException:
            pool.shutdown(cancel_futures=True)
            raise


def _resolve_one(scope: ScanScope, target: object, resolve: Resolver) -> Device | None:
    address = scope.require(target)
    mac = resolve(address)
    return Device(address, mac) if mac is not None else None
