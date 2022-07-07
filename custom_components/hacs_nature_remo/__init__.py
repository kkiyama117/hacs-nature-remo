from homeassistant import core
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from remo.models import Appliance, Device
import voluptuous as vol

from .api import HTTPWrapper, NatureRemoAPIVer1, Response
from .api.wrapper import AioHttpWrapper
from .const import *

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Required({
        CONF_ACCESS_TOKEN: cv.string
    }),
}, extra=vol.ALLOW_EXTRA)


def __get_update_method(_api: NatureRemoAPIVer1):
    async def __inner__():
        LOGGER.debug("Trying to fetch appliance and device list from API.")
        appliances = _api.get_appliances()
        devices = _api.get_devices()
        return {"appliances": await appliances, "devices": await devices}

    return __inner__


async def async_setup(hass: core.HomeAssistant, config: dict) -> bool:
    """Set up the Nature Remo platform."""
    # @TODO: Add setup code.
    LOGGER.debug("Setting up Nature Remo component.")
    if config is None:
        conf = {}
    else:
        conf = config
    conf = conf.get(DOMAIN, {})

    session = async_get_clientsession(hass)

    access_token: str = conf.get(CONF_ACCESS_TOKEN, "")

    if len(access_token) != 0:
        _api = NatureRemoAPIVer1(AioHttpWrapper(session), access_token)
        coordinator = hass.data[DOMAIN] = DataUpdateCoordinator(
            hass,
            LOGGER,
            name="Nature Remo update",
            update_method=__get_update_method(_api),
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )
        await coordinator.async_refresh()
    else:
        # TODO: Add Custom Error
        raise RuntimeError("Error:Token is not set")

    data = {
        "api": _api,
        "coordinator": coordinator,
        "config": conf,
    }
    hass.data[DOMAIN] = data
    for component in PLATFORMS:
        hass.async_create_task(
            hass.helpers.discovery.async_load_platform(component, DOMAIN, {}, config)
        )

    return True


# async def async_setup_entry(hass: core.HomeAssistant, config: dict) -> bool:
#     LOGGER.debug(f"setup entry: {config}")
#     """Set up the Nature Remo from a config entry."""
#     # @TODO: Add setup code.
#     hass.data.setdefault(DOMAIN, {})
#
#     return True


class NatureRemoBase(Entity):
    """Nature Remo entity base class."""

    def __init__(self, coordinator: DataUpdateCoordinator, appliance: Appliance):
        self._coordinator = coordinator
        self._attr_name = f"Nature Remo {appliance.nickname}"
        self._appliance_id = appliance.id
        self._device = appliance.device
        self._attr_unique_id = self._appliance_id
        self._attr_should_poll = False
        self._attr_device_info = DeviceInfo(
            default_manufacturer="Nature Remo",
            identifiers={(DOMAIN, self._device.id)},
            model=self._device.serial_number,
            name=self._device.name,
            sw_version=self._device.firmware_version
        )


class NatureRemoDeviceBase(Entity):
    """Nature Remo Device entity base class."""

    def __init__(self, coordinator, device: Device):
        self._coordinator = coordinator
        self._attr_name = f"Nature Remo {device.name}"
        self._device = device
        self._coordinator = coordinator
        self._appliance_id = device.id
        self._attr_unique_id = self._appliance_id
        self._attr_should_poll = True
        self._attr_device_info = DeviceInfo(
            default_manufacturer="Nature Remo",
            identifiers={(DOMAIN, self._device.id)},
            model=self._device.serial_number,
            name=self._device.name,
            sw_version=self._device.firmware_version
        )

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self._coordinator.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self):
        """Update the entity.
        Only used by the generic entity update service.
        """
        await self._coordinator.async_request_refresh()
