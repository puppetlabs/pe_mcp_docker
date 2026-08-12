# PAG testing

## Description

This directory provides a way to over-ride the PAG (Perforce Agentic Gateway) registry.  This approach is necessary when validating changes to the PE MCP registry entry.  The current registry json is `docs/pag-testing/internal/catalog/servers/pe-mcp-thin/server.json`

## Quick Start

First,

* Update `docs/pag-testing/pag-quickstart-mcp-legacy/.pag/config.local.toml` and `docs/pag-testing/pag-quickstart-mcp-new/.pag/config.local.toml` to have a full path reference to the `server.json`.
* Save the PE's CA cert somewhere local, e.g., `pe-ca.pem`
* Obtain a valid RBAC token from your PE and store it safely.

Then,

* cd to `docs/pag-testing/pag-quickstart-mcp-legacy` and start up a claude session.  Ask claude: "open the PAG catalog in my browser".  This will open a page from which you can enter the 3 environment variables.  For example:

```bash
export PE_MCP_URL=https://dread-candour.delivery.puppetlabs.net/mcp
export PE_CA_CERT=certs/pe-ca.pem
export PE_RBAC_TOKEN=<LONG_LONG_RBAC_TOKEN>
```

* "Enable" these settings and then go back to your claude session and ask: "Lis
t all the tools for the pe-mcp-thin server"
