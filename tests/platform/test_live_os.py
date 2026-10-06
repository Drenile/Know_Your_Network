"""Read-only checks against the real OS this test runs on (Linux or Windows in CI).

These read settings only; nothing is sent on the network.
"""

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
def test_windows_code_refuses_to_load_elsewhere() -> None:
    with pytest.raises(ImportError, match="only works on Windows"):
        import kyn.platform.windows.routes  # noqa: F401
