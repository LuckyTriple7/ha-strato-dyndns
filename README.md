# Strato DynDNS

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Version](https://img.shields.io/github/v/release/LuckyTriple7/ha-strato-dyndns)](https://github.com/LuckyTriple7/ha-strato-dyndns/releases)

Home Assistant Custom Integration für Strato DynDNS. Überwacht die öffentliche IPv4-Adresse und aktualisiert automatisch alle konfigurierten Domains und Subdomains bei Strato, wenn sich die IP ändert.

## Features

- Mehrere Strato-Accounts parallel konfigurierbar
- Öffentliche IP wird über redundante Provider ermittelt (ipify.org, AWS, ifconfig.me)
- Automatisches DynDNS-Update bei IP-Änderung
- Konfigurierbares Prüfintervall (1–60 Minuten)
- Sensor für die aufgelöste IP je Domain (DNS-Lookup)
- Problem-Sensor je Domain — aktiv wenn DNS-IP ≠ öffentliche IP
- Konfiguration komplett über die HA-Oberfläche, kein YAML nötig
- Unterstützung für Haupt-Domain + bis zu 10 Subdomains pro Account

## Installation via HACS

1. HACS öffnen → **Integrationen** → Menü (⋮) → **Benutzerdefinierte Repositories**
2. URL eingeben: `https://github.com/LuckyTriple7/ha-strato-dyndns`
3. Kategorie: **Integration** → **Hinzufügen**
4. Integration suchen: **Strato DynDNS** → **Herunterladen**
5. Home Assistant neu starten

## Konfiguration

1. **Einstellungen → Geräte & Dienste → Integration hinzufügen → Strato DynDNS**
2. Schritt 1: Account-Name, Benutzername und Passwort eingeben
3. Schritt 2: Domains kommagetrennt eingeben und Prüfintervall festlegen

Beispiel Domains: `home.example.de, vpn.example.de, example.de`

Für mehrere Strato-Accounts die Integration einfach erneut hinzufügen.

## Entities

Pro konfiguriertem Account:

| Entity | Typ | Beschreibung |
|--------|-----|--------------|
| `sensor.<account>_public_ip` | Sensor | Aktuell ermittelte öffentliche IP |
| `sensor.<domain>_resolved_ip` | Sensor | Per DNS aufgelöste IP der Domain |
| `binary_sensor.<domain>_ip_mismatch` | Problem-Sensor | `on` wenn DNS-IP ≠ öffentliche IP |

## Strato DynDNS einrichten

In der Strato-Verwaltung muss DynDNS für jede Domain/Subdomain aktiviert sein:
**Domains → Domain verwalten → DynDNS**

Der Benutzername für die DynDNS-API ist die vollständige Domain (z. B. `example.de`), das Passwort wird separat gesetzt.
