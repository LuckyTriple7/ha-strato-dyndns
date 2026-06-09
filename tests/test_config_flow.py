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

DOMAIN_INPUT = {
    "domain_main": "",
    "domain_1": "home.example.de",
    "domain_2": "vpn.example.de",
    "domain_3": "", "domain_4": "", "domain_5": "",
    "domain_6": "", "domain_7": "", "domain_8": "",
    "domain_9": "", "domain_10": "",
}


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
            {CONF_ACCOUNT_NAME: "TestAccount", "username": "u", "password": "p"},
        )
        assert result["step_id"] == "domains"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**DOMAIN_INPUT, CONF_UPDATE_INTERVAL: 60},
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "TestAccount"
        assert result["data"][CONF_DOMAINS] == ["home.example.de", "vpn.example.de"]
        assert result["data"][CONF_UPDATE_INTERVAL] == 60

    async def test_empty_domains_shows_error(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ACCOUNT_NAME: "TestAccount", "username": "u", "password": "p"},
        )
        empty_input = {f: "" for f in [
            "domain_main", "domain_1", "domain_2", "domain_3", "domain_4",
            "domain_5", "domain_6", "domain_7", "domain_8", "domain_9", "domain_10",
        ]}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**empty_input, CONF_UPDATE_INTERVAL: 30},
        )
        assert result["type"] == FlowResultType.FORM
        assert "no_domains" in result["errors"].values()

    async def test_main_domain_only(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ACCOUNT_NAME: "TestAccount", "username": "u", "password": "p"},
        )
        main_only = {f: "" for f in [
            "domain_main", "domain_1", "domain_2", "domain_3", "domain_4",
            "domain_5", "domain_6", "domain_7", "domain_8", "domain_9", "domain_10",
        ]}
        main_only["domain_main"] = "example.de"
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**main_only, CONF_UPDATE_INTERVAL: 30},
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_DOMAINS] == ["example.de"]

    async def test_duplicate_account_aborted(self, hass):
        for flow_id_account in ["TestAccount", "TestAccount"]:
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_ACCOUNT_NAME: flow_id_account, "username": "u", "password": "p"},
            )
            single = {f: "" for f in [
                "domain_main", "domain_1", "domain_2", "domain_3", "domain_4",
                "domain_5", "domain_6", "domain_7", "domain_8", "domain_9", "domain_10",
            ]}
            single["domain_1"] = "home.example.de"
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {**single, CONF_UPDATE_INTERVAL: 30},
            )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"
