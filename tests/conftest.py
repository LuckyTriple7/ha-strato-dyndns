"""Shared fixtures for Strato DynDNS tests."""
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.core import HomeAssistant

from custom_components.strato_dyndns.const import (
    CONF_ACCOUNT_NAME,
    CONF_DOMAINS,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)

MOCK_CONFIG = {
    CONF_ACCOUNT_NAME: "TestAccount",
    "username": "testuser",
    "password": "testpass",
    CONF_DOMAINS: ["home.example.de", "vpn.example.de"],
    CONF_UPDATE_INTERVAL: 5,
}


@pytest.fixture
def mock_public_ip():
    with patch(
        "custom_components.strato_dyndns.coordinator.async_get_public_ip",
        new_callable=AsyncMock,
        return_value="1.2.3.4",
    ) as mock:
        yield mock


@pytest.fixture
def mock_resolve_ip():
    with patch(
        "custom_components.strato_dyndns.coordinator.async_resolve_ip",
        new_callable=AsyncMock,
        return_value="1.2.3.4",
    ) as mock:
        yield mock


@pytest.fixture
def mock_strato_update():
    with patch(
        "custom_components.strato_dyndns.coordinator.StratoDynDNSCoordinator._update_domain",
        new_callable=AsyncMock,
        return_value=("ok", "good 1.2.3.4"),
    ) as mock:
        yield mock
