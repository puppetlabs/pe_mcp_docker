#!/bin/bash
set -euo pipefail

PLACEHOLDER_URL="https://REPLACE_WITH_MCP_NODE_FQDN/mcp/"
PE_MCP_QUICKSTART_URL="https://github.com/puppetlabs/puppetlabs-pe_mcp#quickstart"
RBAC_TOKEN_FILE=/config/rbac-token

# The PE MCP is served at /mcp with no trailing slash. A trailing slash is
# rewritten to /infra-assistant/mcp/ upstream and returns 404 *after* the
# RBAC check passes, which makes it look like a server fault rather than a
# URL typo. Normalize so neither form can bite.
strip_trailing_slash() {
  local url="$1"
  while [ -n "${url}" ] && [ "${url}" != "${url%/}" ]; do
    url="${url%/}"
  done
  printf '%s' "${url}"
}

NORMALIZED_PLACEHOLDER_URL="$(strip_trailing_slash "${PLACEHOLDER_URL}")"

# config.env holds an operator-entered value (a pasted URL) verbatim, so it
# must never be executed as a script -- a value containing `$(...)` or `` ` ``
# would otherwise run as arbitrary shell code every time this is read. Extract
# the value textually instead of sourcing the file.
read_config_value() {
  local key="$1" file="$2"
  sed -n "s/^${key}=//p" "${file}" 2>/dev/null | tail -n1
}

not_configured_help() {
  cat >&2 <<EOF

No PE MCP server connection is set up yet. Two possibilities:

  1) You don't have a PE MCP server deployed on your PE ecosystem yet.
     Deploying one is a separate one-time step using the puppetlabs-pe_mcp
     Bolt module (not this image). Quickstart:
       ${PE_MCP_QUICKSTART_URL}
     Short version, from a workstation with Bolt installed:
       git clone https://github.com/puppetlabs/puppetlabs-pe_mcp.git
       cd puppetlabs-pe_mcp && bolt module install
       cp inventory.yaml.example inventory.yaml   # fill in primary + target node
       export PE_ADMIN_PASSWORD='...'
       bolt plan run pe_mcp::deploy -i inventory.yaml primary=<primary> targets=<mcp-node>

  2) You already have one deployed — you just need to connect this client to it.
     Run:
       docker run --rm -it -v ~/.pe-mcp:/config <image> setup
     and follow the prompts.
EOF
}

