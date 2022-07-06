"""Platform for sensor integration."""
from __future__ import annotations

from typing import List

from homeassistant.const import (
    DEVICE_CLASS_HUMIDITY,
    DEVICE_CLASS_ILLUMINANCE,
    DEVICE_CLASS_POWER,
    DEVICE_CLASS_TEMPERATURE,
    LIGHT_LUX,
    PERCENTAGE,
    POWER_WATT,
    TEMP_CELSIUS,
)
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)
from remo.models import Appliance, Device

from . import NatureRemoBase, NatureRemoDeviceBase
from .const import DOMAIN, LOGGER
from .utils import find_by


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
    _data = hass.data.get(DOMAIN)
    coordinator = _data.get("coordinator")
    appliances = coordinator.data.get("appliances")
    devices = coordinator.data.get("devices")
    entities: List[Entity] = [
        NatureRemoE(coordinator, appliance)
        for appliance in appliances
        if appliance.type == "EL_SMART_METER"
    ]
    # async_add_entities(sensors, update_before_add=True)
    for device in devices:
        for sensor in device.newest_events.keys():
            if sensor == "te":
                entities.append(NatureRemoTemperatureSensor(coordinator, device))
            elif sensor == "hu":
                entities.append(NatureRemoHumiditySensor(coordinator, device))
            elif sensor == "il":
                entities.append(NatureRemoIlluminanceSensor(coordinator, device))
    async_add_entities(entities)


class NatureRemoE(NatureRemoBase):
    """Implementation of a Nature Remo E sensor."""

    def __init__(self, coordinator, appliance):
        super().__init__(coordinator, appliance)
        self._unit_of_measurement = POWER_WATT
        self._attr_device_class = DEVICE_CLASS_POWER

    @property
    def state(self):
        """Return the state of the sensor."""
        appliances: List[Appliance] = self._coordinator.data.get("appliances")
        appliance = find_by(appliances, "id", self._appliance_id)
        if hasattr(appliance, 'smart_meter'):
            smart_meter = appliance.smart_meter
            echonetlite_properties = smart_meter["echonetlite_properties"]
            measured_instantaneous = next(
                value.val for value in echonetlite_properties if value["epc"] == 231
            )
            LOGGER.debug("Current state: %sW", measured_instantaneous)
            return measured_instantaneous
        return "No state"

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


class NatureRemoTemperatureSensor(NatureRemoDeviceBase):
    """Implementation of a Nature Remo sensor."""

    def __init__(self, coordinator, appliance):
        super().__init__(coordinator, appliance)
        self._attr_name = f"Nature Remo {self._device.name} Temperature"
        self._attr_unique_id = self._device.id + "-te"
        self._attr_unit_of_measurement = TEMP_CELSIUS
        self._attr_device_class = DEVICE_CLASS_TEMPERATURE

    @property
    def state(self):
        """Return the state of the sensor."""
        devices: List[Appliance] = self._coordinator.data.get("devices")
        device = find_by(devices, "id", self._device.id)
        return device.newest_events.get("te").val


class NatureRemoHumiditySensor(NatureRemoDeviceBase):
    """Implementation of a Nature Remo sensor."""

    def __init__(self, coordinator, appliance):
        super().__init__(coordinator, appliance)
        self._attr_name = f"Nature Remo {self._device.name} Humidity"
        self._attr_unique_id = self._device.id + "-hu"
        self._attr_unit_of_measurement = PERCENTAGE
        self._attr_device_class = DEVICE_CLASS_HUMIDITY

    @property
    def state(self):
        """Return the state of the sensor."""
        devices: List[Appliance] = self._coordinator.data.get("devices")
        device = find_by(devices, "id", self._device.id)
        return device.newest_events.get("hu").val


class NatureRemoIlluminanceSensor(NatureRemoDeviceBase):
    """Implementation of a Nature Remo sensor."""

    def __init__(self, coordinator, appliance):
        super().__init__(coordinator, appliance)
        self._attr_name = f"Nature Remo {self._device.name} Illuminance"
        self._attr_unique_id = self._device.id + "-il"
        self._attr_unit_of_measurement = LIGHT_LUX
        self._attr_device_class = DEVICE_CLASS_ILLUMINANCE

    @property
    def state(self):
        """Return the state of the sensor."""
        devices: List[Appliance] = self._coordinator.data.get("devices")
        device = find_by(devices, "id", self._device.id)
        return device.newest_events.get("il").val
