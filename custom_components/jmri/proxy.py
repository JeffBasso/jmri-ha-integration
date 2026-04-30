"""HTTP proxy for the JMRI web UI."""
from __future__ import annotations

from http import HTTPStatus
from typing import Any

import aiohttp
from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import HomeAssistant

PROXY_PREFIX = "/api/jmri_proxy"

_HOP_BY_HOP_HEADERS = {
    "connection",
    "content-encoding",
    "content-length",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


class JMRIProxyView(HomeAssistantView):
    """Proxy JMRI web requests through Home Assistant."""

    name = "api:jmri:proxy"
    url = PROXY_PREFIX
    requires_auth = False
    extra_urls = [
        f"{PROXY_PREFIX}/{{path:.*}}",
        "/css/{path:.*}",
        "/js/{path:.*}",
        "/json/{path:.*}",
        "/panel",
        "/panel/{path:.*}",
        "/roster",
        "/roster/{path:.*}",
        "/operations",
        "/operations/{path:.*}",
        "/web/{path:.*}",
    ]

    def __init__(self, hass: HomeAssistant, entry_data: dict[str, Any]) -> None:
        """Initialize the proxy view."""
        self._hass = hass
        self._base_url = f"http://{entry_data[CONF_HOST]}:{entry_data[CONF_PORT]}"

    async def get(self, request: web.Request, path: str = "") -> web.Response:
        """Proxy a GET request to JMRI."""
        return await self._proxy(request, path)

    async def post(self, request: web.Request, path: str = "") -> web.Response:
        """Proxy a POST request to JMRI."""
        return await self._proxy(request, path)

    async def _proxy(self, request: web.Request, path: str) -> web.Response:
        """Proxy a request to the matching JMRI path."""
        target_path = self._target_path(request, path)
        target_url = f"{self._base_url}{target_path}"
        if request.query_string:
            target_url = f"{target_url}?{request.query_string}"

        data = await request.read()
        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in _HOP_BY_HOP_HEADERS and key.lower() != "host"
        }

        try:
            connector = aiohttp.TCPConnector(
                resolver=aiohttp.resolver.ThreadedResolver()
            )
            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.request(
                    request.method,
                    target_url,
                    data=data or None,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=30),
                    allow_redirects=False,
                ) as response:
                    body = await response.read()
                    response_headers = {
                        key: value
                        for key, value in response.headers.items()
                        if key.lower() not in _HOP_BY_HOP_HEADERS
                    }
                    return web.Response(
                        body=body,
                        status=response.status,
                        headers=response_headers,
                    )
        except aiohttp.ClientError as err:
            return web.Response(
                text=f"Unable to reach JMRI web server: {err}",
                status=HTTPStatus.BAD_GATEWAY,
            )

    @staticmethod
    def _target_path(request: web.Request, path: str) -> str:
        """Map the Home Assistant route back to the JMRI route."""
        if request.path == PROXY_PREFIX:
            return "/"
        if request.path.startswith(f"{PROXY_PREFIX}/"):
            return f"/{path}"
        return request.path
