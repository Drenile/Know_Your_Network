"""Scan scope guard: the single place that decides which addresses may be contacted.

Every probe must pass `ScanScope.require()` immediately before it is sent (G1, D-020).
"""

from collections.abc import Iterator
from dataclasses import dataclass
from ipaddress import IPv4Address, IPv4Interface, IPv4Network
from typing import Final, TypeGuard

# RFC 1918 private ranges. This is an allowlist: anything not listed is refused.
# `ipaddress.is_private` is not used because it also accepts ranges that are not
# home networks, such as documentation and benchmarking blocks.
PRIVATE_RANGES: Final = (
    IPv4Network("10.0.0.0/8"),
    IPv4Network("172.16.0.0/12"),
    IPv4Network("192.168.0.0/16"),
)

# Largest network we agree to scan: /22, 1,022 hosts. Bigger networks are more
# likely to belong to a school, office or ISP than to the user.
LARGEST_PREFIX: Final = 22

# Smallest useful network: /30, 2 hosts. A /31 or /32 has no other devices to find.
SMALLEST_PREFIX: Final = 30


class ScopeError(ValueError):
    """A network or address is outside what the app is allowed to scan."""


@dataclass(frozen=True, slots=True)
class ScanScope:
    """The one private network the app may scan, and this computer's place in it.

    Validation runs on creation, so a `ScanScope` that exists is always safe to use.
    """

    network: IPv4Network
    own_address: IPv4Address

    def __post_init__(self) -> None:
        if self.own_address not in self.network:
            raise ScopeError(f"{self.own_address} is not inside {self.network}.")
        if not any(self.network.subnet_of(allowed) for allowed in PRIVATE_RANGES):
            raise ScopeError(
                f"{self.network} is not a private home network, so it won't be scanned."
            )
        if self.network.prefixlen < LARGEST_PREFIX:
            raise ScopeError(
                f"{self.network} has {self.network.num_addresses:,} addresses. "
                "That's larger than a home network, so it won't be scanned."
            )
        if self.network.prefixlen > SMALLEST_PREFIX:
            raise ScopeError(f"{self.network} has no other devices to find.")

    @classmethod
    def from_interface(cls, interface: IPv4Interface) -> ScanScope:
        """Build the scope from this computer's address and network (192.168.1.5/24)."""
        return cls(network=interface.network, own_address=interface.ip)

    def allows(self, address: object) -> TypeGuard[IPv4Address]:
        """Return True only for another device's address inside the scanned network.

        Accepts any object, because this is a security boundary: anything that is not
        an IPv4 address in range (an IPv6 address, a string, None) is refused, not
        trusted. `TypeGuard` tells the type checker that True means "IPv4Address".
        """
        return (
            isinstance(address, IPv4Address)
            and address in self.network
            and address != self.network.network_address
            and address != self.network.broadcast_address
            and address != self.own_address
        )

    def require(self, address: object) -> IPv4Address:
        """Return the address if it may be contacted; otherwise raise `ScopeError`."""
        if self.allows(address):
            return address
        raise ScopeError(
            f"Refusing to contact {address!r}: not another device in {self.network}."
        )

    def targets(self) -> Iterator[IPv4Address]:
        """Yield every address to check: all hosts in the network except this one."""
        return (host for host in self.network.hosts() if host != self.own_address)
