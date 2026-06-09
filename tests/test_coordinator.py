"""Tests for the Strato DynDNS coordinator."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.strato_dyndns.coordinator import (
    StratoDynDNSCoordinator,
    async_get_public_ip,
    async_resolve_ip,
)


class TestAsyncGetPublicIp:
    async def test_returns_ip_from_first_provider(self):
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.text = AsyncMock(return_value="1.2.3.4\n")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        result = await async_get_public_ip(mock_session)
        assert result == "1.2.3.4"

    async def test_falls_back_to_second_provider_on_failure(self):
        call_count = 0

        def fake_get(url, **kwargs):
            nonlocal call_count
            call_count += 1
            ctx = AsyncMock()
            if call_count == 1:
                ctx.__aenter__ = AsyncMock(side_effect=Exception("timeout"))
            else:
                resp = AsyncMock()
                resp.status = 200
                resp.text = AsyncMock(return_value="5.6.7.8")
                ctx.__aenter__ = AsyncMock(return_value=resp)
            ctx.__aexit__ = AsyncMock(return_value=False)
            return ctx

        mock_session = MagicMock()
        mock_session.get = fake_get

        result = await async_get_public_ip(mock_session)
        assert result == "5.6.7.8"

    async def test_returns_none_when_all_providers_fail(self):
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("network error"))

        result = await async_get_public_ip(mock_session)
        assert result is None


class TestAsyncResolveIp:
    async def test_resolves_domain(self):
        with patch(
            "custom_components.strato_dyndns.coordinator.socket.gethostbyname",
            return_value="1.2.3.4",
        ):
            result = await async_resolve_ip("home.example.de")
        assert result == "1.2.3.4"

    async def test_returns_none_on_error(self):
        with patch(
            "custom_components.strato_dyndns.coordinator.socket.gethostbyname",
            side_effect=OSError("Name or service not known"),
        ):
            result = await async_resolve_ip("does-not-exist.example.de")
        assert result is None


class TestStratoDynDNSCoordinator:
    def _make_coordinator(self, hass):
        return StratoDynDNSCoordinator(
            hass=hass,
            account_name="Test",
            username="user",
            password="pass",
            domains=["home.example.de"],
            update_interval=5,
        )

    async def test_first_run_triggers_update(self, hass, mock_public_ip, mock_resolve_ip, mock_strato_update):
        coordinator = self._make_coordinator(hass)
        data = await coordinator._async_update_data()

        assert data["public_ip"] == "1.2.3.4"
        # First run: _last_ip is None → ip_changed=True → update called
        mock_strato_update.assert_called_once_with("home.example.de", "1.2.3.4")

    async def test_no_update_when_ip_unchanged(self, hass, mock_public_ip, mock_resolve_ip, mock_strato_update):
        coordinator = self._make_coordinator(hass)
        coordinator._last_ip = "1.2.3.4"  # simulate already known

        await coordinator._async_update_data()
        mock_strato_update.assert_not_called()

    async def test_update_triggered_on_ip_change(self, hass, mock_public_ip, mock_resolve_ip, mock_strato_update):
        coordinator = self._make_coordinator(hass)
        coordinator._last_ip = "9.9.9.9"  # old IP

        await coordinator._async_update_data()
        mock_strato_update.assert_called_once_with("home.example.de", "1.2.3.4")

    async def test_mismatch_detected(self, hass, mock_public_ip, mock_strato_update):
        with patch(
            "custom_components.strato_dyndns.coordinator.async_resolve_ip",
            new_callable=AsyncMock,
            return_value="9.9.9.9",  # different from public IP
        ):
            coordinator = self._make_coordinator(hass)
            coordinator._last_ip = "1.2.3.4"  # no IP change
            data = await coordinator._async_update_data()

        assert data["domains"]["home.example.de"]["ip_mismatch"] is True

    async def test_no_mismatch_when_ips_match(self, hass, mock_public_ip, mock_resolve_ip, mock_strato_update):
        coordinator = self._make_coordinator(hass)
        coordinator._last_ip = "1.2.3.4"
        data = await coordinator._async_update_data()

        assert data["domains"]["home.example.de"]["ip_mismatch"] is False

    async def test_raises_on_no_public_ip(self, hass):
        from homeassistant.helpers.update_coordinator import UpdateFailed

        with patch(
            "custom_components.strato_dyndns.coordinator.async_get_public_ip",
            new_callable=AsyncMock,
            return_value=None,
        ):
            coordinator = self._make_coordinator(hass)
            with pytest.raises(UpdateFailed):
                await coordinator._async_update_data()
