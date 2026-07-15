# UX prototypes — reimagining the memory map

A spike exploring how the picker's canonical memory model could be
*experienced*, drawing on Firefox Lightbeam (living force graph) and Little
Snitch's Network Monitor (overview + drill-down). Not wired into the build or
tests; `index.html` is untouched. See `SPEC.md` for the shared canonical data
model and constraints all three candidates were built against.

## Candidates

| file | direction | one-liner |
|---|---|---|
| `constellation.html` | **Winner** — Lightbeam-leaning living graph | Contexts and store-orbs in a hand-rolled force sim; shared stores become hubs, per-side silos drift into islands; full drill-down dossier per node |
| `monitor.html` | Little Snitch-leaning monitor | Stable board of the seven memory homes with live traces from selected contexts; click-anything dossier inspector |
| `hybrid.html` | Graph + surprise badges | Force graph with ⚠ badges flagging counterintuitive facts as the navigation; inspector on tap |

All are single self-contained HTML files (no CDN; work from `file://`),
mobile-usable at 390px, and support `?demo` (preselects a representative
7-context selection; used by the screenshot harness).

## Why constellation won

It is the only candidate where the map's headline answer — *which memories
are in sync across your ways of using Claude, and which are silos* — is felt
structurally rather than read: the repo's CLAUDE.md is visibly the one hub
bridging every code context while the Mac/Windows/WSL homes pull into
separate islands. The refinement pass grafted the runners-up's best ideas:
monitor.html's full dossier inspector (what gets in / how it comes back out /
who touches it / sync status / "act on it"), and hybrid.html's "see for
yourself" sibling-store cross-links and coverage counts ("only in: CLI · WSL
— 1 of 7") in the expandable sync strip.

## Run / screenshot

```bash
npm run serve                     # then open http://localhost:8000/prototypes/constellation.html
# or simply open prototypes/constellation.html in a browser (file:// works)

node prototypes/shot.js prototypes/constellation.html   # desktop + mobile PNGs into prototypes/screenshots/
```

## If promoted to replace the real picker

The prototype trades the generated-Mermaid pipeline for a hand-rolled canvas
sim, so promotion would mean: extracting the inlined data model so
`build_picker2.py`'s canonical blocks and the prototype's `MODEL` share one
source of truth (today the facts are duplicated by hand from SPEC.md);
porting the picker's remaining semantics that the spike dropped (scope lens,
brief/full label modes, the `cw_desktop` entry annotation, Settings→Memory
node); adding accessibility the canvas lacks (keyboard navigation and a
screen-reader-readable equivalent of the graph — the sync strip and dossier
are DOM already, the graph itself is not); and rewriting `tests_picker.js`
against the new interaction surface before deleting the Mermaid path.
