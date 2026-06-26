#!/usr/bin/env python3
"""Generate the Claude memory map suite from shared blocks (single source of truth)."""
import re, pathlib

Q = '&quot;'

# ---------------- shared blocks ----------------
CHAT_CTX = '''subgraph CHAT["Claude chat — claude.ai, mobile and desktop apps"]
direction TB
  C1["Standalone chat"]
  C2["Chat inside a Project"]
  C3["Incognito chat
  (no memory in or out)"]
end'''

ACCT = f'''subgraph ACCT["On your account — online, any device"]
direction TB
  S1["Saved facts ({Q}memory edits{Q})
  (applied immediately, not the daily sync)"]
  S2["Chat-history summary
  ({Q}memory summary{Q})"]
  S3["Project memory ({Q}project-scoped
  memory{Q}) — one per Project"]
end'''

SET = f'''SET["Settings → Memory page
({Q}Manage memory{Q} · home of the
{Q}Generate memory from chat history{Q} toggle)"]'''

CHAT_FLOWS = '''C1 -- "synthesized daily" --> S2
C1 -- "saying “remember this”" --> S1
S1 -. "feeds" .-> S2
S2 -- "loaded into every new standalone chat" --> C1
S1 --> C1
C2 <-- "chatting · saying “remember this” · recalled in that Project's chats" --> S3
S2 -. "displayed here, refreshed daily · export" .-> SET
SET -. "your edits · imports" .-> S1'''

CW_CTX = f'''subgraph CW["Claude Cowork — desktop"]
direction TB
  YOU["You, at the desktop"]
  C8["Your phone, via Dispatch"]
  C6["Session inside a project"]
  C7["One-off session ({Q}standalone
  session{Q}) — keeps nothing afterward"]
end

subgraph CWLOC["On one computer — Cowork"]
  S7["Cowork project memory"]
end'''

CW_FLOWS = '''C6 <-- "remembers as you work · recalled when you reopen it" --> S7
YOU -- "work in it directly" --> C6
YOU --> C7
C8 -- "sends tasks to run on the desktop" --> C6
C8 --> C7'''

COWORK_MD = 'CW <-- "you or Claude writes it (e.g. /init) · read at session start" --> S4'
C8NODE = 'C8["Your phone, via Dispatch"]'
DISP_WIN = 'C8 -. "can send tasks to local Claude Code (observed: Windows side only, not WSL)" .-> WINSIDE'
DISP_MAC = 'C8 -. "can send tasks to local Claude Code" .-> MACSIDE'

WSLSIDE = '''subgraph WSLSIDE["runs on the WSL (Linux) side"]
direction TB
  K1["CLI in WSL — bash"]
  K2["CLI in WSL — pwsh
  (pwsh is just a shell; the
  process still lives in WSL)"]
  K3["VS Code on Windows,
  Remote-WSL connection
  (the server runs inside WSL)"]
end'''

WINSIDE = '''subgraph WINSIDE["runs on the Windows side"]
direction TB
  K4["CLI in Windows"]
  K5["VS Code on Windows — local"]
end'''

MACSIDE = '''subgraph MACSIDE["runs on your Mac"]
direction TB
  K6["CLI on Mac — Terminal"]
  K7["VS Code on Mac"]
end'''

C5 = '''C5["On the web
(fresh cloud sandbox per task)"]'''

def repo_block(term):
    return f'''subgraph REPO["Saved with the project's files"]
  S4["Project notes file — CLAUDE.md
  ({Q}project instructions{Q})
  (one per {term},
  read by whatever opens it)"]
end'''

REPO_CODE = repo_block('repo')                      # Claude Code contexts only
REPO_CW   = repo_block('project folder')            # Cowork context only
REPO_BOTH = repo_block('repo/project folder')       # both contexts present

WSLFS = f'''subgraph WSLFS["WSL file system — ~/.claude"]
direction TB
  W1["User CLAUDE.md — WSL
  ({Q}user instructions{Q})
  (all projects on this side)"]
  W2["Claude's own notes — WSL
  ({Q}auto memory{Q})
  (one set per project, on this side only)"]
end'''

WINFS = f'''subgraph WINFS["Windows file system — C:\\Users\\you\\.claude"]
direction TB
  N1["User CLAUDE.md — Windows
  ({Q}user instructions{Q})
  (all projects on this side)"]
  N2["Claude's own notes — Windows
  ({Q}auto memory{Q})
  (one set per project, on this side only)"]
end'''

