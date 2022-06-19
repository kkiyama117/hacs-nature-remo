from homeassistant import core
from homeassistant.const import CONF_ACCESS_TOKEN
import homeassistant.helpers.config_validation as cv
from remo import NatureRemoAPI, NatureRemoError
import voluptuous as vol

from .const import *

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Required({
        CONF_ACCESS_TOKEN: cv.string
    }),
}, extra=vol.ALLOW_EXTRA)


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Nature Remo platform."""
    # @TODO: Add setup code.
    LOGGER.debug(f"setup: {config}")
    if config is None:
        conf = {}
    else:
        conf = config
    conf = conf.get(DOMAIN, {})
    data = {}

    access_token: str = conf.get(CONF_ACCESS_TOKEN, "")
    data.setdefault(CONF_ACCESS_TOKEN, access_token)
    if len(access_token) != 0:
        try:
            api = NatureRemoAPI(access_token)
            user_data = await hass.async_add_executor_job(api.get_user)
            device_data = await hass.async_add_executor_job(api.get_devices)
            app_data = await hass.async_add_executor_job(api.get_appliances)
        except NatureRemoError as e:
            user_data = None
            device_data = None
            app_data = None
            LOGGER.error(e)
        data.setdefault('user', user_data)
        data.setdefault('devices', device_data)
        data.setdefault('appliances', app_data)

    data.setdefault(
        'temperature', 23
    )
    hass.data[DOMAIN] = data
    LOGGER.debug(f"setup2: {data}")
    for component in PLATFORMS:
        hass.async_create_task(
            hass.helpers.discovery.async_load_platform(component, DOMAIN, {}, config)
        )

    return True


async def async_setup_entry(hass: core.HomeAssistant, config: dict) -> bool:
    LOGGER.debug(f"setup entry: {config}")
    """Set up the Nature Remo from a config entry."""
    # @TODO: Add setup code.
    hass.data.setdefault(DOMAIN, {})

    return True
