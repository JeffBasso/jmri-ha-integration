"""JMRI locomotive media player entities."""

import logging

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import API_THROTTLES, DOMAIN
from .coordinator import JMRIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

# map DCC functions to meaningful names
FUNCTION_NAMES = {
    0: "Headlight",
    1: "Bell",
    2: "Horn",
    3: "Dynamic Brake",
    4: "Ditch Lights",
    5: "Cab Lights",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up JMRI locomotive entities from config entry."""
    coordinator: JMRIDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    roster = coordinator.data.get("roster", [])

    entities = []
    if isinstance(roster, list):
        entities.extend([JMRILocomotive(coordinator, loco) for loco in roster])

    async_add_entities(entities, True)


class JMRILocomotive(CoordinatorEntity, MediaPlayerEntity):
    """Represents a JMRI locomotive as a media player."""

    _attr_supported_features = (
        MediaPlayerEntityFeature.PLAY
        | MediaPlayerEntityFeature.STOP
        | MediaPlayerEntityFeature.VOLUME_SET
        | MediaPlayerEntityFeature.TURN_ON
        | MediaPlayerEntityFeature.TURN_OFF
    )
    _attr_icon = "mdi:train"

    def __init__(
        self,
        coordinator: JMRIDataUpdateCoordinator,
        loco_data: dict,
    ) -> None:
        """Initialize the locomotive."""
        super().__init__(coordinator)
        self._loco_id = loco_data.get("name", "unknown")
        self._address = loco_data.get("address", 0)
        self._attr_unique_id = f"jmri_loco_{self._loco_id}"
        self._attr_name = loco_data.get("userName", f"Locomotive {self._loco_id}")
        # local state — not from coordinator
        self._speed = 0
        self._forward = True
        self._running = False
        self._functions = {}

    @property
    def state(self) -> MediaPlayerState:
        """Return the state of the locomotive."""
        if not self._running:
            return MediaPlayerState.OFF
        if self._speed == 0:
            return MediaPlayerState.IDLE
        return MediaPlayerState.PLAYING

    @property
    def volume_level(self) -> float:
        """Return speed as volume 0.0-1.0."""
        return self._speed / 126

    @property
    def media_title(self) -> str:
        """Return direction as media title."""
        direction = "Forward" if self._forward else "Reverse"
        return f"Speed: {self._speed} | {direction}"

    @property
    def extra_state_attributes(self) -> dict:
        """Return extra attributes."""
        return {
            "dcc_address": self._address,
            "speed_step": self._speed,
            "direction": "forward" if self._forward else "reverse",
            "headlight": self._functions.get(0, False),
            "bell": self._functions.get(1, False),
            "horn": self._functions.get(2, False),
            "jmri_id": self._loco_id,
        }

    async def async_turn_on(self) -> None:
        """Enable the locomotive."""
        self._running = True
        self.async_write_ha_state()

    async def async_turn_off(self) -> None:
        """Stop and disable the locomotive."""
        self._speed = 0
        self._running = False
        await self._send_throttle()

    async def async_media_play(self) -> None:
        """Set speed to last non-zero or default 50."""
        self._running = True
        self._speed = 50
        await self._send_throttle()

    async def async_media_stop(self) -> None:
        """Emergency stop."""
        self._speed = 0
        await self._send_throttle()

    async def async_set_volume_level(self, volume: float) -> None:
        """Set speed from volume 0.0-1.0."""
        self._speed = int(volume * 126)
        self._running = True
        await self._send_throttle()

    async def _send_throttle(self) -> None:
        """Send throttle command to JMRI."""
        await self.coordinator.async_send_command(
            f"{API_THROTTLES}/{self._address}",
            {
                "speed": self._speed / 126,
                "forward": self._forward,
            },
        )
        self.async_write_ha_state()

    async def async_set_direction(self, forward: bool) -> None:
        """Set locomotive direction."""
        self._forward = forward
        await self._send_throttle()

    async def async_set_function(self, function: int, active: bool) -> None:
        """Set a DCC function on/off."""
        self._functions[function] = active
        await self.coordinator.async_send_command(
            f"{API_THROTTLES}/{self._address}/function",
            {"function": function, "active": active},
        )
        self.async_write_ha_state()
