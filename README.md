# Strato DynDNS

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/LuckyTriple7/ha-strato-dyndns)](https://github.com/LuckyTriple7/ha-strato-dyndns/releases)

Home Assistant custom integration for Strato DynDNS. Monitors the public IPv4 address and automatically updates all configured domains and subdomains at Strato when the IP changes.

## Features

- Multiple Strato accounts configurable in parallel
- Public IP determined via redundant providers (ipify.org, AWS, ifconfig.me)
- Automatic DynDNS update when DNS-resolved IP differs from public IP
- Configurable polling interval (min. 30 seconds)
- Sensor for the resolved IP per domain (DNS lookup)
- Problem sensor per domain — active when DNS IP ≠ public IP
- Account status sensor with list of failed domains
- Last update timestamp sensor per domain
- "Update Now" button to force an immediate update
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
3. Step 2: Enter domains in the individual fields and set the polling interval

The first field is the main domain (e.g. `example.de`), followed by up to 10 subdomains (e.g. `home.example.de`). None of the fields are mandatory — use only what you need.

To configure multiple Strato accounts, simply add the integration again.

## Entities

Per configured account:

| Entity | Type | Description |
|--------|------|-------------|
| `sensor.<account>_public_ip` | Sensor | Currently detected public IP |
| `sensor.<domain>_resolved_ip` | Sensor | DNS-resolved IP of the domain |
| `sensor.<domain>_last_update` | Sensor | Timestamp of last successful update |
| `binary_sensor.<account>_error` | Problem sensor | `on` when any domain's last update failed (abuse, badauth, …) — attributes: `failed_domains`, `error_details` |
| `binary_sensor.<domain>_ip_mismatch` | Problem sensor | `on` when DNS IP ≠ public IP |
| `button.<account>_update_now` | Button | Force immediate update of all domains |

## Setting up Strato DynDNS

DynDNS must be enabled for each domain/subdomain in the Strato control panel:
**Domains → Manage domain → DynDNS**

The username for the DynDNS API is the full domain (e.g. `example.de`), the password is set separately.

---

## Deutsch

Home Assistant Custom Integration für Strato DynDNS. Überwacht die öffentliche IPv4-Adresse und aktualisiert automatisch alle konfigurierten Domains bei Strato, wenn sich die IP ändert.

### Features

- Mehrere Strato-Accounts parallel konfigurierbar
- Öffentliche IP wird über redundante Provider ermittelt (ipify.org, AWS, ifconfig.me)
- Automatisches DynDNS-Update wenn DNS-IP von der öffentlichen IP abweicht
- Konfigurierbares Prüfintervall (min. 30 Sekunden)
- Sensor für die aufgelöste IP je Domain (DNS-Lookup)
- Problem-Sensor je Domain — aktiv wenn DNS-IP ≠ öffentliche IP
- Account-Status-Sensor mit Liste der fehlgeschlagenen Domains
- Letzter-Update-Zeitstempel-Sensor je Domain
- „Update Now"-Button für sofortige Aktualisierung
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
3. Schritt 2: Domains in die einzelnen Felder eintragen und Prüfintervall festlegen

Das erste Feld ist die Haupt-Domain (z. B. `example.de`), danach bis zu 10 Subdomains (z. B. `home.example.de`). Kein Feld ist Pflicht — nur ausfüllen, was benötigt wird.

Für mehrere Strato-Accounts die Integration einfach erneut hinzufügen.

### Strato DynDNS einrichten

In der Strato-Verwaltung muss DynDNS für jede Domain/Subdomain aktiviert sein:
**Domains → Domain verwalten → DynDNS**

Der Benutzername für die DynDNS-API ist die vollständige Domain (z. B. `example.de`), das Passwort wird separat gesetzt.
