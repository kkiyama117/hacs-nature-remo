"""Support for Nature Remo AC."""
import logging
from typing import Dict

from homeassistant.components.climate import ClimateEntity
from homeassistant.components.climate.const import (
    SUPPORT_FAN_MODE,
    SUPPORT_SWING_MODE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS
from homeassistant.core import callback
from homeassistant.helpers import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from remo.models import AirConParams, AirConRangeMode, Appliance, Device

from custom_components.hacs_nature_remo import NatureRemoAPIVer1, NatureRemoBase
from custom_components.hacs_nature_remo.climate.helper import (
    _check_mode_is_off,
    _mode_ha_to_remo,
    _mode_remo_to_ha,
)
from custom_components.hacs_nature_remo.const import *
from custom_components.hacs_nature_remo.utils import find_by

_LOGGER = logging.getLogger(__name__)

SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE
PREVIOUS_TARGET_TEMP_KEY = "previous_target_temperature"


async def async_setup_platform(hass, config: ConfigType, async_add_entities, discovery_info=None):
    """Set up the Nature Remo AC."""
    if discovery_info is None:
        return
    _LOGGER.debug("Setting up climate platform.")
    _data = hass.data.get(DOMAIN)
    coordinator = _data.get(KEY_COORDINATOR)
    appliances = coordinator.data.get(KEY_APPLIANCES)
    api = _data.get(KEY_API)
    config = _data.get(KEY_CONFIG)
    async_add_entities(
        [
            NatureRemoAC(coordinator, api, appliance, config)
            for appliance in appliances
            if appliance.type == "AC"
        ]
    )


class NatureRemoAC(NatureRemoBase, ClimateEntity):
    """Implementation of a Nature Remo E sensor."""

    def __init__(self, coordinator: DataUpdateCoordinator, api: NatureRemoAPIVer1, appliance: Appliance, config):
        super().__init__(coordinator, appliance)
        self._api = api
        self.__modes: Dict[str, AirConRangeMode] = appliance.aircon.range.modes
        self.__current_mode: str = ""

        # Update static data
        self._attr_supported_features = SUPPORT_FLAGS
        self._attr_temperature_unit = TEMP_CELSIUS
        for v in AIRCON_MODES_REMO:
            self._set_last_target_temp(v, None)
        self._set_hvac_modes()

        self._update(appliance.settings)

    def _update(self, ac_settings: AirConParams, device: Device = None):
        # hold this to determine the ac mode while it's turned-off
        _remo_mode_key = ac_settings.mode
        _remo_mode_value = self.__modes.get(_remo_mode_key)

        if ac_settings.mode:
            self.__current_mode = ac_settings.mode
        else:
            self.__current_mode = "power-off"

        self._set_target_temperature_step()

        # Update target temperature
        try:
            self._attr_target_temperature = float(ac_settings.temp)
            self._set_last_target_temp(_remo_mode_key, self._attr_target_temperature)
        except ValueError:
            self._attr_target_temperature = None

        # Update hvac mode
        if _check_mode_is_off(ac_settings.button):
            self._attr_hvac_mode = HVAC_MODE_OFF
        else:
            self._attr_hvac_mode = _mode_remo_to_ha(self.__current_mode)

        # Update current fan and swing
        self._attr_fan_mode = ac_settings.vol or None
        self._attr_swing_mode = ac_settings.dir or None

        # Update fan and swing modes
        self._attr_fan_modes = _remo_mode_value.vol
        self._attr_swing_modes = _remo_mode_value.dir

        # Update temp lange
        temp_range_list = _get_temp_range_list(self.__modes, self.__current_mode)
        if len(temp_range_list) == 0:
            self._attr_min_temp = 0
            self._attr_max_temp = 0
        else:
            self._attr_min_temp = min(temp_range_list)
            self._attr_max_temp = max(temp_range_list)

        # Update current temperature
        if device is not None:
            self._attr_current_temperature = float(device.newest_events.get("te").val)

    async def async_set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            return
        if target_temp.is_integer():
            # has to cast to whole number otherwise API will return an error
            target_temp = int(target_temp)
        _LOGGER.debug("Set temperature: %d", target_temp)
        await self._post({"temperature": f"{target_temp}"})

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        _LOGGER.debug("Set hvac mode: %s", hvac_mode)
        mode = _mode_ha_to_remo(hvac_mode)
        if _check_mode_is_off(mode):
            await self._post({"button": mode})
        else:
            data = {"operation_mode": mode}
            _last_target_temp = self._get_last_target_temp(mode)
            if _last_target_temp is not None:
                if _last_target_temp.is_integer():
                    # has to cast to whole number otherwise API will return an error
                    _last_target_temp = int(_last_target_temp)
                data.setdefault("temperature", _last_target_temp)
            await self._post(data)

    async def async_set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        _LOGGER.debug("Set fan mode: %s", fan_mode)
        await self._post({"air_volume": fan_mode})

    async def async_set_swing_mode(self, swing_mode):
        """Set new target swing operation."""
        _LOGGER.debug("Set swing mode: %s", swing_mode)
        await self._post({"air_direction": swing_mode})

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self._update_callback)
        )

    async def async_update(self):
        """Update the entity.
        Only used by the generic entity update service.
        """
        await self._coordinator.async_request_refresh()

    @callback
    def _update_callback(self):
        self._update(
            find_by(self._coordinator.data.get("appliances"), "id", self._appliance_id).settings,
            find_by(self._coordinator.data.get("devices"), "id", self._device.id),
        )
        self.async_write_ha_state()

    async def _post(self, data):
        await self._api.update_aircon_settings(self._appliance_id, **data)
        await self._coordinator.async_request_refresh()
        self.async_write_ha_state()

    def _set_target_temperature_step(self):
        temp_range = _get_temp_range_list(self.__modes, self.__current_mode)
        if len(temp_range) >= 2:
            # determine step from the gap of first and second temperature
            step = round(temp_range[1] - temp_range[0], 1)
            if step in [1.0, 0.5]:  # valid steps
                self._attr_target_temperature_step = step
                return step
        self._attr_target_temperature_step = 1
        return 1

    def _set_hvac_modes(self):
        remo_modes = list(self.__modes.keys())
        ha_modes = list(map(_mode_remo_to_ha, remo_modes))
        ha_modes.append(HVAC_MODE_OFF)
        self._attr_hvac_modes = ha_modes

    def _set_last_target_temp(self, mode: str, value):
        if not hasattr(self, "_attr_extra_state_attributes"):
            self._attr_extra_state_attributes = {}
        if mode in AIRCON_MODES_REMO:
            self._attr_extra_state_attributes.setdefault(PREVIOUS_TARGET_TEMP_KEY, {})
            self._attr_extra_state_attributes[PREVIOUS_TARGET_TEMP_KEY][mode] = value
        else:
            pass

    def _get_last_target_temp(self, mode):
        _last_targets = self._attr_extra_state_attributes.get(PREVIOUS_TARGET_TEMP_KEY)
        _LOGGER.debug(_last_targets)
        if _last_targets is not None and _last_targets.get(mode):
            return _last_targets.get(mode)
        return None


def _get_temp_range_list(modes, mode: str):
    if mode in modes:
        temp_range = modes.get(mode).temp
        return list(map(float, filter(None, temp_range)))
    else:
        return []
