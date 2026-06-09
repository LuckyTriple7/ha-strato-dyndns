from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
import async_timeout
import dns.resolver

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, IP_PROVIDERS, IPv6_PROVIDERS, STRATO_OK_CODES, STRATO_UPDATE_URL

_LOGGER = logging.getLogger(__name__)

# Backoff durations per Strato error code (seconds)
_ERROR_BACKOFF: dict[str, int] = {
    "abuse":   900,   # 15 min
    "badauth": 1800,  # 30 min
    "notfqdn": 1800,  # 30 min
    "badsys":  300,   # 5 min
    "dnserr":  300,   # 5 min
    "911":     300,   # 5 min
}
_DEFAULT_BACKOFF = 120  # 2 min


async def async_get_public_ip(session: aiohttp.ClientSession) -> tuple[str, str] | None:
    """Return (ipv4, provider_url) or None if all providers fail."""
    for url in IP_PROVIDERS:
        try:
            async with async_timeout.timeout(10):
                async with session.get(url) as resp:
                    if resp.status == 200:
                        return (await resp.text()).strip(), url
        except Exception:
            continue
    return None


async def async_get_public_ipv6(session: aiohttp.ClientSession) -> tuple[str, str] | None:
    """Return (ipv6, provider_url) or None if all providers fail or no IPv6 connectivity."""
    for url in IPv6_PROVIDERS:
        try:
            async with async_timeout.timeout(10):
                async with session.get(url) as resp:
                    if resp.status == 200:
                        text = (await resp.text()).strip()
                        if ":" in text:  # basic IPv6 sanity check
                            return text, url
        except Exception:
            continue
    return None


_DNS_RESOLVER = dns.resolver.Resolver(configure=False)
_DNS_RESOLVER.nameservers = ["1.1.1.1", "8.8.8.8"]
_DNS_RESOLVER.lifetime = 5.0


def _resolve_sync(domain: str) -> str | None:
    try:
        return str(_DNS_RESOLVER.resolve(domain, "A")[0])
    except Exception:
        return None


def _resolve_ipv6_sync(domain: str) -> str | None:
    try:
        return str(_DNS_RESOLVER.resolve(domain, "AAAA")[0])
    except Exception:
        return None


async def async_resolve_ip(domain: str) -> str | None:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _resolve_sync, domain)


async def async_resolve_ipv6(domain: str) -> str | None:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _resolve_ipv6_sync, domain)


class StratoDynDNSCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(
        self,
        hass: HomeAssistant,
        account_name: str,
        username: str,
        password: str,
        domains: list[str],
        update_interval: int,
        ipv6_enabled: bool = False,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{account_name}",
            update_interval=timedelta(seconds=update_interval),
        )
        self.account_name = account_name
        self.username = username
        self.password = password
        self.domains = domains
        self.ipv6_enabled = ipv6_enabled
        self._last_ip: str | None = None
        self._last_update_times: dict[str, datetime] = {}
        self._last_update_results: dict[str, tuple[str | None, str | None]] = {}
        self._error_backoff: dict[str, datetime] = {}
        self._force_update: bool = False
        self._session: aiohttp.ClientSession | None = None

    @property
    def _http(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _async_update_data(self) -> dict[str, Any]:
        result = await async_get_public_ip(self._http)
        if not result:
            raise UpdateFailed("Could not determine public IP address")
        public_ip, public_ip_provider = result

        if public_ip != self._last_ip and self._last_ip is not None:
            _LOGGER.info("[%s] Public IP changed: %s -> %s", self.account_name, self._last_ip, public_ip)
        else:
            _LOGGER.debug("[%s] Public IP: %s (via %s)", self.account_name, public_ip, public_ip_provider)

        public_ip6: str | None = None
        public_ip6_provider: str | None = None
        if self.ipv6_enabled:
            result6 = await async_get_public_ipv6(self._http)
            if result6:
                public_ip6, public_ip6_provider = result6
                _LOGGER.debug("[%s] Public IPv6: %s (via %s)", self.account_name, public_ip6, public_ip6_provider)
            else:
                _LOGGER.debug("[%s] No public IPv6 detected", self.account_name)

        force = self._force_update
        self._force_update = False
        now = datetime.now(timezone.utc)

        domain_data: dict[str, Any] = {}
        for domain in self.domains:
            resolved_ip = await async_resolve_ip(domain)
            resolved_ip6: str | None = None
            if self.ipv6_enabled:
                resolved_ip6 = await async_resolve_ipv6(domain)
            _LOGGER.debug(
                "[%s] DNS resolved %s -> A=%s AAAA=%s",
                self.account_name, domain, resolved_ip, resolved_ip6,
            )

            ipv4_mismatch = resolved_ip is None or resolved_ip != public_ip
            ipv6_mismatch = (
                self.ipv6_enabled
                and public_ip6 is not None
                and (resolved_ip6 is None or resolved_ip6 != public_ip6)
            )
            needs_update = force or ipv4_mismatch or ipv6_mismatch

            backoff_until = self._error_backoff.get(domain)
            in_backoff = not force and backoff_until is not None and now < backoff_until

            update_status: str | None
            update_response: str | None

            if needs_update and in_backoff:
                remaining = int((backoff_until - now).total_seconds())
                _LOGGER.debug(
                    "[%s] %s in error backoff, retry in %ds",
                    self.account_name, domain, remaining,
                )
                update_status, update_response = self._last_update_results.get(domain, (None, None))

            elif needs_update:
                reason = "forced" if force else f"A={resolved_ip} AAAA={resolved_ip6}"
                _LOGGER.debug(
                    "[%s] Updating %s (public=%s/%s, %s)",
                    self.account_name, domain, public_ip, public_ip6, reason,
                )
                ip6_to_send = public_ip6 if self.ipv6_enabled and public_ip6 else None
                update_status, update_response = await self._update_domain(domain, public_ip, ip6_to_send)
                self._last_update_results[domain] = (update_status, update_response)

                if update_status == "ok":
                    self._error_backoff.pop(domain, None)
                    self._last_update_times[domain] = now
                else:
                    code = (update_response or "").split()[0]
                    backoff_secs = _ERROR_BACKOFF.get(code, _DEFAULT_BACKOFF)
                    self._error_backoff[domain] = now + timedelta(seconds=backoff_secs)
                    _LOGGER.warning(
                        "[%s] %s failed (%s), next retry in %ds",
                        self.account_name, domain, update_response, backoff_secs,
                    )

            else:
                self._error_backoff.pop(domain, None)
                self._last_update_results.pop(domain, None)
                update_status, update_response = None, None
                _LOGGER.debug("[%s] %s DNS up to date — skipping", self.account_name, domain)

            domain_data[domain] = {
                "resolved_ip": resolved_ip,
                "resolved_ip6": resolved_ip6,
                "ip_mismatch": ipv4_mismatch,
                "ip6_mismatch": ipv6_mismatch if self.ipv6_enabled else None,
                "update_status": update_status,
                "update_response": update_response,
                "last_update_time": self._last_update_times.get(domain),
                "backoff_until": self._error_backoff.get(domain),
            }

        self._last_ip = public_ip
        return {
            "public_ip": public_ip,
            "public_ip_provider": public_ip_provider,
            "public_ip6": public_ip6,
            "public_ip6_provider": public_ip6_provider,
            "domains": domain_data,
        }

    async def _update_domain(self, domain: str, ip: str, ip6: str | None = None) -> tuple[str, str]:
        try:
            auth = aiohttp.BasicAuth(self.username, self.password)
            myip = f"{ip},{ip6}" if ip6 else ip
            params = {"system": "dyndns", "hostname": domain, "myip": myip}
            async with async_timeout.timeout(30):
                async with self._http.get(
                    STRATO_UPDATE_URL, auth=auth, params=params
                ) as resp:
                    text = (await resp.text()).strip()
            code = text.split()[0] if text else ""
            status = "ok" if code in STRATO_OK_CODES else "error"
            if status == "ok":
                _LOGGER.debug("[%s] %s update OK: %s", self.account_name, domain, text)
            else:
                _LOGGER.error("[%s] DynDNS update failed for %s: %s", self.account_name, domain, text)
            return status, text
        except Exception as exc:
            _LOGGER.error("[%s] DynDNS update failed for %s: %s", self.account_name, domain, exc)
            return "error", str(exc)

    async def async_force_update(self) -> None:
        """Force update all domains, bypassing backoff."""
        _LOGGER.debug("[%s] Manual update requested", self.account_name)
        self._force_update = True
        await self.async_request_refresh()

    async def async_close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
