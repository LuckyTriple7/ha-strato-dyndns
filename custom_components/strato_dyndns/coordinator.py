from __future__ import annotations

import asyncio
import logging
import socket
from datetime import timedelta
from typing import Any

import aiohttp
import async_timeout

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, IP_PROVIDERS, STRATO_OK_CODES, STRATO_UPDATE_URL

_LOGGER = logging.getLogger(__name__)


async def async_get_public_ip(session: aiohttp.ClientSession) -> str | None:
    for url in IP_PROVIDERS:
        try:
            async with async_timeout.timeout(10):
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return (await resp.text()).strip()
        except Exception:
            continue
    return None


async def async_resolve_ip(domain: str) -> str | None:
    try:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, socket.gethostbyname, domain)
    except Exception:
        return None


class StratoDynDNSCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        account_name: str,
        username: str,
        password: str,
        domains: list[str],
        update_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{account_name}",
            update_interval=timedelta(minutes=update_interval),
        )
        self.account_name = account_name
        self.username = username
        self.password = password
        self.domains = domains
        self._last_ip: str | None = None
        self._session: aiohttp.ClientSession | None = None

    @property
    def _http(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _async_update_data(self) -> dict[str, Any]:
        public_ip = await async_get_public_ip(self._http)
        if not public_ip:
            raise UpdateFailed("Öffentliche IP konnte nicht ermittelt werden")

        ip_changed = public_ip != self._last_ip
        if ip_changed:
            _LOGGER.info(
                "[%s] IP geändert: %s → %s",
                self.account_name,
                self._last_ip,
                public_ip,
            )

        domain_data: dict[str, Any] = {}
        for domain in self.domains:
            resolved_ip = await async_resolve_ip(domain)
            update_status: str | None = None
            update_response: str | None = None

            if ip_changed:
                update_status, update_response = await self._update_domain(domain, public_ip)

            domain_data[domain] = {
                "resolved_ip": resolved_ip,
                "ip_mismatch": resolved_ip != public_ip if resolved_ip else True,
                "update_status": update_status,
                "update_response": update_response,
            }

        self._last_ip = public_ip
        return {"public_ip": public_ip, "domains": domain_data}

    async def _update_domain(self, domain: str, ip: str) -> tuple[str, str]:
        try:
            auth = aiohttp.BasicAuth(self.username, self.password)
            params = {"system": "dyndns", "hostname": domain, "myip": ip}
            async with async_timeout.timeout(30):
                async with self._http.get(
                    STRATO_UPDATE_URL, auth=auth, params=params
                ) as resp:
                    text = (await resp.text()).strip()
            status = "ok" if text.startswith(STRATO_OK_CODES) else "error"
            _LOGGER.debug("[%s] %s → %s (%s)", self.account_name, domain, status, text)
            return status, text
        except Exception as exc:
            _LOGGER.warning("[%s] Update von %s fehlgeschlagen: %s", self.account_name, domain, exc)
            return "error", str(exc)

    async def async_close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
