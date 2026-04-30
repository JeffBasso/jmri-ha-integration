"""The JMRI Model Railroad integration."""
import logging
from pathlib import Path

from homeassistant.components import frontend, panel_custom
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .coordinator import JMRIDataUpdateCoordinator
from .proxy import JMRIProxyView, PROXY_PREFIX

_LOGGER = logging.getLogger(__name__)

PANEL_URL_PATH = "jmri"
PANEL_WEB_COMPONENT = "jmri-panel"
PANEL_MODULE_URL = "/jmri_static/panel.js"


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

    hass.http.register_view(JMRIProxyView(hass, entry.data))
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                PANEL_MODULE_URL,
                str(Path(__file__).with_name("panel.js")),
                cache_headers=False,
            )
        ]
    )

    await panel_custom.async_register_panel(
        hass,
        frontend_url_path=PANEL_URL_PATH,
        webcomponent_name=PANEL_WEB_COMPONENT,
        sidebar_title="JMRI",
        sidebar_icon="mdi:train",
        module_url=PANEL_MODULE_URL,
        trust_external=True,
        config={"url": f"{PROXY_PREFIX}/"},
    )

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
        frontend.async_remove_panel(hass, PANEL_URL_PATH)

    return unload_ok
