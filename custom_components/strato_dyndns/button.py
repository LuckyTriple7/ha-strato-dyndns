from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import StratoDynDNSCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: StratoDynDNSCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([StratoUpdateNowButton(coordinator, entry)])


class StratoUpdateNowButton(CoordinatorEntity[StratoDynDNSCoordinator], ButtonEntity):
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: StratoDynDNSCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_update_now"
        self._attr_name = f"Strato {coordinator.account_name} Update Now"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.account_name)},
            name=f"Strato DynDNS · {coordinator.account_name}",
            manufacturer="Strato AG",
            model="DynDNS",
        )

    async def async_press(self) -> None:
        await self.coordinator.async_force_update()
