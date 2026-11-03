#!/usr/bin/python3
"""Tests for CyberPower 81001/41001 PDU driver."""
# pylint: disable=redefined-outer-name

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pdudaemon.drivers.cyberpower81001 import Cyberpower81001
from pdudaemon.drivers.driver import UnknownCommandException
from pdudaemon.drivers.snmp import SNMP


@pytest.fixture
def test_pdu():
    """Create a CyberPower PDU instance for testing."""
    settings = {"community": "testcommunity"}
    return Cyberpower81001("test.example.com", settings)


@pytest.fixture
def test_pdu_default_community():
    """Create a CyberPower PDU instance with default community string."""
    return Cyberpower81001("test.example.com", {})


@pytest.fixture
def mock_set_cmd():
    with patch("pdudaemon.drivers.snmp.set_cmd", new_callable=AsyncMock) as m:
        m.return_value = (None, 0, 0, [])
        with patch("pdudaemon.drivers.snmp.UdpTransportTarget") as transport:
            transport.create = AsyncMock(return_value=MagicMock())
            with patch("pdudaemon.drivers.snmp.SnmpEngine"):
                yield m


def _sent(mock_set_cmd):
    """Return the community, OID and value passed to set_cmd."""
    # pylint: disable=protected-access
    args = mock_set_cmd.call_args[0]
    objecttype = args[4]
    oid = objecttype._ObjectType__args[0]._ObjectIdentity__args[0]
    value = int(objecttype._ObjectType__args[1])
    return args[1].communityName, oid, value


def test_driver_accepts():
    """Test that the driver accepts both CyberPower model names."""
    assert Cyberpower81001.accepts("cyberpower81001") is True
    assert Cyberpower81001.accepts("cyberpower41001") is True
    assert Cyberpower81001.accepts("other") is False


def test_is_snmp_driver():
    """Test that the driver is selectable as an SNMP driver subclass."""
    assert issubclass(Cyberpower81001, SNMP)


def test_initialization(test_pdu):
    """Test driver initialization with custom settings."""
    assert test_pdu.hostname == "test.example.com"
    assert test_pdu.version == "snmpv1"
    assert test_pdu.community == "testcommunity"


def test_initialization_default_community(test_pdu_default_community):
    """Test driver initialization with default community string."""
    assert test_pdu_default_community.community == "private"


def test_port_interaction_on(mock_set_cmd, test_pdu):
    """Test turning a port on."""
    test_pdu.port_interaction("on", "1")
    assert _sent(mock_set_cmd) == (
        "testcommunity", "1.3.6.1.4.1.3808.1.1.3.3.3.1.1.4.1", 1)


def test_port_interaction_off(mock_set_cmd, test_pdu):
    """Test turning a port off."""
    test_pdu.port_interaction("off", "2")
    assert _sent(mock_set_cmd) == (
        "testcommunity", "1.3.6.1.4.1.3808.1.1.3.3.3.1.1.4.2", 2)


def test_port_interaction_default_community(mock_set_cmd,
                                            test_pdu_default_community):
    """Test that the default community string is sent."""
    test_pdu_default_community.port_interaction("on", "5")
    assert _sent(mock_set_cmd) == (
        "private", "1.3.6.1.4.1.3808.1.1.3.3.3.1.1.4.5", 1)


def test_port_interaction_unknown_command(mock_set_cmd, test_pdu):
    """Test handling of unknown commands."""
    with pytest.raises(UnknownCommandException):
        test_pdu.port_interaction("reboot", "1")
    mock_set_cmd.assert_not_called()
