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
        if coordinator.ipv6_enabled:
            entities.append(StratoDomainIPv6MismatchSensor(coordinator, entry, domain))
    async_add_entities(entities)


def _device_info(coordinator: StratoDynDNSCoordinator) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.account_name)},
        name=f"Strato DynDNS · {coordinator.account_name}",
        manufacturer="Strato AG",
        model="DynDNS",
    )


class StratoAccountErrorSensor(CoordinatorEntity[StratoDynDNSCoordinator], BinarySensorEntity):
    """ON when any domain's last update attempt returned an error."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:cloud-alert"

    def __init__(self, coordinator: StratoDynDNSCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_account_error"
        self._attr_name = f"{coordinator.account_name} Error"
        self._attr_device_info = _device_info(coordinator)

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        ipv6 = self.coordinator.ipv6_enabled
        return any(
            v.get("ip_mismatch") is True
            or (ipv6 and v.get("ip6_mismatch") is True)
            for v in self.coordinator.data["domains"].values()
        )

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        ipv6 = self.coordinator.ipv6_enabled
        problems: dict[str, list[str]] = {}
        for domain, v in self.coordinator.data["domains"].items():
            reasons = []
            if v.get("ip_mismatch") is True:
                reasons.append(f"ipv4_mismatch: {v.get('resolved_ip')} != {self.coordinator.data.get('public_ip')}")
            if ipv6 and v.get("ip6_mismatch") is True:
                reasons.append(f"ipv6_mismatch: {v.get('resolved_ip6')} != {self.coordinator.data.get('public_ip6')}")
            if reasons:
                problems[domain] = reasons
        return {
            "problem_domains": list(problems.keys()),
            "details": problems,
        }


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
        self._attr_name = f"{coordinator.account_name} Domain {domain} IP Mismatch"
        self._attr_device_info = _device_info(coordinator)
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


class StratoDomainIPv6MismatchSensor(CoordinatorEntity[StratoDynDNSCoordinator], BinarySensorEntity):
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
        self._attr_unique_id = f"{entry.entry_id}_{slug}_ipv6_mismatch"
        self._attr_name = f"{coordinator.account_name} Domain {domain} IPv6 Mismatch"
        self._attr_device_info = _device_info(coordinator)
        self._domain = domain

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data["domains"].get(self._domain, {}).get("ip6_mismatch")

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        d = self.coordinator.data["domains"].get(self._domain, {})
        return {
            "resolved_ipv6": d.get("resolved_ip6"),
            "public_ipv6": self.coordinator.data.get("public_ip6"),
            "last_update_status": d.get("update_status"),
            "last_update_response": d.get("update_response"),
        }
