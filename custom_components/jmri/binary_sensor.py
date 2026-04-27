"""JMRI block detection binary sensors."""
import logging
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, STATE_ACTIVE
from .coordinator import JMRIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JMRI block sensors from config entry."""
    coordinator: JMRIDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # wait for first data
    sensors = coordinator.data.get("sensors", [])

    entities = [
        JMRIBlockSensor(coordinator, sensor)
        for sensor in sensors
        if isinstance(sensors, list)
    ]

    async_add_entities(entities, True)


class JMRIBlockSensor(CoordinatorEntity, BinarySensorEntity):
    """Represents a JMRI block occupancy sensor."""

    _attr_device_class = BinarySensorDeviceClass.OCCUPANCY

    def __init__(
        self,
        coordinator: JMRIDataUpdateCoordinator,
        sensor_data: dict,
    ) -> None:
        """Initialize the block sensor."""
        super().__init__(coordinator)
        self._sensor_name = sensor_data.get("name", "unknown")
        self._attr_unique_id = f"jmri_sensor_{self._sensor_name}"
        self._attr_name = f"Block {self._sensor_name}"

    @property
    def is_on(self) -> bool:
        """Return true if block is occupied."""
        sensors = self.coordinator.data.get("sensors", [])
        if not isinstance(sensors, list):
            return False
        for sensor in sensors:
            if sensor.get("name") == self._sensor_name:
                return sensor.get("state") == STATE_ACTIVE
        return False

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        return {
            "jmri_name": self._sensor_name,
            "source": "JMRI",
        }
