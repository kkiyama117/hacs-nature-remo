"""The Nature Remo integration."""

import logging
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.config_validation import PLATFORM_SCHEMA, time_period
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_SCAN_INTERVAL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType
from remo import NatureRemoAPI
from remo.models import Device as NRDevice, Appliance as NRAppliance

from .const import *

_LOGGER = logging.getLogger(__name__)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_ACCESS_TOKEN): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL): time_period,
            }
        ),
    },
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Setup our skeleton component. Provide Setup of platform."""
    _LOGGER.debug("Setting up Nature Remo component.")
    hass.states.async_set(f"{DOMAIN}.hello_world", 'Works!')
    access_token = config[DOMAIN][CONF_ACCESS_TOKEN]
    api = WrappedAPI(access_token=access_token)
    coordinator = hass.data[DOMAIN] = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Nature Remo data update",
        update_method=api.get,
        update_interval=CONF_SCAN_INTERVAL,
    )
    await coordinator.async_refresh()
    hass.data[DOMAIN] = {
        "api": api,
        "coordinator": coordinator,
        "config": config[DOMAIN],
    }

    _LOGGER.debug(hass.data[DOMAIN])
    _LOGGER.debug("Setting up Nature Remo component finished with no error.")
    # Return boolean to indicate that initialization was successfully.
    return True


class WrappedAPI:
    """Nature Remo API client"""

    def __init__(self, access_token):
        """Init API client"""
        self._access_token = access_token
        self._session = NatureRemoAPI(access_token)

    async def get(self):
        return {"devices": await self.devices(), "appliances": await self.appliances()}

    async def devices(self):
        _LOGGER.debug("Trying to fetch device list from API.")
        return self._session.get_devices()

    async def appliances(self):
        _LOGGER.debug("Trying to fetch appliance list from API.")
        return self._session.get_appliances()


class NatureRemoDevice(Entity):
    def __init__(self, coordinator, device: NRDevice):
        self.coordinator = coordinator
        self._api_info = device


class NatureRemoAppliance(Entity):
    def __init__(self, coordinator, appliance: NRAppliance):
        self.coordinator = coordinator
        self._api_info = appliance

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Nature Remo {self._api_info.nickname}"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return self._api_info.id

    @property
    def should_poll(self):
        """Return the polling requirement of the entity."""
        return False

    @property
    def device_info(self):
        """Return the device info for the sensor."""
        # Since device registration requires Config Entries, this dosen't work for now

        return {
            "identifiers": {(DOMAIN, f"appliance_{self._api_info.id}")},
            "manufacturer": self._api_info.model.manufacturer,
            "model": self._api_info.model.id,
            "name": self._api_info.id,
            "sw_version": self._api_info.device.firmware_version,
            "hw_version": self._api_info.model.name
        }
#
# async def async_setup_entry(hass, config_entry):
# 	config_entry.data = ensure_config(config_entry.data)  # make sure that missing storage values will be default (const function)
# 	config_entry.options = config_entry.data
# 	config_entry.add_update_listener(update_listener)
#
# 	hass.data.setdefault(DOMAIN, {})
# 	hass.data[DOMAIN][config_entry.entry_id] = {}
#
# 	# Add sensor
# 	for platform in PLATFORMS:
# 		hass.async_add_job(
# 			hass.config_entries.async_forward_entry_setup(config_entry, platform)
# 		)
# 	return True
#
#
#
# async def async_remove_entry(hass, config_entry):
# 	"""Handle removal of an entry."""
# 	for platform in PLATFORMS:
# 		try:
# 			await hass.config_entries.async_forward_entry_unload(config_entry, platform)
# 			_LOGGER.info(
# 				"Successfully removed sensor from the integration"
# 			)
# 		except ValueError:
# 			pass

#
# async def update_listener(hass, entry):
# 	"""Update listener."""
# 	entry.data = entry.options
# 	for platform in PLATFORMS:
# 		await hass.config_entries.async_forward_entry_unload(entry, platform)
# 		hass.async_add_job(hass.config_entries.async_forward_entry_setup(entry, platform))
