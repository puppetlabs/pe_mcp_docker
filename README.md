# pe-mcp-thin

A small, standalone stdio↔HTTPS proxy that lets **any MCP client** — Claude
Code, GitHub Copilot, Cursor, or anything else that speaks MCP — talk to a
**PE MCP server** already deployed on your Puppet Enterprise infrastructure.

- **No PAG required.** This runs entirely on its own; PAG is one *optional*
  way to distribute and configure it, not a dependency.
- **No specific client required.** It's a normal stdio MCP server —
  wire it into whatever MCP client you use the same way you'd wire in any
  other stdio MCP server.
- **No persistent install required.** The fastest way to run it needs
  nothing on disk beyond `uv`'s own cache — see Quickstart below.

This is thin-client-only: it does not deploy a PE MCP server itself. If you
don't have one yet, see [Deploying a PE MCP server](#deploying-a-pe-mcp-server-if-you-dont-have-one-yet) below.

> **Need more than setup?** This README is deliberately just a quickstart.
> For every command, both PE MCP targets, and troubleshooting output to
> compare your own against, see [CHEATSHEET.md](CHEATSHEET.md). For how this
> proxy actually works, see [docs/explanation_architecture.md](docs/explanation_architecture.md).

## Quickstart (fastest — no install)

Requires [`uv`](https://docs.astral.sh/uv/getting-started/installation/).
This is the same mechanism PAG's registry entry uses to run this server —
if it works here, it'll work there too.

```bash
export PE_MCP_URL="https://<mcp-node-fqdn>/mcp"    # NO trailing slash
export PE_CA_CERT="/path/to/pe-ca.pem"              # see "Getting the CA cert" below

# self-check: confirms the connection works before wiring up a client
uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@v1.0.1 pe-mcp-thin validate
```

Expect:

```
Checking PE MCP at https://<mcp-node-fqdn>/mcp ...
PASS: connected to PE MCP, 10 tool(s) available:
  - puppet_node_lookup
  - puppet_pql_query
  ...
```

Once that passes, point your MCP client at the exact same command with
`serve` instead of `validate` — see [Connecting an MCP client](#connecting-an-mcp-client-any-client) below.

## Getting the CA cert

Your PE MCP's nginx presents a certificate signed by your PE Certificate
Authority, not a public one — this client needs to trust it explicitly. On
any PE-enrolled node (the primary, or the MCP node itself):

```bash
cat /etc/puppetlabs/puppet/ssl/certs/ca.pem
```

Save that output locally as `pe-ca.pem` and point `PE_CA_CERT` at it.

## Other ways to run this

The `uvx` command above is the fastest path and needs nothing persistent.
Two alternatives, if you'd rather not depend on `uv`:

<details>
<summary><strong>pip install</strong> (not on PyPI yet — installs the GitHub Release wheel directly)</summary>

```bash
pip install https://github.com/puppetlabs/pe_mcp_docker/releases/latest/download/pe_mcp_thin-1.0.1-py3-none-any.whl

export PE_MCP_URL="https://<mcp-node-fqdn>/mcp"
export PE_CA_CERT="/path/to/pe-ca.pem"

pe-mcp-thin validate
pe-mcp-thin serve
```

Once PyPI hosting is available this becomes `pip install pe-mcp-thin` — no
other change to the commands above.
</details>

<details>
<summary><strong>Docker</strong> (build locally — <code>puppet/pe-mcp-thin</code> is not yet published to Docker Hub)</summary>

Publishing to Docker Hub is on the roadmap (the `image-push.yml` CI job
exists for when it happens) but hasn't shipped yet — build the image
yourself for now:

```bash
git clone https://github.com/puppetlabs/pe_mcp_docker.git
cd pe_mcp_docker
docker build -t pe-mcp-thin:local .

docker run --rm \
  -e PE_MCP_URL="https://<mcp-node-fqdn>/mcp" \
  -e PE_CA_CERT=/pe-ca.pem \
  -v /path/to/pe-ca.pem:/pe-ca.pem:ro \
  pe-mcp-thin:local validate
```

There's also an interactive `setup` wizard (`docker run --rm -it -v ~/.pe-mcp:/config pe-mcp-thin:local setup`)
that walks you through both env vars and persists them to a mounted
`/config` volume instead of passing `-e` flags every time — see
[CHEATSHEET.md](CHEATSHEET.md) for the full walkthrough.
</details>

## Connecting an MCP client (any client)

This is a standard stdio MCP server — the same `command`/`args`/`env` shape
works in any MCP client's configuration, you're just pointing at
`pe-mcp-thin serve` (or the Docker/uvx equivalent) instead of some other
server binary:

```json
{
  "mcpServers": {
    "pe-mcp": {
      "type": "stdio",
      "command": "uvx",
      "args": ["--from", "git+https://github.com/puppetlabs/pe_mcp_docker.git@v1.0.1", "pe-mcp-thin", "serve"],
      "env": {
        "PE_MCP_URL": "https://<mcp-node-fqdn>/mcp",
        "PE_CA_CERT": "/path/to/pe-ca.pem"
      }
    }
  }
}
```

Where that JSON goes depends on your client — this isn't a Claude-specific
tool, so consult your client's own MCP docs for the exact file/location:

| Client | Where to configure |
|---|---|
| Claude Code | project `.mcp.json`, or the user-level config for all projects — see [Claude Code MCP docs](https://docs.claude.com/en/docs/claude-code/mcp) |
| GitHub Copilot | see [Copilot MCP docs](https://docs.github.com/en/copilot/how-tos/context/model-context-protocol/extend-copilot-chat-with-mcp) |
| Any other MCP-compatible client | consult that client's own MCP server configuration docs — the JSON shape above is standard |

After wiring it in, restart your client and confirm `pe-mcp` shows connected.

## Which PE MCP target am I connecting to?

This client can reach either of two different servers behind the same env
vars — which one changes whether `PE_RBAC_TOKEN` is needed:

| Target | What it is | `PE_RBAC_TOKEN` |
|---|---|---|
| **Decoupled PE MCP** (`puppetlabs-pe_mcp`) | A standalone, read-only MCP deployed via the [`puppetlabs-pe_mcp`](https://github.com/puppetlabs/puppetlabs-pe_mcp) Bolt module | Not needed — ignored if set |
| **`pe-infra-assistant`** (built into PE console-services, PE 2025.11+) | The older MCP embedded in Puppet Enterprise itself | **Required** — every request 401s without it |

Full walkthrough for the `pe-infra-assistant` target (token generation, PE-side
prerequisites) is in [CHEATSHEET.md](CHEATSHEET.md#pe-infra-assistant--token-generation-and-connection).

## Deploying a PE MCP server (if you don't have one yet)

That's a separate, one-time step using the [`puppetlabs-pe_mcp`](https://github.com/puppetlabs/puppetlabs-pe_mcp#quickstart)
Bolt module — this repo only builds the client that connects to it:

```bash
git clone https://github.com/puppetlabs/puppetlabs-pe_mcp.git
cd puppetlabs-pe_mcp && bolt module install
cp inventory.yaml.example inventory.yaml   # fill in your primary + target node
export PE_ADMIN_PASSWORD='...'
bolt plan run pe_mcp::deploy -i inventory.yaml primary=<pe-primary> targets=<mcp-node>
```

## Commands

| Command | Purpose |
|---|---|
| `validate` | Self-check: a real `tools/list` handshake against the configured PE MCP. Reports PASS with discovered tools, or a clear FAIL diagnostic. |
| `serve` (default) | Runs the actual stdio MCP proxy — what your MCP client invokes. Fails fast to stderr (never prompts) if not configured, so the stdout MCP protocol stream is never corrupted. |
| `setup` (Docker only) | Interactive wizard: collects `PE_MCP_URL` + the CA cert and persists them to a mounted `/config` volume. |

## Troubleshooting

See [CHEATSHEET.md](CHEATSHEET.md#gotchas) for the full list with verified
error text. The short version:

- **"PE_MCP_URL is not configured"** — the env var isn't set (or, for Docker's `setup` flow, doesn't match the mounted `/config` volume).
- **"requires authentication but no PE_RBAC_TOKEN was supplied"** — you're pointed at `pe-infra-assistant` without a token. See [Which PE MCP target](#which-pe-mcp-target-am-i-connecting-to) above.
- **`PE_MCP_URL` with a trailing slash** — gets rewritten upstream and 404s after auth passes. Always omit the trailing slash.

## License

Apache-2.0
