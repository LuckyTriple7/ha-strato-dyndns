"""Tests for the Strato DynDNS config flow."""
import pytest
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType

from custom_components.strato_dyndns.const import (
    CONF_ACCOUNT_NAME,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
    DOMAIN_FIELDS,
)


def _domain_input(**kwargs) -> dict:
    """Build a full domain input dict with all fields, overriding with kwargs."""
    base = {f: "" for f in DOMAIN_FIELDS}
    base.update(kwargs)
    return base


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture(autouse=True)
def mock_setup(mock_public_ip, mock_resolve_ip, mock_strato_update):
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

        domain_input = _domain_input(domain_1="home.example.de", domain_2="vpn.example.de")
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**domain_input, CONF_UPDATE_INTERVAL: 60},
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "TestAccount"
        # Field positions are stored directly
        assert result["data"]["domain_1"] == "home.example.de"
        assert result["data"]["domain_2"] == "vpn.example.de"
        assert result["data"]["domain_main"] == ""
        assert result["data"][CONF_UPDATE_INTERVAL] == 60

    async def test_empty_domains_shows_error(self, hass):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ACCOUNT_NAME: "TestAccount", "username": "u", "password": "p"},
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**_domain_input(), CONF_UPDATE_INTERVAL: 30},
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
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**_domain_input(domain_main="example.de"), CONF_UPDATE_INTERVAL: 30},
        )
        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"]["domain_main"] == "example.de"

    async def test_subdomain_fields_preserved_on_options(self, hass):
        """Domains entered in domain_1/domain_2 must not shift to domain_main on re-open."""
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_ACCOUNT_NAME: "TestAccount", "username": "u", "password": "p"},
        )
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {**_domain_input(domain_1="home.example.de", domain_2="vpn.example.de"),
             CONF_UPDATE_INTERVAL: 30},
        )
        entry = hass.config_entries.async_entries(DOMAIN)[0]
        # Verify positions are correct after initial setup
        assert entry.data["domain_main"] == ""
        assert entry.data["domain_1"] == "home.example.de"
        assert entry.data["domain_2"] == "vpn.example.de"

    async def test_duplicate_account_aborted(self, hass):
        for _ in range(2):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {CONF_ACCOUNT_NAME: "TestAccount", "username": "u", "password": "p"},
            )
            result = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                {**_domain_input(domain_1="home.example.de"), CONF_UPDATE_INTERVAL: 30},
            )

        assert result["type"] == FlowResultType.ABORT
        assert result["reason"] == "already_configured"
