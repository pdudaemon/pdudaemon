#!/usr/bin/python3

import socket

from pdudaemon.drivers.tplink import TPLink


def test_timeout_kept_for_the_whole_exchange(mocker):
    """The socket used to be put back into blocking mode after connect()."""
    sock = mocker.patch("socket.socket").return_value
    sock.recv.return_value = b""

    TPLink("dummy", {})

    sock.settimeout.assert_called_once_with(10)
    sock.connect.assert_called_once_with(("dummy", 9999))


def test_unreachable_device_is_handled(mocker):
    sock = mocker.patch("socket.socket").return_value
    sock.connect.side_effect = socket.timeout()

    pdu = TPLink("dummy", {})

    assert pdu.send_command("{}") is None
