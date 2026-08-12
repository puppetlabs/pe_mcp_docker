# Releasing `pe-mcp-thin`

Maintainer checklist for cutting a new release. Written up-front for 1.0.2 but the shape applies to every subsequent `vX.Y.Z` tag — swap the version numbers.

## What a release actually is

A release is one thing: an **annotated `v*` git tag pushed to `main`**. The tag push fires two GitHub Actions workflows:

| Workflow | Trigger | Effect | Status |
| --- | --- | --- | --- |
| [`release.yml`](.github/workflows/release.yml) | `push: tags: v*` | Builds sdist + wheel with `python -m build` and attaches them to the GitHub Release page for that tag. | Succeeds on every tag since `v0.1.0`. **This is the actual release artifact.** |
| [`image-push.yml`](.github/workflows/image-push.yml) | `push: tags: v*` | Attempts to log in to Docker Hub with `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` secrets and push `puppet/pe-mcp-thin:vX.Y.Z` + `:latest`. | **Has never succeeded** — those secrets are not configured on the repo, so every past run has failed. Firing it on a new tag is a no-op externally, but it does produce a red workflow badge. |

Nothing else ships. There is **no PyPI publish**, **no `twine upload`**, **no ghcr push**, **no external registry write** beyond the (currently no-op) Docker Hub attempt. If a future release starts publishing to PyPI or Docker Hub, update this file and the table above.

Consumers install this release via `uvx --from git+…@vX.Y.Z`, `pip install …/releases/latest/download/pe_mcp_thin-X.Y.Z-py3-none-any.whl`, or by building the Docker image from source at that tag — all three are documented in [`CHEATSHEET.md`](CHEATSHEET.md).

## Pre-flight — before you tag

Do these in order. Don't tag until every box is ticked.

- [ ] **PR merged.** The change that motivates this release has been merged into `main` via a green PR. Confirm with `gh pr view <N> --json state,mergedAt` → `MERGED`.
- [ ] **`pyproject.toml` version matches the intended tag.** The tag is the source of truth for the release name, but the wheel/sdist filename comes from `pyproject.toml`, so they must agree.

  ```bash
  grep '^version' pyproject.toml
  # -> version = "1.0.2"     # must match the vX.Y.Z you're about to tag
  ```

- [ ] **`CHANGELOG.md` has a real `[X.Y.Z]` entry** for this release (date accurate, PR links accurate, scope matches what actually landed). Don't tag with a placeholder date or a stale PR reference.
- [ ] **CI is green on `main` at the tip commit.**

  ```bash
  gh run list --branch main --limit 5
  # -> latest ci/main run should show conclusion: success
  ```

- [ ] **You've bumped `CHEATSHEET.md` to the new version.** The cheatsheet hard-codes the version in three places (see [Post-flight](#post-flight) — but do the edit _before_ the tag so the release commit that people land on already points at the correct artifacts).

  Files/lines to update for 1.0.2:
  - `CHEATSHEET.md:9` — `@v1.0.1` → `@v1.0.2` (Quick Reference table)
  - `CHEATSHEET.md:24-25` — `@v1.0.1` → `@v1.0.2` (uvx worked example, `validate` + `serve`)
  - `CHEATSHEET.md:33` — `pe_mcp_thin-1.0.1-py3-none-any.whl` → `pe_mcp_thin-1.0.2-py3-none-any.whl` (pip install URL)

  Either update these on the same PR that bumps `pyproject.toml`, or land them as a separate small PR that merges _before_ the tag push.

  > **Longer-term fix (out of scope for 1.0.2):** rewrite line 33 as `pe_mcp_thin-*-py3-none-any.whl` under `/releases/latest/download/` so it self-updates every release, and consider whether lines 9/24/25 should switch to `@main` or a `{version}` placeholder. Track separately if you want to do that.

- [ ] **`README.md` is fine as-is.** It uses `@main` (always current), no version references — nothing to change per release.
- [ ] **Confirm no unexpected side-effect workflows.** A quick sanity check that no new publish path snuck in since the last release:

  ```bash
  grep -rE 'pypi|twine|publish|dockerhub|docker.io|ghcr' .github/workflows/
  # -> should only match image-push.yml (the known no-op)
  ```

## Tag & push

From a clean checkout of `main` on your workstation, **not** from any PR branch:

```bash
cd repositories/pe_mcp_docker

git checkout main
git pull origin main

# Sanity: the tip commit should be the merge commit for the PR that bumped pyproject.toml + CHANGELOG.
git log -1 --oneline

# Create the annotated tag on the merge commit.
git tag -a v1.0.2 -m "Release 1.0.2 — PE RBAC token support"

# Push the tag. This fires release.yml + image-push.yml.
git push origin v1.0.2
```

If you notice something wrong _after_ creating the tag locally but _before_ `git push`, delete the local tag (`git tag -d v1.0.2`) and start again. Once the tag is pushed, treat it as immutable — retag with `v1.0.2.1` (or bump to `v1.0.3`) instead of force-pushing a moved tag.

