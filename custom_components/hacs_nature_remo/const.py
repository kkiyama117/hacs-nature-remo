# Should be equal to the name of your component.
from datetime import timedelta
from logging import Logger, getLogger

from homeassistant.components.climate.const import (
    HVAC_MODE_AUTO,
    HVAC_MODE_COOL,
    HVAC_MODE_DRY,
    HVAC_MODE_FAN_ONLY,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
)

PLATFORMS: any = {"sensor", "climate", "light", "switch"}
DOMAIN: str = "hacs_nature_remo"

LOGGER: Logger = getLogger(__package__)

DEFAULT_UPDATE_INTERVAL = timedelta(seconds=60)

KEY_API = "api"
KEY_CONFIG = "api"
KEY_COORDINATOR = "coordinator"
KEY_APPLIANCES = "appliances"
KEY_DEVICES = "devices"

# For climate
STR_POWER_OFF = "power-off"
MODE_HA_TO_REMO = {
    HVAC_MODE_AUTO: "auto",
    HVAC_MODE_FAN_ONLY: "blow",
    HVAC_MODE_COOL: "cool",
    HVAC_MODE_DRY: "dry",
    HVAC_MODE_HEAT: "warm",
    HVAC_MODE_OFF: STR_POWER_OFF,
}

MODE_REMO_TO_HA = {
    "auto": HVAC_MODE_AUTO,
    "blow": HVAC_MODE_FAN_ONLY,
    "cool": HVAC_MODE_COOL,
    "dry": HVAC_MODE_DRY,
    "warm": HVAC_MODE_HEAT,
    STR_POWER_OFF: HVAC_MODE_OFF,
}

AIRCON_MODES_REMO = MODE_REMO_TO_HA.keys()
