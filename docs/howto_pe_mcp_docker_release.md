---
tags:
  - -inbox/pag
---
<!--
# Common Guidelines
**Orientation — capture the knowledge behind the problem (read this first):**

- This document is almost always written mid-investigation — while fixing a bug, a broken build, or a failing test. **The problem is the lens, not the subject.** Solving it is the author's day-job; it is not what this document is for.
- The document's enduring value is the **domain knowledge that the problem revealed** — how the system (e.g. Bolt, Puppet, Puppet Enterprise) actually works. Make that the centre of gravity.
- Before writing, answer for yourself: *What does this problem and its solution verify about the domain? What is now understood better about how this system behaves, because of this issue?* Let those answers drive the content.
- Keep the triggering problem to a brief motivating context (a sentence or two: "this surfaced while fixing X"). Spend the document on the mental model, mechanism, and transferable insight that outlive the specific incident.
- Litmus test: if the specific problem vanished tomorrow, the document should still be worth reading as an account of how the domain works.

**Style Guidelines (Strict):**

- Treat this document as a template to be filled, not redesigned.
- Replace placeholder text completely; do not leave generic filler.
- Keep wording concise, specific, and scoped to this document's topic.
- Use bulleted lists with `-` instead of numbered lists for easy reordering.
- Create headings without numbers (e.g., `### Install Package` not `### Step 1: Install Package`).
- Keep headings descriptive so steps can be rearranged without renumbering.

**Heading Rules:**
- All `###` and lower subheadings must be concise, descriptive titles (3-7 words).
- Placeholder headings (e.g., `### Concept 1`, `### Change 1`) must be replaced with topic-specific titles before completion.
- Use `####` subheadings for subsections instead of bold text with numbers.

