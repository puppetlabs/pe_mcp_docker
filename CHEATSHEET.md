# pe-mcp-thin operational reference

Copy-paste commands for running, validating, and troubleshooting the thin client against either PE MCP target. See [README.md](README.md) for setup and the target overview this reference assumes.

## Quick Reference

| Task | Command / Pattern |
| --- | --- |
| Validate, no install (uvx) | `PE_MCP_URL=... PE_CA_CERT=... uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@v1.0.1 pe-mcp-thin validate` |
| Validate against `pe-infra-assistant` | same, plus `PE_RBAC_TOKEN=...` |
| Get a PE RBAC token | `puppet-access login --lifetime 1y && cat ~/.puppetlabs/token` |
| Get the PE CA cert (on a PE-enrolled node) | `cat /etc/puppetlabs/puppet/ssl/certs/ca.pem` |
| Get the PE CA cert (remote, no node access) | `curl -k "https://<pe-primary-fqdn>:8140/puppet-ca/v1/certificate/ca" -o pe-ca.pem` |
| Build the Docker image locally | `docker build -t pe-mcp-thin:local .` |

## Install & run — all three ways, verified

### uvx (fastest, no install)

```bash
export PE_MCP_URL="https://<mcp-node-fqdn>/mcp"
export PE_CA_CERT="/path/to/pe-ca.pem"

uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@v1.0.1 pe-mcp-thin validate
uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@v1.0.1 pe-mcp-thin serve
```

**Verified 2026-08-07 against a live decoupled MCP (`raw-millennium`):** both `validate` and `serve` work exactly as above — `validate` returns `PASS: connected to PE MCP, 10 tool(s) available`; `serve` starts the FastMCP stdio server and prints its startup banner. This is the same `uvx --from git+...` pattern PAG's own registry entry uses — proving it here proves it works there too.

### pip install

```bash
pip install https://github.com/puppetlabs/pe_mcp_docker/releases/latest/download/pe_mcp_thin-1.0.1-py3-none-any.whl

export PE_MCP_URL="https://<mcp-node-fqdn>/mcp"
export PE_CA_CERT="/path/to/pe-ca.pem"

pe-mcp-thin validate
```

**Verified 2026-08-07** in a clean virtualenv against the same live decoupled MCP — installs cleanly, `pe-mcp-thin` resolves on `PATH`, `validate` PASSes.

### Docker (local build — not yet published to Docker Hub)

```bash
git clone https://github.com/puppetlabs/pe_mcp_docker.git
cd pe_mcp_docker
docker build -t pe-mcp-thin:local .

# direct env vars — no /config volume needed for a one-off check
docker run --rm \
  -e PE_MCP_URL="https://<mcp-node-fqdn>/mcp" \
  -e PE_CA_CERT=/pe-ca.pem \
  -v /path/to/pe-ca.pem:/pe-ca.pem:ro \
  pe-mcp-thin:local validate
```

**Verified 2026-08-07** — `docker build` succeeds, and `validate` PASSes against the same live decoupled MCP as above.

**Persistent alternative — the interactive `setup` wizard**, if you'd rather configure once and reuse a mounted volume instead of passing `-e` flags every time:

```bash
docker run --rm -it -v ~/.pe-mcp:/config pe-mcp-thin:local setup
# walks through: do you have a server deployed? -> PE MCP URL -> CA cert
# (paste PEM, or mount one at /import/pe-ca.pem:ro) -> writes
# /config/config.env + /config/pe-ca.pem

docker run --rm -it -v ~/.pe-mcp:/config pe-mcp-thin:local validate
docker run --rm -i  -v ~/.pe-mcp:/config pe-mcp-thin:local        # serve (default command)
```

`setup` only exists in the Docker image — native `uvx`/`pip` installs set `PE_MCP_URL`/`PE_CA_CERT` directly instead, as shown above.

**Why isn't the image on Docker Hub yet?** Intentional — publishing is on the roadmap (the `image-push.yml` CI job exists, triggered on `v*` tags) but hasn't been turned on yet. Build locally per above until it is.

## Decoupled MCP — regression-check that PE_RBAC_TOKEN is ignored

Three cases, not two — absent, invalid, and a well-formed-but-fake value — since this target should be completely indifferent to `PE_RBAC_TOKEN`:

```bash
export PE_MCP_URL="https://<decoupled-mcp-node-fqdn>/mcp"
export PE_CA_CERT="/path/to/pe-ca.pem"

unset PE_RBAC_TOKEN
pe-mcp-thin validate   # baseline — must PASS

export PE_RBAC_TOKEN="clearly-not-a-real-token"
pe-mcp-thin validate   # invalid — must still PASS, identical tool list

export PE_RBAC_TOKEN="00000000000000000000000000000000"
pe-mcp-thin validate   # well-formed fake — must still PASS
unset PE_RBAC_TOKEN
```

All three: expect `PASS: connected to PE MCP, N tool(s) available` with an identical tool list every time.
