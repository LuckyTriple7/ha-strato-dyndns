"""Tests for the Strato DynDNS diagnostics."""
from unittest.mock import MagicMock

from custom_components.strato_dyndns.const import DOMAIN
from custom_components.strato_dyndns.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.strato_dyndns.coordinator import StratoDynDNSCoordinator


def _make_coordinator(hass):
    coordinator = StratoDynDNSCoordinator(
        hass=hass,
        account_name="Test",
        username="user",
        password="pass",
        domains=["home.example.de"],
        update_interval=5,
        ipv6_enabled=True,
        notifications_enabled=True,
    )
    coordinator.data = {
        "public_ip": "1.2.3.4",
        "public_ip_provider": "https://api.ipify.org",
        "public_ip6": None,
        "public_ip6_provider": None,
        "domains": {
            "home.example.de": {
                "resolved_ip": "1.2.3.4",
                "ip_mismatch": False,
                "update_status": "ok",
                "update_response": "good 1.2.3.4",
            }
        },
    }
    return coordinator


class TestDiagnostics:
    async def test_redacts_sensitive_fields(self, hass):
        coordinator = _make_coordinator(hass)
        entry = MagicMock()
        entry.data = {
            "account_name": "Test",
            "username": "user",
            "password": "pass",
            "domain_main": "home.example.de",
        }
        entry.options = {}
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

        result = await async_get_config_entry_diagnostics(hass, entry)

        assert result["entry_data"]["username"] == "**REDACTED**"
        assert result["entry_data"]["password"] == "**REDACTED**"
        assert result["entry_data"]["account_name"] == "**REDACTED**"
        assert result["entry_data"]["domain_main"] == "home.example.de"

    async def test_includes_coordinator_data(self, hass):
        coordinator = _make_coordinator(hass)
        entry = MagicMock()
        entry.data = {"account_name": "Test"}
        entry.options = {}
        hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

        result = await async_get_config_entry_diagnostics(hass, entry)

        assert result["coordinator_data"]["public_ip"] == "1.2.3.4"
        assert result["ipv6_enabled"] is True
        assert result["notifications_enabled"] is True
        assert result["domains"] == ["home.example.de"]
