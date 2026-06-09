from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ACCOUNT_NAME,
    CONF_DOMAINS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    DOMAIN_FIELDS,
)

# Ordered list of all domain input field keys
# domain_main = Hauptdomain (optional), domain_1..10 = Subdomains (optional)


def _fields_to_domains(data: dict) -> list[str]:
    return [v for f in DOMAIN_FIELDS if (v := data.get(f, "").strip().lower())]


def _domains_to_fields(domains: list[str]) -> dict[str, str]:
    return {f: domains[i] if i < len(domains) else "" for i, f in enumerate(DOMAIN_FIELDS)}


def _domain_schema(defaults: dict[str, str]) -> vol.Schema:
    return vol.Schema(
        {vol.Optional(f, default=defaults.get(f, "")): str for f in DOMAIN_FIELDS}
    )


class StratoDynDNSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_domains()

        schema = vol.Schema(
            {
                vol.Required(CONF_ACCOUNT_NAME): str,
                vol.Required("username"): str,
                vol.Required("password"): str,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_domains(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            domains = _fields_to_domains(user_input)
            interval = user_input[CONF_UPDATE_INTERVAL]
            if not domains:
                errors["base"] = "no_domains"
            else:
                self._data[CONF_DOMAINS] = domains
                self._data[CONF_UPDATE_INTERVAL] = interval

                unique_id = self._data[CONF_ACCOUNT_NAME].lower().replace(" ", "_")
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=self._data[CONF_ACCOUNT_NAME],
                    data=self._data,
                )

        schema = _domain_schema({})
        schema = schema.extend(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): vol.All(int, vol.Range(min=30, max=3600)),
            }
        )
        return self.async_show_form(
            step_id="domains", data_schema=schema, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return StratoDynDNSOptionsFlow()


class StratoDynDNSOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            domains = _fields_to_domains(user_input)
            if not domains:
                errors["base"] = "no_domains"
            else:
                return self.async_create_entry(
                    title="",
                    data={
                        CONF_DOMAINS: domains,
                        CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                    },
                )

        effective = {**self.config_entry.data, **self.config_entry.options}
        current_domains = effective.get(CONF_DOMAINS, [])
        current_interval = effective.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)

        schema = _domain_schema(_domains_to_fields(current_domains))
        schema = schema.extend(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=current_interval
                ): vol.All(int, vol.Range(min=30, max=3600)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
