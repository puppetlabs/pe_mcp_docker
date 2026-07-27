#!/bin/bash
set -euo pipefail

PLACEHOLDER_URL="https://REPLACE_WITH_MCP_NODE_FQDN/mcp/"
PE_MCP_QUICKSTART_URL="https://github.com/puppetlabs/puppetlabs-pe_mcp#quickstart"

not_configured_help() {
  cat >&2 <<EOF

No Smart MCP server connection is set up yet. Two possibilities:

  1) You don't have a Smart MCP server deployed on your PE ecosystem yet.
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
  echo "Do you already have a Smart MCP server deployed on Puppet Enterprise"
  echo "infrastructure?"
  echo
  echo "  1) Yes — help me connect to it"
  echo "  2) No  — I need to deploy one first"
  echo
  read -r -p "Choice [1/2]: " have_server

  if [ "${have_server}" != "1" ]; then
    cat <<EOF

No problem — deploying a Smart MCP server is a separate, one-time step
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
  echo "Smart MCP URL — the HTTPS endpoint of your deployed server:"
  echo "  https://<mcp-node-fqdn>/mcp/"
  echo "where <mcp-node-fqdn> is the node you ran 'pe_mcp::deploy' against."
  echo
  read -r -p "Smart MCP URL: " smart_url
  if [ -z "${smart_url}" ]; then
    echo "ERROR: URL cannot be empty." >&2
    exit 1
  fi

  echo
  echo "PE CA certificate — your Smart MCP's nginx uses a certificate signed"
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

  cat > /config/config.env <<EOF
SMART_MCP_URL=${smart_url}
EOF

  echo
  echo "Setup complete. Wrote:"
  echo "  /config/config.env"
  echo "  /config/pe-ca.pem"
  echo
  echo "Next: run 'validate' to confirm connectivity, e.g.:"
  echo "  docker run --rm -it -v ~/.pe-mcp:/config <image> validate"
}

load_config() {
  if [ -z "${SMART_MCP_URL:-}" ] && [ -f /config/config.env ]; then
    # shellcheck disable=SC1091
    source /config/config.env
  fi
  if [ -z "${PE_CA_CERT:-}" ] && [ -f /config/pe-ca.pem ]; then
    export PE_CA_CERT=/config/pe-ca.pem
  fi
}

validate() {
  load_config

  if [ -z "${SMART_MCP_URL:-}" ] || [ "${SMART_MCP_URL}" = "${PLACEHOLDER_URL}" ]; then
    echo "SMART_MCP_URL is not configured." >&2
    not_configured_help
    exit 1
  fi
  if [ -z "${PE_CA_CERT:-}" ] || [ ! -f "${PE_CA_CERT}" ]; then
    echo "PE CA certificate not found." >&2
    not_configured_help
    exit 1
  fi

  export SMART_MCP_URL PE_CA_CERT
  exec python selftest.py
}

serve() {
  load_config

  if [ -z "${SMART_MCP_URL:-}" ] || [ "${SMART_MCP_URL}" = "${PLACEHOLDER_URL}" ]; then
    echo "ERROR: SMART_MCP_URL is not configured." >&2
    not_configured_help
    exit 1
  fi
  if [ -z "${PE_CA_CERT:-}" ] || [ ! -f "${PE_CA_CERT}" ]; then
    echo "ERROR: PE CA certificate not found at '${PE_CA_CERT:-<unset>}'." >&2
    not_configured_help
    exit 1
  fi

  export SMART_MCP_URL PE_CA_CERT
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
