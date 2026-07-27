"""Self-check: verify the configured Smart MCP is reachable and responding.

Used by both `entrypoint.sh validate` and CI smoke tests. Performs a real
tools/list handshake against SMART_MCP_URL using PE_CA_CERT for TLS
verification, and reports a clear PASS/FAIL diagnostic.
"""

import asyncio
import os
import sys

from fastmcp import Client


async def check(url, ca_cert):
    client = Client(url, verify=ca_cert)
    async with client:
        tools = await client.list_tools()
    return [t.name for t in tools]


def main():
    url = os.environ.get("SMART_MCP_URL")
    ca_cert = os.environ.get("PE_CA_CERT")

    if not url or url == "https://REPLACE_WITH_MCP_NODE_FQDN/mcp/":
        print("FAIL: SMART_MCP_URL is not configured. Run `setup` first.", file=sys.stderr)
        sys.exit(1)

    if not ca_cert or not os.path.isfile(ca_cert):
        print(f"FAIL: PE CA cert not found at '{ca_cert}'. Run `setup` first.", file=sys.stderr)
        sys.exit(1)

    print(f"Checking Smart MCP at {url} ...", flush=True)
    try:
        tools = asyncio.run(check(url, ca_cert))
    except Exception as exc:
        print(f"FAIL: could not reach or authenticate to the Smart MCP: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"PASS: connected to Smart MCP, {len(tools)} tool(s) available:")
    for name in tools:
        print(f"  - {name}")
    sys.exit(0)


if __name__ == "__main__":
    main()
