"""Read the kernel's neighbour (ARP) table on Linux.

/proc/net/arp is a plain-text file any normal user can read. Each line looks like:

    IP address       HW type     Flags       HW address            Mask     Device
    192.168.1.1      0x1         0x2         aa:bb:cc:dd:ee:ff     *        wlan0

Only complete Ethernet entries are kept. Every field is validated, because the
kernel copies some of this from replies sent by devices on the network.
"""

from ipaddress import IPv4Address
from pathlib import Path
from typing import Final

from kyn.core.devices import Device
from kyn.core.mac import MacAddress

NEIGHBOUR_TABLE: Final = Path("/proc/net/arp")

_HW_TYPE_ETHERNET: Final = 0x1  # Wi-Fi uses the Ethernet type too.
_ATF_COM: Final = 0x2  # "Complete": the device answered with its MAC address.
_COLUMNS: Final = 6


def read_neighbours(interface_name: str) -> list[Device]:
    """Return devices in the neighbour table for one network adapter."""
    text = NEIGHBOUR_TABLE.read_text(encoding="ascii", errors="replace")
    return parse_neighbour_table(text, interface_name)


def parse_neighbour_table(text: str, interface_name: str) -> list[Device]:
    """Parse /proc/net/arp text, keeping complete entries on `interface_name`."""
    lines = text.splitlines()[1:]  # The first line is the header.
    return [d for line in lines if (d := _parse_line(line, interface_name))]


def _parse_line(line: str, interface_name: str) -> Device | None:
    columns = line.split()
    if len(columns) != _COLUMNS:
        return None
    ip_text, hw_type_text, flags_text, mac_text, _mask, device_name = columns
    if device_name != interface_name:
        return None
    try:
        hw_type = int(hw_type_text, 16)
        flags = int(flags_text, 16)
        ip = IPv4Address(ip_text)
        mac = MacAddress.parse(mac_text)
    except ValueError:  # Includes AddressValueError and MacAddressError.
        return None
    if hw_type != _HW_TYPE_ETHERNET or not flags & _ATF_COM or mac.value == 0:
        return None
    return Device(ip, mac)
