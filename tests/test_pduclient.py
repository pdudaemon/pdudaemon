#!/usr/bin/python3
"""Tests for the bundled pduclient script.

It is a script rather than a module, so load it by path.
"""

import importlib.util
import pathlib
import urllib.parse

import pytest

CLIENT = pathlib.Path(__file__).resolve().parent.parent / "pduclient"


@pytest.fixture(name="pduclient")
def fixture_pduclient():
    spec = importlib.util.spec_from_loader(
        "pduclient", importlib.machinery.SourceFileLoader("pduclient", str(CLIENT))
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Options:
    pdudaemonhostname = "localhost"
    pdudaemonport = 16421
    pducommand = "on"
    pduhostname = "pdu01"
    pduportnum = "3"
    pdudelay = None


def sent_query(pduclient, mocker, **overrides):
    """Return the query the client would send, as parsed by the listener."""
    urlopen = mocker.patch("urllib.request.urlopen")
    options = Options()
    for key, value in overrides.items():
        setattr(options, key, value)
    with pytest.raises(SystemExit):
        pduclient.do_http_request(options)
    url = urlopen.call_args[0][0]
    return urllib.parse.parse_qs(urllib.parse.urlparse(url).query)


def test_query_is_sent(pduclient, mocker):
    query = sent_query(pduclient, mocker)
    assert query == {"hostname": ["pdu01"], "port": ["3"]}


def test_delay_is_included(pduclient, mocker):
    assert sent_query(pduclient, mocker, pdudelay=5)["delay"] == ["5"]


@pytest.mark.parametrize("name", ["pdu+lab", "pdu lab", "pdu&port=9", "pdu/01"])
def test_pdu_name_survives_encoding(pduclient, mocker, name):
    """A PDU name can be any string, so it has to be encoded."""
    query = sent_query(pduclient, mocker, pduhostname=name)
    assert query["hostname"] == [name]
    assert query["port"] == ["3"]