MACFS = f'''subgraph MACFS["Mac file system — ~/.claude"]
direction TB
  M1["User CLAUDE.md — Mac
  ({Q}user instructions{Q})
  (all projects on this Mac)"]
  M2["Claude's own notes — Mac
  ({Q}auto memory{Q})
  (one set per project)"]
end'''

WRITE_READ = "you write it · read at session start"
JOTS = "it jots notes as it works, incl. “remember this” · read at session start"
BUNDLED = "you write the user file · it jots notes, incl. “remember this” · all read at session start"

WEB_FLOWS = '''S4 -- "read at session start" --> C5
C5 -. "can update it by saving changes to the project" .-> S4'''

def detail_flows(side, user, auto):
    return (f'{side} <-- "{WRITE_READ}" --> {user}\n'
            f'{side} <-- "{JOTS}" --> {auto}\n'
            f'{side} <-- "{WRITE_READ}" --> S4')

def bundled_flows(side, fs):
    return (f'{side} <-- "{BUNDLED}" --> {fs}\n'
            f'{side} <-- "{WRITE_READ}" --> S4')

# ---------------- styling ----------------
CLASSDEFS = '''classDef ctx fill:#FFFFFF,stroke:#8A8478,stroke-width:1.2px,color:#3D3A34
classDef quiet fill:#FDFBF7,stroke:#B7B1A4,stroke-width:1px,color:#6B675E
classDef acct fill:#EEF3F8,stroke:#4A6B8F,stroke-width:1.2px,color:#3D3A34
classDef repo fill:#F7F3E8,stroke:#9A6F33,stroke-width:1.2px,color:#3D3A34
classDef wsl fill:#EFF5F0,stroke:#54805C,stroke-width:1.2px,color:#3D3A34
classDef win fill:#FBF0EC,stroke:#B06A4F,stroke-width:1.2px,color:#3D3A34
classDef mac fill:#EDF1F5,stroke:#5B6B7F,stroke-width:1.2px,color:#3D3A34
classDef cwloc fill:#F6EFF4,stroke:#8F5C82,stroke-width:1.2px,color:#3D3A34'''

NODE_CLASS = {
    'ctx':  ['C1','C2','K1','K2','K3','K4','K5','K6','K7','C5','C6','C8','YOU','SET'],
    'quiet':['C3','C7'],
    'acct': ['S1','S2','S3'],
    'repo': ['S4'],
    'wsl':  ['W1','W2'],
    'win':  ['N1','N2'],
    'mac':  ['M1','M2'],
    'cwloc':['S7'],
}

SG_STYLE = {
    'CHAT':   'fill:#FDFBF7,stroke:#C9C3B6,stroke-width:1px,color:#6B675E',
    'CODE':   'fill:#FDFBF7,stroke:#C9C3B6,stroke-width:1px,color:#6B675E',
    'CW':     'fill:#FDFBF7,stroke:#C9C3B6,stroke-width:1px,color:#6B675E',
    'WSLSIDE':'fill:#FCFEFC,stroke:#A9C2AF,stroke-width:1px,color:#54805C',
    'WINSIDE':'fill:#FFFBF9,stroke:#D6A893,stroke-width:1px,color:#B06A4F',
    'MACSIDE':'fill:#FBFCFE,stroke:#9FAEBE,stroke-width:1px,color:#5B6B7F',
    'ACCT':   'fill:#FBFDFF,stroke:#A8BBD1,stroke-width:1px,color:#4A6B8F',
    'REPO':   'fill:#FFFEF9,stroke:#C9A36B,stroke-width:1px,color:#9A6F33',
    'WSLFS':  'fill:#FCFEFC,stroke:#A9C2AF,stroke-width:1px,color:#54805C',
    'WINFS':  'fill:#FFFBF9,stroke:#D6A893,stroke-width:1px,color:#B06A4F',
    'MACFS':  'fill:#FBFCFE,stroke:#9FAEBE,stroke-width:1px,color:#5B6B7F',
    'CWLOC':  'fill:#FEFCFE,stroke:#C2A9BB,stroke-width:1px,color:#8F5C82',
}

