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

## Troubleshooting

### TLS Hostname mismatch against the Legacy MCP (`console-cert` missing FQDN SAN)

**Symptom** — `pe-mcp-thin validate` against the Legacy MCP (the `/mcp` endpoint served by the PE console vhost) fails with:

```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch,
certificate is not valid for '<pe-primary-fqdn>'.
```

**Why** — the Legacy MCP's `/mcp` path is a `location` block inside the same nginx vhost as the PE console (`/etc/puppetlabs/nginx/conf.d/infra_assistant_mcp.inc`). That vhost presents PE's `console-cert`, which PE generates with a **single hardcoded SAN** (`puppet_enterprise::console_host`) — not the multi-SAN `dns_alt_names` set for the primary's own agent cert. If `console_host` is set to the short hostname, the FQDN isn't a SAN, and any TLS client verifying against the FQDN fails hostname verification. This is not a `pe-mcp-thin` bug — `pe-mcp-thin` deliberately has no way to bypass hostname verification.

**Diagnose** — check the actual SANs on `console-cert` (from your workstation, no PE access needed):

```bash
openssl s_client -connect <pe-primary-fqdn>:443 -servername <pe-primary-fqdn> 2>/dev/null \
  | openssl x509 -noout -subject -ext subjectAltName
# subject=CN=console-cert
# X509v3 Subject Alternative Name:
#     DNS:<short-hostname>, DNS:console-cert
# If the FQDN is missing from that DNS list, you have this gotcha.
```

**Fix** — regenerate `console-cert` on the primary with the FQDN added as a SAN. Requires PE primary access (root/sudo); the thin client cannot work around this from the client side.

```bash
# on the PE primary, as root:

# 1. clean/revoke the old console-cert
puppetserver ca clean --certname console-cert

# 2. remove the on-disk PEM/public-key artifacts too — otherwise `ca generate`
#    errors out with "Existing entry found for certname console-cert"
rm -f /etc/puppetlabs/puppet/ssl/certs/console-cert.pem
rm -f /etc/puppetlabs/puppet/ssl/public_keys/console-cert.pem

# 3. regenerate with the FQDN added alongside the two SANs PE would set by default
#    (keep the short hostname + console-cert so nothing else that trusts them breaks)
puppetserver ca generate \
    --certname console-cert \
    --subject-alt-names <short-hostname>,console-cert,<pe-primary-fqdn>

# 4. apply — this is what actually copies the new cert into the console-services
#    data dir and cascades pe-console-services / pe-nginx restarts via PE's own
#    file{} / notify wiring (no manual systemctl restart needed).
puppet agent -t

# 5. confirm the new SAN list contains the FQDN
openssl x509 -in /etc/puppetlabs/puppet/ssl/certs/console-cert.pem -noout -ext subjectAltName
```

Then, from the workstation, re-run `pe-mcp-thin validate` against the FQDN — it should now pass. Also load the PE console in a browser as a regression check (that vhost is shared).

**HA/DR caveat (PE-44605)** — on a CA-DB-backend / HA topology, `console-cert` is pglogical-replicated to the replica's CA DB, and PE's own promotion logic will re-fire the `ca generate` step using only `console_host` on failover. A manually-added FQDN SAN will be **dropped** on promotion and needs re-applying. File-based CA topologies (the default) are unaffected.

**Won't-work shortcuts** —

- `--ca-client --force`: this flag is for regenerating an identity `pe-puppetserver` itself uses as a client (e.g. the primary's own agent cert) and requires stopping `pe-puppetserver` first. `console-cert` is not that identity; don't pass this flag or you'll be forced into an unnecessary service stop.
- `peadm::modify_certificate`: PEADM's cert-regen plan operates on a node's own agent certname, not on `console-cert` — this is not a shortcut.
- `PE_CA_CERT=<some-other-ca>` or editing the CA bundle: irrelevant. This is a hostname-verification failure, not a chain-of-trust failure. The CA is fine; the SAN list is the problem.
