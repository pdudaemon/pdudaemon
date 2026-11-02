from unittest.mock import MagicMock

import pytest
from pdudaemon.drivers.driver import FailedRequestException
from pdudaemon.drivers.tasmota import GenericTasmota


@pytest.fixture
def pdu():
    return GenericTasmota("dummy", {"ip": "192.0.2.1"})


@pytest.fixture(name="requests_get_mock")
def fixture_requests_get_mock(mocker):
    return mocker.patch("pdudaemon.drivers.tasmota.requests.get")


def mock_response(mget, payload):
    result = MagicMock()
    result.json.return_value = payload
    result.raise_for_status.return_value = None
    mget.return_value = result


class TestTasmota:

    def test_port_on_single_outlet(self, pdu, requests_get_mock):
        # Tasmota >= 12 single outlet devices reply with the "POWER" key
        mock_response(requests_get_mock, {"POWER": "ON"})
        pdu.port_interaction("on", 1)

    def test_port_off_single_outlet(self, pdu, requests_get_mock):
        mock_response(requests_get_mock, {"POWER": "OFF"})
        pdu.port_interaction("off", 1)

    def test_port_on_multi_outlet(self, pdu, requests_get_mock):
        # older firmware and multi outlet devices reply with "POWER<n>"
        mock_response(requests_get_mock, {"POWER1": "ON"})
        pdu.port_interaction("on", 1)

    def test_get_single_outlet_reports_state(self, pdu, requests_get_mock):
        # "Power<n> Get" reports the state on single outlet devices
        mock_response(requests_get_mock, {"POWER": "OFF"})
        pdu.port_interaction("get", 1)

    def test_get_multi_outlet_echoes_get(self, pdu, requests_get_mock):
        mock_response(requests_get_mock, {"POWER1": "GET"})
        pdu.port_interaction("get", 1)

    def test_wrong_state_raises(self, pdu, requests_get_mock):
        mock_response(requests_get_mock, {"POWER": "OFF"})
        with pytest.raises(FailedRequestException):
            pdu.port_interaction("on", 1)

    def test_unexpected_payload_raises(self, pdu, requests_get_mock):
        mock_response(requests_get_mock, {"SomeOther": "Thing"})
        with pytest.raises(FailedRequestException):
            pdu.port_interaction("on", 1)

    def test_port_number_out_of_range(self, pdu):
        with pytest.raises(FailedRequestException):
            pdu.port_interaction("on", pdu.port_count + 1)

        with pytest.raises(FailedRequestException):
            pdu.port_interaction("on", 0)

    def test_request_uses_timeout(self, pdu, requests_get_mock):
        mock_response(requests_get_mock, {"POWER": "ON"})
        pdu.port_interaction("on", 1)
        assert requests_get_mock.call_args.kwargs.get("timeout") == 10

    def test_timeout_setting(self, requests_get_mock):
        pdu = GenericTasmota("dummy", {"ip": "192.0.2.1", "timeout": "3"})
        mock_response(requests_get_mock, {"POWER": "ON"})
        pdu.port_interaction("on", 1)
        assert requests_get_mock.call_args.kwargs.get("timeout") == 3
