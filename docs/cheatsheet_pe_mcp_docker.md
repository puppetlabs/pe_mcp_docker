# pe_mcp_docker

Copy-paste commands for running, validating, and troubleshooting `pe-mcp-thin` against either PE MCP target — see [`../README.md`](../README.md) for setup and the target overview this reference assumes.
## Pre-requisites

**The following `PE_*` environment variables MUST HAVE valid entries in order to proceed**:

* `PE_MCP_URL`: A valid endpoint to a PE MCP server, e.g., `https://mcp.example.com/mcp`.  If you don't already have an existing MCP URL, then refer to [puppetlabs-pe_mcp module](https://github.com/puppetlabs/puppetlabs-pe_mcp) for instructions on how to set one up.
* `PE_RBAC_TOKEN`: A valid PE RBAC token.  For more information and how to obtain one via the PE console (see [PE Console RBAC documenation](https://help.puppet.com/pe/2025.9/topics/rbac-token-auth-generate-token-console.htm)).  If you have ssh access to the primary, then you can also obtain this token via something like `puppet access login --username=<YOURUSER> --lifetime=1y --print` .  **Keep this token safe and secure.**
* `PE_CA_CERT`: The path to a valid CA cert.  **NOTE: the path NOT the contents of this cert!**.  Without this CA cert from your primary, your local connection will not "trust" the `PE_MCP_URL`.  Therefore, save a copy of this cert locally to something like `${HOME}/certs/pe-ca.pem`.  For example:

```bash
`curl -k "https://<pe-primary-fqdn>:8140/puppet-ca/v1/certificate/ca" -o ${HOME}/certs/pe-ca.pem`
```

## Install & run

There are 3 different ways to run this server: `uvx`, `pip`, and `docker`.
### uvx (fastest, no install)

```bash
export PE_MCP_URL="https://<mcp-node-fqdn>/mcp"
export PE_CA_CERT="/path/to/pe-ca.pem"
export PE_RBAC_TOKEN="LONG_LONG_RBAC_TOKEN"

uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@main pe-mcp-thin validate   # verified 2026-08-07 on raw-millennium: PASS, 10 tool(s)
uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@main pe-mcp-thin serve      # verified 2026-08-07 on raw-millennium: FastMCP stdio server starts
```

### pip install

For this, check for the latest release [here](https://github.com/puppetlabs/pe_mcp_docker/releases) and set `LATEST_RELEASE` accordingly.  For example:

```bash
LATEST_RELEASE='1.0.2'
pip install "https://github.com/puppetlabs/pe_mcp_docker/releases/latest/download/pe_mcp_thin-${LATEST_RELEASE}-py3-none-any.whl"   # verified 2026-08-07 in clean venv

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

## Troubleshooting

### TLS Hostname mismatch against the Legacy MCP (`console-cert` missing FQDN SAN)

If `pe-mcp-thin validate` against the MCP fails with something as below then your MCP server probably doesn't have a valid certificate.  

```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch,
certificate is not valid for '<pe-primary-fqdn>'.
```

This may happen when you attempt to connect to the [infra-assistant MCP](https://help.puppet.com/pe/2025.9/topics/infra-assistant-code-assist.htm), which is located on the the PE primary via something like `https://<PRIMARY_HOST>/mcp`.  In the case of the infra-assistant, the above error may present itself because the certificate presented by the server has only been signed with the "shortname" of the primary.  

For example, if your primary endpoint is `https://myprimary.example.com`, then verify the certificate, whether it has all the required Subject Alternative Names.  One quick way to check is to use `openssl` as described below:

```bash
PRIMARY_ENDPOINT=<pe-primary-fqdn>
echo | \
	openssl s_client -connect ${PRIMARY_ENDPOINT}:443 -servername ${PRIMARY_ENDPOINT} 2>/dev/null | \
	openssl x509 -noout -text \
	> primary-cert.txt

cat primary-cert.txt | openssl x509 -noout -subject -ext subjectAltName
# subject=CN=console-cert
# X509v3 Subject Alternative Name:
#     DNS:<short-hostname>, DNS:console-cert
# If the FQDN is missing from that DNS list, you have this gotcha.
```

If the <PRIMARY_HOST> certificate does not contain the FQDN, then you'll need to re-generate it.  One way to do this is as follows and requires PE primary access (root/sudo):

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
