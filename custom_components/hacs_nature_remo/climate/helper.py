from homeassistant.components.climate import HVAC_MODE_OFF

from custom_components.hacs_nature_remo import (
    MODE_HA_TO_REMO,
    MODE_REMO_TO_HA,
    STR_POWER_OFF,
)


def _mode_ha_to_remo(name: str) -> str:
    return MODE_HA_TO_REMO.get(name, None)


def _mode_remo_to_ha(mode: str) -> str:
    return MODE_REMO_TO_HA.get(mode, None)


def _check_mode_is_off(mode: str) -> bool:
    return mode == STR_POWER_OFF