setup() {
  if [ ! -d /config ]; then
    echo "ERROR: /config is not mounted. Run with: -v ~/.pe-mcp:/config" >&2
    exit 1
  fi

  echo "PE MCP thin-client setup"
  echo "========================"
  echo
  echo "Do you already have a PE MCP server deployed on Puppet Enterprise"
  echo "infrastructure?"
  echo
  echo "  1) Yes — help me connect to it"
  echo "  2) No  — I need to deploy one first"
  echo
  read -r -p "Choice [1/2]: " have_server

  if [ "${have_server}" != "1" ]; then
    cat <<EOF

No problem — deploying a PE MCP server is a separate, one-time step
using the puppetlabs-pe_mcp Bolt module (this image doesn't do that part).

Full quickstart:
  ${PE_MCP_QUICKSTART_URL}

Short version, from a workstation with Bolt installed:
  git clone https://github.com/puppetlabs/puppetlabs-pe_mcp.git
  cd puppetlabs-pe_mcp && bolt module install
  cp inventory.yaml.example inventory.yaml   # fill in your PE primary + target node
  export PE_ADMIN_PASSWORD='...'
  bolt plan run pe_mcp::deploy -i inventory.yaml primary=<pe-primary> targets=<mcp-node>

Once that's deployed, re-run this setup and choose option 1.
EOF
    exit 0
  fi

  echo
  echo "PE MCP URL — the HTTPS endpoint of your deployed server:"
  echo "  https://<mcp-node-fqdn>/mcp"
  echo "where <mcp-node-fqdn> is the node you ran 'pe_mcp::deploy' against."
  echo "Note: no trailing slash."
  echo
  read -r -p "PE MCP URL: " smart_url
  if [ -z "${smart_url}" ]; then
    echo "ERROR: URL cannot be empty." >&2
    exit 1
  fi

  normalized_url="$(strip_trailing_slash "${smart_url}")"
  if [ "${normalized_url}" != "${smart_url}" ]; then
    echo "Note: dropped the trailing slash — using ${normalized_url}"
    smart_url="${normalized_url}"
  fi

  echo
  echo "PE CA certificate — your PE MCP's nginx uses a certificate signed"
  echo "by your PE Certificate Authority (not a public CA), so this client"
  echo "needs to trust it explicitly."
  echo
  echo "To get it, run this on (or copy it from) any PE-enrolled node — the"
  echo "PE primary or the MCP node itself both have it:"
  echo "  cat /etc/puppetlabs/puppet/ssl/certs/ca.pem"
  echo
  echo "Choose how to provide it:"
  echo "  1) Paste the PEM content now"
  echo "  2) Copy from a file already mounted into this container"
  echo "     (e.g. -v /path/to/ca.pem:/import/pe-ca.pem:ro)"
  read -r -p "Choice [1/2]: " cert_choice

  if [ "${cert_choice}" = "2" ]; then
    if [ ! -f /import/pe-ca.pem ]; then
      echo "ERROR: /import/pe-ca.pem not found. Mount it with -v /path/to/ca.pem:/import/pe-ca.pem:ro" >&2
      exit 1
    fi
    cp /import/pe-ca.pem /config/pe-ca.pem
  else
    echo "Paste the PEM content, then press Ctrl-D on an empty line when done:"
    cat > /config/pe-ca.pem
  fi

  if ! grep -q "BEGIN CERTIFICATE" /config/pe-ca.pem 2>/dev/null; then
    echo "ERROR: that doesn't look like a PEM certificate (no 'BEGIN CERTIFICATE' found)." >&2
    rm -f /config/pe-ca.pem
    exit 1
  fi

  echo
  echo "PE RBAC token — where the MCP endpoint is gated on PE RBAC, this"
  echo "client sends the token as the X-Authentication header. If your"
  echo "deployment isn't gated, leave this blank and press Enter."
  echo
  echo "To get one, from a workstation with the PE client tools installed:"
  echo "  puppet-access login --lifetime 1y"
  echo "  cat ~/.puppetlabs/token"
  echo
  echo "The token is not echoed as you type or paste it."
  read -r -s -p "PE RBAC token (blank for none): " rbac_token
  echo

  if [ -n "${rbac_token}" ]; then
    # Kept out of config.env and mode 0600 — it's a credential, not config.
    ( umask 077; printf '%s\n' "${rbac_token}" > "${RBAC_TOKEN_FILE}" )
  else
    # Clear any token from a previous run, so "blank" means blank.
    rm -f "${RBAC_TOKEN_FILE}"
    echo "No token stored — this client will send no X-Authentication header."
  fi

  cat > /config/config.env <<EOF
PE_MCP_URL=${smart_url}
EOF

  echo
  echo "Setup complete. Wrote:"
  echo "  /config/config.env"
  echo "  /config/pe-ca.pem"
  if [ -n "${rbac_token}" ]; then
    echo "  ${RBAC_TOKEN_FILE} (mode 0600)"
  fi
  echo
  echo "Next: run 'validate' to confirm connectivity, e.g.:"
  echo "  docker run --rm -it -v ~/.pe-mcp:/config <image> validate"
}

load_config() {
  if [ -z "${PE_MCP_URL:-}" ] && [ -f /config/config.env ]; then
    PE_MCP_URL="$(read_config_value PE_MCP_URL /config/config.env)"
    export PE_MCP_URL
  fi
  if [ -z "${PE_CA_CERT:-}" ] && [ -f /config/pe-ca.pem ]; then
    export PE_CA_CERT=/config/pe-ca.pem
  fi
  if [ -z "${PE_RBAC_TOKEN:-}" ] && [ -f "${RBAC_TOKEN_FILE}" ]; then
    PE_RBAC_TOKEN="$(cat "${RBAC_TOKEN_FILE}")"
    export PE_RBAC_TOKEN
  fi
  # An explicit -e PE_MCP_URL=... bypasses setup's normalization, so redo it here.
  if [ -n "${PE_MCP_URL:-}" ]; then
    PE_MCP_URL="$(strip_trailing_slash "${PE_MCP_URL}")"
    export PE_MCP_URL
  fi
}

validate() {
  load_config

  if [ -z "${PE_MCP_URL:-}" ] || [ "${PE_MCP_URL}" = "${NORMALIZED_PLACEHOLDER_URL}" ]; then
    echo "PE_MCP_URL is not configured." >&2
    not_configured_help
    exit 1
  fi
  if [ -z "${PE_CA_CERT:-}" ] || [ ! -f "${PE_CA_CERT}" ]; then
    echo "PE CA certificate not found." >&2
    not_configured_help
    exit 1
  fi
  # PE_RBAC_TOKEN is deliberately not required — deployments that don't gate
  # on RBAC need no token, and selftest.py reports a 401 with a hint if one
  # was actually needed.
  export PE_MCP_URL PE_CA_CERT PE_RBAC_TOKEN
  exec python selftest.py
}

serve() {
  load_config

  if [ -z "${PE_MCP_URL:-}" ] || [ "${PE_MCP_URL}" = "${NORMALIZED_PLACEHOLDER_URL}" ]; then
    echo "ERROR: PE_MCP_URL is not configured." >&2
    not_configured_help
    exit 1
  fi
  if [ -z "${PE_CA_CERT:-}" ] || [ ! -f "${PE_CA_CERT}" ]; then
    echo "ERROR: PE CA certificate not found at '${PE_CA_CERT:-<unset>}'." >&2
    not_configured_help
    exit 1
  fi
  # Not required — see validate(). An unauthenticated PE MCP is a valid target.
  export PE_MCP_URL PE_CA_CERT PE_RBAC_TOKEN
  exec python proxy.py
}

case "${1:-serve}" in
  setup)
    setup
    ;;
  validate)
    validate
    ;;
  serve)
    serve
    ;;
  *)
    echo "Unknown command: ${1}" >&2
    echo "Usage: $0 {setup|validate|serve}" >&2
    exit 1
    ;;
esac
