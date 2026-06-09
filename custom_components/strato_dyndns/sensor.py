from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
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
    entities: list[SensorEntity] = [StratoPublicIPSensor(coordinator, entry)]
    for domain in coordinator.domains:
        entities.append(StratoDomainResolvedIPSensor(coordinator, entry, domain))
    async_add_entities(entities)


def _device_info(coordinator: StratoDynDNSCoordinator) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.account_name)},
        name=f"Strato DynDNS · {coordinator.account_name}",
        manufacturer="Strato AG",
        model="DynDNS",
    )


class StratoPublicIPSensor(CoordinatorEntity[StratoDynDNSCoordinator], SensorEntity):
    _attr_icon = "mdi:ip-network"

    def __init__(self, coordinator: StratoDynDNSCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_public_ip"
        self._attr_name = f"Strato {coordinator.account_name} Public IP"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("public_ip")


class StratoDomainResolvedIPSensor(CoordinatorEntity[StratoDynDNSCoordinator], SensorEntity):
    _attr_icon = "mdi:dns"

    def __init__(
        self,
        coordinator: StratoDynDNSCoordinator,
        entry: ConfigEntry,
        domain: str,
    ) -> None:
        super().__init__(coordinator)
        slug = domain.replace(".", "_").replace("-", "_")
        self._attr_unique_id = f"{entry.entry_id}_{slug}_resolved_ip"
        self._attr_name = f"Strato {domain} Resolved IP"
        self._attr_device_info = _device_info(coordinator)
        self._domain = domain

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data["domains"].get(self._domain, {}).get("resolved_ip")

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        d = self.coordinator.data["domains"].get(self._domain, {})
        return {
            "public_ip": self.coordinator.data.get("public_ip"),
            "update_status": d.get("update_status"),
            "update_response": d.get("update_response"),
        }
