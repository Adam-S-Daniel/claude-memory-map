# Prototype spec — reimagined UX for the Claude memory map

This directory holds UX prototypes (spikes) that reimagine how `index.html`'s
canonical memory model is *experienced*. They are not wired into the build or
tests, and must not modify anything outside `prototypes/`.

References: Firefox Lightbeam (living force graph; shared nodes visibly bridge,
siloed ones stand apart; the picture assembles incrementally) and Little
Snitch's Network Monitor (at-a-glance overview + per-item drill-down; pairing
revelation with agency). Design finding to honor: maps of hidden system
behavior earn love when they give **agency or delight**, not transparency
alone — there must be an equivalent of "click the surprising connection and
inspect it."

## Hard constraints (all prototypes)

1. **Single self-contained HTML file** in `prototypes/`. No CDN dependency for
   core function — hand-roll layout/rendering (SVG or canvas + your own force
   sim / layout code). Works from `file://`.
2. **Faithful to the canonical model below** — its facts, edge labels, and
   official terminology. Do not invent stores, flows, or sync behavior.
3. **Mobile is not an afterthought**: 390px-wide layout must be genuinely
   usable (44px touch targets, no horizontal page scroll, readable text).
4. **Demo mode**: when loaded with `?demo` in the URL, preselect this
   representative set — `ch_standalone, ch_project, mac_cli, win_cli_native,
   win_cli_wsl, code_web, cw_project` — and, if the design has an
   inspector/drill-down, open it on a *surprising* item (see Surprises). Used
   by the screenshot harness.
5. Plain vanilla JS, no build step, no external fonts. Keep the repo's calm
   paper-toned aesthetic as a starting point (`--paper:#FDFBF7 --ink:#3D3A34
   --line:#E4DFD4`, accent colors below) but you may evolve it.

## Canonical data model (single source of truth: src/build_picker2.py + build_picker3.py)

Inline this model (verbatim facts; adapt the JS shape freely).

### Contexts (the ways you use Claude — user-selectable)

| id | label | group | stores touched |
|---|---|---|---|
| ch_standalone | Chats not inside a Project ("standalone" chats) | Claude chat | chatmem, prefs |
| ch_project | Chats inside a Project | Claude chat | projmem, prefs |
| mac_app_local | Claude Desktop app — local sessions (Mac) | Claude Code · Mac | macumd, macauto, repo |
| mac_cli | CLI in the terminal (Mac) | Claude Code · Mac | macumd, macauto, repo |
| mac_vscode | VS Code with the Claude Code extension (Mac) | Claude Code · Mac | macumd, macauto, repo |
| mac_app_web | Desktop app (Mac) → Claude Code on the web sessions | Claude Code · web | repo |
| win_app_local | Claude Desktop app — local sessions (Windows side) | Claude Code · Windows | winumd, winauto, repo |
| win_cli_native | CLI in Windows — native | Claude Code · Windows | winumd, winauto, repo |
| win_vscode_local | VS Code — local, not WSL (Windows) | Claude Code · Windows | winumd, winauto, repo |
| win_app_web | Desktop app (Windows) → Claude Code on the web sessions | Claude Code · web | repo |
| win_app_rc_wsl | Desktop app (Windows) remote-controlling a CLI session in WSL (Remote Control, /rc) | Claude Code · WSL | wslumd, wslauto, repo |
| win_cli_wsl | CLI in WSL | Claude Code · WSL | wslumd, wslauto, repo |
| win_vscode_wsl | VS Code on Windows connected to WSL (the "WSL" extension) | Claude Code · WSL | wslumd, wslauto, repo |
| code_web | Claude Code on the web — claude.ai/code (fresh cloud sandbox per task) | Claude Code · web | repo |
| cw_project | Cowork sessions inside a project | Claude Cowork | cwmem, repo, prefs |
| cw_standalone | Cowork one-off sessions ("standalone") — keeps nothing afterward | Claude Cowork | repo, prefs |

Notes:
- `win_app_rc_wsl` **implies** `win_cli_wsl` (remote-controlling a WSL CLI
  session implies a CLI session in WSL); session + memory stay in WSL (observed).
- The original picker also has `cw_desktop` ("in the Claude Desktop app") — a
  way *into* Cowork, not a session; it touches no stores. Prototypes may fold
  it away or keep it as an entry annotation.
- The desktop app used only as a web-session launcher is client-only: nothing
  lands on that machine.

### Stores (memory homes → stores)

