"""Config flow for JMRI integration."""

import aiohttp
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT

from .const import DEFAULT_HOST, DEFAULT_NAME, DEFAULT_PORT, DOMAIN


class JMRIConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for JMRI."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            # test the connection before accepting
            # ThreadedResolver bypasses aiodns which has a Python 3.13 incompatibility
            try:
                connector = aiohttp.TCPConnector(
                    resolver=aiohttp.resolver.ThreadedResolver()
                )
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(
                        f"http://{host}:{port}/json/power",
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as resp:
                        if resp.status == 200:
                            return self.async_create_entry(
                                title=user_input[CONF_NAME],
                                data=user_input,
                            )
                        errors["base"] = "cannot_connect"
            except aiohttp.ClientConnectionError, OSError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        # show the form
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default=DEFAULT_NAME): str,
                vol.Required(CONF_HOST, default=DEFAULT_HOST): str,
                vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )
