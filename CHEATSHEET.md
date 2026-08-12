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

## Cutting a release (maintainer checklist)

A release is one thing: an annotated `v*` git tag pushed to `main`. That fires `.github/workflows/release.yml` (builds sdist + wheel, attaches them to the GitHub Release — the actual artifact) and `.github/workflows/image-push.yml` (Docker Hub push — expected to fail until `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` are configured). No PyPI, no `twine`, no ghcr.

Swap the version numbers for each subsequent release. Example below is `v1.0.2`.

### Pre-flight

- [ ] PR merged into `main`: `gh pr view <N> --json state,mergedAt` → `MERGED`.
- [ ] `pyproject.toml` version matches the intended tag: `grep '^version' pyproject.toml` → `version = "1.0.2"`.
- [ ] `CHANGELOG.md` has a real `[1.0.2]` entry (accurate date, real PR links).
- [ ] CI green on `main` tip: `gh run list --branch main --limit 5`.
- [ ] `CHEATSHEET.md` version refs bumped (this file — lines 9, 24, 25, 33: `@v1.0.1` → `@v1.0.2`, `pe_mcp_thin-1.0.1-*.whl` → `pe_mcp_thin-1.0.2-*.whl`). Land on the same PR that bumps `pyproject.toml`, or a small PR that merges before the tag push.
- [ ] `README.md` needs no change — uses `@main`.
- [ ] No new publish workflow snuck in: `grep -rE 'pypi|twine|publish|dockerhub|docker.io|ghcr' .github/workflows/` should only match `image-push.yml`.

### Tag & push

From a clean checkout of `main` (not from a PR branch):

```bash
cd repositories/pe_mcp_docker
git checkout main
git pull origin main
git log -1 --oneline                                    # sanity: tip = the release PR's merge commit
git tag -a v1.0.2 -m "Release 1.0.2 — PE RBAC token support"
git push origin v1.0.2
```

If you notice something wrong _before_ `git push`: `git tag -d v1.0.2` and start again. Once pushed, treat the tag as immutable — retag as `v1.0.2.1` or bump to `v1.0.3` instead of force-pushing.

### Watch the workflows

```bash
gh run watch --workflow=release.yml                     # must succeed
gh run list --workflow=image-push.yml --limit 1         # expected: conclusion=failure (no Docker Hub secrets)
```

If `release.yml` fails, read `gh run view <run-id> --log-failed`, fix on `main`, cut `v1.0.3` — do not force-push tags.

### Populate the release notes

```bash
gh release edit v1.0.2 --notes-file <(
  sed -n '/^## \[1.0.2\]/,/^## \[1.0.1\]/p' CHANGELOG.md | sed '$d'
)
gh release view v1.0.2
```

### Post-flight

- [ ] Release page has both assets: `gh release view v1.0.2 --json assets --jq '.assets[].name'` → `pe_mcp_thin-1.0.2-py3-none-any.whl` and `pe_mcp_thin-1.0.2.tar.gz`.
- [ ] `uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@v1.0.2 pe-mcp-thin validate` PASSes against a live MCP.
- [ ] `pip install https://github.com/puppetlabs/pe_mcp_docker/releases/latest/download/pe_mcp_thin-1.0.2-py3-none-any.whl` works in a throwaway venv, then `pe-mcp-thin validate` PASSes.
- [ ] Close any superseded PRs (for 1.0.2: `gh pr close 8 --comment "Superseded by #11, released as v1.0.2"`).
- [ ] Bump the PAG catalog (`pag-testing/uvx/internal/catalog/servers/pe-mcp-thin/server.json`) from `@gavins-rbac-token` to `@v1.0.2` and re-run both flavours of PAG test (`pag-quickstart-mcp-new/` and `pag-quickstart-mcp-legacy/`).

### Known non-issues

- `image-push.yml` shows failed on every release — expected until Docker Hub credentials are configured. Does not block the release.
- `softprops/action-gh-release@v2` briefly shows a draft state in the UI while assets upload; it's non-draft by the time the workflow finishes.

### If a release goes wrong

- Wrong version in `pyproject.toml` (tag says `v1.0.2` but wheel filename says `1.0.1`): bump `pyproject.toml`, merge to `main`, cut `v1.0.3`. Do not retag `v1.0.2`.
- `release.yml` succeeds but the wheel is broken: land the fix on `main`, cut `v1.0.3`, mark `v1.0.2` pre-release (or delete the release object — but leave the tag; deleting the tag breaks anyone who already pinned `@v1.0.2`).
- Tag pushed to the wrong commit: do not force-push. Delete the release object, cut a new tag at the intended commit, note it in `CHANGELOG.md` alongside the fixed version.
