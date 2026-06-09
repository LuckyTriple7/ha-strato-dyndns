# Changelog

All notable changes to this project will be documented in this file.

## [0.1.3] - 2026-06-09
### Added
- Optional IPv6 support (enable per account in config/options)
- Public IPv6 sensor (`sensor.strato_dyndns_public_ipv6`) — network-wide, no account prefix
- Public IPv4 sensor renamed to `…_public_ipv4` with `provider` attribute (breaking rename)
- Resolved IPv6 sensor per domain (AAAA DNS lookup via 1.1.1.1/8.8.8.8)
- IPv6 mismatch binary sensor per domain
- Update trigger: OR logic — update when IPv4 OR IPv6 DNS doesn't match public IP
- Strato update sends `myip=<ipv4>,<ipv6>` when IPv6 is active

## [0.1.2] - 2026-06-09
### Added
- Error backoff per domain: after a failed update, retries are paused to avoid making errors worse
  - `abuse` → 15 min, `badauth` / `notfqdn` → 30 min, `dnserr` / `badsys` / `911` → 5 min, other errors → 2 min
- Error sensor stays `ON` during backoff (last known error result is preserved)
- `retry_after` attribute on the resolved-IP sensor when a domain is in backoff
- "Update Now" button bypasses backoff and forces an immediate retry

## [0.1.1] - 2026-06-09
### Changed
- Entity naming cleaned up (breaking change — delete and re-add the integration)
- Removed redundant "Strato" prefix from all entity names
- Domain sensors now include account name and "Domain" separator for clarity
- Examples: `server_de_domain_bookstack_server_de_resolved_ip`, `server_de_error`

## [0.1.0] - 2026-06-09
### Changed
- Minimum polling interval lowered from 30 to 10 seconds
- Safe because Strato is only called when DNS-resolved IP ≠ public IP, not on every poll

## [0.0.9] - 2026-06-09
### Changed
- Replaced account status text sensor (`ok`/`error`) with a binary problem sensor
- Binary sensor is `ON` when any domain's last update returned an error (including `abuse`, `badauth`, `dnserr`)
- Attributes: `failed_domains` (list) and `error_details` (domain → Strato response code)

## [0.0.8] - 2026-06-09
### Changed
- DNS resolution now uses Cloudflare (`1.1.1.1`) and Google (`8.8.8.8`) instead of the system resolver
- Avoids stale cached results from the local router after a DynDNS update
### Added
- `dnspython==2.7.0` as dependency (installed automatically by HA)

## [0.0.7] - 2026-06-09
### Changed
- Update trigger is now per-domain: Strato is only called when the domain's DNS-resolved IP differs from the public IP
- Avoids unnecessary `nochg` calls that can trigger an `abuse` block from Strato
- "Update Now" button uses a dedicated force flag instead of clearing the last known IP
- All log messages switched to English

## [0.0.6] - 2026-06-09
### Added
- Account status sensor showing `ok`/`error` with failed domains as attribute
- Last update timestamp sensor per domain (respects `good` and `nochg` as success)
- "Update Now" button to force immediate update of all domains
- Error logging in HA log on failed updates, debug logging for update flow
### Fixed
- Domain fields no longer shift positions when reopening the options dialog (breaking change: VERSION 2)
- Icon now correctly placed in `brand/` subdirectory (HA 2026.3+ requirement)

## [0.0.5] - 2026-06-08
### Changed
- Domain input replaced with individual fields: one main domain + up to 10 subdomains
- No field is mandatory — use only what you need
- Breaking change: existing entries must be reconfigured

## [0.0.4] - 2026-06-08
### Fixed
- Options Flow Error 500 (`AttributeError` on `config_entry` property in HA 2024+)
- Polling interval unit changed from minutes to seconds (minimum 30 seconds)

## [0.0.3] - 2026-06-08
### Added
- German and English translations for config flow UI

## [0.0.2] - 2026-06-08
### Added
- HACS compatibility (`hacs.json`)
- Integration icon (`brand/icon.png`)
- README with installation and configuration docs

## [0.0.1] - 2026-06-07
### Added
- Initial release
- Config Flow (no YAML required)
- Public IP detection with fallback providers (ipify.org, AWS, ifconfig.me)
- Automatic DynDNS update at Strato when IP changes
- Sensor: public IP, resolved IP per domain, IP mismatch problem sensor per domain
- Support for multiple Strato accounts
