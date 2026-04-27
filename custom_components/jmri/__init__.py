"""The JMRI Model Railroad integration."""
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import JMRIDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up JMRI from a config entry."""

    # create the coordinator
    coordinator = JMRIDataUpdateCoordinator(hass, entry)

    # fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # store coordinator for platforms to access
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # set up all platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    # unload all platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # close aiohttp session
        coordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_close()

        # remove coordinator from hass.data
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
