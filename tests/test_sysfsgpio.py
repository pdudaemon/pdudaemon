#!/usr/bin/python3

#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

import pytest
from pdudaemon.drivers.driver import PDUDriver
from pdudaemon.drivers.sysfsgpio import SysfsGPIO


@pytest.fixture
def sysfs(tmp_path, monkeypatch):
    monkeypatch.setattr(SysfsGPIO, "sysfs_path", str(tmp_path))
    (tmp_path / "export").write_text("")
    return tmp_path


def exported(sysfs, index, direction="in"):
    gpio = sysfs / ("gpio%d" % index)
    gpio.mkdir()
    (gpio / "direction").write_text(direction)
    return gpio


def gpiochip(sysfs, base, label, ngpio=54):
    chip = sysfs / ("gpiochip%d" % base)
    chip.mkdir()
    (chip / "base").write_text("%d\n" % base)
    (chip / "label").write_text(label + "\n")
    (chip / "ngpio").write_text("%d\n" % ngpio)


def test_select():
    assert PDUDriver.select("sysfsgpio") is SysfsGPIO


@pytest.mark.parametrize(
    "invert, command, expected",
    [
        (False, "on", "high"),
        (False, "off", "low"),
        (True, "on", "low"),
        (True, "off", "high"),
    ],
)
def test_port_interaction(sysfs, invert, command, expected):
    gpio = exported(sysfs, 17)
    pdu = SysfsGPIO("gpio", {"driver": "sysfsgpio", "invert": invert})

    pdu.port_interaction(command, "17")

    assert (gpio / "direction").read_text() == expected
    assert (sysfs / "export").read_text() == ""


def test_handle(sysfs):
    gpio = exported(sysfs, 5, "out")
    pdu = SysfsGPIO("gpio", {})

    pdu.handle("on", 5)
    assert (gpio / "direction").read_text() == "high"
    pdu.handle("off", 5)
    assert (gpio / "direction").read_text() == "low"


def test_export(sysfs, monkeypatch):
    real_open = open

    def fake_open(path, mode="r", *args, **kwargs):
        # The kernel creates gpio<N> when the number is written to export.
        if path == str(sysfs / "export"):
            exported(sysfs, 23)
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr("builtins.open", fake_open)
    pdu = SysfsGPIO("gpio", {})

    pdu.port_interaction("on", 23)

    assert (sysfs / "export").read_text() == "23"
    assert (sysfs / "gpio23" / "direction").read_text() == "high"


def test_export_fails(sysfs):
    pdu = SysfsGPIO("gpio", {})

    with pytest.raises(RuntimeError, match="GPIO 42 not found"):
        pdu.port_interaction("on", 42)


@pytest.mark.parametrize("port", ["abc", None, -1])
def test_bad_port(sysfs, port):
    pdu = SysfsGPIO("gpio", {})

    with pytest.raises(RuntimeError, match="GPIO number"):
        pdu.port_interaction("on", port)


def test_bad_invert():
    with pytest.raises(RuntimeError, match="invert"):
        SysfsGPIO("gpio", {"invert": "yes"})


def test_chip(sysfs):
    gpiochip(sysfs, 512, "gpio-brcmstb@107d508500", 32)
    gpiochip(sysfs, 571, "pinctrl-rp1")
    gpio = exported(sysfs, 575)
    pdu = SysfsGPIO("gpio", {"chip": "pinctrl-rp1"})

    pdu.port_interaction("on", 4)

    assert (gpio / "direction").read_text() == "high"


def test_chip_not_found(sysfs):
    gpiochip(sysfs, 512, "pinctrl-bcm2835")
    pdu = SysfsGPIO("gpio", {"chip": "pinctrl-rp1"})

    with pytest.raises(RuntimeError, match="no gpiochip labelled 'pinctrl-rp1'"):
        pdu.port_interaction("on", 4)


def test_chip_ambiguous(sysfs):
    gpiochip(sysfs, 496, "pca9555", 16)
    gpiochip(sysfs, 480, "pca9555", 16)
    pdu = SysfsGPIO("gpio", {"chip": "pca9555"})

    with pytest.raises(RuntimeError, match="2 gpiochips labelled 'pca9555'"):
        pdu.port_interaction("on", 1)


def test_chip_line_out_of_range(sysfs):
    gpiochip(sysfs, 496, "pca9555", 16)
    pdu = SysfsGPIO("gpio", {"chip": "pca9555"})

    with pytest.raises(RuntimeError, match="no line 16"):
        pdu.port_interaction("on", 16)


@pytest.mark.parametrize("chip", ["", 5])
def test_bad_chip(chip):
    with pytest.raises(RuntimeError, match="chip"):
        SysfsGPIO("gpio", {"chip": chip})


def test_unknown_command(sysfs):
    gpio = exported(sysfs, 17)
    pdu = SysfsGPIO("gpio", {})

    pdu.port_interaction("reboot", 17)

    assert (gpio / "direction").read_text() == "in"
