__author__ = 'matt'

from driver import PDUDriver

class apc7952(PDUDriver):
    def _pdu_logout(self):
        self._back_to_main()
        print("Logging out")
        self.connection.send("4\r")

    def _back_to_main(self):
        print("Returning to main menu")
        self.connection.expect('>')
        for i in range(1,20):
            #print("Sending escape character")
            self.connection.send("\x1B")
            self.connection.send("\r")
            res = self.connection.expect(["4- Logout","> "])
            if res == 0:
                print("Back at main menu")
                break
        #self.connection.send("\r")
        #self.connection.expect("4- Logout")
        #self.connection.expect("> ")

    def _enter_outlet(self, outlet):
        self.connection.expect("Press <ENTER> to continue...")
        self.connection.send("\r")
        self.connection.expect("> ")
        self.connection.send(outlet)
        self.connection.send("\r")

    def _port_interaction(self, command, port_number):
        print("Attempting command: %s port: %i" % (command, port_number))
        ### make sure in main menu here
        self._back_to_main()
        self.connection.send("\r")
        self.connection.expect("1- Device Manager")
        self.connection.expect("> ")
        self.connection.send("1\r")
        res = self.connection.expect(["3- Outlet Control/Configuration","2- Outlet Control","2- Outlet Management"])
        if res == 0:
            self.connection.send("3\r")
            self._enter_outlet(port_number)
        elif res == 1:
            self.connection.send("2\r")
            self._enter_outlet(port_number)
        elif res == 2:
            self.connection.send("2\r")
        res = self.connection.expect(["1- Control Outlet", "1- Outlet Control/Configuration"])
        self.connection.expect("> ")
        self.connection.send("1\r")
        res = self.connection.expect(["> ","Press <ENTER> to continue..."])
        if res == 1:
            print("Stupid paging thingmy detected, pressing enter")
            self.connection.send("\r")
        print("We should now be at the outlet list")
        self.connection.send("%s\r" % port_number)
        self.connection.send("1\r")
        self.connection.expect("3- Immediate Reboot")
        self.connection.expect("> ")
        if command == "reboot":
            self.connection.send("3\r")
            self.connection.expect("Immediate Reboot")
            self._do_it()
        elif command == "delayed":
            self.connection.send("6\r")
            self.connection.expect("Delayed Reboot")
            self._do_it()
        elif command == "on":
            self.connection.send("1\r")
            self.connection.expect("Immediate On")
            self._do_it()
        elif command == "off":
            self.connection.send("2\r")
            self.connection.expect("Immediate Off")
            self._do_it()
        else:
            print("Unknown command!")

    def _do_it(self):
        self.connection.expect("Enter 'YES' to continue or <ENTER> to cancel :")
        self.connection.send("YES\r")
        self.connection.expect("Press <ENTER> to continue...")
        self.connection.send("\r")

    def port_delayed(self, port_number):
        self._port_interaction("delayed", port_number)

    def port_on(self, port_number):
        self._port_interaction("on", port_number)

    def port_off(self, port_number):
        self._port_interaction("off", port_number)

    def port_reboot(self, port_number):
        self._port_interaction("reboot", port_number)

class apc8959(PDUDriver):
    connection = None

    def _pdu_logout(self):
        print("logging out")
        self.connection.send("\r")
        self.connection.send("exit")
        self.connection.send("\r")
        print("done")

    def _pdu_get_to_prompt(self):
        self.connection.send("\r")
        self.connection.expect ('apc>')

    def _port_interaction(self, command, port_number):
        print("Attempting %s on port %i" % (command, port_number))
        self._pdu_get_to_prompt()
        self.connection.sendline(self.pdu_commands[command] + (" %i" % port_number))
        self.connection.expect("E000: Success")
        print("done")

    def port_delayed(self, port_number):
        self._port_interaction("delayed", port_number)

    def port_on(self, port_number):
        self._port_interaction("on", port_number)

    def port_off(self, port_number):
        self._port_interaction("off", port_number)

    def port_reboot(self, port_number):
        self._port_interaction("reboot", port_number)