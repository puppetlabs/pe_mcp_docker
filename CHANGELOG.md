# Changelog

All notable changes to `pe_mcp_docker` are documented here.

## [1.0.2] - 2026-08-12

- Added `PE_RBAC_TOKEN` support so this client can talk to both the "legacy" (`pe-infra-assistant`) MCP and the new decoupled PE MCP. The token is forwarded as the `X-Authentication` HTTP header; an absent/blank value sends no header at all (unauthenticated PE MCP deployments remain a valid target). See [Add PE RBAC Token #11](https://github.com/puppetlabs/pe_mcp_docker/pull/11) (based on the original [#8](https://github.com/puppetlabs/pe_mcp_docker/pull/8), rebased onto latest `main`).
- URL normalization: `PE_MCP_URL` values with trailing slashes are stripped in both the Docker entrypoint and the Python client, avoiding a post-auth 404 that previously surfaced as an opaque "Session terminated" during MCP initialize.
- Diagnostics: `selftest.py` now classifies 401/404 responses off the real HTTP status code (falling back to substring matching only when the exception carries none) and prints an actionable hint pointing at the missing/expired token or the wrong URL path. `proxy.py` prints the same hint once, on stderr, when a 401 goes past mid-session.
- Security hardening in the Docker entrypoint:
  - `load_config()` no longer `source`s `/config/config.env` — it parses the `PE_MCP_URL` value out textually instead. Sourcing meant any pasted URL containing `$(...)` or backticks would run as arbitrary shell code on every `validate`/`serve`. Pre-existing on `main`; fixed here since the RBAC token load rides the same code path. A new CI regression test proves a malicious payload no longer executes.
  - The RBAC token is stored at `/config/rbac-token` mode 0600 (never in `config.env`), and re-running `setup` with a blank token clears any prior one so "blank" reliably means "no token". `load_config()` also gives a specific diagnostic when the token file exists but isn't readable by the current UID (rather than a raw `cat: Permission denied`).
  - Every interactive prompt now surfaces EOF (piped input running dry, or no tty) as an actionable message instead of an opaque unlabeled exit.
- Documentation: README rewritten as a lean quickstart (uvx as the primary path), `CHEATSHEET.md` added for operational commands, and a link to the Infra Assistant docs was added for readers coming from the legacy MCP. See [Simplify quickstart and add operational cheatsheet #9](https://github.com/puppetlabs/pe_mcp_docker/pull/9).
- Test coverage: added tests asserting the RBAC token never appears in stdout/stderr on the success or failure paths of either `proxy.py` or `selftest.py`, plus an integration-style test that builds a real `httpx.AsyncClient` via the actual factory and sends a real loopback HTTP request to confirm `X-Authentication` lands on the wire.

## [1.0.1] - 2026-07-29

- **Breaking**: renamed the `SMART_MCP_URL` environment variable to `PE_MCP_URL` across the Docker entrypoint, the pip-installed CLI, and the proxy/selftest scripts. No backward-compatible alias is provided — update any `docker run -e SMART_MCP_URL=...`, `.mcp.json` env blocks, or `/config/config.env` files to use `PE_MCP_URL` instead. "Smart MCP" naming was also updated to "PE MCP" throughout for consistency with the rest of the project.
- Fixed `image-push.yml`'s tag trigger (`[0-9]+.*` → `v*`) so it actually fires on `v*` release tags, matching `release.yml`. Previously it silently never ran for `v0.1.0` or `v1.0.0`, so no image was ever pushed to Docker Hub.

## [1.0.0] - 2026-07-29

- First tagged release. Docker thin-client image (`puppet/pe-mcp-thin`) and the native `pe-mcp-thin` pip package (wheel/sdist attached to the GitHub Release; not yet published to Docker Hub or PyPI).
- Added Semgrep static analysis and Dependabot (pip + github-actions).