Homes: **On your account** (online, any device) · **Saved with the project's
files** (travels with the repo) · **Mac file system** `~/.claude` · **Windows
file system** `C:\Users\you\.claude` · **WSL file system** `~/.claude` ·
**On one computer — Cowork** · *(Claude Code on the web has no home of its
own: fresh cloud sandbox per task.)*

| id | official name | home | scope | facts (in / out) |
|---|---|---|---|---|
| chatmem | Memory from chat history | account | across | Two parts: chat-history summary ("memory summary", synthesized daily from standalone chats) + saved facts ("memory edits", applied immediately when you say "remember this"). Saved facts feed the summary. Loaded into every new standalone chat. Displayed & managed at Settings → Memory ("Manage memory", home of the "Generate memory from chat history" toggle; your edits/imports become saved facts; export available). |
| prefs | Instructions for Claude | account | across | Free-text box at Settings → Profile ("Instructions" in the app). Anthropic: "Claude will keep these in mind across chats and Cowork within Anthropic's guidelines." Applied to every chat and to Cowork sessions. |
| projmem | Project memory ("project-scoped memory") | account | within | One per claude.ai Project. Filled by chatting and by saying "remember this" in that Project; recalled in that Project's chats only. |
| repo | Project notes file — CLAUDE.md ("project instructions") | repo | within | One per repo/project folder; read at session start by whatever opens it. You write it (code contexts); in Cowork, you or Claude writes it (e.g. /init). Web sessions read it at session start and can update it by saving changes to the project. |
| macumd | User CLAUDE.md — Mac ("user instructions") | macfs | across | You write it; applies to all projects on this Mac; read at session start. |
| winumd | User CLAUDE.md — Windows ("user instructions") | winfs | across | Same, for the Windows side. |
| wslumd | User CLAUDE.md — WSL ("user instructions") | wslfs | across | Same, for the WSL side. |
| macauto | Auto memory — Mac (Claude's own notes) | macfs | within | Claude jots notes as it works, incl. "remember this"; one set per project, on this side only; read at session start. Relocatable into a repo-tracked folder via the `autoMemoryDirectory` setting. |
| winauto | Auto memory — Windows | winfs | within | Same, Windows side. |
| wslauto | Auto memory — WSL | wslfs | within | Same, WSL side. |
| cwmem | Cowork project memory | cwloc | within | One per Cowork project, kept on that computer. Remembers as you work; recalled when you reopen that project. |

### Sync semantics (the headline question)

A store is **in sync across your selection** iff *every* selected session
context touches it; otherwise it is **kept separate** (show who has it).
Caveats: CLAUDE.md sync assumes the contexts open the same repo/project
folder; with a single context selected there is nothing to sync across yet.

Scope lens (optional but valued): "remembered across projects/repos" =
chatmem, prefs, macumd, winumd, wslumd; "within one project/repo" = projmem,
repo, macauto, winauto, wslauto, cwmem. Under the across-lens, web contexts
remember nothing across repos; under the within-lens, standalone chats
remember nothing project-scoped.

### Surprises (the "click the surprising connection" inventory)

- WSL and native Windows are **different sides**: separate user CLAUDE.md and
  separate auto memory, even on the same physical machine.
- Claude Code on the web reads **only the repo's CLAUDE.md** — no user
  CLAUDE.md, no auto memory; fresh cloud sandbox per task.
- Remote Control (/rc) from the Windows desktop app: the session **and its
  memory stay in WSL** (observed).
- One-off Cowork sessions **keep nothing afterward** (they still read
  CLAUDE.md and your Instructions).
- Auto memory is **machine-local by default**; the `autoMemoryDirectory`
  setting can move it into the repo so it travels (see docs/portable-memory.md).
- Standalone chats and Project chats have **disjoint memories**: memory from
  chat history is loaded only into standalone chats; Project memory is
  recalled only inside its Project. Only "Instructions for Claude" spans both.

### Palette (from index.html)

account/blue `#4A6B8F` · repo/amber `#9A6F33` · WSL green `#54805C` ·
Windows rust `#B06A4F` · Mac slate `#5B6B7F` · Cowork plum `#8F5C82` ·
web/cloud gray `#8A8478` · paper `#FDFBF7` · ink `#3D3A34` · line `#E4DFD4`.

## Screenshot harness

`node prototypes/shot.js prototypes/<file>.html` → writes
`prototypes/screenshots/<file>-desktop.png` (1400×900) and
`<file>-mobile.png` (390×844), loading the page with `?demo`. Requires
`npm install` to have run (puppeteer-core; auto-detects Chrome under
`~/.cache/puppeteer`, same resolution as tests/tests_picker.js).
