"""List this computer's network adapters and their IPv4 addresses, using psutil."""

import socket
from ipaddress import IPv4Interface

import psutil


def interface_addresses() -> dict[str, list[IPv4Interface]]:
    """Return {adapter name: [address/mask, ...]} for adapters that are switched on.

    Values come from the OS, but are still validated: anything that doesn't parse as
    an IPv4 address and mask is skipped.
    """
    stats = psutil.net_if_stats()
    result: dict[str, list[IPv4Interface]] = {}
    for name, addresses in psutil.net_if_addrs().items():
        if name not in stats or not stats[name].isup:
            continue
        parsed = [
            interface
            for address in addresses
            if address.family == socket.AF_INET
            and (interface := _parse(address.address, address.netmask)) is not None
        ]
        if parsed:
            result[name] = parsed
    return result


def _parse(address: str, netmask: str | None) -> IPv4Interface | None:
    if netmask is None:
        return None
    try:
        return IPv4Interface(f"{address}/{netmask}")
    except ValueError:
        return None