**Linking Rules:**
- Every reference in Related Topics must be a real link (no placeholder bullets).
- **Code**: Link to GitHub with a **permalink** — a commit-SHA-pinned URL with line numbers, NOT a `blob/main` branch URL: [`filename:line`](https://github.com/org/repo/blob/<commit-sha>/path/file.rb#L123). Use the full 40-char SHA (or at least the abbreviated one). Permalinks are mandatory because branch URLs silently drift to the wrong lines as the file changes; a SHA pin always points at the code as it was when you wrote about it. (On GitHub press `y` to convert a branch URL to a permalink.)
- **Commits**: Link to the actual commit: [`short-sha`](https://github.com/org/repo/commit/full-sha). In PR descriptions, each change section must include a commit link so reviewers can navigate directly to the diff.
- **Docs**: Link to official documentation pages.
- **Local**: Link to local docs with Obsidian-style wiki links: `[[doc-filename]]` or `[[doc-filename|display text]]`. Use the filename without the `.md` extension. Wiki links resolve by filename, so they survive file moves within the vault.

**Code Evidence Requirement (required when code is referenced):**
- For each major section,
  - include BOTH a source link to real code (with line numbers), and a short "Code Sample" block that clarifies intent.
- The "Code Sample" may be:
  - A minimal real excerpt, or
  - A simplified pseudocode version with brief comments.
- The sample must explain behavior, not just repeat syntax.
- Keep samples small and focused (about 5-20 lines).
- Add 1-3 bullets under each sample explaining:
  - what the code is doing,
  - why it matters in this document,
  - and any important caveat/assumption.
- Never fabricate APIs or behavior; if code cannot be verified, explicitly state that and omit the sample.

**Evidence Discipline — proven vs. inferred is a first-class distinction (mandatory, universal to every diataxis type):**

- **Bias toward proven.** Every factual claim in this document must default to proven-with-evidence. A claim is *proven* only when it is backed by a first-hand artefact the reader can independently open — a commit-SHA permalink, a quoted log line, a live command's exit code and output, a Slack `ts` link, a ticket ID, a screenshot, a test that reproduces it. Restating what someone said without a link is **not** proof.
- **Never smuggle an inferred claim into a proven-looking sentence.** If any sub-claim inside a paragraph, bullet, table row, evidence block, or code annotation is not first-hand-verifiable, that sub-claim MUST be marked inline with the literal bolded phrase **`Inferred, not proven.`** (verbatim, so it is greppable). Do not soften with adjacent language ("likely proven", "probably confirmed"); the marker is binary. When multiple sub-claims share a section, prefer a per-claim verdict table (claim → evidence → verdict) over prose, because prose hides gaps and tables surface them.
- **Every inferred claim owes the reader two things: what would prove it, and why it isn't proven yet.** Beside every `**Inferred, not proven.**` marker, name the specific artefact that *would* upgrade it (e.g. "would be proven by inspecting the Jenkins job history for `pipeline_release-packages_publish` between 2026-02-10 and 2026-07-31") and briefly say why that check was not done in this investigation (out of scope, no access, blocked on X, next step). An inferred claim without a named upgrade-path is a bug in the document.
- **Follow-up is not optional if it matters.** If the inferred claim is load-bearing for the document's conclusion (root cause, recommended fix, next step, ADR verdict), the document MUST also record either (a) a named follow-up action (ticket, task, next investigation), or (b) an explicit acknowledgement that the conclusion is contingent on that unproved link. Load-bearing inference without a follow-up is prohibited.
- **Author's checklist before publishing.** Before saving the file, grep it for weasel-words that mask inference: "clearly", "must have", "obviously", "certainly", "we know that", "presumably". Every occurrence is a mandatory review point — either replace with a proven citation, or replace with `**Inferred, not proven.**` + upgrade path.

This discipline exists because a diataxis document that reads *proven* on the surface but contains hidden inferred assertions silently invalidates every conclusion built on top of it. Transparency of provenance is not an optional courtesy — it is how the document earns the reader's trust to act on it.

**Diagrams (use Mermaid where it earns its place):**
- Reach for a Mermaid diagram when a picture explains structure or flow faster than prose would — for example: how components fit together, a sequence of steps or messages, a state transition, or a before/after of a change.
- Do NOT add a diagram just to have one. If the prose is already clear, or the relationship is trivial (two or three linear steps), skip it — a needless diagram is worse than none.
- Prefer one focused diagram over a single sprawling one; split distinct ideas into separate diagrams. If a diagram would otherwise grow wide (many parallel subgraphs/branches, or several loosely-related stages), first check whether splitting it into two or more smaller diagrams reads more clearly than one large one — prefer that split over cramming everything into a single diagram.
- Use a fenced ` ```mermaid ` block. Keep node labels short and the diagram readable without zooming.
- **Orient top-to-bottom for flowcharts and state diagrams**: use `flowchart TD` (or `TB`) and `stateDiagram-v2` default direction, not `flowchart LR`. Rendered width grows with the diagram in a top-to-bottom layout, so the reader scrolls vertically (natural) instead of horizontally (requires scrolling the page sideways, which most viewers handle poorly). Only use `LR` when the content is inherently a short horizontal sequence (2-4 nodes) that reads awkwardly stacked vertically — a rare exception, not the default. This does NOT apply to `sequenceDiagram` — participants are naturally laid out left-to-right with time flowing down, so that convention stays as-is.
- If a flowchart has several parallel branches (e.g. multiple subgraphs or sibling paths), stack them as sequential top-to-bottom sections rather than side-by-side columns, even if that makes the diagram taller — taller is scrollable in place, wider is not. If stacking makes the single diagram feel overloaded, split it instead (see above).
- Always keep the surrounding prose self-sufficient: the diagram should reinforce the explanation, not be the only place a key point is made (it may not render on every surface).

**File Setup Formatting Rule (required for how-to steps):**
- Do not use heredoc-style file creation commands such as `cat > file <<'EOF'` in instructional steps.
- For each file, present setup as:
  - `Create <path/filename>` (short purpose sentence), then
  - one fenced code block containing the file contents.
- Include the filename as the first line in the code block (for example, `# hosts.yaml`).
- Keep command blocks for executable commands only (for example, directory setup, `bundle install`, and test execution).

# Template-Specific Guidelines

**Purpose Section Requirement:**
- Rewrite the Purpose questions so they explicitly describe what this specific document explains.
- Do not keep generic Purpose questions if they are template placeholders.

**Surface the domain concept, not just the keystrokes:**
- Even a how-to is captured because the steps taught something about how the domain works (see the Orientation guideline above). Name that insight — don't reduce the doc to a runbook.
- Where a step exercises a non-obvious behaviour of the system, add a one-line **Key concept:** note (linking to the companion explanation if one exists) so the reader learns *why* the step works, not only *that* it works.
- If the underlying knowledge is substantial, prefer splitting it into a companion `explanation` doc and linking the two, rather than burying it in step commentary.

**Concept-Mapped Code Snippets (required when a companion explanation doc exists):**
- When the howto has a companion explanation document, each code snippet or proof script must map to a specific named concept from that explanation.
- Open each step's section with a **Key concept:** line that names the concept being demonstrated and links to the explanation doc using a wiki link.
- Keep one concept per snippet — split multi-concept scripts into separate files so each is self-contained and independently runnable.
- The sequence of snippets should build progressively, each adding one concept on top of the previous.

**Final Compliance Check (required before finishing):**
- Heading structure unchanged.
- Placeholder text removed.
- Purpose questions are document-specific.
- Related Topics links are all concrete and valid.
- Each code reference includes both a link and an explanatory code sample.
- File setup instructions use “Create <file>” + code block format (no `cat > ...` heredoc flow).
- If a companion explanation exists, every code snippet has a **Key concept:** line linking to it.
-->

# pe_mcp_docker release

## Description

This guide is the maintainer checklist for cutting a new `pe-mcp-thin` release. It's written up-front for `v1.0.2`, but the shape applies to every subsequent `vX.Y.Z` tag — swap the version numbers.

**Key concept — what a release actually is.** A release of this project is one thing: an **annotated `v*` git tag pushed to `main`**. Everything else — the wheel, the sdist, the GitHub Release page — is a side effect of that tag push. There is no separate publish step, no PyPI upload, no ghcr push. Understanding this framing is what makes every step below make sense.

The tag push fires two GitHub Actions workflows:

| Workflow | Trigger | Effect | Status |
| --- | --- | --- | --- |
| [`release.yml`](../.github/workflows/release.yml) | `push: tags: v*` | Builds sdist + wheel with `python -m build` and attaches them to the GitHub Release page for that tag. | Succeeds on every tag since `v0.1.0`. **This is the actual release artifact.** |
| [`image-push.yml`](../.github/workflows/image-push.yml) | `push: tags: v*` | Attempts to log in to Docker Hub with `DOCKERHUB_USERNAME` / `DOCKERHUB_TOKEN` secrets and push `puppet/pe-mcp-thin:vX.Y.Z` + `:latest`. | **Has never succeeded** — those secrets are not configured on the repo, so every past run has failed. Firing it on a new tag is a no-op externally, but it does produce a red workflow badge. |

Nothing else ships. There is **no PyPI publish**, **no `twine upload`**, **no ghcr push**, **no external registry write** beyond the (currently no-op) Docker Hub attempt. If a future release starts publishing to PyPI or Docker Hub, update this guide and the table above.

Consumers install the release via `uvx --from git+…@vX.Y.Z`, `pip install …/releases/latest/download/pe_mcp_thin-X.Y.Z-py3-none-any.whl`, or by building the Docker image from source at that tag — all three are documented in [`cheatsheet_pe_mcp_docker.md`](cheatsheet_pe_mcp_docker.md).

## Prerequisites

- Write access to `puppetlabs/pe_mcp_docker` on GitHub, and a local checkout with `origin` pointed at it.
- `gh` CLI authenticated (`gh auth status` → logged in), used for PR checks and release notes.
- A clean local checkout — no uncommitted work on `main` when you tag.
- The change that motivates this release has been merged into `main` via a green PR.
- You know what the intended tag is (e.g. `v1.0.2`) and it matches the version bumped in `pyproject.toml`.

## Usage

### Pre-flight — before you tag

Do these in order. Don't tag until every box is ticked.

- [ ] **PR merged.** Confirm the motivating PR is merged:

  ```bash
  gh pr view <N> --json state,mergedAt
  # -> state: MERGED
  ```

- [ ] **`pyproject.toml` version matches the intended tag.** The tag is the source of truth for the release name, but the wheel/sdist filename comes from `pyproject.toml`, so they must agree.

  ```bash
  grep '^version' pyproject.toml
  # -> version = "1.0.2"     # must match the vX.Y.Z you're about to tag
  ```

- [ ] **`CHANGELOG.md` has a real `[X.Y.Z]` entry** for this release — date accurate, PR links accurate, scope matches what actually landed. Don't tag with a placeholder date or a stale PR reference.

- [ ] **CI is green on `main` at the tip commit.**

  ```bash
  gh run list --branch main --limit 5
  # -> latest ci/main run should show conclusion: success
  ```

- [ ] **`docs/cheatsheet_pe_mcp_docker.md` bumped to the new version.** The cheatsheet hard-codes the version in three places (see [Post-flight](#post-flight-after-the-tag-lands)) — do the edit *before* the tag so the release commit people land on already points at the correct artifacts.

  Files/lines to update for 1.0.2:
  - `docs/cheatsheet_pe_mcp_docker.md:9` — `@v1.0.1` → `@v1.0.2` (Quick Reference table)
  - `docs/cheatsheet_pe_mcp_docker.md:27-28` — `@v1.0.1` → `@v1.0.2` (uvx worked example, `validate` + `serve`)
  - `docs/cheatsheet_pe_mcp_docker.md:34` — `pe_mcp_thin-1.0.1-py3-none-any.whl` → `pe_mcp_thin-1.0.2-py3-none-any.whl` (pip install URL)

  Either land these on the same PR that bumps `pyproject.toml`, or ship them as a separate small PR that merges *before* the tag push.

  > **Longer-term fix (out of scope for 1.0.2):** rewrite line 34 as `pe_mcp_thin-*-py3-none-any.whl` under `/releases/latest/download/` so it self-updates every release, and consider whether lines 9/27/28 should switch to `@main` or a `{version}` placeholder. Track separately if you want to do that.

- [ ] **`README.md` is fine as-is.** It uses `@main` (always current), no version references — nothing to change per release.

- [ ] **No unexpected side-effect workflows.** Quick sanity check that no new publish path snuck in since the last release:

  ```bash
  grep -rE 'pypi|twine|publish|dockerhub|docker.io|ghcr' .github/workflows/
  # -> should only match image-push.yml (the known no-op)
  ```

### Tag and push

From a clean checkout of `main` on your workstation, **not** from any PR branch:

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

**Key concept — tags are immutable once pushed.** If you notice something wrong *after* creating the tag locally but *before* `git push`, delete the local tag (`git tag -d v1.0.2`) and start again. Once the tag is pushed, treat it as immutable — retag with `v1.0.2.1` (or bump to `v1.0.3`) instead of force-pushing a moved tag. Anyone who has already pinned `@v1.0.2` (e.g. via `uvx --from git+…@v1.0.2`) will get a different artifact than you if you rewrite it, and the divergence is silent.

### Watch the workflows

```bash
# release.yml — this is the one that has to succeed.
gh run watch --workflow=release.yml

# Expect: workflow completes successfully, and a GitHub Release for v1.0.2
# now exists at https://github.com/puppetlabs/pe_mcp_docker/releases/tag/v1.0.2
# with pe_mcp_thin-1.0.2-py3-none-any.whl and pe_mcp_thin-1.0.2.tar.gz attached.

# image-push.yml — expected to fail. Fine to skip watching.
gh run list --workflow=image-push.yml --limit 1
# -> conclusion=failure is expected until DOCKERHUB_USERNAME/DOCKERHUB_TOKEN
#    secrets are configured.
```

If `release.yml` fails: read the run log (`gh run view <run-id> --log-failed`), fix the root cause on `main`, and cut a new tag (e.g. `v1.0.3`) rather than retrying against `v1.0.2`. Do not force-push tags.

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

### Post-flight — after the tag lands

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

- [ ] **Close any superseded PRs.** For 1.0.2 specifically:

  ```bash
  gh pr close 8 --comment "Superseded by #11, released as v1.0.2"
  ```

- [ ] **Update the PAG catalog.** `pag-testing/uvx/internal/catalog/servers/pe-mcp-thin/server.json` currently pins `@gavins-rbac-token`. After the tag ships, bump to `@v1.0.2` and re-run the two flavours of PAG test (`pag-quickstart-mcp-new/` and `pag-quickstart-mcp-legacy/`) using `pag-testing/uvx/` as the template.

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

### Related Resources

- [`.github/workflows/release.yml`](../.github/workflows/release.yml) — the workflow that builds sdist + wheel and attaches them to the GitHub Release on `v*` tag push.
- [`.github/workflows/image-push.yml`](../.github/workflows/image-push.yml) — the (currently no-op) Docker Hub push workflow.
- [`CHANGELOG.md`](../CHANGELOG.md) — the per-version entry `gh release edit` pulls its notes body from.
- [`cheatsheet_pe_mcp_docker.md`](cheatsheet_pe_mcp_docker.md) — the operator reference whose hard-coded version strings must be bumped in pre-flight.
- [`softprops/action-gh-release`](https://github.com/softprops/action-gh-release) — the GitHub Action that creates the Release object and uploads assets.
- [Semantic Versioning](https://semver.org/) — the versioning scheme the `vX.Y.Z` tags follow.

### Known non-issues you can ignore

- **`image-push.yml` shows failed on every release.** Expected until Docker Hub credentials are configured on the repo. It does not block the release.
- **Draft release created briefly during `release.yml`.** `softprops/action-gh-release@v2` creates the release object, uploads the assets, and marks it non-draft in one step — you'll see a very short-lived draft state in the UI while assets upload.

### Troubleshooting: a release goes wrong

The failure modes worth thinking about in advance:

#### Wrong version in `pyproject.toml`

Symptoms: You tagged `v1.0.2`, but the assets on the Release page are named `pe_mcp_thin-1.0.1-*.whl` / `pe_mcp_thin-1.0.1.tar.gz`. The wheel is filename-tied to `pyproject.toml`, not to the tag, so if they diverge the tag and the artifact disagree.

Solution:

- Bump `pyproject.toml` to the intended version on `main`.
- Cut a new tag (e.g. `v1.0.3`) — do **not** retag `v1.0.2`.
- Note the aborted `v1.0.2` in `CHANGELOG.md` so future readers understand why it was skipped.

#### `release.yml` succeeds but the wheel is broken

Symptoms: `release.yml` went green and the assets exist, but users report `pip install …/pe_mcp_thin-1.0.2-*.whl` or `uvx --from …@v1.0.2` fails — bad metadata, missing files, unimportable module.

Solution:

- Land the fix on `main`.
- Cut `v1.0.3`.
- Either mark `v1.0.2` as pre-release in the GitHub UI, or delete the Release object. The tag itself stays — deleting the tag breaks `uvx --from …@v1.0.2` for anyone who already pinned it.

#### Tag pushed by mistake to the wrong commit

Symptoms: `v1.0.2` was pushed pointing at the wrong commit (e.g. before the CHANGELOG merge landed).

Solution:

- Do **not** force-push the tag — anyone who already resolved `@v1.0.2` will silently get a different artifact than you.
- Delete the Release object.
- Cut a new tag at the intended commit.
- Note it in `CHANGELOG.md` next to the fixed version so the trail is auditable.
