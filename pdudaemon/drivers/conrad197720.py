#!/usr/bin/python3
"""#
# Copyright 2023 Joachim Schiffer <joachim.schiffer@bosch.com>.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# SPDX-License-Identifier: GPL-2.0-or-later
#
# Script to control conrad components relais card 197720
# Up to 255 cards can be concatenated at one serial port
# https://www.conrad.de/de/p/conrad-components-197720-relaiskarte-baustein-12-v-dc-24-v-dc-197720.html
#
"""

import serial
import os
import logging

from pdudaemon.drivers.driver import PDUDriver
log = logging.getLogger("pdud.drivers." + os.path.basename(__file__))

# number of retries on communication error
RETRY_COUNT = 1

# timeout while receiving
SERIAL_TIMEOUT = .1

# given by hardware
PORTS_PER_CARD = 8
MAX_CARDS = 255
FRAME_SIZE = 4

# as described in manual, address 0 for first card does not work
ADDR_FIRST_CARD = 1

# valid commands
CMD_INIT = 1
CMD_GETPORT = 2
CMD_SETPORT = 3
CMD_GETOPTION = 4
CMD_SETOPTION = 5
CMD_SETSINGLE = 6
CMD_DELSINGLE = 7
CMD_TOGGLESINGLE = 8

# parameter for CMD_SETOPTION / CMD_GETOPTION
OPTION_BROADCAST_NO_SEND_AND_NO_BLOCK = 0
OPTION_BROADCAST_SEND_AND_NO_BLOCK = 1  # default
OPTION_BROADCAST_NO_SEND_AND_BLOCK = 2
OPTION_BROADCAST_SEND_AND_BLOCK = 3


