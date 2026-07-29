# pe_mcp_docker

A ready-to-run Docker image for the PE MCP **thin client** — the local
stdio↔HTTPS proxy that lets Claude Code (or any MCP client) talk to a
**PE MCP server** already deployed on your Puppet Enterprise
infrastructure. No Python environment or repo checkout required — pull the
image, run a one-time setup, and connect from any directory on your
workstation.

This image is thin-client-only. It does not deploy a PE MCP server —
that's a separate step using the [`puppetlabs-pe_mcp`](https://github.com/puppetlabs/puppetlabs-pe_mcp)
Bolt module. If you don't have one yet, the `setup` wizard below will tell
you exactly how to get one.

## Native install (no Docker)

Not on PyPI yet (pending an internal hosting decision) — install the wheel
directly from the latest GitHub Release instead:

```bash
pip install https://github.com/puppetlabs/pe_mcp_docker/releases/latest/download/pe_mcp_thin-1.0.1-py3-none-any.whl

export PE_MCP_URL='https://<mcp-node-fqdn>/mcp/'
export PE_CA_CERT='/path/to/pe-ca.pem'   # see "Getting the CA cert" below

pe-mcp-thin validate   # self-check
pe-mcp-thin serve      # what Claude Code's MCP config should invoke
```

Once PyPI hosting is available this becomes `pip install pe-mcp-thin` — no
other change to the commands above. `setup`'s interactive `/config`-volume
wizard is Docker-specific; native installs just set the two env vars
directly, same as `docker run -e PE_MCP_URL=... -e PE_CA_CERT=...` below.

## Docker Quickstart

```bash
# Pull (or build locally: docker build -t puppet/pe-mcp-thin .)
docker pull puppet/pe-mcp-thin

# One-time interactive setup — walks you through everything, including
# what to do if you don't have a PE MCP server yet
docker run --rm -it -v ~/.pe-mcp:/config puppet/pe-mcp-thin setup

# Self-check: confirm the connection actually works
docker run --rm -it -v ~/.pe-mcp:/config puppet/pe-mcp-thin validate
```

`setup` first asks whether you already have a PE MCP server deployed:

- **No** — it prints the exact commands to deploy one via
  [`puppetlabs-pe_mcp`](https://github.com/puppetlabs/puppetlabs-pe_mcp#quickstart)
  (`bolt plan run pe_mcp::deploy`), then exits — nothing to configure yet.
- **Yes** — it asks for the PE MCP's URL and its PE CA certificate
  (with instructions on exactly where to get both), then writes them to
  `~/.pe-mcp/` on your host so every future container run picks them up
  automatically.

## Connecting Claude Code

Once `setup`/`validate` succeed, wire it into your MCP config (project
`.mcp.json`, or Claude Code's user-level config so it works from *any*
directory — not just one project):

```json
{
  "mcpServers": {
    "pe-mcp": {
      "type": "stdio",
      "command": "docker",
      "args": ["run", "--rm", "-i", "-v", "~/.pe-mcp:/config", "puppet/pe-mcp-thin:latest"]
    }
  }
}
```

Restart Claude Code and check the `/mcp` panel — `pe-mcp` should show connected.

Or, using the native install instead of Docker:

```json
{
  "mcpServers": {
    "pe-mcp": {
      "type": "stdio",
      "command": "pe-mcp-thin",
      "args": ["serve"],
      "env": {
        "PE_MCP_URL": "https://<mcp-node-fqdn>/mcp/",
        "PE_CA_CERT": "/path/to/pe-ca.pem"
      }
    }
  }
}
```

## Commands

| Command | Interactive? | Purpose |
|---|---|---|
| `setup` | Yes | One-time wizard: deploy-first coaching, or collect PE MCP URL + CA cert and persist them to `/config` |
| `validate` | No (but human-readable) | Self-check: real `tools/list` handshake against the configured PE MCP; reports PASS with discovered tools, or a clear FAIL diagnostic |
| `serve` (default) | No | Runs the actual stdio MCP proxy — what Claude Code invokes. Fails fast to stderr (never prompts) if not configured, so the stdout MCP protocol stream is never corrupted |

All three read config from `/config/config.env` + `/config/pe-ca.pem` (written by `setup`), or you can skip the mounted volume entirely and pass `-e PE_MCP_URL=... -e PE_CA_CERT=/path/to/mounted/cert.pem` directly on `docker run`.

## Troubleshooting

- **"PE_MCP_URL is not configured"** — you haven't run `setup` yet, or the mounted `/config` volume doesn't match what you used during setup. Re-run `setup`.
- **"could not reach or authenticate to the PE MCP"** (from `validate`) — check the PE MCP URL is correct and reachable, and that the CA cert matches the certificate your PE MCP's nginx actually presents (it's signed by your PE CA, not a public one — see below).
- **Don't have a PE MCP server yet?** See [`puppetlabs-pe_mcp`](https://github.com/puppetlabs/puppetlabs-pe_mcp#quickstart) — deploy one with `bolt plan run pe_mcp::deploy`, then come back and run `setup` here.
- **Getting the CA cert**: on any PE-enrolled node (the primary, or the MCP node itself):
  ```bash
  cat /etc/puppetlabs/puppet/ssl/certs/ca.pem
  ```

## License

Apache-2.0
