"""Thin MCP proxy — local stdio server forwarding to remote PE MCP over HTTPS.

Runs as a stdio MCP server for Claude Code. Connects to the PE MCP
behind the nginx reverse proxy, using the PE CA certificate for TLS
verification.
"""

import os
from pathlib import Path

from fastmcp import Client
from fastmcp.server import create_proxy

DEFAULT_CA_CERT = Path("/config/pe-ca.pem")

REMOTE_MCP_URL = os.environ.get(
    "PE_MCP_URL",
    "https://REPLACE_WITH_MCP_NODE_FQDN/mcp/",
)
CA_CERT_PATH = os.environ.get("PE_CA_CERT", str(DEFAULT_CA_CERT))

client = Client(REMOTE_MCP_URL, verify=CA_CERT_PATH)
proxy = create_proxy(client, name="PE Thin MCP Proxy")

if __name__ == "__main__":
    proxy.run(transport="stdio")
