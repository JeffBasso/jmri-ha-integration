"""JMRI Data Update Coordinator."""
import logging
import aiohttp
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import (
    DOMAIN,
    SCAN_INTERVAL,
    API_ROSTER,
    API_SENSORS,
    API_TURNOUTS,
    API_POWER,
    API_SIGNALS,
)

_LOGGER = logging.getLogger(__name__)


class JMRIDataUpdateCoordinator(DataUpdateCoordinator):
    """Fetch data from JMRI REST API."""

    def __init__(self, hass: HomeAssistant, entry) -> None:
        """Initialize the coordinator."""
        self.host = entry.data[CONF_HOST]
        self.port = entry.data[CONF_PORT]
        self.base_url = f"http://{self.host}:{self.port}"
        self.session = aiohttp.ClientSession()

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        """Fetch data from JMRI."""
        try:
            data = {}

            # fetch each endpoint
            data["roster"] = await self._fetch(API_ROSTER)
            data["sensors"] = await self._fetch(API_SENSORS)
            data["turnouts"] = await self._fetch(API_TURNOUTS)
            data["power"] = await self._fetch(API_POWER)
            data["signals"] = await self._fetch(API_SIGNALS)

            return data

        except aiohttp.ClientConnectionError as err:
            raise UpdateFailed(f"Cannot connect to JMRI at {self.base_url}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error fetching JMRI data: {err}") from err

    async def _fetch(self, endpoint: str):
        """Fetch a single endpoint from JMRI."""
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    _LOGGER.warning("JMRI returned %s for %s", resp.status, url)
                    return []
        except Exception as err:
            _LOGGER.error("Error fetching %s: %s", url, err)
            return []

    async def async_send_command(self, endpoint: str, payload: dict):
        """Send a command to JMRI."""
        url = f"{self.base_url}{endpoint}"
        try:
            async with self.session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                return resp.status == 200
        except Exception as err:
            _LOGGER.error("Error sending command to %s: %s", url, err)
            return False

    async def async_close(self):
        """Close the aiohttp session."""
        await self.session.close()
