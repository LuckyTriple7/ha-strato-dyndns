DOMAIN = "strato_dyndns"

CONF_ACCOUNT_NAME = "account_name"
CONF_DOMAINS = "domains"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_UPDATE_INTERVAL = 30  # seconds

# Individual domain input fields: one main domain + 10 subdomains
DOMAIN_FIELDS = ["domain_main"] + [f"domain_{i}" for i in range(1, 11)]

STRATO_UPDATE_URL = "http://dyndns.strato.com/nic/update"

IP_PROVIDERS = [
    "https://api.ipify.org",
    "https://checkip.amazonaws.com",
    "https://ifconfig.me/ip",
]

# Strato response codes
STRATO_OK_CODES = ("good", "nochg")
