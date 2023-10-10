#  Copyright 2020 Leonard Crestez <cdleonard@gmail.com>
#
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

import logging
from pdudaemon.drivers.driver import PDUDriver
import serial

import os
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))


class NumatoUSB(PDUDriver):
    """Supports various numato USB relay modules.

    Comes in many variants with similar protocols

    Protocol documentation link:
    https://numato.com/docs/16-channel-usb-relay-module/#the-command-set-23

    There are slight differences for 32 and 64-channel modules
    """
    def __init__(self, hostname, settings):
        super(NumatoUSB, self).__init__()
        self.hostname = hostname
        self.settings = settings
        self.device = settings.get("device", "/dev/ttyACM0")
        log.debug("device: %s" % self.device)
        self.serial_port = None

    def _read_reply(self):
        msg = self.serial_port.read_until(b'>').decode('utf8')
        x = msg.find('\n\r')
        return msg[x + 2:-3]

    def _open(self):
        self.serial_port = serial.serial_for_url(self.device, timeout=1)
        log.debug("open: %s for %s", self.serial_port.port, self.device)
        # resync prompt
        self.serial_port.reset_input_buffer()
        self.serial_port.write(b'\r')
        self.serial_port.read_until(b'>')
        # show relay module info
        self.serial_port.write(b'ver\r')
        log.info("ver: %s", self._read_reply())
        self.serial_port.write(b'id get\r')
        log.info("id: %s", self._read_reply())

    def port_interaction(self, command, port_number):
        port_number = int(port_number)
        if port_number > self.port_count or port_number < 1:
            err = "Port should be in the range 1 - %d" % (self.port_count)
            raise RuntimeError(err)

        if command == "on":
            msg = 'relay on %s\r' % (self.format_portid(port_number - 1),)
        elif command == "off":
            msg = 'relay off %s\r' % (self.format_portid(port_number - 1),)
        else:
            raise RuntimeError("Unknown command %s" % (command))

        try:
            if not self.serial_port:
                self._open()
            log.debug("write %r on %s", msg, self.serial_port.port)
            self.serial_port.write(msg.encode('utf8'))
            self.serial_port.read_until(b'>')
        except (serial.serialutil.SerialException, OSError) as e:
            log.error(e)
            self.serial_port = None
            raise

    def format_portid(self, portid):
        # See https://numato.com/docs/16-channel-usb-relay-module/#the-command-set-23
        return '%x' % portid

    @classmethod
    def accepts(cls, drivername):
        if not getattr(cls, 'port_count', None):
            return False
        return drivername == "NumatoUSB%d" % cls.port_count


class NumatoUSB1(NumatoUSB):
    port_count = 1


class NumatoUSB2(NumatoUSB):
    port_count = 2


class NumatoUSB4(NumatoUSB):
    port_count = 4


class NumatoUSB8(NumatoUSB):
    port_count = 8


class NumatoUSB16(NumatoUSB):
    port_count = 16


class NumatoUSB32(NumatoUSB):
    port_count = 32

    def format_portid(self, portid):
        # See https://numato.com/docs/32-channel-usb-relay-module/#the-command-set-23
        if portid < 10:
            return '%d' % portid
        else:
            return chr(ord('A') + portid - 10)


class NumatoUSB64(NumatoUSB):
    port_count = 64

    def format_portid(self, portid):
        # See https://numato.com/docs/64-channel-usb-relay-module-user-guide/#the-commands-set-4
        return '%02d' % portid
