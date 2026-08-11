"""Tests for stale device cleanup on setup/reload."""
from homeassistant.helpers import device_registry as dr
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.strato_dyndns import _async_cleanup_stale_devices
from custom_components.strato_dyndns.const import DOMAIN


class TestCleanupStaleDevices:
    async def test_removes_device_for_renamed_or_dropped_domain(self, hass):
        entry = MockConfigEntry(domain=DOMAIN, data={"account_name": "Test"})
        entry.add_to_hass(hass)

        device_registry = dr.async_get(hass)
        account_device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, "Test")},
            name="Test",
        )
        old_domain_device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, "Test_old.example.de")},
            name="old.example.de",
        )
        new_domain_device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, "Test_new.example.de")},
            name="new.example.de",
        )

        # Subdomain "old.example.de" was renamed to "new.example.de" -> only
        # the new domain is in the current domain list.
        _async_cleanup_stale_devices(hass, entry, "Test", ["new.example.de"])

        assert device_registry.async_get(account_device.id) is not None
        assert device_registry.async_get(new_domain_device.id) is not None
        assert device_registry.async_get(old_domain_device.id) is None

    async def test_keeps_devices_for_unchanged_domains(self, hass):
        entry = MockConfigEntry(domain=DOMAIN, data={"account_name": "Test"})
        entry.add_to_hass(hass)

        device_registry = dr.async_get(hass)
        domain_device = device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, "Test_home.example.de")},
            name="home.example.de",
        )

        _async_cleanup_stale_devices(hass, entry, "Test", ["home.example.de"])

        assert device_registry.async_get(domain_device.id) is not None

    async def test_ignores_devices_from_other_config_entries(self, hass):
        entry = MockConfigEntry(domain=DOMAIN, data={"account_name": "Test"})
        entry.add_to_hass(hass)
        other_entry = MockConfigEntry(domain=DOMAIN, data={"account_name": "Other"})
        other_entry.add_to_hass(hass)

        device_registry = dr.async_get(hass)
        other_device = device_registry.async_get_or_create(
            config_entry_id=other_entry.entry_id,
            identifiers={(DOMAIN, "Other_untouched.example.de")},
            name="untouched.example.de",
        )

        # Cleanup runs for `entry`, which has no domains at all -> must not
        # touch devices that belong to `other_entry`.
        _async_cleanup_stale_devices(hass, entry, "Test", [])

        assert device_registry.async_get(other_device.id) is not None
