# pe-mcp-thin

This repository is a small, standalone stdio↔HTTPS proxy that lets **any MCP client** (claude, copilot, cursor, etc) talk to a existing **PE MCP server** already deployed on your Puppet Enterprise infrastructure.

If you don't have **an existing PE MCP**, then choose one of the following:
* The **New** MCP:  This one will work on any PE installation.  For more information see the [`puppetlabs-pe_mcp`](https://github.com/puppetlabs/puppetlabs-pe_mcp#quickstart) Bolt module; or
* The **Legacy** MCP: This one is only present on PE installations >= 2025.11.  For more information see 

## Quickstart (fastest — no install)

The `uvx` command below is the fastest path and needs nothing persistent and requires * [`uv`](https://docs.astral.sh/uv/getting-started/installation/).

If you'd rather not depend on `uv` , they you can also use `pip` and `docker`.  For more information see the [[shared_repositories/pe_mcp-private/repositories/pe_mcp_docker/CHEATSHEET|CHEATSHEET]]
### (1) Get the CA cert

In order to connect to the MCP, this thin client must load the certificate authority CA that signed your MCP server's certificate.  

If your PE ecosystem uses the self-signed CA on the primary, then it's easy, do the following:

```bash
# create a 'certs' directory, e.g.,
mkdir -p certs

# download the primary's CA (-k is required for this fetch because you don't have 
# the cert to verify against itself yet).  If you have access to the primary directly
# via ssh, then this cert lives here: /etc/puppetlabs/puppet/ssl/certs/ca.pem
curl -k "https://<pe-primary-fqdn>:8140/puppet-ca/v1/certificate/ca" -o certs/pe-ca.pem
```

If, however, your PE ecosystem browser certificates are signed by another authority (a company one, for example), then download this CA instead.  

Remember the path to this cert because you'll need it in step **(3)**.

### (2) Get a valid RBAC token

There are a number of ways to get an RBAC token.  One is to log onto the PE console and follow [these instructions](https://help.puppet.com/pe/2025.11/topics/rbac-token-auth-generate-token-console.htm)  Save this token securely somewhere because you'll need this in step **(3)**.

### (3) Validate your connection to the MCP

This step assumes you have the path to your CA cert from (1) and a valid RBAC token (2)

```bash
export PE_CA_CERT="$(pwd)/certs/pe-ca.pem"         # set this to the path of the cert downloaded above
export PE_MCP_URL="https://<mcp-node-fqdn>/mcp"    # NOTE: no trailing slash!
export PE_RBAC_TOKEN="..."                         # only if pointed at pe-infra-assistant, see below

# self-check: confirms the connection works before wiring up a client
uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@main pe-mcp-thin validate
```

Expect:

```
Checking PE MCP at https://<mcp-node-fqdn>/mcp ...
PASS: connected to PE MCP, 10 tool(s) available:
  - puppet_node_lookup
  - puppet_pql_query
  ...
```

Once that passes, point your MCP client at the exact same command with `serve` instead of `validate` — see [Connecting an MCP client](#connecting-an-mcp-client-any-client) below.

### (4) Connect your provider

The following is a standard stdio MCP server configuration that spins up the `pe-mcp-thin` via `uvx` and should work with any MCP supported tool.

```json
{
  "mcpServers": {
    "pe-mcp-thin": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/puppetlabs/pe_mcp_docker.git@main",
        "pe-mcp-thin",
        "serve"
      ],
      "env": {
        "PE_MCP_URL": "https://<mcp-node-fqdn>/mcp",
        "PE_CA_CERT": "/path/to/pe-ca.pem",
        "PE_RBAC_TOKEN": "..."
      }
    }
  }
}
```

Claude is one of many available providers and will be used in a worked example below:
* Copy the above block and paste it into either `~/.mcp.json` for every project or into a `.mcp.json` for one specific project.
* Restart claude and confirm that the `pe-mcp-thin` server is connected.

| Client | Where to configure |
| --- | --- |
| Claude Code | `~/.mcp.json` (all projects), or a project-root `.mcp.json` (that project only) — see [Claude Code MCP docs](https://docs.claude.com/en/docs/claude-code/mcp) |
| GitHub Copilot | see [Copilot MCP docs](https://docs.github.com/en/copilot/how-tos/context/model-context-protocol/extend-copilot-chat-with-mcp) |
| Any other MCP-compatible client | consult that client's own MCP server configuration docs — the JSON shape above is standard |

After wiring it in, restart your client and confirm `pe-mcp` shows connected.
