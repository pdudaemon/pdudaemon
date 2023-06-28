from unittest import mock
from .numatousb import NumatoUSB4
from .numatousb import NumatoUSB32
from .numatousb import NumatoUSB64


def test_numato4():
    with mock.patch('serial.serial_for_url') as m:
        dev = NumatoUSB4('h', dict(device='/dev/fake'))
        dev.port_on(3)
    m.return_value.write.assert_called_with(b'relay on 2\r')


def test_numato32():
    with mock.patch('serial.serial_for_url') as m:
        dev = NumatoUSB32('h', dict(device='/dev/fake'))
        dev.port_on(32)
    m.return_value.write.assert_called_with(b'relay on V\r')


def test_numato64():
    with mock.patch('serial.serial_for_url') as m:
        dev = NumatoUSB64('h', dict(device='/dev/fake'))
        dev.port_on(32)
    m.return_value.write.assert_called_with(b'relay on 31\r')
