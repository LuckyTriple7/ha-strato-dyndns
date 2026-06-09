"""Tests for the Strato DynDNS config flow."""
import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.strato_dyndns.const import (
    CONF_ACCOUNT_NAME,
    CONF_DOMAINS,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)

from tests.conftest import MOCK_CONFIG


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def mock_setup(mock_public_ip, mock_resolve_ip, mock_strato_update):
    """Prevent real network calls when HA sets up the integration after entry creation."""
    yield


class TestConfigFlow:
    async def test_user_step_shows_form(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

    async def test_full_flow_creates_entry(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ACCOUNT_NAME: "TestAccount",
                "username": "testuser",
                "password": "testpass",
            },
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "domains"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_DOMAINS: "home.example.de, vpn.example.de",
                CONF_UPDATE_INTERVAL: 10,
            },
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "TestAccount"
        assert result["data"][CONF_DOMAINS] == ["home.example.de", "vpn.example.de"]
        assert result["data"][CONF_UPDATE_INTERVAL] == 10

    async def test_empty_domains_shows_error(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_ACCOUNT_NAME: "TestAccount",
                "username": "testuser",
                "password": "testpass",
            },
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DOMAINS: "   ,  , ", CONF_UPDATE_INTERVAL: 5},
        )
        assert result["type"] == FlowResultType.FORM
        assert "no_domains" in result["errors"].values()

    async def test_duplicate_account_aborted(self, hass):
        # First entry
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ACCOUNT_NAME: "TestAccount", "username": "u", "password": "p"},
        )
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_DOMAINS: "home.example.de", CONF_UPDATE_INTERVAL: 5},
        )

        # Second entry with same account name
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_ACCOUNT_NAME: "TestAccount", "username": "u", "password": "p"},
        )
        result2 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_DOMAINS: "other.example.de", CONF_UPDATE_INTERVAL: 5},
        )
        assert result2["type"] == FlowResultType.ABORT
        assert result2["reason"] == "already_configured"
