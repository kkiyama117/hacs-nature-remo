"""Support for Nature Remo AC."""
import logging

from homeassistant.components.switch import SwitchEntity
from remo.models import Appliance

from . import (
    DEFAULT_COORDINATOR_SCHEMA,
    DOMAIN,
    KEY_APPLIANCES,
    KEY_COORDINATOR,
    NatureRemoAPIVer1,
    NatureRemoBase,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None) -> None:
    """Set up the Nature Remo IR."""
    if discovery_info is None:
        return
    _LOGGER.debug("Setting up IR platform.")
    _data = hass.data.get(DOMAIN)
    coordinator = _data.get(KEY_COORDINATOR, DEFAULT_COORDINATOR_SCHEMA)
    appliances = coordinator.data.get(KEY_APPLIANCES)
    api = _data.get("api")
    config = _data.get("config")
    async_add_entities(
        [
            NatureRemoIR(coordinator, api, appliance, config)
            for appliance in appliances
            if appliance.type == "IR"
        ]
    )


class NatureRemoIR(NatureRemoBase, SwitchEntity):
    """Implementation of a Nature Remo IR."""

    def __init__(self, coordinator, api: NatureRemoAPIVer1, appliance: Appliance, config) -> None:
        super().__init__(coordinator, appliance)
        self._api = api
        # self._signals = {s["name"]: s["id"] for s in appliance["signals"]}
        self._signals = appliance.signals
        self._attr_is_on = False
        self._attr_assumed_state = True

    def _set_on(self, is_on: bool) -> None:
        self._attr_is_on = is_on
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs) -> None:
        """Turn on the switch."""
        _LOGGER.debug("Set state: ON")
        try:
            await self._post_icon([
                "ico_on",
                "ico_io",
            ])
            self._set_on(True)
        except OSError:
            _LOGGER.debug("Cannot find on signal")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the switch."""
        _LOGGER.debug("Set state: OFF")
        try:
            await self._post_icon([
                "ico_off",
                "ico_io",
            ])
            self._set_on(False)
        except OSError:
            _LOGGER.debug("Cannot find off signal")

    async def _post_icon(self, names: [str]) -> None:
        images = [x.image for x in self._signals]
        for name in names:
            if name in images:
                await self._post(self._signals[images.index(name)].id)
                break

    async def _post(self, signal: str) -> None:
        _LOGGER.debug("Send Signals using signal: %s, signal")
        response = await self._api.send_signal(signal)
        self.async_write_ha_state()
