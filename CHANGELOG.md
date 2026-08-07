# Changelog

All notable changes to `pe_mcp_docker` are documented here.

## [1.0.2] - 2026-09-10

Added `PE_RBAC_TOKEN` to enable client access to both the "legacy" (`infra-assistant`) and new PE MCP's.  For more information see [Add PE RBAC Token #8](https://github.com/puppetlabs/pe_mcp_docker/pull/8)

Simplified documentation: (1) README rewritten as a lean quickstart (uvx as the primary); (2) Added `CHEATSHEET.md` for quick operational access commands.  For more information see [Simplify quickstart and add operational cheatsheet #9](https://github.com/puppetlabs/pe_mcp_docker/pull/9)

## [1.0.1] - 2026-07-29

- **Breaking**: renamed the `SMART_MCP_URL` environment variable to `PE_MCP_URL` across the Docker entrypoint, the pip-installed CLI, and the proxy/selftest scripts. No backward-compatible alias is provided — update any `docker run -e SMART_MCP_URL=...`, `.mcp.json` env blocks, or `/config/config.env` files to use `PE_MCP_URL` instead. "Smart MCP" naming was also updated to "PE MCP" throughout for consistency with the rest of the project.
- Fixed `image-push.yml`'s tag trigger (`[0-9]+.*` → `v*`) so it actually fires on `v*` release tags, matching `release.yml`. Previously it silently never ran for `v0.1.0` or `v1.0.0`, so no image was ever pushed to Docker Hub.

## [1.0.0] - 2026-07-29

- First tagged release. Docker thin-client image (`puppet/pe-mcp-thin`) and the native `pe-mcp-thin` pip package (wheel/sdist attached to the GitHub Release; not yet published to Docker Hub or PyPI).
- Added Semgrep static analysis and Dependabot (pip + github-actions).
