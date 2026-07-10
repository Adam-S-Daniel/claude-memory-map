# Claude Memory Map

**What Claude remembers — an interactive map.** Check the ways you use Claude (chat, Claude Code, Cowork) and a diagram of every memory store assembles live: what gets in, where it lives, and how it comes back out.

**[Open the picker → `index.html`](./index.html)** (one self-contained file; works from a local clone or GitHub Pages)

## What it answers

- Which memories follow you across projects and repos, and which stay siloed in one?
- Work in WSL *and* native Windows — which stores are you keeping twice?
- What does Claude Code on the web actually read? (The repo's `CLAUDE.md`. Nothing cross-repo.)
- What do standalone chats remember that project chats don't — and vice versa?
- Why doesn't Cowork know what chat knows? (Anthropic: "Memory is chat-only. What Claude remembers about you in chat doesn't carry into Cowork sessions yet.")

## Features

- **Live composition** — every node and edge is generated at render time from your selection: ~2M possible maps from one canonical block set
- **Sync summary** — above the chart: which stores are in sync across your selection, which are kept separate, and who has what
- **Scope lens** — filter to memory that crosses projects/repos, stays within one, or both; contexts that can't support the chosen scope disable themselves and say why
- **Brief/Full labels** — compact names with a legend, or self-contained descriptions
- **Official terminology throughout** — every store carries Anthropic's shipping name ("Memory from chat history", "Instructions for Claude", "auto memory", "folder instructions", "global instructions"…)
- **Mobile-friendly** — stacked layout, 44px touch targets, sticky sync summary, fit-width default

## Repository layout

```
index.html            the picker (build output — fully self-contained)
src/
  build_picker3.py    builds index.html (UI shell, sync model, labels)
  build_picker2.py    canonical Mermaid block generator (extracted at build time)
  generate_suite.py   builds the 8 static curated diagrams in suite/
tests/
  tests_picker.js     81-test puppeteer e2e suite
scripts/
  dev-server.js       zero-dep dev server: serve + live-reload + auto-rebuild
suite/                .mermaid sources for those diagrams — a fuller reference set
                      that keeps contexts the picker omits (incognito chats,
                      Dispatch) and some earlier labels. index.html is the
                      source of truth for terminology and coverage.
```

## Build & test

```bash
python3 src/build_picker3.py     # writes index.html
npm install                      # puppeteer-core + chromium for tests
node tests/tests_picker.js       # 81 tests: behavior, mobile, semantics, regressions
```

Rendering uses Mermaid 11.12.0 from cdnjs at runtime; if the CDN is unreachable the page degrades gracefully and shows the generated Mermaid source instead.

## Local development & debugging

CI runs serverless Chromium (`@sparticuz/chromium` at `/tmp/chromium`). Locally the harness auto-detects a desktop Chrome, so a one-time install is all you need:

```bash
npm install
npm run setup:browser    # Chrome-for-Testing into ~/.cache/puppeteer (Linux/WSL)
npm test
```

**Run the suite:** `npm test` picks a browser in this order — `CHROMIUM_PATH` → newest Chrome under `~/.cache/puppeteer` → `/tmp/chromium` (CI). To watch it drive the UI:

```bash
npm run test:headed      # visible browser window
npm run test:debug       # visible + DevTools + 150ms slow-mo per step
# ad hoc:  HEADED=1 DEVTOOLS=1 SLOWMO=200 node tests/tests_picker.js
#          CHROMIUM_PATH=/path/to/chrome node tests/tests_picker.js
```

**Debug the page:** a zero-dependency dev server serves `index.html` over HTTP (a real origin, not `file://`), re-runs the Python build whenever `src/*.py` changes, and live-reloads:

```bash
npm run dev              # build once, then serve on http://localhost:8000 with watch + reload
npm run serve            # serve current index.html, no initial build
# options:  node scripts/dev-server.js --port 9000 --no-build
```

On WSL, open the printed URL in your Windows browser — `localhost` is forwarded. Edit a builder in `src/` and save: the server rebuilds `index.html` and the page reloads itself.

## Publishing to adamdaniel.ai

The map is embedded on [adamdaniel.ai/tools/claude-memory-map](https://adamdaniel.ai/tools/claude-memory-map/) as a vendored copy of `index.html` (the site stays hermetic — it never fetches this repo at build time). Two workflows here keep that copy current; the site repo needs no machinery of its own beyond its normal PR pipeline:

- **`site-sync.yml`** — on every push to `main` that changes `index.html`: force-pushes the file + a provenance record (`_data/tool_sources/claude-memory-map.yml`) to the site branch `tool-sync/claude-memory-map`, opens/reuses a PR, and enables auto-merge. The site's own CI + deploy take it live with no manual step.
- **`site-preview.yml`** — on every PR here that changes `index.html`: mirrors the PR's file to the site branch `tool-preview/claude-memory-map-pr-<n>` as a **draft** PR, which the site's existing deploy-preview pipeline publishes at `https://preview-pr<N>.adamdaniel.ai/tools/claude-memory-map/`. The URL is commented on the PR here and updates on every push. Closing the PR closes the mirror and tears the preview down; merging it lands via `site-sync` instead (never merge the draft mirror).

From the next cms-platform release, the site's visual-regression gate treats `tool-sync/claude-memory-map` PRs as deliberately non-salient and auto-passes them. That's by design, not a gap: the substantive review already happened here, in this repo's PR and its preview mirror.

Both copy the **committed** `index.html` — safe because CI's drift check fails any PR where the committed file doesn't match the deterministic `npm run build` output.

Setup (one-time): a fine-grained PAT scoped to `Adam-S-Daniel/adamdaniel.ai` with **Contents** and **Pull requests** read-write, stored as the `SITE_SYNC_TOKEN` Actions secret in this repo. A PAT (not `GITHUB_TOKEN`) is required so the PRs it opens still trigger the site's CI. Auto-merge assumes "Allow auto-merge" is enabled on the site repo; if it isn't, the sync PR stays open with a warning in the run log. Until the secret exists, `site-preview` **soft-skips** with a warning (a preview is a nice-to-have) while `site-sync` **fails loudly** (a silently stale live site would be worse). Fork PRs are skipped (no secret access). If the vendored directory doesn't exist on the site's `main` (it landed in adamdaniel.ai#2280; the guard matters again if the tool is ever unvendored), both workflows no-op with a warning.

## Guides

- [Portable memory across machines](./docs/portable-memory.md) — why auto memory is machine-local by default, and how to make it travel with the repo via `autoMemoryDirectory`.

## Sourcing conventions

Every store, edge, and term traces to documented vanilla behavior in Anthropic's products. Where official docs and the shipping UI disagreed, the shipping UI won. No user-specific configuration is represented.

## License

MIT
