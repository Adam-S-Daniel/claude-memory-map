# Claude Memory Map

**What Claude remembers — an interactive map.** Check the ways you use Claude (chat, Claude Code, Cowork) and watch a diagram of every memory store assemble live: what gets in, where it lives, and how it comes back out.

**[Open the picker → `index.html`](./index.html)** (single self-contained file; works from a local clone or GitHub Pages)

## What it answers

- Which memories follow you across projects/repos, and which stay siloed per project?
- If you work in WSL *and* native Windows, which stores are duplicated?
- What does Claude Code on the web actually read? (Only the repo's `CLAUDE.md` — nothing cross-repo.)
- What do standalone chats remember that project chats don't, and vice versa?

## Features

- **Live composition** — every node/edge is generated at render time from your checkbox selection (~2M permutations from one canonical block set; no pre-rendered variants)
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
  tests_picker.js     71-test puppeteer e2e suite (developed red/green TDD)
suite/                static curated diagram variants (.mermaid sources)
```

## Build & test

```bash
python3 src/build_picker3.py     # writes index.html
npm install                      # puppeteer-core + chromium for tests
node tests/tests_picker.js       # 71 tests: behavior, mobile, semantics, regressions
```

Rendering uses Mermaid 11.12.0 from cdnjs at runtime; the page degrades gracefully (shows the generated Mermaid source) if the CDN is unreachable.

## Sourcing conventions

Every store, edge, and term traces to documented vanilla behavior in Anthropic's products. Where official docs and the shipping UI disagreed, the shipping UI won. No user-specific configuration is represented.

## License

MIT
