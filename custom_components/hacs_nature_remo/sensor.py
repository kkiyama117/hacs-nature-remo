"""Platform for sensor integration."""
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import TEMP_CELSIUS
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import (
    ConfigType,
    DiscoveryInfoType,
    HomeAssistantType,
)

from .const import DOMAIN, LOGGER


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
    sensors = [ExampleSensor()]
    # async_add_entities(sensors, update_before_add=True)
    async_add_entities(sensors)


class ExampleSensor(SensorEntity):
    """Representation of a Sensor."""

    _attr_name = f"{DOMAIN}.temperature"
    _attr_native_unit_of_measurement = TEMP_CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    """Representation of a sensor."""

    def update(self) -> None:
        """Fetch new state data for the sensor.
        This is the only method that should fetch new data for Home Assistant.
        """
        self._attr_native_value = self.hass.data[DOMAIN]['temperature']
        LOGGER.debug(f"get value of  {self._attr_name}: {self._attr_native_value}")
