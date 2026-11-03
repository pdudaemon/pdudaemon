#!/usr/bin/python3
"""Tests for the IP9258 PDU driver."""
# pylint: disable=redefined-outer-name

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pdudaemon.drivers.driver import UnknownCommandException
from pdudaemon.drivers.ip9258 import IP9258
from pdudaemon.drivers.snmp import SNMP


@pytest.fixture
def test_pdu():
    """Create an IP9258 PDU instance for testing."""
    return IP9258("test.example.com", {})


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
    """Test that the driver accepts its name only."""
    assert IP9258.accepts("ip9258") is True
    assert IP9258.accepts("other") is False


def test_is_snmp_driver():
    """Test that the driver is selectable as an SNMP driver subclass."""
    assert issubclass(IP9258, SNMP)


def test_initialization(test_pdu):
    """Test driver initialization."""
    assert test_pdu.hostname == "test.example.com"
    assert test_pdu.version == "snmpv1"
    assert test_pdu.community == "public"


def test_port_interaction_on(mock_set_cmd, test_pdu):
    """Test turning a port on."""
    test_pdu.port_interaction("on", "1")
    assert _sent(mock_set_cmd) == ("public", "1.3.6.1.4.1.92.58.2.1.0", 1)


def test_port_interaction_off(mock_set_cmd, test_pdu):
    """Test turning a port off."""
    test_pdu.port_interaction("off", "3")
    assert _sent(mock_set_cmd) == ("public", "1.3.6.1.4.1.92.58.2.3.0", 0)


def test_port_interaction_unknown_command(mock_set_cmd, test_pdu):
    """Test handling of unknown commands."""
    with pytest.raises(UnknownCommandException):
        test_pdu.port_interaction("reboot", "1")
    mock_set_cmd.assert_not_called()
