from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .config_flow import _fields_to_domains
from .const import (
    CONF_ACCOUNT_NAME,
    CONF_IPV6_ENABLED,
    CONF_NOTIFICATIONS_ENABLED,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)
from .coordinator import StratoDynDNSCoordinator

PLATFORMS = ["sensor", "binary_sensor", "button"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    effective = {**entry.data, **entry.options}
    account_name = effective[CONF_ACCOUNT_NAME]
    domains = _fields_to_domains(effective)

    coordinator = StratoDynDNSCoordinator(
        hass=hass,
        account_name=account_name,
        username=effective["username"],
        password=effective["password"],
        domains=domains,
        update_interval=effective.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        ipv6_enabled=effective.get(CONF_IPV6_ENABLED, False),
        notifications_enabled=effective.get(CONF_NOTIFICATIONS_ENABLED, True),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    _async_cleanup_stale_devices(hass, entry, account_name, domains)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_reload_entry))
    return True


def _async_cleanup_stale_devices(
    hass: HomeAssistant, entry: ConfigEntry, account_name: str, domains: list[str]
) -> None:
    """Remove devices (and their entities) for domains no longer in this entry.

    Renaming/removing a subdomain via the options flow changes the per-domain
    device identifier (account_name + domain), so the old device is orphaned
    otherwise — it survives disabling and HA restarts since nothing ever
    tells the registry it's gone.
    """
    device_registry = dr.async_get(hass)
    keep = {(DOMAIN, account_name)} | {
        (DOMAIN, f"{account_name}_{domain}") for domain in domains
    }
    for device in dr.async_entries_for_config_entry(device_registry, entry.entry_id):
        if not device.identifiers & keep:
            device_registry.async_update_device(
                device.id, remove_config_entry_id=entry.entry_id
            )


async def _async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
