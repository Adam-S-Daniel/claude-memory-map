# Claude Memory Map

**What Claude remembers — an interactive map.** Check the ways you use Claude (chat, Claude Code, Cowork) and watch a diagram of every memory store assemble live: what gets in, where it lives, and how it comes back out.

**[Open the picker → `index.html`](./index.html)** (single self-contained file; works from a local clone or GitHub Pages)

## What it answers

- Which memories follow you across projects/repos, and which stay siloed per project?
- If you work in WSL *and* native Windows, which stores are duplicated?
- What does Claude Code on the web actually read? (Only the repo's `CLAUDE.md` — nothing cross-repo.)
- What do standalone chats remember that project chats don't, and vice versa?

## Features

- **Live composition** — every node/edge is generated at render time from your checkbox selection (~2M permutations from one canonical block set)
- **Sync summary** — above the chart: which stores are *in sync across your selection* vs *kept separate*, with per-store context coverage
- **Scope lens** — "I'm interested in" filters to memory remembered across projects/repos, within one, or both; contexts that can't support the chosen scope disable with an inline explanation
- **Brief/Full labels** — compact names with a legend, or self-contained descriptions, toggleable
- **Official terminology throughout** — every store carries Anthropic's shipping name (e.g. "Memory from chat history", "Instructions for Claude", "auto memory", "user/project instructions"), with per-context terms (repo vs project folder) adapting to the selection
- **Mobile-friendly** — stacked layout, 44px touch targets, sticky sync summary, fit-width default

## Repository layout

```
index.html            the picker (build output — fully self-contained)
src/
  build_picker3.py    builds index.html (UI shell, sync model, labels)
  build_picker2.py    canonical Mermaid block generator (extracted at build time)
  generate_suite.py   builds the 8 static curated diagrams in suite/
tests/
  tests_picker.js     71-test puppeteer e2e suite
scripts/
  dev-server.js       zero-dep dev server: serve + live-reload + auto-rebuild
suite/                .mermaid sources for those diagrams — a fuller reference set
                      that intentionally includes contexts the interactive picker omits
                      (incognito chats, Dispatch) and some earlier labels. index.html
                      is the current source of truth for terminology and coverage.
```

## Build & test

```bash
python3 src/build_picker3.py     # writes index.html
npm install                      # puppeteer-core + chromium for tests
node tests/tests_picker.js       # 71 tests: behavior, mobile, semantics, regressions
```

Rendering uses Mermaid 11.12.0 from cdnjs at runtime; the page degrades gracefully (shows the generated Mermaid source) if the CDN is unreachable.

## Local development & debugging

The test harness runs serverless Chromium in CI (`@sparticuz/chromium` at `/tmp/chromium`). For local work it auto-detects a desktop Chrome, so a one-time browser install is all that's needed:

```bash
npm install
npm run setup:browser    # downloads Chrome-for-Testing into ~/.cache/puppeteer (Linux/WSL)
npm test                 # uses that Chrome automatically
```

**Run the suite (local):** `npm test` resolves a browser in this order — `CHROMIUM_PATH` → newest Chrome under `~/.cache/puppeteer` → `/tmp/chromium` (CI). To watch it drive the UI:

```bash
npm run test:headed      # visible browser window
npm run test:debug       # visible + DevTools open + 150ms SLOWMO per step
# or ad hoc:  HEADED=1 DEVTOOLS=1 SLOWMO=200 node tests/tests_picker.js
#             CHROMIUM_PATH=/path/to/chrome node tests/tests_picker.js
```

**Interactively debug `index.html`:** a zero-dependency dev server serves the page over HTTP (real origin, not `file://`), live-reloads on rebuild, and re-runs the Python build whenever `src/*.py` changes:

```bash
npm run dev              # build once, then serve with watch + live-reload on http://localhost:8000
npm run serve            # serve current index.html without the initial build
# options:  node scripts/dev-server.js --port 9000 --no-build
```

Open the printed `http://localhost:<port>/` in your browser (on WSL, your Windows browser works — `localhost` is forwarded) and use DevTools (F12). Edit a `src/*.py` builder and save: the server rebuilds `index.html` and the page reloads itself.

## Guides

- [Portable memory across machines](./docs/portable-memory.md) — why auto memory is machine-local by default, and how to make it travel with the repo via `autoMemoryDirectory`.

## Sourcing conventions

Every store, edge, and term traces to documented vanilla behavior in Anthropic's products. Where official docs and the shipping UI disagreed, the shipping UI won. No user-specific configuration is represented.

## License

MIT
