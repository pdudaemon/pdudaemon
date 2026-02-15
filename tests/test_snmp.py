import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pdudaemon.drivers.driver import FailedRequestException, UnknownCommandException
from pdudaemon.drivers.snmp import SNMP


SNMPV1_SETTINGS = {
    "driver": "snmpv1",
    "mib": "PowerNet-MIB",
    "controlpoint": "sPDUOutletCtl",
    "onsetting": "1",
    "offsetting": "2",
    "community": "private",
}

SNMPV3_SETTINGS = {
    "driver": "snmpv3",
    "mib": "PowerNet-MIB",
    "controlpoint": "sPDUOutletCtl",
    "onsetting": "1",
    "offsetting": "2",
    "username": "testuser",
    "authpassphrase": "authpass123",
    "privpassphrase": "privpass123",
}


@pytest.fixture
def snmpv1_pdu():
    return SNMP("192.168.1.100", SNMPV1_SETTINGS)


@pytest.fixture
def snmpv3_pdu():
    return SNMP("192.168.1.100", SNMPV3_SETTINGS)


class TestAccepts:
    def test_accepts_snmpv1(self):
        assert SNMP.accepts("snmpv1") is True

    def test_accepts_snmpv3(self):
        assert SNMP.accepts("snmpv3") is True

    def test_rejects_unknown(self):
        assert SNMP.accepts("snmpv99") is False
        assert SNMP.accepts("telnet") is False


class TestInit:
    def test_snmpv1_init(self, snmpv1_pdu):
        assert snmpv1_pdu.hostname == "192.168.1.100"
        assert snmpv1_pdu.version == "snmpv1"
        assert snmpv1_pdu.community == "private"
        assert snmpv1_pdu.mib == "PowerNet-MIB"
        assert snmpv1_pdu.controlpoint == "sPDUOutletCtl"
        assert snmpv1_pdu.onsetting == "1"
        assert snmpv1_pdu.offsetting == "2"

    def test_snmpv3_init(self, snmpv3_pdu):
        assert snmpv3_pdu.version == "snmpv3"
        assert snmpv3_pdu.username == "testuser"
        assert snmpv3_pdu.authpass == "authpass123"
        assert snmpv3_pdu.privpass == "privpass123"

    def test_optional_settings_default_none(self, snmpv1_pdu):
        assert snmpv1_pdu.inside_number is None
        assert snmpv1_pdu.static_ending is None
        assert snmpv1_pdu.auth_protocol is None
        assert snmpv1_pdu.priv_protocol is None
        assert snmpv1_pdu.username is None


class TestPortInteraction:
    def test_unknown_command_raises(self, snmpv1_pdu):
        with pytest.raises(UnknownCommandException):
            snmpv1_pdu.port_interaction("reboot", 1)

    @patch("pdudaemon.drivers.snmp.asyncio.run")
    def test_on_command(self, mock_run, snmpv1_pdu):
        snmpv1_pdu.port_interaction("on", 1)
        mock_run.assert_called_once()
        # The first positional arg to asyncio.run is the coroutine
        coro = mock_run.call_args[0][0]
        # It should be a coroutine created with onsetting
        assert asyncio.iscoroutine(coro)
        coro.close()  # prevent RuntimeWarning

    @patch("pdudaemon.drivers.snmp.asyncio.run")
    def test_off_command(self, mock_run, snmpv1_pdu):
        snmpv1_pdu.port_interaction("off", 1)
        mock_run.assert_called_once()
        coro = mock_run.call_args[0][0]
        assert asyncio.iscoroutine(coro)
        coro.close()


