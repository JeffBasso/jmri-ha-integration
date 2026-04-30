"""JMRI signal mast sensors."""

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import JMRIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# map JMRI signal aspects to colors for icon
ASPECT_ICONS = {
    "Clear": "mdi:circle-slice-8",  # green
    "Approach": "mdi:circle-slice-8",  # yellow
    "Stop": "mdi:circle-slice-8",  # red
    "StopAndProceed": "mdi:circle-slice-4",  # red/yellow
    "Unlit": "mdi:circle-outline",  # dark
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JMRI signal mast sensors from config entry."""
    coordinator: JMRIDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    signals = coordinator.data.get("signals", [])

    entities = []
    if isinstance(signals, list):
        entities.extend([JMRISignalMast(coordinator, signal) for signal in signals])

    async_add_entities(entities, True)


class JMRISignalMast(CoordinatorEntity, SensorEntity):
    """Represents a JMRI signal mast."""

    _attr_icon = "mdi:traffic-light"

    def __init__(
        self,
        coordinator: JMRIDataUpdateCoordinator,
        signal_data: dict,
    ) -> None:
        """Initialize the signal mast."""
        super().__init__(coordinator)
        self._signal_name = signal_data.get("name", "unknown")
        self._attr_unique_id = f"jmri_signal_{self._signal_name}"
        self._attr_name = f"Signal {self._signal_name}"

    @property
    def native_value(self) -> str:
        """Return the current signal aspect."""
        signals = self.coordinator.data.get("signals", [])
        if not isinstance(signals, list):
            return "Unknown"
        for signal in signals:
            if signal.get("name") == self._signal_name:
                return signal.get("aspect", "Unknown")
        return "Unknown"

    @property
    def icon(self) -> str:
        """Return icon based on aspect."""
        aspect = self.native_value
        return ASPECT_ICONS.get(aspect, "mdi:traffic-light")

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        signals = self.coordinator.data.get("signals", [])
        if isinstance(signals, list):
            for signal in signals:
                if signal.get("name") == self._signal_name:
                    return {
                        "jmri_name": self._signal_name,
                        "aspect": signal.get("aspect", "Unknown"),
                        "lit": signal.get("lit", True),
                        "held": signal.get("held", False),
                        "source": "JMRI",
                    }
        return {"jmri_name": self._signal_name}
