"""Tests for the Strato DynDNS coordinator."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.strato_dyndns import coordinator as coordinator_module
from custom_components.strato_dyndns.const import IP_PROVIDERS
from custom_components.strato_dyndns.coordinator import (
    StratoDynDNSCoordinator,
    async_get_public_ip,
    async_resolve_ip,
)


class TestAsyncGetPublicIp:
    async def test_returns_ip_and_provider_from_first_provider(self):
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.text = AsyncMock(return_value="1.2.3.4\n")
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)

        mock_session = MagicMock()
        mock_session.get = MagicMock(return_value=mock_resp)

        # Returns a (ip, provider_url) tuple so the provider can be logged and
        # exposed as an attribute.
        assert await async_get_public_ip(mock_session) == ("1.2.3.4", IP_PROVIDERS[0])

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

        assert await async_get_public_ip(mock_session) == ("5.6.7.8", IP_PROVIDERS[1])

    async def test_returns_none_when_all_providers_fail(self):
        mock_session = MagicMock()
        mock_session.get = MagicMock(side_effect=Exception("network error"))

        assert await async_get_public_ip(mock_session) is None


class TestAsyncResolveIp:
    async def test_resolves_domain(self):
        # Resolution goes through dnspython against fixed nameservers, not
        # through the system resolver.
        with patch.object(
            coordinator_module._DNS_RESOLVER, "resolve", return_value=["1.2.3.4"]
        ) as resolve:
            result = await async_resolve_ip("home.example.de")

        assert result == "1.2.3.4"
        resolve.assert_called_once_with("home.example.de", "A")

    async def test_returns_none_on_error(self):
        with patch.object(
            coordinator_module._DNS_RESOLVER,
            "resolve",
            side_effect=Exception("NXDOMAIN"),
        ):
            assert await async_resolve_ip("does-not-exist.example.de") is None


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

    async def test_sends_update_when_dns_differs_on_first_run(
        self, hass, mock_public_ip, mock_strato_update
    ):
        # No prior state (fresh start): the DNS record decides, so a stale
        # record means Strato has to be told about the current IP.
        with patch(
            "custom_components.strato_dyndns.coordinator.async_resolve_ip",
            new_callable=AsyncMock,
            return_value="9.9.9.9",
        ):
            coordinator = self._make_coordinator(hass)
            data = await coordinator._async_update_data()

        assert data["public_ip"] == "1.2.3.4"
        assert data["public_ip_provider"] == "https://api.ipify.org"
        mock_strato_update.assert_called_once_with("home.example.de", "1.2.3.4", None)

    async def test_no_update_when_dns_already_matches(
        self, hass, mock_public_ip, mock_resolve_ip, mock_strato_update
    ):
        coordinator = self._make_coordinator(hass)
        await coordinator._async_update_data()

        mock_strato_update.assert_not_called()

    async def test_update_triggered_on_ip_change(
        self, hass, mock_public_ip, mock_resolve_ip, mock_strato_update
    ):
        coordinator = self._make_coordinator(hass)
        coordinator._last_sent_ip4["home.example.de"] = "9.9.9.9"  # old IP was sent

        await coordinator._async_update_data()

        mock_strato_update.assert_called_once_with("home.example.de", "1.2.3.4", None)

    async def test_no_resend_while_dns_is_still_propagating(
        self, hass, mock_public_ip, mock_strato_update
    ):
        # Already sent this exact IP, DNS just hasn't caught up yet — sending
        # again would only risk an "abuse" block.
        with patch(
            "custom_components.strato_dyndns.coordinator.async_resolve_ip",
            new_callable=AsyncMock,
            return_value="9.9.9.9",
        ):
            coordinator = self._make_coordinator(hass)
            coordinator._last_sent_ip4["home.example.de"] = "1.2.3.4"
            await coordinator._async_update_data()

        mock_strato_update.assert_not_called()

    async def test_force_update_ignores_everything(
        self, hass, mock_public_ip, mock_resolve_ip, mock_strato_update
    ):
        coordinator = self._make_coordinator(hass)
        coordinator._last_sent_ip4["home.example.de"] = "1.2.3.4"  # nothing to do
        coordinator._force_update = True

        await coordinator._async_update_data()

        mock_strato_update.assert_called_once_with("home.example.de", "1.2.3.4", None)
        assert coordinator._force_update is False  # consumed by the run

    async def test_mismatch_detected(self, hass, mock_public_ip, mock_strato_update):
        with patch(
            "custom_components.strato_dyndns.coordinator.async_resolve_ip",
            new_callable=AsyncMock,
            return_value="9.9.9.9",  # different from public IP
        ):
            coordinator = self._make_coordinator(hass)
            data = await coordinator._async_update_data()

        assert data["domains"]["home.example.de"]["ip_mismatch"] is True

    async def test_no_mismatch_when_ips_match(
        self, hass, mock_public_ip, mock_resolve_ip, mock_strato_update
    ):
        coordinator = self._make_coordinator(hass)
        data = await coordinator._async_update_data()

        assert data["domains"]["home.example.de"]["ip_mismatch"] is False

    async def test_failed_update_puts_domain_into_backoff(
        self, hass, mock_public_ip, mock_resolve_ip
    ):
        with patch(
            "custom_components.strato_dyndns.coordinator.StratoDynDNSCoordinator._update_domain",
            new_callable=AsyncMock,
            return_value=("error", "abuse"),
        ) as failing_update:
            coordinator = self._make_coordinator(hass)
            coordinator._last_sent_ip4["home.example.de"] = "9.9.9.9"
            data = await coordinator._async_update_data()

            assert data["domains"]["home.example.de"]["update_status"] == "error"
            assert "home.example.de" in coordinator._error_backoff

            # Second run within the backoff window must not hit Strato again.
            await coordinator._async_update_data()

        failing_update.assert_called_once()

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
