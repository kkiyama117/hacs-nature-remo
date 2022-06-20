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
from remo import NatureRemoAPI
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
    devices: list[NRDevice] = hass.data.get(DOMAIN, {"devices": []})["devices"]
    sensors = [RemoMiniEntity(get_api_base(hass), i.id) for i in devices]
    # async_add_entities(sensors, update_before_add=True)
    async_add_entities(sensors)


class RemoMiniEntity(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = f"{DOMAIN}.temperature"
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    """Representation of a sensor."""

    def __init__(self, api, device_id: str):
        self._api = api
        self._device_id = device_id
        devices = self._api.get_devices()
        device = list(filter(lambda x: x.id == device_id, devices))[0]
        LOGGER.debug(f"initialize device: {self.name}: {self._api}")
        self._attr_device_info = DeviceInfo(
            default_manufacturer="Nature",
            identifiers={(DOMAIN, device.id)},
            model=device.serial_number,
            name=device.name,
            sw_version=device.firmware_version
        )

    @property
    def name(self) -> str | None:
        return f"{DOMAIN}.domain.{self.device_info.get('id')}"

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        if self._api is not None:
            devices = self._api.get_devices()
            device = list(filter(lambda x: x.id == self._device_id, devices))[0]
            self._attr_native_value = self._api.newest_events.get('te').val
            LOGGER.debug(f"get value of  {self._attr_name}: {self._attr_native_value}")
        else:
            LOGGER.error(f"error get temperature of  {self._attr_name}")
