#!/usr/bin/python3

# It turns out that the device ID of the EnerGenie devices isn't the same
# as the serial number printed on the unit. This script will return the
# IDs of the devices found connected. The ID needs to be used in the
# "device" field when configuring pdudaemon.conf to use an energenie PDU.

import usb.core

dev = list()
dev += list(usb.core.find(find_all=True, idVendor=0x04b4, idProduct=0xfd10))
dev += list(usb.core.find(find_all=True, idVendor=0x04b4, idProduct=0xfd11))
dev += list(usb.core.find(find_all=True, idVendor=0x04b4, idProduct=0xfd12))
dev += list(usb.core.find(find_all=True, idVendor=0x04b4, idProduct=0xfd13))
dev += list(usb.core.find(find_all=True, idVendor=0x04b4, idProduct=0xfd15))

for d in dev:
    buf = bytes([0x00, 0x00, 0x00, 0x00, 0x00])
    ret = d.ctrl_transfer(0xa1, 0x01, 0x0301, 0, buf, 500)
    id = ":".join(format(x, '02x') for x in ret.tolist())
    print(id)
