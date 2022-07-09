"""Support for Nature Remo Light."""
from enum import Enum
import logging
from typing import List

from homeassistant.components.light import LightEntity
from homeassistant.helpers import ConfigType, config_validation as cv, entity_platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from remo import Appliance, Signal
import voluptuous as vol

from . import DOMAIN, NatureRemoAPIVer1, NatureRemoBase
from .const import *
from .utils import find_by

_LOGGER = logging.getLogger(__name__)

SERVICE_PRESS_LIGHT_BUTTON = "press_light_button"
SERVICE_PRESS_CUSTOM_BUTTON = "press_custom_button"

ATTR_IS_NIGHT = "is_night"


class LightButton(Enum):
    on = "on"
    max = "on-100"
    favorite = "on-favorite"
    on_off = "onoff"
    night = "night"
    bright_up = "bright-up"
    bright_down = "bright-down"
    color_temp_up = "colortemp-up"
    color_temp_down = "colortemp-down"


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Nature Remo Light."""
    if discovery_info is None:
        return
    _LOGGER.debug("Setting up light platform.")
    _data = hass.data.get(DOMAIN)
    coordinator = hass.data.get(KEY_COORDINATOR)
    appliances: List[Appliance] = coordinator.data.get(KEY_APPLIANCES)
    api = _data.get(KEY_API)
    config = _data.get(KEY_CONFIG)
    async_add_entities(
        [
            NatureRemoLight(coordinator, api, appliance, config)
            for appliance in appliances
            if appliance.type == "LIGHT"
        ]
    )
    platform = entity_platform.current_platform.get()
    _LOGGER.debug("Registering light entity services.")
    platform.async_register_entity_service(
        SERVICE_PRESS_LIGHT_BUTTON,
        {vol.Required("button_name"): cv.enum(LightButton)},
        NatureRemoLight.async_press_light_button,
    )
    platform.async_register_entity_service(
        SERVICE_PRESS_CUSTOM_BUTTON,
        {vol.Required("button_name"): cv.string},
        NatureRemoLight.async_press_custom_button,
    )


class NatureRemoLight(NatureRemoBase, LightEntity):
    """Implementation of a Nature Remo Light component."""

    def __init__(self, coordinator: DataUpdateCoordinator, api: NatureRemoAPIVer1, appliance: Appliance,
                 config: ConfigType):
        super().__init__(coordinator, appliance)
        self._api = api
        self._buttons = appliance.light.buttons
        self._signals = appliance.signals
        self._is_night = False
        # self._buttons = [b["name"] for b in appliance["light"]["buttons"]]
        # self._signals = {s["name"]: s["id"] for s in appliance["signals"]}
        self._attr_is_on = False
        self._attr_supported_features = 0
        self._attr_extra_state_attributes = {ATTR_IS_NIGHT: self._is_night}
        self._attr_assumed_state = True

    def _update(self, is_on: bool, is_night: bool = False):
        self._is_night = is_night
        if is_on:
            self._attr_is_on = True
            self._attr_extra_state_attributes = {ATTR_IS_NIGHT: self._is_night}
        else:
            self._attr_is_on = False
            self._attr_extra_state_attributes = {}
        self.async_write_ha_state()

    # ToggleEntity methods
    async def async_turn_on(self, **kwargs):
        """Turn device on."""
        await self._post("on")
        self._update(True)

    async def async_turn_off(self, **kwargs):
        """Turn device off."""
        await self._post("off")
        self._update(False)

    # own methods
    async def _post(self, button):
        await self._api.send_light_infrared_signal(self._appliance_id, button)

    async def async_press_light_button(self, service_call):
        button = LightButton(service_call.data["button_name"])
        await self._post(button.value)
        if button == LightButton.on_off and self._attr_is_on \
                or (button == LightButton.night and self._is_night):
            self._update(False)
        else:
            self._update(True, button == LightButton.night)

    async def async_press_custom_button(self, service_call):
        signal_name = service_call.data["button_name"]
        signal_id = find_by(self._signals, 'name', signal_name).id

        if signal_id is None:
            _LOGGER.error(f"Invalid signal name: {signal_name}")
            return
        await self._api.send_signal(signal_id)
        self._update(True)
