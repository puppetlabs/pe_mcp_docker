"""Self-check: verify the configured PE MCP is reachable and responding.

Used by both `entrypoint.sh validate` and CI smoke tests. Performs a real
tools/list handshake against PE_MCP_URL using PE_CA_CERT for TLS
verification, and reports a clear PASS/FAIL diagnostic.
"""

import asyncio
import os
import sys

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


async def check(url, ca_cert, rbac_token):
    # An empty/unset token means the deployment doesn't gate on RBAC — send no
    # header rather than an empty one.
    headers = {"X-Authentication": rbac_token} if rbac_token else {}
    client = Client(StreamableHttpTransport(url, headers=headers), verify=ca_cert)
    async with client:
        tools = await client.list_tools()
    return [t.name for t in tools]


def main():
    # Normalized the same way proxy.py does — see the note there on why a
    # trailing slash 404s after auth rather than failing visibly.
    url = os.environ.get("PE_MCP_URL", "").strip().rstrip("/")
    ca_cert = os.environ.get("PE_CA_CERT", "").strip()
    rbac_token = os.environ.get("PE_RBAC_TOKEN", "").strip()

    if not url or url == "https://REPLACE_WITH_MCP_NODE_FQDN/mcp":
        print("FAIL: PE_MCP_URL is not configured. Run `setup` first.", file=sys.stderr)
        sys.exit(1)

    if not ca_cert or not os.path.isfile(ca_cert):
        print(f"FAIL: PE CA cert not found at '{ca_cert}'. Run `setup` first.", file=sys.stderr)
        sys.exit(1)

    # No PE_RBAC_TOKEN check here on purpose: deployments that don't gate on
    # RBAC need no token, so let the server's actual response decide.
    auth_desc = "with RBAC token" if rbac_token else "without RBAC token"
    print(f"Checking PE MCP at {url} ({auth_desc}) ...", flush=True)
    try:
        tools = asyncio.run(check(url, ca_cert, rbac_token))
    except Exception as exc:
        print(f"FAIL: could not reach or authenticate to the PE MCP: {exc}", file=sys.stderr)
        # Prefer the real status code when the exception carries one (e.g.
        # httpx.HTTPStatusError) — substring-matching the message is a fallback
        # for exceptions that don't, not the primary signal.
        status_code = getattr(getattr(exc, "response", None), "status_code", None)
        is_404 = status_code == 404 or (status_code is None and "404" in str(exc))
        is_401 = status_code == 401 or (status_code is None and "401" in str(exc))
        if is_404:
            print(
                "HINT: the endpoint was reached but the path was not found. PE "
                "serves the MCP at https://<mcp-node-fqdn>/mcp — check the path "
                f"in PE_MCP_URL (currently {url}).",
                file=sys.stderr,
            )
        elif is_401 and not rbac_token:
            print(
                "HINT: this PE MCP requires authentication but no PE_RBAC_TOKEN "
                "was supplied. Generate one with `puppet-access login` and set "
                "PE_RBAC_TOKEN (or re-run `setup`).",
                file=sys.stderr,
            )
        elif is_401:
            print(
                "HINT: the PE RBAC token was rejected. It may be expired — "
                "regenerate with `puppet-access login`.",
                file=sys.stderr,
            )
        sys.exit(1)

    print(f"PASS: connected to PE MCP, {len(tools)} tool(s) available:")
    for name in tools:
        print(f"  - {name}")
    sys.exit(0)


if __name__ == "__main__":
    main()