## Watch the workflows

```bash
# release.yml — this is the one that has to succeed.
gh run watch --workflow=release.yml

# Expect: workflow completes successfully, and a GitHub Release for v1.0.2
# now exists at https://github.com/puppetlabs/pe_mcp_docker/releases/tag/v1.0.2
# with pe_mcp_thin-1.0.2-py3-none-any.whl and pe_mcp_thin-1.0.2.tar.gz attached.

# image-push.yml — expected to fail. Fine to skip watching.
gh run list --workflow=image-push.yml --limit 1
# -> conclusion=failure is expected until DOCKERHUB_USERNAME/DOCKERHUB_TOKEN secrets are configured.
```

If `release.yml` fails: read the run log (`gh run view <run-id> --log-failed`), fix the root cause, and cut a new tag (e.g. `v1.0.3`) rather than retrying against `v1.0.2`. Do not force-push tags.

## Populate the GitHub Release notes

`softprops/action-gh-release@v2` creates the release object automatically when it attaches the artifacts. Its body defaults to empty (matches how `v1.0.0` and `v1.0.1` were left). Fill it in with the CHANGELOG entry:

```bash
# Extract just this version's CHANGELOG entry and set it as the release body.
gh release edit v1.0.2 --notes-file <(
  sed -n '/^## \[1.0.2\]/,/^## \[1.0.1\]/p' CHANGELOG.md | sed '$d'
)

# Confirm.
gh release view v1.0.2
```

Prior releases left the body empty. Filling it in is a nicety, not a requirement.

## Post-flight — after the tag lands

- [ ] **GitHub Release page shows the right assets.**

  ```bash
  gh release view v1.0.2 --json assets --jq '.assets[].name'
  # -> pe_mcp_thin-1.0.2-py3-none-any.whl
  # -> pe_mcp_thin-1.0.2.tar.gz
  ```

- [ ] **`uvx --from git+…@v1.0.2 pe-mcp-thin validate` resolves the tag.** Quick end-to-end smoke test:

  ```bash
  export PE_MCP_URL="https://<mcp-node-fqdn>/mcp"
  export PE_CA_CERT="/path/to/pe-ca.pem"
  # export PE_RBAC_TOKEN="..."  # only if the target is pe-infra-assistant

  uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@v1.0.2 pe-mcp-thin validate
  # -> PASS: connected to PE MCP, N tool(s) available
  ```

- [ ] **`pip install …/releases/latest/download/pe_mcp_thin-1.0.2-py3-none-any.whl` works.** Same shape, in a throwaway virtualenv:

  ```bash
  python -m venv /tmp/thin-1.0.2 && source /tmp/thin-1.0.2/bin/activate
  pip install https://github.com/puppetlabs/pe_mcp_docker/releases/latest/download/pe_mcp_thin-1.0.2-py3-none-any.whl
  pe-mcp-thin validate
  deactivate && rm -rf /tmp/thin-1.0.2
  ```

- [ ] **Close any superseded PRs.** For 1.0.2 specifically: `gh pr close 8 --comment "Superseded by #11, released as v1.0.2"`.
- [ ] **Update the PAG catalog.** `pag-testing/uvx/internal/catalog/servers/pe-mcp-thin/server.json` currently pins `@gavins-rbac-token`. After the tag ships, bump to `@v1.0.2` and re-run the two flavours of PAG test (`pag-quickstart-mcp-new/` and `pag-quickstart-mcp-legacy/`) using `pag-testing/uvx/` as the template.

## Known non-issues you can ignore

- **`image-push.yml` shows failed on every release.** Expected until Docker Hub credentials are configured on the repo. It does not block the release.
- **Draft release created briefly during `release.yml`.** `softprops/action-gh-release@v2` creates the release object, uploads the assets, and marks it non-draft in one step — you'll see a very short-lived draft state in the UI while assets upload.

## If a release goes wrong

The failure modes worth thinking about in advance:

- **Wrong version in `pyproject.toml`.** The wheel is filename-tied to `pyproject.toml`, not to the tag. If they diverge (e.g. tag `v1.0.2` but `pyproject.toml` still says `1.0.1`), you'll get `pe_mcp_thin-1.0.1-*.whl` attached to a `v1.0.2` release. Fix: bump `pyproject.toml`, merge to `main`, cut `v1.0.3` — do not retag `v1.0.2`.
- **`release.yml` succeeds but the wheel is broken** (bad metadata, missing files, unimportable module). Users notice via a broken `pip install` or `uvx --from`. Fix: land the fix on `main`, cut `v1.0.3`, mark `v1.0.2` pre-release in the GitHub UI or delete the release object (the tag itself stays — deleted tags cause `uvx --from …@v1.0.2` to break for anyone who pinned it).
- **Tag pushed by mistake to the wrong commit.** Do not force-push the tag. Delete the release object, cut a new tag at the intended commit, and note it in `CHANGELOG.md` next to the fixed version.
