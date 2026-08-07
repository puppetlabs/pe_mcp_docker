# pe-mcp-thin operational reference

Copy-paste commands for running, validating, and troubleshooting the thin
client against either PE MCP target. See [README.md](README.md) for setup
and the target overview this reference assumes.

## Quick Reference

| Task | Command / Pattern |
|---|---|
| Validate against the decoupled MCP | `PE_MCP_URL=... PE_CA_CERT=... pe-mcp-thin validate` |
| Validate against `pe-infra-assistant` | same, plus `PE_RBAC_TOKEN=...` |
| Get a PE RBAC token | `puppet-access login --lifetime 1y && cat ~/.puppetlabs/token` |
| Get the PE CA cert | `cat /etc/puppetlabs/puppet/ssl/certs/ca.pem` (on any PE-enrolled node) |

## Decoupled MCP — regression-check that PE_RBAC_TOKEN is ignored

Three cases, not two — absent, invalid, and a well-formed-but-fake value —
since this target should be completely indifferent to `PE_RBAC_TOKEN`:

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

All three: expect `PASS: connected to PE MCP, N tool(s) available` with an
identical tool list every time.

## `pe-infra-assistant` — token generation and connection

```bash
# generate a token; the RBAC user needs infrastructure_assistant:use:*
puppet-access login --lifetime 1y
export PE_RBAC_TOKEN="$(cat ~/.puppetlabs/token)"

export PE_MCP_URL="https://<pe-primary-fqdn>/mcp"   # NO trailing slash
export PE_CA_CERT="/path/to/pe-ca.pem"

# without a token — expect a clear, actionable failure, not a generic 401
unset PE_RBAC_TOKEN
pe-mcp-thin validate
# expect: "requires authentication but no PE_RBAC_TOKEN was provided"

# with a real token — expect PASS and infra-assistant's own 5 tools
export PE_RBAC_TOKEN="<token from above>"
pe-mcp-thin validate
# expect: PASS, tools include get_device_info, get_edgeops_docs,
#         get_puppet_guide, list_puppet_entities, get_puppet_entity_docs
```

## Gotchas

- **`X-Authentication` is the header name**, not the more common `Authorization: Bearer`. `pe-infra-assistant` (and PE's other RBAC-gated services) expect the raw token in `X-Authentication`; this thin client handles that for you, but it matters if you're cross-checking against raw `curl`.
- **`PE_MCP_URL` must have no trailing slash.** A trailing slash is rewritten upstream to `/infra-assistant/mcp/` and 404s *after* the RBAC check passes, producing an opaque "Session terminated" instead of a clear diagnostic.
- **`PE_RBAC_TOKEN` is read-and-ignored for the decoupled MCP**, not validated against it — an absent, invalid, or fake value all behave identically. Only `pe-infra-assistant` actually checks it.
- **A 401 during the handshake** triggers an actionable stderr message naming whether a token was missing or is likely expired/rejected — read it before re-running with a fresh token.

## Related Topics

- [README.md](README.md) — setup, target overview, `mcpServers` config examples
- [`puppetlabs-pe_mcp`](https://github.com/puppetlabs/puppetlabs-pe_mcp) — deploys the decoupled MCP target
- [PE Enabling the MCP server](https://help.puppet.com/pe/current/topics/enabling-the-mcp-server.htm) — `pe-infra-assistant`'s own prerequisites (PE 2025.11+, license entitlement, classification)
