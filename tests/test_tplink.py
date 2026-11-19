#!/usr/bin/python3

import json
import socket

import pytest
from pdudaemon.drivers import tplink
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


# a power strip's get_sysinfo, long enough to come in more than one segment
SYSINFO = {
    "system": {
        "get_sysinfo": {
            "model": "HS300(US)",
            "children": [
                {"id": "%040d" % i, "alias": "Plug %d" % (i + 1), "state": 0,
                 "on_time": 0, "next_action": {"type": -1}}
                for i in range(6)
            ],
            "padding": "x" * 1024,
        }
    }
}


class FakeSocket:
    """A TCP socket whose replies come in chunks of the given sizes."""

    connected: list = []
    sent: list = []
    chunks = None

    def __init__(self, *args):
        self.data = b""

    def settimeout(self, timeout):
        pass

    def connect(self, address):
        FakeSocket.connected.append(address)

    def send(self, data):
        FakeSocket.sent.append(data)
        self.data = TPLink.encrypt(None, json.dumps(SYSINFO))
        return len(data)

    def recv(self, size):
        n = min(size, FakeSocket.chunks.pop(0) if FakeSocket.chunks else size)
        out, self.data = self.data[:n], self.data[n:]
        return out

    def close(self):
        pass


@pytest.fixture
def fake_socket(monkeypatch):
    FakeSocket.connected, FakeSocket.sent = [], []
    monkeypatch.setattr(tplink.socket, "socket", FakeSocket)
    return FakeSocket


@pytest.mark.parametrize("chunks", [[4096], [1024], [1, 3, 1000], [700, 700]])
def test_reply_in_several_reads(fake_socket, chunks):
    fake_socket.chunks = list(chunks)
    pdu = TPLink("hs300", {})
    assert [c["alias"] for c in pdu.childinfo] == ["Plug %d" % i for i in range(1, 7)]
    assert pdu.get_id("1") == {"child_ids": ["%040d" % 0]}
    assert pdu.get_id("6") == {"child_ids": ["%040d" % 5]}
    assert pdu.get_id("0") is False


def test_address_is_the_name(fake_socket):
    fake_socket.chunks = [4096]
    TPLink("hs300.example.com", {})
    assert fake_socket.connected == [("hs300.example.com", 9999)]


def test_address_from_ip_setting(fake_socket):
    fake_socket.chunks = [4096]
    TPLink("lab-strip-1", {"ip": "192.0.2.10"})
    assert fake_socket.connected == [("192.0.2.10", 9999)]
