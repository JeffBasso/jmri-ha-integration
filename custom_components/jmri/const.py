"""Constants for the JMRI integration."""

DOMAIN = "jmri"
DEFAULT_HOST = "homeassistant"
DEFAULT_PORT = 12080
DEFAULT_NAME = "JMRI Railroad"

# JMRI REST API endpoints
API_ROSTER = "/json/roster"
API_TURNOUTS = "/json/turnouts"
API_SENSORS = "/json/sensors"
API_LIGHTS = "/json/lights"
API_SIGNALS = "/json/signalMasts"
API_POWER = "/json/power"
API_THROTTLES = "/json/throttles"

# JMRI WebSocket endpoint
WS_ENDPOINT = "/json/"

# JMRI state values
STATE_ACTIVE = 2
STATE_INACTIVE = 4
STATE_THROWN = 4
STATE_CLOSED = 2
STATE_ON = 2
STATE_OFF = 4

# HA entity platforms
PLATFORMS = [
    "binary_sensor",
    "switch",
    "media_player",
    "sensor",
]

# Update interval for polling fallback
SCAN_INTERVAL = 2
