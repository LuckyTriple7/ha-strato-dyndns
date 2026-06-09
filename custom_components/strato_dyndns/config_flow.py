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
)


def _parse_domains(raw: str) -> list[str]:
    return [d.strip().lower() for d in raw.split(",") if d.strip()]


def _domains_to_str(domains: list[str]) -> str:
    return ", ".join(domains)


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
            domains = _parse_domains(user_input[CONF_DOMAINS])
            if not domains:
                errors[CONF_DOMAINS] = "no_domains"
            else:
                self._data[CONF_DOMAINS] = domains
                self._data[CONF_UPDATE_INTERVAL] = user_input[CONF_UPDATE_INTERVAL]

                unique_id = self._data[CONF_ACCOUNT_NAME].lower().replace(" ", "_")
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=self._data[CONF_ACCOUNT_NAME],
                    data=self._data,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_DOMAINS): str,
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
            domains = _parse_domains(user_input[CONF_DOMAINS])
            if not domains:
                errors[CONF_DOMAINS] = "no_domains"
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

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_DOMAINS, default=_domains_to_str(current_domains)
                ): str,
                vol.Required(
                    CONF_UPDATE_INTERVAL, default=current_interval
                ): vol.All(int, vol.Range(min=30, max=3600)),
            }
        )
        return self.async_show_form(
            step_id="init", data_schema=schema, errors=errors
        )