class TestPortInteractionAsync:
    """Test the async _port_interaction_async method directly."""

    @pytest.fixture
    def mock_set_cmd(self):
        with patch("pdudaemon.drivers.snmp.set_cmd", new_callable=AsyncMock) as m:
            m.return_value = (None, 0, 0, [])
            yield m

    @pytest.fixture
    def mock_transport(self):
        with patch("pdudaemon.drivers.snmp.UdpTransportTarget") as m:
            m.create = AsyncMock(return_value=MagicMock())
            yield m

    @pytest.fixture
    def mock_engine(self):
        with patch("pdudaemon.drivers.snmp.SnmpEngine") as m:
            engine_instance = MagicMock()
            m.return_value = engine_instance
            yield engine_instance

    @pytest.mark.asyncio
    async def test_snmpv1_set_cmd_called(self, snmpv1_pdu, mock_set_cmd, mock_transport, mock_engine):
        result = await snmpv1_pdu._port_interaction_async("1", 1)
        assert result is True
        mock_set_cmd.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_snmpv3_set_cmd_called(self, snmpv3_pdu, mock_set_cmd, mock_transport, mock_engine):
        result = await snmpv3_pdu._port_interaction_async("1", 1)
        assert result is True
        mock_set_cmd.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_snmpv3_no_username_raises(self, mock_set_cmd, mock_transport, mock_engine):
        settings = {**SNMPV3_SETTINGS, "username": None}
        pdu = SNMP("192.168.1.100", settings)
        # username is explicitly None
        pdu.username = None
        with pytest.raises(FailedRequestException, match="No username"):
            await pdu._port_interaction_async("1", 1)

    @pytest.mark.asyncio
    async def test_snmpv1_no_community_raises(self, mock_set_cmd, mock_transport, mock_engine):
        settings = {**SNMPV1_SETTINGS, "community": None}
        pdu = SNMP("192.168.1.100", settings)
        pdu.community = None
        with pytest.raises(FailedRequestException, match="No community"):
            await pdu._port_interaction_async("1", 1)

    @pytest.mark.asyncio
    async def test_unknown_version_raises(self, mock_set_cmd, mock_transport, mock_engine):
        settings = {**SNMPV1_SETTINGS, "driver": "snmpv99"}
        pdu = SNMP("192.168.1.100", settings)
        with pytest.raises(FailedRequestException, match="Unknown snmp version"):
            await pdu._port_interaction_async("1", 1)

    @pytest.mark.asyncio
    async def test_error_indication_raises(self, snmpv1_pdu, mock_set_cmd, mock_transport, mock_engine):
        mock_set_cmd.return_value = ("some error", 0, 0, [])
        with pytest.raises(FailedRequestException):
            await snmpv1_pdu._port_interaction_async("1", 1)

    @pytest.mark.asyncio
    async def test_error_status_raises(self, snmpv1_pdu, mock_set_cmd, mock_transport, mock_engine):
        mock_set_cmd.return_value = (None, "badValue", 1, [])
        with pytest.raises(FailedRequestException):
            await snmpv1_pdu._port_interaction_async("1", 1)

    @pytest.mark.asyncio
    async def test_engine_closed_on_error(self, snmpv1_pdu, mock_set_cmd, mock_transport, mock_engine):
        mock_set_cmd.side_effect = RuntimeError("connection failed")
        with pytest.raises(RuntimeError):
            await snmpv1_pdu._port_interaction_async("1", 1)

    @pytest.mark.asyncio
    async def test_inside_number_controlpoint(self, mock_set_cmd, mock_transport, mock_engine):
        settings = {
            **SNMPV1_SETTINGS,
            "controlpoint": "outlet*.0",
            "inside_number": True,
        }
        pdu = SNMP("192.168.1.100", settings)
        await pdu._port_interaction_async("1", 5)
        mock_set_cmd.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_inside_number_with_static_ending(self, mock_set_cmd, mock_transport, mock_engine):
        settings = {
            **SNMPV1_SETTINGS,
            "controlpoint": "outlet*.0",
            "inside_number": True,
            "static_ending": "42",
        }
        pdu = SNMP("192.168.1.100", settings)
        await pdu._port_interaction_async("1", 3)
        mock_set_cmd.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_snmpv3_with_auth_priv_protocols(self, mock_set_cmd, mock_transport, mock_engine):
        settings = {
            **SNMPV3_SETTINGS,
            "auth_protocol": "USM_AUTH_HMAC96_SHA",
            "priv_protocol": "USM_PRIV_CFB128_AES",
        }
        pdu = SNMP("192.168.1.100", settings)
        result = await pdu._port_interaction_async("1", 1)
        assert result is True
        mock_set_cmd.assert_awaited_once()
