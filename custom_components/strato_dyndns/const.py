DOMAIN = "strato_dyndns"

CONF_ACCOUNT_NAME = "account_name"
CONF_DOMAINS = "domains"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_UPDATE_INTERVAL = 30  # seconds

# Individual domain input fields: one main domain + 10 subdomains
DOMAIN_FIELDS = ["domain_main"] + [f"domain_{i}" for i in range(1, 11)]

# Human-readable descriptions for Strato DynDNS response codes
STRATO_RESPONSE_DESCRIPTIONS: dict[str, str] = {
    "good": "Update erfolgreich — IP wurde aktualisiert",
    "nochg": "Keine Änderung — IP war bereits aktuell",
    "badauth": "Authentifizierung fehlgeschlagen — Benutzername/Passwort prüfen",
    "notfqdn": "Ungültiger Hostname — DynDNS im Strato-Kundenbereich nicht konfiguriert",
    "badsys": "Systemfehler — fehlerhafte URL-Syntax oder fehlende Parameter",
    "dnserr": "DNS-Fehler auf Serverseite",
    "abuse": "Blockiert — zu viele Anfragen ohne IP-Wechsel",
    "911": "Serverfehler — bitte später erneut versuchen",
}

STRATO_UPDATE_URL = "http://dyndns.strato.com/nic/update"

IP_PROVIDERS = [
    "https://api.ipify.org",
    "https://checkip.amazonaws.com",
    "https://ifconfig.me/ip",
]

# Strato response codes
STRATO_OK_CODES = ("good", "nochg")
