# Strato DynDNS

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/LuckyTriple7/ha-strato-dyndns)](https://github.com/LuckyTriple7/ha-strato-dyndns/releases)

Home Assistant custom integration for Strato DynDNS. Monitors your public IPv4 (and optionally IPv6) address and automatically updates all configured domains at Strato when the IP changes.

## Features

- Multiple Strato accounts configurable in parallel
- Public IP determined via redundant providers (ipify.org, AWS, ident.me) with automatic fallback
- Optional IPv6 support (AAAA records, separate public IPv6 detection)
- Smart update trigger — Strato is only called when necessary (see [Update Logic](#update-logic))
- Error backoff per domain to prevent `abuse` blocks from Strato
- Configurable polling interval (min. 10 seconds)
- Optional persistent notifications for IP mismatches and update errors
- Fully configured through the HA UI, no YAML required
- Supports main domain + up to 10 subdomains per account

## Installation via HACS

1. Open HACS → **Integrations** → Menu (⋮) → **Custom repositories**
2. Enter URL: `https://github.com/LuckyTriple7/ha-strato-dyndns`
3. Category: **Integration** → **Add**
4. Search for **Strato DynDNS** → **Download**
5. Restart Home Assistant

## Configuration

1. **Settings → Devices & Services → Add Integration → Strato DynDNS**
2. Step 1: Enter account name, username and password
3. Step 2: Enter domains, set the polling interval and optional features

The first field is the main domain (e.g. `example.de`), followed by up to 10 subdomains (e.g. `home.example.de`). None of the fields are mandatory — use only what you need.

To configure multiple Strato accounts, simply add the integration again.

## Entities

Per configured account:

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.<account>_public_ipv4` | Sensor | Currently detected public IPv4 address |
| `sensor.strato_dyndns_public_ipv6` | Sensor | Currently detected public IPv6 address (when IPv6 enabled) |
| `sensor.<account>_domain_<domain>_resolved_ip` | Sensor | DNS-resolved IPv4 of the domain (via 1.1.1.1 / 8.8.8.8) |
| `sensor.<account>_domain_<domain>_resolved_ipv6` | Sensor | DNS-resolved IPv6 of the domain (when IPv6 enabled) |
| `sensor.<account>_domain_<domain>_last_update` | Sensor | Timestamp of last successful Strato update |
| `binary_sensor.<account>_error` | Problem sensor | `on` when any domain's DNS-resolved IP differs from the public IP |
| `binary_sensor.<account>_domain_<domain>_ip_mismatch` | Problem sensor | `on` when DNS IPv4 ≠ public IPv4 |
| `binary_sensor.<account>_domain_<domain>_ipv6_mismatch` | Problem sensor | `on` when DNS IPv6 ≠ public IPv6 (when IPv6 enabled) |
| `button.<account>_update_now` | Button | Force immediate update of all domains, bypassing backoff |

## Update Logic

The integration uses a two-stage trigger to avoid unnecessary Strato API calls:

**On HA start / after restart** — no prior state is available, so the DNS-resolved IP is compared with the public IP:
- DNS IP = public IP → no update (IP hasn't changed)
- DNS IP ≠ public IP → update sent to Strato

**During a running session** — after a successful update, the sent IP is remembered per domain:
- Public IP unchanged since last send → no update, even if DNS is still propagating the previous change
- Public IP changed → update sent to Strato

This prevents duplicate API calls during DNS propagation delay (which can take several minutes) while still reacting immediately to any IP change.

Additionally, a per-domain **error backoff** prevents rapid retries after a Strato error (`abuse` → 15 min, `badauth` / `notfqdn` → 30 min, `dnserr` / `badsys` / `911` → 5 min, other → 2 min). The "Update Now" button bypasses the backoff for an immediate retry.

## Setting up Strato DynDNS

DynDNS must be enabled for each domain/subdomain in the Strato control panel:
**Domains → Manage domain → DynDNS**

The username for the DynDNS API is the full domain (e.g. `example.de`), the password is set separately in Strato.

---

## Deutsch

Home Assistant Custom Integration für Strato DynDNS. Überwacht die öffentliche IPv4-Adresse (und optional IPv6) und aktualisiert automatisch alle konfigurierten Domains bei Strato, wenn sich die IP ändert.

### Features

- Mehrere Strato-Accounts parallel konfigurierbar
- Öffentliche IP über redundante Provider ermittelt (ipify.org, AWS, ident.me) mit automatischem Fallback
- Optionale IPv6-Unterstützung (AAAA-Records, separate IPv6-Erkennung)
- Intelligente Update-Logik — Strato wird nur bei Bedarf kontaktiert (siehe [Update-Logik](#update-logik))
- Error-Backoff je Domain verhindert `abuse`-Sperren bei Strato
- Konfigurierbares Prüfintervall (min. 10 Sekunden)
- Optionale persistente Benachrichtigungen bei IP-Abweichungen und Update-Fehlern
- Konfiguration komplett über die HA-Oberfläche, kein YAML nötig
- Unterstützung für Haupt-Domain + bis zu 10 Subdomains pro Account

### Installation via HACS

1. HACS öffnen → **Integrationen** → Menü (⋮) → **Benutzerdefinierte Repositories**
2. URL eingeben: `https://github.com/LuckyTriple7/ha-strato-dyndns`
3. Kategorie: **Integration** → **Hinzufügen**
4. Integration suchen: **Strato DynDNS** → **Herunterladen**
5. Home Assistant neu starten

### Konfiguration

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Strato DynDNS**
2. Schritt 1: Account-Name, Benutzername und Passwort eingeben
3. Schritt 2: Domains eintragen, Prüfintervall und optionale Funktionen festlegen

Das erste Feld ist die Haupt-Domain (z. B. `example.de`), danach bis zu 10 Subdomains (z. B. `home.example.de`). Kein Feld ist Pflicht — nur ausfüllen, was benötigt wird.

Für mehrere Strato-Accounts die Integration einfach erneut hinzufügen.

### Entitäten

Pro konfiguriertem Account:

| Entität | Typ | Beschreibung |
|---------|-----|--------------|
| `sensor.<account>_public_ipv4` | Sensor | Aktuell erkannte öffentliche IPv4-Adresse |
| `sensor.strato_dyndns_public_ipv6` | Sensor | Aktuell erkannte öffentliche IPv6-Adresse (wenn IPv6 aktiv) |
| `sensor.<account>_domain_<domain>_resolved_ip` | Sensor | Per DNS aufgelöste IPv4 der Domain (via 1.1.1.1 / 8.8.8.8) |
| `sensor.<account>_domain_<domain>_resolved_ipv6` | Sensor | Per DNS aufgelöste IPv6 der Domain (wenn IPv6 aktiv) |
| `sensor.<account>_domain_<domain>_last_update` | Sensor | Zeitstempel des letzten erfolgreichen Strato-Updates |
| `binary_sensor.<account>_error` | Problem-Sensor | `an` wenn bei einer Domain DNS-IP ≠ öffentliche IP |
| `binary_sensor.<account>_domain_<domain>_ip_mismatch` | Problem-Sensor | `an` wenn DNS-IPv4 ≠ öffentliche IPv4 |
| `binary_sensor.<account>_domain_<domain>_ipv6_mismatch` | Problem-Sensor | `an` wenn DNS-IPv6 ≠ öffentliche IPv6 (wenn IPv6 aktiv) |
| `button.<account>_update_now` | Button | Sofortige Aktualisierung aller Domains, Backoff wird ignoriert |

### Update-Logik

Die Integration verwendet eine zweistufige Trigger-Logik, um unnötige Strato-API-Calls zu vermeiden:

**Beim HA-Start / nach Neustart** — kein Zustand vorhanden, daher wird die DNS-aufgelöste IP mit der öffentlichen IP verglichen:
- DNS-IP = öffentliche IP → kein Update (IP hat sich nicht geändert)
- DNS-IP ≠ öffentliche IP → Update wird an Strato gesendet

**Im laufenden Betrieb** — nach einem erfolgreichen Update wird die gesendete IP pro Domain gespeichert:
- Öffentliche IP unverändert seit letztem Senden → kein Update, auch wenn DNS noch die alte IP zeigt (Propagierungs-Verzögerung)
- Öffentliche IP hat sich geändert → Update wird an Strato gesendet

Damit werden doppelte API-Calls während der DNS-Propagierung (die einige Minuten dauern kann) vermieden, während gleichzeitig sofort auf IP-Änderungen reagiert wird.

Zusätzlich verhindert ein **Error-Backoff** pro Domain schnelle Wiederholungen nach einem Strato-Fehler (`abuse` → 15 Min., `badauth` / `notfqdn` → 30 Min., `dnserr` / `badsys` / `911` → 5 Min., sonstige → 2 Min.). Der „Update Now"-Button umgeht den Backoff für eine sofortige Wiederholung.

### Strato DynDNS einrichten

In der Strato-Verwaltung muss DynDNS für jede Domain/Subdomain aktiviert sein:
**Domains → Domain verwalten → DynDNS**

Der Benutzername für die DynDNS-API ist die vollständige Domain (z. B. `example.de`), das Passwort wird separat in Strato gesetzt.
