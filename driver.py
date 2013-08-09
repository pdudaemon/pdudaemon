__author__ = 'matt'

class PDUDriver():
    connection = None
    pdu_commands = {"off":"olOff","on":"olOn","reboot":"olReboot","delayed":"olDlyReboot"}

    def __init__(self, connection):
        self.connection = connection

