"""Diagnostics support for Strato DynDNS."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import StratoDynDNSCoordinator

TO_REDACT = {"username", "password", "account_name"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: StratoDynDNSCoordinator = hass.data[DOMAIN][entry.entry_id]

    return {
        "entry_data": async_redact_data(dict(entry.data), TO_REDACT),
        "entry_options": async_redact_data(dict(entry.options), TO_REDACT),
        "coordinator_data": coordinator.data,
        "ipv6_enabled": coordinator.ipv6_enabled,
        "notifications_enabled": coordinator.notifications_enabled,
        "domains": coordinator.domains,
    }
