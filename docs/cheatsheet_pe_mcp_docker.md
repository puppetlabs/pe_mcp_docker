# pe_mcp_docker

Copy-paste commands for running, validating, and troubleshooting `pe-mcp-thin` against either PE MCP target — see [`../README.md`](../README.md) for setup and the target overview this reference assumes.

## Quick Reference

| Task | Command / Pattern |
| --- | --- |
| Validate, no install (uvx) | `PE_MCP_URL=... PE_CA_CERT=... uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@main pe-mcp-thin validate` |
| Validate against an RBAC-gated MCP (e.g. `pe-infra-assistant`) | same, plus `PE_RBAC_TOKEN=...` — forwarded as `X-Authentication` |
| Get a PE RBAC token | `puppet-access login --lifetime 1y && cat ~/.puppetlabs/token` |
| Get the PE CA cert (on a PE-enrolled node) | `cat /etc/puppetlabs/puppet/ssl/certs/ca.pem` |
| Get the PE CA cert (remote, no node access) | `curl -k "https://<pe-primary-fqdn>:8140/puppet-ca/v1/certificate/ca" -o pe-ca.pem` |
| Build the Docker image locally | `docker build -t pe-mcp-thin:local .` |
| Cut a release | see [`howto_pe_mcp_docker_release.md`](howto_pe_mcp_docker_release.md) |

## Install & run — all three ways, verified

> 📖 **Deeper dive:** [`explanation_why_pe_mcp_thin_is_a_proxy_not_a_direct_client.md`](explanation_why_pe_mcp_thin_is_a_proxy_not_a_direct_client.md)

### uvx (fastest, no install)

```bash
export PE_MCP_URL="https://<mcp-node-fqdn>/mcp"
export PE_CA_CERT="/path/to/pe-ca.pem"
export PE_RBAC_TOKEN="LONG_LONG_RBAC_TOKEN"

uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@main pe-mcp-thin validate   # verified 2026-08-07 on raw-millennium: PASS, 10 tool(s)
uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@main pe-mcp-thin serve      # verified 2026-08-07 on raw-millennium: FastMCP stdio server starts
```

### pip install

```bash
pip install https://github.com/puppetlabs/pe_mcp_docker/releases/latest/download/pe_mcp_thin-1.0.1-py3-none-any.whl   # verified 2026-08-07 in clean venv

export PE_MCP_URL="https://<mcp-node-fqdn>/mcp"
export PE_CA_CERT="/path/to/pe-ca.pem"
export PE_RBAC_TOKEN="LONG_LONG_RBAC_TOKEN"

pe-mcp-thin validate   # verified 2026-08-07 on raw-millennium: PASS
```

### Docker (local build — not yet published to Docker Hub)

```bash
git clone https://github.com/puppetlabs/pe_mcp_docker.git
cd pe_mcp_docker
docker build -t pe-mcp-thin:local .                                                            # verified 2026-08-07: builds clean

# direct env vars — no /config volume needed for a one-off check
docker run --rm \
  -e PE_MCP_URL="https://<mcp-node-fqdn>/mcp" \
  -e PE_CA_CERT=/pe-ca.pem \
  -e PE_RBAC_TOKEN="LONG_LONG_RBAC_TOKEN" \
  -v /path/to/pe-ca.pem:/pe-ca.pem:ro \
  pe-mcp-thin:local validate                                                                   # verified 2026-08-07 on raw-millennium: PASS
```

Persistent alternative — the interactive `setup` wizard, if you'd rather configure once and reuse a mounted volume instead of passing `-e` flags every time:

```bash
docker run --rm -it -v ~/.pe-mcp:/config pe-mcp-thin:local setup   # walks through: server deployed? → PE MCP URL → CA cert (paste PEM or mount at /import/pe-ca.pem:ro) → RBAC token (optional) → writes /config/config.env + /config/pe-ca.pem + /config/rbac-token (mode 0600, only if a token was entered)
docker run --rm -it -v ~/.pe-mcp:/config pe-mcp-thin:local validate
docker run --rm -i  -v ~/.pe-mcp:/config pe-mcp-thin:local        # serve (default command)
```

The token file is deliberately kept out of `config.env` (which is `source`-parsed only as text, never executed) and stored mode 0600. Re-running `setup` with a blank token clears any prior file, so "blank" reliably means "no token". An explicit `-e PE_RBAC_TOKEN=...` at `docker run` time still overrides whatever is in the volume.

## Legacy MCP (`pe-infra-assistant`) — PE_RBAC_TOKEN is required

Where nginx in front of the PE MCP gates on PE RBAC, the token goes on the wire in the `X-Authentication` header. Without it every request comes back **401 Unauthorized**. Get one with `puppet-access login --lifetime 1y && cat ~/.puppetlabs/token`, then:

```bash
export PE_MCP_URL="https://<pe-infra-assistant-fqdn>/mcp"
export PE_CA_CERT="/path/to/pe-ca.pem"
export PE_RBAC_TOKEN="$(cat ~/.puppetlabs/token)"

pe-mcp-thin validate                                          # expect PASS with the token; without it, expect 401 + a hint
```

A missing / expired token surfaces as a `selftest.py` diagnostic pointing at the fix (regenerate with `puppet-access login`; under PAG, enter it at `/servers/<alias>/secrets`) — not a raw stack trace.

## Decoupled MCP — regression-check that PE_RBAC_TOKEN is ignored

Three cases, not two — absent, invalid, and a well-formed-but-fake value — since the decoupled target should be completely indifferent to `PE_RBAC_TOKEN`:

```bash
export PE_MCP_URL="https://<decoupled-mcp-node-fqdn>/mcp"
export PE_CA_CERT="/path/to/pe-ca.pem"

unset PE_RBAC_TOKEN
pe-mcp-thin validate                                          # baseline — must PASS

export PE_RBAC_TOKEN="clearly-not-a-real-token"
pe-mcp-thin validate                                          # invalid — must still PASS, identical tool list

export PE_RBAC_TOKEN="00000000000000000000000000000000"
pe-mcp-thin validate                                          # well-formed fake — must still PASS
unset PE_RBAC_TOKEN
```

All three: expect `PASS: connected to PE MCP, N tool(s) available` with an identical tool list every time.
