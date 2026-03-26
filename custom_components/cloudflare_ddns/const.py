"""Constants for Cloudflare DDNS."""

DOMAIN = "cloudflare_ddns"

# Config
CONF_RECORDS = "records"
CONF_ZONES = "zones"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_UPDATE_INTERVAL = 60  # in minutes
MIN_UPDATE_INTERVAL = 5       # in minutes — hard minimum
WARN_UPDATE_INTERVAL = 15     # in minutes — warn below this

# Services
SERVICE_UPDATE_RECORDS = "update_records"
