"""JMRI turnout and track power switches."""

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    API_POWER,
    API_TURNOUTS,
    DOMAIN,
    STATE_CLOSED,
    STATE_OFF,
    STATE_ON,
    STATE_THROWN,
)
from .coordinator import JMRIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JMRI switches from config entry."""
    coordinator: JMRIDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # add track power switch
    entities.append(JMRITrackPower(coordinator))

    # add turnout switches
    turnouts = coordinator.data.get("turnouts", [])
    if isinstance(turnouts, list):
        entities.extend([JMRITurnout(coordinator, turnout) for turnout in turnouts])

    async_add_entities(entities, True)


class JMRITrackPower(CoordinatorEntity, SwitchEntity):
    """Track power on/off switch."""

    _attr_name = "Track Power"
    _attr_unique_id = "jmri_track_power"
    _attr_icon = "mdi:train"

    def __init__(self, coordinator: JMRIDataUpdateCoordinator) -> None:
        """Initialize track power switch."""
        super().__init__(coordinator)

    @property
    def is_on(self) -> bool:
        """Return true if track power is on."""
        power = self.coordinator.data.get("power", {})
        if isinstance(power, dict):
            return power.get("state") == STATE_ON
        return False

    async def async_turn_on(self, **kwargs):
        """Turn track power on."""
        await self.coordinator.async_send_command(API_POWER, {"state": STATE_ON})
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn track power off."""
        await self.coordinator.async_send_command(API_POWER, {"state": STATE_OFF})
        await self.coordinator.async_request_refresh()


class JMRITurnout(CoordinatorEntity, SwitchEntity):
    """Represents a JMRI turnout."""

    _attr_icon = "mdi:train-variant"

    def __init__(
        self,
        coordinator: JMRIDataUpdateCoordinator,
        turnout_data: dict,
    ) -> None:
        """Initialize the turnout."""
        super().__init__(coordinator)
        self._turnout_name = turnout_data.get("name", "unknown")
        self._attr_unique_id = f"jmri_turnout_{self._turnout_name}"
        self._attr_name = f"Turnout {self._turnout_name}"

    @property
    def is_on(self) -> bool:
        """Return true if turnout is thrown."""
        turnouts = self.coordinator.data.get("turnouts", [])
        if not isinstance(turnouts, list):
            return False
        for turnout in turnouts:
            if turnout.get("name") == self._turnout_name:
                return turnout.get("state") == STATE_THROWN
        return False

    async def async_turn_on(self, **kwargs):
        """Throw the turnout."""
        await self.coordinator.async_send_command(
            f"{API_TURNOUTS}/{self._turnout_name}",
            {"state": STATE_THROWN},
        )
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        """Close the turnout."""
        await self.coordinator.async_send_command(
            f"{API_TURNOUTS}/{self._turnout_name}",
            {"state": STATE_CLOSED},
        )
        await self.coordinator.async_request_refresh()

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        return {
            "jmri_name": self._turnout_name,
            "source": "JMRI",
        }