def styles_for(body):
    out = [CLASSDEFS]
    for cls, nodes in NODE_CLASS.items():
        present = [n for n in nodes if re.search(rf'\b{n}\[', body)]
        if present:
            out.append(f"class {','.join(present)} {cls}")
    for sg, st in SG_STYLE.items():
        if re.search(rf'subgraph {sg}\[', body):
            out.append(f"style {sg} {st}")
    return '\n'.join(out)

def assemble(title, blocks, spacing=None):
    body = '\n\n'.join(blocks)
    cfg = ''
    if spacing:
        cfg = f'config:\n  flowchart:\n    nodeSpacing: {spacing[0]}\n    rankSpacing: {spacing[1]}\n'
    return f'---\ntitle: "{title}"\n{cfg}---\nflowchart LR\n\n{body}\n\n{styles_for(body)}\n'

def code_wrap(sides_and_web):
    inner = '\n\n'.join(sides_and_web)
    inner = '\n'.join('  ' + l if l else l for l in inner.split('\n'))
    return f'subgraph CODE["Claude Code"]\ndirection TB\n\n{inner}\nend'

# ---------------- variants ----------------
variants = {}

variants['chat'] = assemble('Claude memory map — chat only',
    [CHAT_CTX, ACCT, SET, CHAT_FLOWS])

variants['except-claude-code'] = assemble('Claude memory map — everything except Claude Code',
    [CHAT_CTX, ACCT, SET, CW_CTX, REPO_CW, CHAT_FLOWS, CW_FLOWS, COWORK_MD])

variants['claude-code-windows'] = assemble('Claude memory map — Claude Code (Windows, incl. WSL)',
    [WSLSIDE, WINSIDE, C5, REPO_CODE, WSLFS, WINFS,
     detail_flows('WSLSIDE','W1','W2'), detail_flows('WINSIDE','N1','N2'), WEB_FLOWS,
     C8NODE, DISP_WIN])

variants['claude-code-mac'] = assemble('Claude memory map — Claude Code (Mac)',
    [MACSIDE, C5, REPO_CODE, MACFS, detail_flows('MACSIDE','M1','M2'), WEB_FLOWS,
     C8NODE, DISP_MAC])

variants['claude-code-all'] = assemble('Claude memory map — Claude Code (all platforms)',
    [MACSIDE, WINSIDE, WSLSIDE, C5, MACFS, WINFS, WSLFS, REPO_CODE,
     detail_flows('MACSIDE','M1','M2'), detail_flows('WINSIDE','N1','N2'),
     detail_flows('WSLSIDE','W1','W2'), WEB_FLOWS,
     C8NODE, DISP_WIN, DISP_MAC], spacing=(70,120))

variants['complete-windows'] = assemble('Claude memory map — complete (Windows, incl. WSL)',
    [CHAT_CTX, ACCT, SET, code_wrap([WSLSIDE, WINSIDE, C5]), REPO_BOTH, WSLFS, WINFS, CW_CTX,
     CHAT_FLOWS, bundled_flows('WSLSIDE','WSLFS'), bundled_flows('WINSIDE','WINFS'),
     WEB_FLOWS, CW_FLOWS, COWORK_MD, DISP_WIN])

variants['complete-mac'] = assemble('Claude memory map — complete (Mac)',
    [CHAT_CTX, ACCT, SET, code_wrap([MACSIDE, C5]), REPO_BOTH, MACFS, CW_CTX,
     CHAT_FLOWS, bundled_flows('MACSIDE','MACFS'), WEB_FLOWS, CW_FLOWS, COWORK_MD, DISP_MAC])

variants['complete-all'] = assemble('Claude memory map — complete (all platforms)',
    [CHAT_CTX, ACCT, SET, code_wrap([WSLSIDE, WINSIDE, MACSIDE, C5]), REPO_BOTH,
     WSLFS, WINFS, MACFS, CW_CTX,
     CHAT_FLOWS, bundled_flows('WSLSIDE','WSLFS'), bundled_flows('WINSIDE','WINFS'),
     bundled_flows('MACSIDE','MACFS'), WEB_FLOWS, CW_FLOWS, COWORK_MD, DISP_WIN, DISP_MAC])

outdir = pathlib.Path(__file__).resolve().parent.parent / 'suite'
outdir.mkdir(parents=True, exist_ok=True)
for name, src in variants.items():
    (outdir / f'{name}.mermaid').write_text(src)
    print('wrote', name)
