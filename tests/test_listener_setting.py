from types import SimpleNamespace

import pytest

from pdudaemon import PDUDaemon
from pdudaemon.httplistener import HTTPListener


@pytest.mark.parametrize("option,setting", [
    (None, None),
    (None, "http"),
    (None, "tcp"),
    ("tcp", "http"),
])
def test_listener_is_always_http(option, setting):
    daemon = {"hostname": "localhost"}
    if setting:
        daemon["listener"] = setting
    pdud = PDUDaemon(SimpleNamespace(listener=option), {"daemon": daemon, "pdus": {}})
    assert isinstance(pdud.listener, HTTPListener)
