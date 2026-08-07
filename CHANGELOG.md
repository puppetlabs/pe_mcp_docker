# Changelog

All notable changes to `pe_mcp_docker` are documented here.

## [Unreleased]

- Documentation-only overhaul: README rewritten as a lean quickstart
  (uvx as the primary, no-install path, matching how PAG's registry entry
  actually runs this server; pip and local-only Docker builds as
  alternatives). Clarified that `puppet/pe-mcp-thin` is intentionally not
  yet published to Docker Hub. Added client-agnostic MCP wiring guidance
  (Claude Code, GitHub Copilot, or any other MCP client — this was never
  Claude-specific). Added `CHEATSHEET.md` (full command reference,
  verified against a live PE) and `docs/explanation_architecture.md`
  (why this is a stdio↔HTTPS proxy, not a direct client).
- Note: `PE_RBAC_TOKEN` support (dual-target auth, PR #8) is a separate,
  not-yet-merged change — its own changelog entry lands with that PR, not
  this one.

## [1.0.1] - 2026-07-29

- **Breaking**: renamed the `SMART_MCP_URL` environment variable to
  `PE_MCP_URL` across the Docker entrypoint, the pip-installed CLI, and the
  proxy/selftest scripts. No backward-compatible alias is provided — update
  any `docker run -e SMART_MCP_URL=...`, `.mcp.json` env blocks, or
  `/config/config.env` files to use `PE_MCP_URL` instead. "Smart MCP" naming
  was also updated to "PE MCP" throughout for consistency with the rest of
  the project.
- Fixed `image-push.yml`'s tag trigger (`[0-9]+.*` → `v*`) so it actually
  fires on `v*` release tags, matching `release.yml`. Previously it
  silently never ran for `v0.1.0` or `v1.0.0`, so no image was ever pushed
  to Docker Hub.

## [1.0.0] - 2026-07-29

- First tagged release. Docker thin-client image (`puppet/pe-mcp-thin`) and
  the native `pe-mcp-thin` pip package (wheel/sdist attached to the GitHub
  Release; not yet published to Docker Hub or PyPI).
- Added Semgrep static analysis and Dependabot (pip + github-actions).
