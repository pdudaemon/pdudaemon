#!/usr/bin/python3
"""Tests for CyberPower 41001 PDU driver."""
# pylint: disable=redefined-outer-name

import pytest
from unittest.mock import Mock, patch
from pdudaemon.drivers.cyberpower41001 import Cyberpower41001


@pytest.fixture
def test_pdu():
    """Create a CyberPower 41001 PDU instance for testing."""
    settings = {"community": "testcommunity"}
    return Cyberpower41001("test.example.com", settings)


@pytest.fixture
def test_pdu_default_community():
    """Create a CyberPower 41001 PDU instance with default community string."""
    return Cyberpower41001("test.example.com", {})


def test_driver_accepts():
    """Test that the driver accepts the correct driver name."""
    assert Cyberpower41001.accepts("cyberpower41001") is True
    assert Cyberpower41001.accepts("cyberpower81001") is False
    assert Cyberpower41001.accepts("other") is False


def test_initialization(test_pdu):
    """Test driver initialization with custom settings."""
    assert test_pdu.hostname == "test.example.com"
    assert test_pdu.community == "testcommunity"


def test_initialization_default_community(test_pdu_default_community):
    """Test driver initialization with default community string."""
    assert test_pdu_default_community.community == "private"


@patch('subprocess.call')
def test_port_interaction_on(mock_subprocess, test_pdu):
    """Test turning a port on."""
    # pylint: disable=protected-access
    test_pdu._port_interaction("on", "1")
    expected_cmd = (
        "/usr/bin/snmpset -v 1 -c testcommunity test.example.com "
        "SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.1 integer 1 >/dev/null"
    )
    mock_subprocess.assert_called_once_with(expected_cmd, shell=True)


@patch('subprocess.call')
def test_port_interaction_off(mock_subprocess, test_pdu):
    """Test turning a port off."""
    # pylint: disable=protected-access
    test_pdu._port_interaction("off", "2")
    expected_cmd = (
        "/usr/bin/snmpset -v 1 -c testcommunity test.example.com "
        "SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.2 integer 2 >/dev/null"
    )
    mock_subprocess.assert_called_once_with(expected_cmd, shell=True)


@patch('subprocess.call')
def test_port_interaction_reboot(mock_subprocess, test_pdu):
    """Test rebooting a port."""
    # pylint: disable=protected-access
    test_pdu._port_interaction("reboot", "3")
    expected_cmd = (
        "/usr/bin/snmpset -v 1 -c testcommunity test.example.com "
        "SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.3 integer 3 >/dev/null"
    )
    mock_subprocess.assert_called_once_with(expected_cmd, shell=True)


@patch('subprocess.call')
def test_port_interaction_cancel(mock_subprocess, test_pdu):
    """Test canceling a port action."""
    # pylint: disable=protected-access
    test_pdu._port_interaction("cancel", "4")
    expected_cmd = (
        "/usr/bin/snmpset -v 1 -c testcommunity test.example.com "
        "SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.4 integer 4 >/dev/null"
    )
    mock_subprocess.assert_called_once_with(expected_cmd, shell=True)


@patch('subprocess.call')
def test_port_interaction_numeric_commands(mock_subprocess, test_pdu):
    """Test numeric command equivalents."""
    # pylint: disable=protected-access
    test_pdu._port_interaction("1", "1")  # Same as "on"
    expected_cmd = (
        "/usr/bin/snmpset -v 1 -c testcommunity test.example.com "
        "SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.1 integer 1 >/dev/null"
    )
    mock_subprocess.assert_called_once_with(expected_cmd, shell=True)


@patch('subprocess.call')
@patch('logging.getLogger')
def test_port_interaction_unknown_command(mock_logger, mock_subprocess, test_pdu):
    """Test handling of unknown commands."""
    mock_log = Mock()
    mock_logger.return_value = mock_log

    # pylint: disable=protected-access
    test_pdu._port_interaction("unknown", "1")

    # Should not call subprocess for unknown commands
    mock_subprocess.assert_not_called()


def test_port_number_conversion(test_pdu):
    """Test that string port numbers are converted to integers."""
    with patch('subprocess.call') as mock_subprocess:
        # pylint: disable=protected-access
        test_pdu._port_interaction("on", "5")
        expected_cmd = (
            "/usr/bin/snmpset -v 1 -c testcommunity test.example.com "
            "SNMPv2-SMI::enterprises.3808.1.1.3.3.3.1.1.4.5 integer 1 >/dev/null"
        )
        mock_subprocess.assert_called_once_with(expected_cmd, shell=True)


def test_actions_mapping():
    """Test that all expected actions are properly mapped."""
    # Test the mapping indirectly by checking command behavior
    test_pdu_instance = Cyberpower41001("test.example.com", {})
    with patch('subprocess.call') as mock_subprocess:
        # pylint: disable=protected-access
        test_pdu_instance._port_interaction("on", "1")
        assert mock_subprocess.called

        mock_subprocess.reset_mock()
        # pylint: disable=protected-access
        test_pdu_instance._port_interaction("1", "1")
        assert mock_subprocess.called
