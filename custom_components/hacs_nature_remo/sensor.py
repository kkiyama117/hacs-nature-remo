"""Platform for sensor integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
from remo.models import Device as NRDevice

from .const import DOMAIN, LOGGER
from .helper import get_api_base


async def async_setup_platform(
        hass: HomeAssistantType,
        config: ConfigType,
        async_add_entities: AddEntitiesCallback,
        discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return
    LOGGER.debug("Setting up sensor platform.")
    devices: list[NRDevice] = hass.data.get(DOMAIN, {"devices": []})["devices"]
    sensors = [RemoMiniEntity(hass, get_api_base(hass), i) for i in devices]
    # async_add_entities(sensors, update_before_add=True)
    async_add_entities(sensors)


class RemoMiniEntity(SensorEntity):
    """Representation of a Sensor."""

    # _attr_name = f"{DOMAIN}.device"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    """Representation of a sensor."""

    def __init__(self, hass, api, device: NRDevice):
        super().__init__()
        self._api = api
        self._device = device
        self._attr_name = f"{DOMAIN}_{self._device.name}"
        self._attr_unique_id = f"{DOMAIN}.domain.{self._device.name}"
        LOGGER.debug(f"initialize device: {self.name}: {self._api}")
        self._attr_device_info = DeviceInfo(
            default_manufacturer="Nature",
            identifiers={(DOMAIN, self._device.id)},
            model=self._device.serial_number,
            name=self._device.name,
            sw_version=self._device.firmware_version
        )

    def _set_temp_unit(self):
        self._attr_native_unit_of_measurement = TEMP_CELSIUS

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        if self._api is not None:
            # devices = await self._hass.async_add_executor_job(
            #     self._api.get_devices
            # )
            devices = self._api.get_devices()
            device = list(filter(lambda x: x.id == self._device.id, devices))[0]
            self._device = device
            self._attr_native_value = self._device.newest_events.get('te').val
            LOGGER.debug(f"get value of  {self._attr_name}: {self._attr_native_value}")
        else:
            LOGGER.error(f"error get temperature of  {self._attr_name}")
