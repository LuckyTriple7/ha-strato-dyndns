from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    entities: list[BinarySensorEntity] = [StratoAccountErrorSensor(coordinator, entry)]
    for domain in coordinator.domains:
        entities.append(StratoDomainMismatchSensor(coordinator, entry, domain))
    async_add_entities(entities)


class StratoAccountErrorSensor(CoordinatorEntity[StratoDynDNSCoordinator], BinarySensorEntity):
    """ON when any domain's last update attempt returned an error."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:cloud-alert"

    def __init__(self, coordinator: StratoDynDNSCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_account_error"
        self._attr_name = f"Strato {coordinator.account_name} Error"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.account_name)},
            name=f"Strato DynDNS · {coordinator.account_name}",
            manufacturer="Strato AG",
            model="DynDNS",
        )

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return any(
            v.get("update_status") == "error"
            for v in self.coordinator.data["domains"].values()
        )

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        failed = {
            domain: v.get("update_response")
            for domain, v in self.coordinator.data["domains"].items()
            if v.get("update_status") == "error"
        }
        return {"failed_domains": list(failed.keys()), "error_details": failed}


class StratoDomainMismatchSensor(CoordinatorEntity[StratoDynDNSCoordinator], BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(
        self,
        coordinator: StratoDynDNSCoordinator,
        entry: ConfigEntry,
        domain: str,
    ) -> None:
        super().__init__(coordinator)
        slug = domain.replace(".", "_").replace("-", "_")
        self._attr_unique_id = f"{entry.entry_id}_{slug}_mismatch"
        self._attr_name = f"Strato {domain} IP Mismatch"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.account_name)},
            name=f"Strato DynDNS · {coordinator.account_name}",
            manufacturer="Strato AG",
            model="DynDNS",
        )
        self._domain = domain

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data["domains"].get(self._domain, {}).get("ip_mismatch", True)

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        d = self.coordinator.data["domains"].get(self._domain, {})
        return {
            "resolved_ip": d.get("resolved_ip"),
            "public_ip": self.coordinator.data.get("public_ip"),
            "last_update_status": d.get("update_status"),
            "last_update_response": d.get("update_response"),
        }
