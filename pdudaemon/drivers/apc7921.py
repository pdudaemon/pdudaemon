#! /usr/bin/python

import logging
from pdudaemon.drivers.apc7952 import APC7952
log = logging.getLogger(__name__)


class APC7921(APC7952):

    @classmethod
    def accepts(cls, drivername):
        if drivername == "apc7921":
            return True
        return False

    def _port_interaction(self, command, port_number):
        log.debug("Attempting command: %s port: %i",
                  command, port_number)
        # make sure in main menu here
        self._back_to_main()
        self.connection.send("\r")
        self.connection.expect("1- Device Manager")
        self.connection.expect("> ")
        log.debug("Entering Device Manager")
        self.connection.send("1\r")
        self.connection.expect("------- Device Manager")
        self.connection.send("2\r")
        self.connection.expect("1- Outlet Control/Configuration")
        self.connection.expect("> ")
        self.connection.send("1\r")
        self._enter_outlet(port_number, False)
        self.connection.expect("1- Control Outlet")
        self.connection.send("1\r")
        self.connection.expect("> ")
        if command == "on":
            self.connection.send("1\r")
            self.connection.expect("Immediate On")
            self._do_it()
        elif command == "off":
            self.connection.send("2\r")
            self.connection.expect("Immediate Off")
            self._do_it()
        else:
            log.debug("Unknown command!")
