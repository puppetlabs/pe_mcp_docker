"""Thin MCP proxy — local stdio server forwarding to remote PE MCP over HTTPS.

Runs as a stdio MCP server for Claude Code. Connects to the PE MCP
behind the nginx reverse proxy, using the PE CA certificate for TLS
verification and, where the deployment requires it, the PE RBAC token
for authentication.
"""

import os
import sys
from pathlib import Path

import httpx
from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.server import create_proxy

DEFAULT_CA_CERT = Path("/config/pe-ca.pem")

# PE serves the MCP endpoint at /mcp with no trailing slash. A trailing slash
# is rewritten upstream to /infra-assistant/mcp/ and 404s *after* the RBAC check
# passes, so the caller sees an opaque "Session terminated" during initialize
# rather than anything pointing at the URL. Both forms are things people
# reasonably type, so accept either and normalize.
REMOTE_MCP_URL = os.environ.get(
    "PE_MCP_URL",
    "https://REPLACE_WITH_MCP_NODE_FQDN/mcp/",
).strip().rstrip("/")
CA_CERT_PATH = os.environ.get("PE_CA_CERT", str(DEFAULT_CA_CERT)).strip()
RBAC_TOKEN = os.environ.get("PE_RBAC_TOKEN", "").strip()

# Where nginx in front of the PE MCP gates on PE RBAC, the token goes in the
# X-Authentication header; without it every request comes back 401. Not every
# deployment gates on RBAC, so an empty/unset token is valid: send no header
# at all rather than an empty one, which some proxies reject outright.
AUTH_HEADERS = {"X-Authentication": RBAC_TOKEN} if RBAC_TOKEN else {}

# A 401 during the MCP initialize handshake otherwise surfaces to the caller as
# a bare "Session terminated" with no clue that a token is what's missing. Watch
# responses as they go past and say so plainly on stderr, which is where stdio
# MCP hosts collect server output.
_warned_401 = False


async def _diagnose_response(response: httpx.Response) -> None:
    """Explain a 401 in terms of what the operator has to do about it."""
    global _warned_401

    if response.status_code != 401 or _warned_401:
        return
    _warned_401 = True

    if RBAC_TOKEN:
        print(
            "ERROR: PE MCP rejected the PE RBAC token (401 Unauthorized).\n"
            "       The token may be expired or lack the required permissions.\n"
            "       Generate a fresh one with: puppet-access login --lifetime 1y",
            file=sys.stderr,
            flush=True,
        )
    else:
        print(
            "ERROR: PE MCP requires authentication (401 Unauthorized) and no\n"
            "       PE_RBAC_TOKEN was provided.\n"
            "       This PE deployment gates the MCP endpoint on PE RBAC, so a\n"
            "       token is required. Generate one with:\n"
            "         puppet-access login --lifetime 1y\n"
            "       then set PE_RBAC_TOKEN to its value. Under PAG, enter it in\n"
            "       the dashboard at /servers/<alias>/secrets.",
            file=sys.stderr,
            flush=True,
        )


def _httpx_client_factory(**kwargs) -> httpx.AsyncClient:
    """Build fastmcp's httpx client, plus the response diagnostic hook.

    Takes **kwargs on purpose: fastmcp passes headers/auth/follow_redirects and
    may add more, and its docs call for **kwargs for forward compatibility.

    Supplying a factory makes fastmcp ignore the transport's `verify`, so the
    CA cert has to be applied here or TLS silently falls back to system CAs.
    """
    kwargs.setdefault("follow_redirects", True)
    if kwargs.get("timeout") is None:
        kwargs["timeout"] = httpx.Timeout(30.0, read=300.0)
    kwargs["verify"] = CA_CERT_PATH

    hooks = dict(kwargs.get("event_hooks") or {})
    hooks["response"] = [*hooks.get("response", []), _diagnose_response]
    kwargs["event_hooks"] = hooks

    return httpx.AsyncClient(**kwargs)


transport = StreamableHttpTransport(
    REMOTE_MCP_URL,
    headers=AUTH_HEADERS,
    httpx_client_factory=_httpx_client_factory,
)
# No verify= here: the factory owns it (see _httpx_client_factory), and passing
# both makes fastmcp warn and drop the verify.
client = Client(transport)
proxy = create_proxy(client, name="PE Thin MCP Proxy")

if __name__ == "__main__":
    proxy.run(transport="stdio")
