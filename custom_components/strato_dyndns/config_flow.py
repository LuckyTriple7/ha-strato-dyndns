from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ACCOUNT_NAME,
    CONF_IPV6_ENABLED,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    DOMAIN_FIELDS,
)


def _fields_to_domains(data: dict) -> list[str]:
    return [v for f in DOMAIN_FIELDS if (v := data.get(f, "").strip().lower())]


def _domain_schema(defaults: dict[str, str]) -> vol.Schema:
    return vol.Schema(
        {vol.Optional(f, default=defaults.get(f, "")): str for f in DOMAIN_FIELDS}
    )


class StratoDynDNSConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_domains()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ACCOUNT_NAME): str,
                    vol.Required("username"): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_domains(self, user_input=None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            domains = _fields_to_domains(user_input)
            if not domains:
                errors["base"] = "no_domains"
            else:
                for field in DOMAIN_FIELDS:
                    self._data[field] = user_input.get(field, "").strip().lower()
                self._data[CONF_UPDATE_INTERVAL] = user_input[CONF_UPDATE_INTERVAL]
                self._data[CONF_IPV6_ENABLED] = user_input.get(CONF_IPV6_ENABLED, False)

                unique_id = self._data[CONF_ACCOUNT_NAME].lower().replace(" ", "_")
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=self._data[CONF_ACCOUNT_NAME],
                    data=self._data,
                )

        schema = _domain_schema({}).extend(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                ): vol.All(int, vol.Range(min=10, max=3600)),
                vol.Optional(CONF_IPV6_ENABLED, default=False): bool,
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
                        **{f: user_input.get(f, "").strip().lower() for f in DOMAIN_FIELDS},
                        CONF_UPDATE_INTERVAL: user_input[CONF_UPDATE_INTERVAL],
                        CONF_IPV6_ENABLED: user_input.get(CONF_IPV6_ENABLED, False),
                    },
                )

        effective = {**self.config_entry.data, **self.config_entry.options}
        defaults = {f: effective.get(f, "") for f in DOMAIN_FIELDS}
        current_interval = effective.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        current_ipv6 = effective.get(CONF_IPV6_ENABLED, False)

        schema = _domain_schema(defaults).extend(
            {
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=current_interval
                ): vol.All(int, vol.Range(min=10, max=3600)),
                vol.Optional(CONF_IPV6_ENABLED, default=current_ipv6): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema, errors=errors)
