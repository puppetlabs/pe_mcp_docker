---
tags:
  - -inbox/pag
---
# Release pe_mcp_docker

## Description

This guide is the maintainer checklist for cutting a new `pe_mcp_docker` release. It's written up-front for `v1.0.2`, but the shape applies to every subsequent `vX.Y.Z` tag.
## Usage

Since pushing a new tag triggers the `release.yml` GitHub Action workflow; therefore, make sure you **follow all steps in the "pre-flight" below before you tag**.

### Pre-flight — before you tag

Do these in order. Don't tag until every box is ticked.
* Confirm the motivating PR(s) is merged
* Ensure the `pyproject.toml` will match the intended tag.  Since the wheel/sdist filename comes from `pyproject.toml`, then the new [X.Y.Z] tag and this file **MUST AGREE**!
* Ensure the `CHANGELOG.md` has a real [X.Y.Z] entry for this release
* CI is green on main

For example, the following will check everything (apart from the CHANGELOG):
 
```bash
# Confirm the motivating PR is merged:
gh pr view <N> --json state,mergedAt
# -> state: MERGED
  
# verify `pyproject.toml` contains the expected new tag version
grep '^version' pyproject.toml
# -> version = "1.0.2"     # must match the vX.Y.Z you're about to tag

# verify that CI is green
gh run list --branch main --limit 5
# -> latest ci/main run should show conclusion: success
```

### Tag and push

Only after you've verified the pre-flight checks, then tag:  From a clean checkout of `main` on your workstation, **not** from any PR branch:

```bash
cd repositories/pe_mcp_docker

git checkout main
git pull origin main

# Sanity: the tip commit should be the merge commit for the PR that bumped
# pyproject.toml + CHANGELOG.
git log -1 --oneline

# Create the annotated tag on the merge commit.
git tag -a v1.0.2 -m "Release 1.0.2 — PE RBAC token support"

# Push the tag. This fires release.yml + image-push.yml.
git push origin v1.0.2
```

**THE RELEASE WILL NOW BE PRODUCED AUTOMATICALLY**

Watch the release progress through to successful completion as follows:

```bash
# release.yml — this is the one that has to succeed.
gh run watch --workflow=release.yml

# Expect: workflow completes successfully, and a GitHub Release for v1.0.2
# now exists at https://github.com/puppetlabs/pe_mcp_docker/releases/tag/v1.0.2
# with pe_mcp_thin-1.0.2-py3-none-any.whl and pe_mcp_thin-1.0.2.tar.gz attached.
```

Optionally, populate the github release notes with the contents of the latest `CHANGELOG` entry.  One way to do this is in the appendix.

### Post-flight — after the tag lands

#### Verify the integrity of the new release

Do the following to make sure the new release is ok:
* Verify that the github release page shows the right assets.
* Verify that the new release will connect successfully to an existing PE MCP server via `uvx` and `pip`.

```bash
# Verify that the github release page shows the right assets.
gh release view v1.0.2 --json assets --jq '.assets[].name'
# -> pe_mcp_thin-1.0.2-py3-none-any.whl
# -> pe_mcp_thin-1.0.2.tar.gz

###############################################
# Verify the release against an existing PE MCP
###############################################
# export the PE_* variables
export PE_MCP_URL="https://<mcp-node-fqdn>/mcp"
export PE_CA_CERT="/path/to/pe-ca.pem"
export PE_RBAC_TOKEN="..."

# verify `uvx`
uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@v1.0.2 pe-mcp-thin validate
# -> PASS: connected to PE MCP, N tool(s) available

# verify `pip`
python -m venv /tmp/thin-1.0.2 && source /tmp/thin-1.0.2/bin/activate
pip install https://github.com/puppetlabs/pe_mcp_docker/releases/latest/download/pe_mcp_thin-1.0.2-py3-none-any.whl
pe-mcp-thin validate
# -> PASS: connected to PE MCP, N tool(s) available

# clean-up
deactivate && rm -rf /tmp/thin-1.0.2
```

#### Update the PAG (Puppet Agentic Gateway) catalog

The [**Puppet Agentic Gateway**](https://github.com/perforce/perforce-agentic-gateway) must be updated everytime there is a new release of this `pe_mcp_docker`.  This is very important, though out of scope in this document.

The [docs/pag-testing/internal/catalog/servers/pe-mcp-thin/server.json](https://github.com/puppetlabs/pe_mcp_docker/blob/dd7194e38b33ceb1ec138ed844e2ca2a3cb0bb45/docs/pag-testing/internal/catalog/servers/pe-mcp-thin/server.json) is the latest PAG configuration for the `pe_mcp_docker`.  If you need to bump the version number, for example, then contact the appropriate team to handle any necessary updates.

## Appendix

### Sample usage output

Successful `release.yml` run and populated Release page for a `v1.0.2` tag push:

```bash
$ git push origin v1.0.2
To github.com:puppetlabs/pe_mcp_docker.git
 * [new tag]         v1.0.2 -> v1.0.2

$ gh run watch --workflow=release.yml
✓ release.yml #<n> · <sha>
  Triggered via push about 1 minute ago

$ gh release view v1.0.2 --json assets --jq '.assets[].name'
pe_mcp_thin-1.0.2-py3-none-any.whl
pe_mcp_thin-1.0.2.tar.gz

$ uvx --from git+https://github.com/puppetlabs/pe_mcp_docker.git@v1.0.2 pe-mcp-thin validate
Checking PE MCP at https://<mcp-node-fqdn>/mcp (without RBAC token) ...
PASS: connected to PE MCP, 10 tool(s) available:
  - puppet_node_lookup
  - puppet_pql_query
  ...
```

### Populate the GitHub Release notes

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
