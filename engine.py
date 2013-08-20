import pexpect
import sys
import os
from apcdrivers import apc8959
from apcdrivers import apc7952
import logging

class PDUEngine():
    connection = None
    pdu_commands = {"off":"olOff","on":"olOn","reboot":"olReboot","delayed":"olDlyReboot"}
    prompt = 0
    driver = None

    def __init__(self, pdu_hostname, pdu_telnetport = 23):
        self.connection = pexpect.spawn("/usr/bin/telnet %s %d" % (pdu_hostname, pdu_telnetport))
        #self.connection.logfile_read = sys.stdout
        self._pdu_login("apc","apc")
        if self.prompt == 0:
            logging.debug("Found a v5 prompt")
            self.driver = apc8959(self.connection)
        elif self.prompt == 1:
            logging.debug("Found a v3 prompt")
            self.driver = apc7952(self.connection)
        else:
            logging.debug("Unknown prompt!")

    def is_busy(self):
        if os.path.exists("/proc/%i" % self.connection.pid):
            return True
        return False

    def close(self):
        self.driver._pdu_logout()
        self.connection.close(True)

    def _pdu_login(self, username, password):
        logging.debug("attempting login with username %s, password %s" % (username,password))
        self.connection.send("\r")
        self.connection.expect ("User Name :")
        self.connection.send("apc\r")
        self.connection.expect("Password  :")
        self.connection.send("apc\r")
        self.prompt = self.connection.expect(["apc>", ">"])
        #print("prompt: %s" % self.prompt)


if __name__ == "__main__":
    pe1 = PDUEngine("pdu15")
    pe1.driver.port_off(22)
    pe1.driver.port_on(22)
    pe1.close()
    pe2 = PDUEngine("pdu14")
    pe2.driver.port_off(6)
    pe2.driver.port_on(6)
    pe2.close()
    pe3 = PDUEngine("pdu01")
    pe3.driver.port_reboot(1)
    pe3.driver.port_off(1)
    pe3.driver.port_on(1)
    pe3.close()
    pe4 = PDUEngine("pdu02")
    pe4.driver.port_reboot(8)
    pe4.driver.port_off(8)
    pe4.driver.port_on(8)
    pe4.close()

