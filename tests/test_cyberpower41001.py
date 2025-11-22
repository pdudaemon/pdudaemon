#!/usr/bin/python3

import pytest
from unittest.mock import Mock, patch
from pdudaemon.drivers.cyberpower41001 import Cyberpower41001


@pytest.fixture
def pdu():
    """Create a CyberPower 41001 PDU instance for testing."""
    settings = {"community": "testcommunity"}
    return Cyberpower41001("test.example.com", settings)


@pytest.fixture
def pdu_default_community():
    """Create a CyberPower 41001 PDU instance with default community string."""
    return Cyberpower41001("test.example.com", {})


def test_driver_accepts():
    """Test that the driver accepts the correct driver name."""
    assert Cyberpower41001.accepts("cyberpower41001") is True
    assert Cyberpower41001.accepts("cyberpower81001") is False
    assert Cyberpower41001.accepts("other") is False


def test_initialization(pdu):
    """Test driver initialization with custom settings."""
    assert pdu.hostname == "test.example.com"
    assert pdu.community == "testcommunity"


def test_initialization_default_community(pdu_default_community):
    """Test driver initialization with default community string."""
    assert pdu_default_community.community == "private"


@patch('subprocess.call')
def test_port_interaction_on(mock_subprocess, pdu):
    """Test turning a port on."""
    pdu._port_interaction("on", "1")
    expected_cmd = "/usr/bin/snmpset -v 1 -c testcommunity test.example.com SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.1 integer 1 >/dev/null"
    mock_subprocess.assert_called_once_with(expected_cmd, shell=True)


@patch('subprocess.call')
def test_port_interaction_off(mock_subprocess, pdu):
    """Test turning a port off."""
    pdu._port_interaction("off", "2")
    expected_cmd = "/usr/bin/snmpset -v 1 -c testcommunity test.example.com SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.2 integer 2 >/dev/null"
    mock_subprocess.assert_called_once_with(expected_cmd, shell=True)


@patch('subprocess.call')
def test_port_interaction_reboot(mock_subprocess, pdu):
    """Test rebooting a port."""
    pdu._port_interaction("reboot", "3")
    expected_cmd = "/usr/bin/snmpset -v 1 -c testcommunity test.example.com SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.3 integer 3 >/dev/null"
    mock_subprocess.assert_called_once_with(expected_cmd, shell=True)


@patch('subprocess.call')
def test_port_interaction_cancel(mock_subprocess, pdu):
    """Test canceling a port action."""
    pdu._port_interaction("cancel", "4")
    expected_cmd = "/usr/bin/snmpset -v 1 -c testcommunity test.example.com SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.4 integer 4 >/dev/null"
    mock_subprocess.assert_called_once_with(expected_cmd, shell=True)


@patch('subprocess.call')
def test_port_interaction_numeric_commands(mock_subprocess, pdu):
    """Test numeric command equivalents."""
    pdu._port_interaction("1", "1")  # Same as "on"
    expected_cmd = "/usr/bin/snmpset -v 1 -c testcommunity test.example.com SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.1 integer 1 >/dev/null"
    mock_subprocess.assert_called_once_with(expected_cmd, shell=True)


@patch('subprocess.call')
@patch('logging.getLogger')
def test_port_interaction_unknown_command(mock_logger, mock_subprocess, pdu):
    """Test handling of unknown commands."""
    mock_log = Mock()
    mock_logger.return_value = mock_log

    pdu._port_interaction("unknown", "1")

    # Should not call subprocess for unknown commands
    mock_subprocess.assert_not_called()


def test_port_number_conversion(pdu):
    """Test that string port numbers are converted to integers."""
    with patch('subprocess.call') as mock_subprocess:
        pdu._port_interaction("on", "5")
        expected_cmd = "/usr/bin/snmpset -v 1 -c testcommunity test.example.com SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.5 integer 1 >/dev/null"
        mock_subprocess.assert_called_once_with(expected_cmd, shell=True)


def test_actions_mapping():
    """Test that all expected actions are properly mapped."""
    expected_actions = {
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "on": 1,
        "off": 2,
        "reboot": 3,
        "cancel": 4,
    }
    assert Cyberpower41001._actions == expected_actions
