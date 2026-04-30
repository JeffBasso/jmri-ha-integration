#!/usr/bin/env python3
"""Ingress-aware reverse proxy for the JMRI web UI.

Listens on 12088 (HA ingress_port), proxies to JMRI on 12080.
When X-Ingress-Path is present, rewrites absolute URLs in HTML and
JavaScript responses so they resolve correctly through the ingress
token URL.  When accessed directly the header is absent and all
rewriting is skipped.
"""
import asyncio
import re
import aiohttp
from aiohttp import web, WSMsgType

JMRI_HTTP = "http://127.0.0.1:12080"
JMRI_WS   = "ws://127.0.0.1:12080"

_HOP_BY_HOP = frozenset({
    "connection", "keep-alive", "transfer-encoding", "te", "trailer",
    "upgrade", "content-length", "content-encoding",
    "proxy-authenticate", "proxy-authorization",
})

# Matches href=", src=", action=" followed by /
_HTML_RE = re.compile(r'((?:href|src|action)=["\'])/')

# Matches quoted absolute paths to known JMRI endpoints inside JS
_JS_RE = re.compile(
    r'(["\'])/(json|roster|operations|tables|panel|web|css|js|images|help|servlet)/'
)


def _rewrite_html(data: bytes, base: str) -> bytes:
    text = data.decode("utf-8", errors="replace")
    text = _HTML_RE.sub(rf"\g<1>{base}/", text)
    return text.encode("utf-8")


def _rewrite_js(data: bytes, base: str) -> bytes:
    text = data.decode("utf-8", errors="replace")
    text = _JS_RE.sub(rf"\g<1>{base}/\g<2>/", text)
    return text.encode("utf-8")


async def _proxy_ws(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    url = JMRI_WS + request.path_qs
    session: aiohttp.ClientSession = request.app["session"]
    try:
        upstream = await session.ws_connect(url)
    except Exception as exc:
        await ws.close(message=f"upstream error: {exc}".encode())
        return ws

    async def pipe(src, dst):
        async for msg in src:
            if msg.type == WSMsgType.TEXT:
                await dst.send_str(msg.data)
            elif msg.type == WSMsgType.BINARY:
                await dst.send_bytes(msg.data)
            else:
                break
        await dst.close()

    tasks = [
        asyncio.ensure_future(pipe(ws, upstream)),
        asyncio.ensure_future(pipe(upstream, ws)),
    ]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
    for t in pending:
        t.cancel()

    return ws


async def handle(request: web.Request) -> web.StreamResponse:
    if request.headers.get("Upgrade", "").lower() == "websocket":
        return await _proxy_ws(request)

    ingress = request.headers.get("X-Ingress-Path", "")

    fwd_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in _HOP_BY_HOP and k.lower() != "host"
    }
    fwd_headers["Accept-Encoding"] = "identity"

    body = await request.read()
    url = JMRI_HTTP + request.path_qs

    session: aiohttp.ClientSession = request.app["session"]
    async with session.request(
        request.method,
        url,
        headers=fwd_headers,
        data=body or None,
        allow_redirects=False,
    ) as resp:
        ct = resp.headers.get("Content-Type", "")
        data = await resp.read()

        if ingress:
            if "text/html" in ct:
                data = _rewrite_html(data, ingress)
            elif "javascript" in ct:
                data = _rewrite_js(data, ingress)

        out_headers = {
            k: v for k, v in resp.headers.items()
            if k.lower() not in _HOP_BY_HOP
        }

        if ingress and "Location" in out_headers:
            loc = out_headers["Location"]
            if loc.startswith("/"):
                out_headers["Location"] = ingress + loc

        return web.Response(body=data, status=resp.status, headers=out_headers)


async def _startup(app: web.Application) -> None:
    app["session"] = aiohttp.ClientSession()


async def _cleanup(app: web.Application) -> None:
    await app["session"].close()


app = web.Application()
app.on_startup.append(_startup)
app.on_cleanup.append(_cleanup)
app.router.add_route("*", "/", handle)
app.router.add_route("*", "/{path:.*}", handle)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=12088, access_log=None)
