#!/usr/bin/python3
"""Tests for the APC firmware_version setting.

APC firmware versions are dotted numbers which don't follow PEP 440, so they
are compared as tuples of ints rather than with a version parser.
"""

import pytest

from pdudaemon.drivers.apc7900 import APC7900
from pdudaemon.drivers.apcbase import APCBase


@pytest.mark.parametrize(
    "setting, expected",
    [
        ("3.7.3", (3, 7, 3)),
        ("2.7.3", (2, 7, 3)),
        ("3.7.3.1", (3, 7, 3, 1)),
        ("4", (4,)),
        (None, (0,)),
        ("", (0,)),
        ("v3.7.3", (0,)),
        ("unknown", (0,)),
    ],
)
def test_parse_firmware_version(setting, expected):
    assert APCBase.parse_firmware_version(setting) == expected


@pytest.mark.parametrize(
    "setting, expected",
    [(None, (0,)), ("2.7.3", (2, 7, 3)), ("3.7.3", (3, 7, 3))],
)
def test_driver_reads_the_setting(setting, expected):
    settings = {} if setting is None else {"firmware_version": setting}
    assert APC7900("pdu.example.com", settings).firmware_version == expected


@pytest.mark.parametrize(
    "setting, outlet_management",
    [
        (None, False),
        ("2.7.3", False),
        ("3.7.2", False),
        ("3.7.3", True),
        ("3.7.4", True),
        ("4.0", True),
    ],
)
def test_which_menu_the_version_selects(setting, outlet_management):
    """3.7.3 and later need the extra Outlet Management menu."""
    settings = {} if setting is None else {"firmware_version": setting}
    pdu = APC7900("pdu.example.com", settings)
    assert (pdu.firmware_version >= pdu.OUTLET_MANAGEMENT_FIRMWARE) is outlet_management