class Conrad197720(PDUDriver):
    """Driver for Conrad Components 197720 and 197730 relay card.

    https://www.conrad.com/p/conrad-components-197720-relay-card-component-12-v-dc-24-v-dc-197720
    https://www.conrad.com/p/conrad-components-197730-relay-card-component-12-v-dc-197730

    Up to 255 relay cards can be used on one serial port
    The difference between model 197720 and model 197730 is the switching power of the relays
    The protocol is the same for both card types
    """
    def __init__(self, hostname, settings):
        self.com = serial.Serial()
        self.num_cards = 0
        self.hostname = hostname
        self.__openConnection(settings.get("device", "/dev/ttyUSB0"))  # /dev/ttyUSB0 is default
        self.__init()

    def __del__(self):
        """Cleanup on delete."""
        if self.com.is_open:
            self.com.close()

    @classmethod
    def accepts(cls, drivername):
        return drivername == "conrad197720"

    def port_interaction(self, command, port_number):
        """Pdudaemon method for port interaction.

        :param self: The object itself
        :param command: The command string
        :param port_number: The port number 0...n
        """
        port_number = int(port_number)
        self.__updateSingle(command, port_number)

    def getNumPorts(self):
        """Return amount of ports available.

        :param self: The object itself
        :return: number of ports
        :rtype: int
        """
        return self.num_cards * PORTS_PER_CARD

    def __txFrame(self, tx_data):
        """Private function to send an array of data bytes.

        :param self: The object itself
        :param tx_data: The array of data bytes to send
        :raises RuntimeError: tx_data array too big
        """
        if len(tx_data) != 3:
            raise RuntimeError("tx_data has more than 3 bytes")
        checksum = tx_data[0] ^ tx_data[1] ^ tx_data[2]
        tx_data.append(checksum)
        if not self.com.is_open:
            self.__openConnection(self.portname)
        self.com.write(tx_data)
        log.debug(f"sent: {tx_data}")

    def __txSingleByte(self):
        """Private function to send a single byte.

        The card(s) always send and receive frames of FRAME_SIZE bytes,
        if this is not in sync, this function can be used to send single
        bytes, until a correct answer is received. In theory this
        function should be called 3 times at most during script runtime
        :param self: The object itself
        """
        byte = 0
        if not self.com.is_open:
            self.__openConnection(self.portname)
        self.com.write(byte.to_bytes(1, byteorder='big'))
        log.debug("sent single byte")

    def __rxFrame(self, num_frames):
        """Private function to receive frame(s).

        :param self: The object itself
        :param num_frames: The number of frames to wait for (until timeout SERIAL_TIMEOUT occurs)
        :return: The received data
        :rtype: array
        """
        rx_data = []
        if not self.com.is_open:
            self.__openConnection(self.portname)
        for i in range(0, (num_frames * FRAME_SIZE)):
            recv = self.com.read(1)
            if len(recv) == 0:
                break
            recv = int.from_bytes(recv, 'little')
            rx_data.append(recv)
        log.debug(f"recv: {rx_data}")
        return rx_data

    def __checkFrameChecksum(self, data):
        """Private function to check the XOR checksum of the received frame.

        :param self: The object itself
        :param data: The array holding the received data bytes, length must be a multiple of FRAME_SIZE
        :return: True, if checksum(s) match
        :rtype: boolean
        """
        if len(data) % FRAME_SIZE != 0 or len(data) == 0:
            return False
        for i in range(0, int(len(data) / FRAME_SIZE)):
            # check if checksum matches
            if (data[int(i / FRAME_SIZE) + 0] ^ data[int(i / FRAME_SIZE) + 1]
               ^ data[int(i / FRAME_SIZE) + 2]) != data[int(i / FRAME_SIZE) + 3]:
                print(f"checksum of frame {i} does not match")
                return False
        return True

    def __sendCommand(self, cmd_byte, addr_byte, data_byte):
        """Private function to send a command to the card(s) / retry / parse the response.

        :param self: The object itself
        :param cmd_byte: The command to the card(s)
        :param addr_byte: The card address, used when more than one relay card is connected to the same serial port
        :param data_byte: The data byte to be transmitted
        :return: the response data byte
        :rtype: int
        :raises RuntimeError: all retries failed, communication error
        """
        for i in range(0, RETRY_COUNT):
            self.__txFrame([cmd_byte, addr_byte, data_byte])
            num_frames = 1
            # for init we might receive n+1 frames in case there n cards cascaded
            if cmd_byte == CMD_INIT:
                num_frames = MAX_CARDS + 1
            recv_data = self.__rxFrame(num_frames)
            # check if received data is valid
            if len(recv_data) > 0 and self.__checkFrameChecksum(recv_data):
                # retry, if there is no valid reply on init command
                if cmd_byte == CMD_INIT:
                    if (self.__checkNumCards(recv_data) <= 0):
                        log.debug("__sendCommand retry reason: no valid reply on init command")
                        continue
                # check if the addr and cmd in the reply is the correct answer
                if recv_data[0] == 255 - cmd_byte and recv_data[1] == addr_byte:
                    return recv_data[2]
                # if not.. retry
                else:
                    log.debug("__sendCommand retry reason: address of card in response frame invalid")
                    continue
            else:
                # send up to FRAME_SIZE single bytes until we receive correct frames
                # since there might be wrong communication before,
                # especially in the beginning of communication
                for j in range(0, FRAME_SIZE):
                    self.__txSingleByte()
                    recv_data = self.__rxFrame(255)
                    if self.__checkFrameChecksum(recv_data):
                        break
                    log.debug("__sendCommand retry reason: checksum mismatch")
        raise RuntimeError("All retries failed, communication error")

    def __checkNumCards(self, data):
        """Private function to parse the amount of concatenated card at this serial port.

        :param self: The object itself
        :return: number of cards
        :rtype: int
        """
        self.num_cards = 0
        for i in range(0, int(len(data) / FRAME_SIZE)):
            if (data[(i * FRAME_SIZE)] == 255 - CMD_INIT):
                self.num_cards = self.num_cards + 1
        log.debug(f"found {self.num_cards} cards")
        return self.num_cards

    def __getNumCards(self):
        """Return amount of cards found after init().

        :param self: The object itself
        :return: number of cards
        :rtype: int
        """
        return self.num_cards

    def __openConnection(self, portname):
        """Open serial connection.

        :param self: The object itself
        :param portname: The string describing the serial device to open (e.g. "/dev/ttyUSB1" or "/dev/serial/by-id/...")
        """
        self.portname = portname
        self.com.port = self.portname
        self.com.baudrate = 19200
        self.com.bytesize = 8
        self.com.parity = serial.PARITY_NONE
        self.com.stopbits = serial.STOPBITS_ONE
        self.com.timeout = SERIAL_TIMEOUT
        self.com.open()

    def __init(self):
        """Init all cards.

        :param self: The object itself
        :raises RuntimeError: all retries failed, communication error
        """
        self.__sendCommand(CMD_INIT, ADDR_FIRST_CARD, 0)
        # make sure, all cards run with default setting
        for card_addr in range(1, self.__getNumCards() + 1):
            option = self.__sendCommand(CMD_GETOPTION, card_addr, 0)
            if option != OPTION_BROADCAST_SEND_AND_NO_BLOCK:
                # set card to default setting
                log.debug(f"set option to default for card: {card_addr}")
                self.__sendCommand(CMD_SETOPTION, card_addr, OPTION_BROADCAST_SEND_AND_NO_BLOCK)

    def __updateSingle(self, command, port):
        """Update a single port of a card.

        :param self: The object itself
        :param command: The command to execute, "on" "off" or "toggle"
        :param port: The port number 0..n, all ports of all cards are in one range, e.g. port 9 is the second port of the second card
        :return: True on success
        :rtype: boolean
        :raises RuntimeError: unknown command
        :raises RuntimeError: no cards present
        :raises RuntimeError: port number invalid
        :raises RuntimeError: all retries failed, communication error
        """
        for i in range(0, RETRY_COUNT + 1):
            card_addr = int(port / PORTS_PER_CARD) + 1
            port_index = int(port % PORTS_PER_CARD)

            if command == "off":
                card_command = CMD_DELSINGLE
            elif command == "on":
                card_command = CMD_SETSINGLE
            else:
                raise RuntimeError(f"Unknown command {command}")

            if 0 == self.__getNumCards():
                # retry init
                self.__init()
                if 0 == self.__getNumCards():
                    raise RuntimeError("No conrad197720 compatible cards present")

            if port < 0 or card_addr > self.__getNumCards():
                raise RuntimeError(f"Port number {port} has to be between 0 and {(self.__getNumCards() * PORTS_PER_CARD)-1}")

            recv = self.__sendCommand(CMD_GETPORT, card_addr, 0)
            old_state = (recv & 1 << port_index) >> port_index

            recv = self.__sendCommand(card_command, card_addr, 1 << port_index)
            new_state = (recv & 1 << port_index) >> port_index

            log.debug(f"__updateSingle card_addr {card_addr} port_index {port_index} command {command} state {old_state} -> {new_state}")

            if (command == "off" and new_state == 0) or \
               (command == "on" and new_state == 1):
                return True

            log.debug("__updateSingle retry")

        raise RuntimeError("All retries failed, communication error")
