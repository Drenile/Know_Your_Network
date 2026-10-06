"""Work out which network this computer is on and which router it uses (A1)."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Interface


class NoConnectionError(Exception):
    """This computer's home network connection could not be identified."""


@dataclass(frozen=True, slots=True)
class Connection:
    """This computer's place on its network, e.g. 192.168.1.23/24 via 192.168.1.1."""

    interface_name: str
    address: IPv4Interface
    gateway: IPv4Address


def pick_connection(
    gateway: IPv4Address | None,
    interfaces: Mapping[str, Iterable[IPv4Interface]],
) -> Connection:
    """Choose the adapter whose network contains the router.

    This one rule works on every OS and skips adapters that Docker, VirtualBox or a
    VPN add, because their networks don't contain the default router. If two
    adapters are on the router's network (Wi-Fi and cable at once), the first by
    name is chosen so the result is always the same.
    """
    if gateway is None:
        raise NoConnectionError(
            "No router found. Check that this computer is connected to a network."
        )
    for name in sorted(interfaces):
        for address in interfaces[name]:
            if gateway in address.network and address.ip != gateway:
                return Connection(name, address, gateway)
    raise NoConnectionError(f"No network adapter is on the same network as {gateway}.")
