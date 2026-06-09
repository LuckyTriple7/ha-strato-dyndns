from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STRATO_RESPONSE_DESCRIPTIONS
from .coordinator import StratoDynDNSCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: StratoDynDNSCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        StratoPublicIPv4Sensor(coordinator, entry),
    ]
    if coordinator.ipv6_enabled:
        entities.append(StratoPublicIPv6Sensor(coordinator, entry))
    for domain in coordinator.domains:
        entities.append(StratoDomainResolvedIPSensor(coordinator, entry, domain))
        entities.append(StratoDomainLastUpdateSensor(coordinator, entry, domain))
        if coordinator.ipv6_enabled:
            entities.append(StratoDomainResolvedIPv6Sensor(coordinator, entry, domain))
    async_add_entities(entities)


def _device_info(coordinator: StratoDynDNSCoordinator) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.account_name)},
        name=f"Strato DynDNS · {coordinator.account_name}",
        manufacturer="Strato AG",
        model="DynDNS",
    )


class StratoPublicIPv4Sensor(CoordinatorEntity[StratoDynDNSCoordinator], SensorEntity):
    _attr_icon = "mdi:ip-network"

    def __init__(self, coordinator: StratoDynDNSCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_public_ipv4"
        self._attr_name = f"{coordinator.account_name} Public IPv4"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("public_ip")

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        return {"provider": self.coordinator.data.get("public_ip_provider")}


class StratoPublicIPv6Sensor(CoordinatorEntity[StratoDynDNSCoordinator], SensorEntity):
    _attr_icon = "mdi:ip-network-outline"

    def __init__(self, coordinator: StratoDynDNSCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_public_ipv6"
        # No account prefix — public IPv6 is network-wide, not per account
        self._attr_name = "Public IPv6"
        self._attr_device_info = _device_info(coordinator)

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("public_ip6")

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        return {"provider": self.coordinator.data.get("public_ip6_provider")}


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
        self._attr_name = f"{coordinator.account_name} Domain {domain} Resolved IP"
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
        response = d.get("update_response") or ""
        code = response.split()[0] if response else None
        attrs = {
            "public_ip": self.coordinator.data.get("public_ip"),
            "update_status": d.get("update_status"),
            "update_response": response or None,
        }
        if code:
            attrs["update_response_detail"] = STRATO_RESPONSE_DESCRIPTIONS.get(code, response)
        if d.get("backoff_until"):
            attrs["retry_after"] = d["backoff_until"].isoformat()
        return attrs


class StratoDomainResolvedIPv6Sensor(CoordinatorEntity[StratoDynDNSCoordinator], SensorEntity):
    _attr_icon = "mdi:dns-outline"

    def __init__(
        self,
        coordinator: StratoDynDNSCoordinator,
        entry: ConfigEntry,
        domain: str,
    ) -> None:
        super().__init__(coordinator)
        slug = domain.replace(".", "_").replace("-", "_")
        self._attr_unique_id = f"{entry.entry_id}_{slug}_resolved_ipv6"
        self._attr_name = f"{coordinator.account_name} Domain {domain} Resolved IPv6"
        self._attr_device_info = _device_info(coordinator)
        self._domain = domain

    @property
    def native_value(self) -> str | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data["domains"].get(self._domain, {}).get("resolved_ip6")

    @property
    def extra_state_attributes(self) -> dict:
        if not self.coordinator.data:
            return {}
        d = self.coordinator.data["domains"].get(self._domain, {})
        return {"public_ip6": self.coordinator.data.get("public_ip6")}


class StratoDomainLastUpdateSensor(CoordinatorEntity[StratoDynDNSCoordinator], SensorEntity):
    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_icon = "mdi:clock-check-outline"

    def __init__(
        self,
        coordinator: StratoDynDNSCoordinator,
        entry: ConfigEntry,
        domain: str,
    ) -> None:
        super().__init__(coordinator)
        slug = domain.replace(".", "_").replace("-", "_")
        self._attr_unique_id = f"{entry.entry_id}_{slug}_last_update"
        self._attr_name = f"{coordinator.account_name} Domain {domain} Last Update"
        self._attr_device_info = _device_info(coordinator)
        self._domain = domain

    @property
    def native_value(self) -> datetime | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data["domains"].get(self._domain, {}).get("last_update_time")
