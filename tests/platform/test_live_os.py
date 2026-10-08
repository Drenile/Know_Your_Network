"""Read-only checks against the real OS this test runs on (Linux or Windows in CI).

These read settings only; nothing is sent on the network.
"""

import importlib
import sys
from ipaddress import IPv4Address

import pytest

from kyn.core.connection import pick_connection
from kyn.platform import default_gateway
from kyn.platform.interfaces import interface_addresses


def test_reads_this_computers_connection() -> None:
    gateway = default_gateway()
    if gateway is None:
        pytest.skip("This computer has no network connection.")

    assert isinstance(gateway, IPv4Address)
    connection = pick_connection(gateway, interface_addresses())
    assert gateway in connection.address.network


@pytest.mark.skipif(sys.platform == "win32", reason="Checks the non-Windows guard.")
@pytest.mark.parametrize("module", ["routes", "arp"])
def test_windows_code_refuses_to_load_elsewhere(module: str) -> None:
    with pytest.raises(ImportError, match="only works on Windows"):
        importlib.import_module(f"kyn.platform.windows.{module}")


@pytest.mark.skipif(sys.platform != "win32", reason="SendARP exists only on Windows.")
def test_sendarp_loads_on_windows() -> None:
    """Loading the module finds SendARP in iphlpapi.dll. Nothing is sent."""
    from kyn.platform.windows.arp import send_arp

    assert callable(send_arp)
