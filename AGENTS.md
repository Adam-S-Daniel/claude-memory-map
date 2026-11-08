<!-- BEGIN MANAGED SECTION — DO NOT EDIT ABOVE "## Repo-specific additions" -->
<!-- Source: _agent-guidance -->
<!-- Sections: none -->
<!-- Mode: stub -->

# AGENTS.md

> **Managed by [`_agent-guidance`].**
> Edit only below the `## Repo-specific additions` header.
> Everything above it will be overwritten on the next sync.

guidance-marker: fleet-stub (transcript counts use this line; keep it)

## Fleet guidance is delivered once per session — not by this file

The full guidance, floor rules included, is installed into user memory by
the `fleet-memory` SessionStart hook, whose verdict line says whether it
loaded. `installed` or `current`: it is in context. `DEGRADED` or no verdict:
it is not, so read [`agents-md/base.md`](https://github.com/Adam-S-Daniel/_agent-guidance/blob/main/agents-md/base.md)
before non-trivial work and say you ran degraded. `skipped`: read it too, but
it is the owner's choice, so do not report or "fix" it. Always, and above all
before you have read it: never push to a default branch, force-push a shared
branch, commit a secret, or print personal data to a CI log. Keep this file
under 32 KiB (Codex silently truncates it).

**Your first reply to the user in a session begins**
`fleet-guidance check: <value>`, copied from the installed guidance's
`fleet-guidance check value:` line, or `fleet-guidance check: none` when no
such line is in your context. Never guess one or copy it from a file you
read; only in replies to the user.

<!-- END MANAGED SECTION -->
## Repo-specific additions

<!-- Add your repo-specific agent guidance below this line -->

- `index.html` is a **committed build artifact**: after touching anything in
  `src/`, run `npm run build` and commit the regenerated `index.html` in the
  same change — CI fails on drift between the two.
- Merges to `main` that change `index.html` **auto-publish** to
  adamdaniel.ai (vendor-bump PR with auto-merge), and PRs that change it get
  a site preview mirror + preview URL comment. See README →
  "Publishing to adamdaniel.ai". Never merge the draft `tool-preview/*`
  mirror PRs in the site repo.
- The site's visual-regression gate **auto-passes sync PRs by design**
  (existing-tool updates are reviewed here, not there). A sync PR that
  unexpectedly demands a human regression review means something beyond the
  vendored asset changed — investigate before approving. If site PRs stop
  appearing at all: `site-sync` fails loudly when `SITE_SYNC_TOKEN` is
  missing/expired while `site-preview` soft-skips with a warning — check
  this repo's Actions tab first.
- `site-{sync,preview}.yml` + `scripts/sync-to-site.sh` are the **reference
  implementation** for any tool repo syncing onto the site's `/tools/`
  section — keep them copy-portable (slug/paths parameterized up top, no
  memory-map-specific logic below).

### Action pins

Workflows name third-party actions by release tag; [`.github/workflows/actions.lock`](.github/workflows/actions.lock) locks each tag to an exact commit, and the runner runs the locked commit even when it disagrees with the tag. The `test` job's "Verify action lockfile" step is the shared action [`Adam-S-Daniel/verify-actions-lock`](https://github.com/Adam-S-Daniel/verify-actions-lock); it runs only when a PR touches workflow dependencies (`.github/workflows/**`, `.github/actions/**`, `action.yml`/`action.yaml`), and fails on any `--verify` finding except `cooldown-config-ignored` (dependabot.yml's cooldown `exclude`, which the tool ignores). It is not the only guard: the runner rejects forged pins. Write the exact tag by hand, regenerate with `gh actions-lock --no-narrow`, and commit both files; review an `actions.lock` diff as you would a SHA pin. A stale or moved pin is fixed with `gh actions-lock --accept-moved`; review the diff. A `reachability-unknown` failure means the GitHub API was unreachable: re-run. Cross-repo reusable workflows (`jobs.<id>.uses`) are not locked, so they take a full commit SHA (`Adam-S-Daniel/cms-platform` refs excepted); a test enforces it. Fleet rule: [ADR 0024](https://github.com/Adam-S-Daniel/_agent-guidance/blob/main/docs/decisions/0024-actions-pin-through-lockfiles.md).
