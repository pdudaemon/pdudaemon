from unittest.mock import create_autospec

import pytest
from pdudaemon.drivers.modbustcp import ModBusTCP


class Client:
    def connect(self):
        pass

    def close(self):
        pass


class OldClient(Client):
    def write_coil(self, address, value, *, slave=1):
        pass


class NewClient(Client):
    def write_coil(self, address, value, *, device_id=1):
        pass


@pytest.mark.parametrize("client, unit_arg", [(OldClient, "slave"), (NewClient, "device_id")])
def test_port_interaction(mocker, client, unit_arg):
    mock = create_autospec(client, instance=True)
    mocker.patch("pdudaemon.drivers.modbustcp.ModbusTcpClient", return_value=mock)
    pdu = ModBusTCP("dummy", {"unit": 7})

    pdu.port_interaction("on", "3")

    mock.connect.assert_called_once_with()
    mock.write_coil.assert_called_once_with(address=3, value=True, **{unit_arg: 7})


def test_reconnects_after_failure(mocker):
    mock = create_autospec(NewClient, instance=True)
    mock.write_coil.side_effect = [BrokenPipeError(), None]
    mocker.patch("pdudaemon.drivers.modbustcp.ModbusTcpClient", return_value=mock)
    pdu = ModBusTCP("dummy", {})

    with pytest.raises(BrokenPipeError):
        pdu.port_interaction("off", 1)
    pdu._bombout()
    pdu.port_interaction("off", 1)

    assert mock.close.call_count == 1
    assert mock.connect.call_count == 2
