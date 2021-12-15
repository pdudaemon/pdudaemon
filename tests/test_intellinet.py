from unittest.mock import ANY

import pytest
from pdudaemon.drivers.driver import FailedRequestException
from pdudaemon.drivers.intellinet import Intellinet


@pytest.fixture
def pdu():
    return Intellinet("dummy", {})


@pytest.fixture(name="api_mock")
def fixture_api_mock(mocker):
    return mocker.patch("pdudaemon.drivers.intellinet.Intellinet._api")


def test_port_interaction(pdu, api_mock):
    pdu.port_interaction("on", 0)
    api_mock.assert_called_once_with(pdu.endpoints["outlet"], ANY)


def test_port_interaction_port_in_range(pdu):
    pdu = Intellinet("dummy", {})

    with pytest.raises(FailedRequestException):
        pdu.port_interaction("on", pdu.port_count)

    with pytest.raises(FailedRequestException):
        pdu.port_interaction("on", -1)
