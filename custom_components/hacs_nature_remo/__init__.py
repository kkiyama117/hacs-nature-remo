"""
The "hello world" custom component.
This component implements the bare minimum that a component should implement.
Configuration:
To use the hello_world component you will need to add the following to your
configuration.yaml file.
hello_world_async:
"""
"""Provide the initial setup."""
import logging
from .const import *

from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

# The domain of your component. Should be equal to the name of your component.
_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Setup our skeleton component. Provide Setup of platform."""

    # States are in the format DOMAIN.OBJECT_ID.
    hass.states.async_set(f"{DOMAIN}.Hello_World", 'Works!')
    _LOGGER.debug("Setting up Nature Remo component.")

    # Return boolean to indicate that initialization was successfully.
    return True

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
