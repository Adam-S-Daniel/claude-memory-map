#!/usr/bin/env python3
"""Build the interactive memory-map picker v2: checkbox tree -> runtime-composed Mermaid chart.

This module now exists solely to hold JS_GENERATOR — the single canonical source of the
Mermaid block generator (compose()). build_picker3.py extracts the JS_GENERATOR string at
build time; nothing executes this file directly.
"""

JS_GENERATOR = r'''
// ---------- canonical text blocks (single source of truth) ----------
const Q = '&quot;';
const NODES = {
  C1:  `C1["Chats not inside a Project\n  (${Q}standalone${Q} chats)"]`,
  C2:  `C2["Chats inside a Project"]`,
  S1:  `S1["Saved facts (${Q}memory edits${Q})\n  (applied immediately, not the daily sync)"]`,
  S2:  `S2["Chat-history summary\n  (${Q}memory summary${Q})"]`,
  S3:  `S3["Project memory (${Q}project-scoped\n  memory${Q}) — one per Project"]`,
  PRF: `PRF["Instructions for Claude — Settings → Profile\n  (${Q}Instructions${Q} in the app)\n  (kept in mind across chats & Cowork)"]`,
  SET: `SET["Settings → Capabilities — Memory\n(${Q}View and edit memory${Q} opens the ${Q}Manage memory${Q} panel ·\nhome of the ${Q}Generate memory from chat history${Q} toggle)"]`,
  MAPP:`MAPP["Claude Desktop app__MAPP_SUFFIX__"]`,
  K6:  `K6["CLI on Mac — Terminal"]`,
  K7:  `K7["VS Code with the\nClaude Code extension — Mac"]`,
  WAPP:`WAPP["Claude Desktop app__WAPP_SUFFIX__"]`,
  K4:  `K4["CLI in Windows — native"]`,
  K5:  `K5["VS Code with the\nClaude Code extension —\nlocal (not WSL)"]`,
  KW:  `KW["CLI in WSL"]`,
  KV:  `KV["VS Code on Windows,\nconnected to WSL\n(the ${Q}WSL${Q} extension,\nformerly ${Q}Remote - WSL${Q})"]`,
  C5:  `C5["On the web\n(fresh cloud sandbox per task)"]`,
  C6R: `C6R["Session inside a project"]`,
  C7R: `C7R["Session outside a project\n  (no memory carries forward)"]`,
  C6L: `C6L["Session inside a project"]`,
  C7L: `C7L["Session outside a project\n  (no memory carries forward)"]`,
  GI:  `GI["Global instructions — Settings → Cowork\n  (standing instructions for every Cowork session)"]`,
  FI:  `FI["Folder instructions — with a local folder\n  (project-specific context · Claude can\n  update them during a session)"]`,
  S8:  `S8["Cowork sessions & files Claude delivers\n  (reopen on any surface · past remote\n  sessions found by title only)"]`,
  W1:  `W1["User CLAUDE.md — WSL\n  (${Q}user instructions${Q})\n  (all projects on this side)"]`,
  W2:  `W2["Claude's own notes — WSL\n  (${Q}auto memory${Q})\n  (one set per project, on this side only)"]`,
  N1:  `N1["User CLAUDE.md — Windows\n  (${Q}user instructions${Q})\n  (all projects on this side)"]`,
  N2:  `N2["Claude's own notes — Windows\n  (${Q}auto memory${Q})\n  (one set per project, on this side only)"]`,
  M1:  `M1["User CLAUDE.md — Mac\n  (${Q}user instructions${Q})\n  (all projects on this Mac)"]`,
  M2:  `M2["Claude's own notes — Mac\n  (${Q}auto memory${Q})\n  (one set per project, on this Mac only)"]`,
};

function s4Node(){
  return `S4["Project notes file — CLAUDE.md\n  (${Q}project instructions${Q})\n  (one per repo,\n  read by whatever opens it)"]`;
}

function s7Node(remote){
  if (remote) return `S7["Cowork project memory — one per project\n  (what Claude learns in one project\n  doesn't carry over to others)\n  (stored on that computer for desktop projects;\n  not yet documented for remote sessions)"]`;
  return `S7["Cowork project memory\n  (what Claude learns in one project\n  doesn't carry over to others)"]`;
}

const BUNDLED = `you write the user file · it jots notes, incl. “remember this” · all read at session start`;
const WRITE_READ = `you write it · read at session start`;

const CHAT_FLOWS_ALL = [
  ['C1','S2', 'C1 -- "synthesized daily" --> S2'],
  ['C1','S1', 'C1 -- "saying “remember this”" --> S1'],
  ['S1','S2', 'S1 -. "feeds" .-> S2'],
  ['S2','C1', 'S2 -- "loaded into every new standalone chat" --> C1'],
  ['S1','C1', 'S1 --> C1'],
  ['C2','S3', 'C2 <-- "chatting · saying “remember this” · recalled in that Project’s chats" --> S3'],
  ['S2','SET','S2 -. "displayed here, refreshed daily · export" .-> SET'],
  ['SET','S1','SET -. "your edits (immediate) · imports (within a day)" .-> S1'],
];

const CLASSDEFS = `classDef ctx fill:#FFFFFF,stroke:#8A8478,stroke-width:1.2px,color:#3D3A34
classDef quiet fill:#FDFBF7,stroke:#B7B1A4,stroke-width:1px,color:#6B675E
classDef acct fill:#EEF3F8,stroke:#4A6B8F,stroke-width:1.2px,color:#3D3A34
classDef repo fill:#F7F3E8,stroke:#9A6F33,stroke-width:1.2px,color:#3D3A34
classDef wsl fill:#EFF5F0,stroke:#54805C,stroke-width:1.2px,color:#3D3A34
classDef win fill:#FBF0EC,stroke:#B06A4F,stroke-width:1.2px,color:#3D3A34
classDef mac fill:#EDF1F5,stroke:#5B6B7F,stroke-width:1.2px,color:#3D3A34
classDef cwloc fill:#F6EFF4,stroke:#8F5C82,stroke-width:1.2px,color:#3D3A34`;

const NODE_CLASS = {
  ctx: ['C1','C2','MAPP','K6','K7','WAPP','K4','K5','KW','KV','C5','C6R','C6L','SET'],
  quiet: ['C7R','C7L','S8'],
  acct: ['S1','S2','S3','PRF'], repo: ['S4'],
  wsl: ['W1','W2'], win: ['N1','N2'], mac: ['M1','M2'], cwloc: ['S7','FI','GI'],
};
const SG_STYLE = {
  CHAT:'fill:#FDFBF7,stroke:#C9C3B6,stroke-width:1px,color:#6B675E',
  CW:'fill:#FDFBF7,stroke:#C9C3B6,stroke-width:1px,color:#6B675E',
  CWR:'fill:#FDFBF7,stroke:#C9C3B6,stroke-width:1px,color:#6B675E',
  CWL:'fill:#FDFBF7,stroke:#C9C3B6,stroke-width:1px,color:#6B675E',
  WSLSIDE:'fill:#FCFEFC,stroke:#A9C2AF,stroke-width:1px,color:#54805C',
  WINSIDE:'fill:#FFFBF9,stroke:#D6A893,stroke-width:1px,color:#B06A4F',
  MACSIDE:'fill:#FBFCFE,stroke:#9FAEBE,stroke-width:1px,color:#5B6B7F',
  ACCT:'fill:#FBFDFF,stroke:#A8BBD1,stroke-width:1px,color:#4A6B8F',
  REPO:'fill:#FFFEF9,stroke:#C9A36B,stroke-width:1px,color:#9A6F33',
  WSLFS:'fill:#FCFEFC,stroke:#A9C2AF,stroke-width:1px,color:#54805C',
  WINFS:'fill:#FFFBF9,stroke:#D6A893,stroke-width:1px,color:#B06A4F',
  MACFS:'fill:#FBFCFE,stroke:#9FAEBE,stroke-width:1px,color:#5B6B7F',
  CWLOC:'fill:#FEFCFE,stroke:#C2A9BB,stroke-width:1px,color:#8F5C82',
};

// ---------- composition ----------
function compose(sel){
  const hints = [];
  const has = id => !!sel[id];

  // implications
  const kw  = has('win_cli_wsl') || has('win_app_rc_wsl');
  if (has('win_app_rc_wsl') && !has('win_cli_wsl'))
    hints.push('Remote-controlling a WSL CLI session implies a CLI session in WSL — added to the map.');
  const k6  = has('mac_cli');

  const wapp = has('win_app_local') || has('win_app_web') || has('win_app_rc_wsl');
  const mapp = has('mac_app_local') || has('mac_app_web');
  // side = an actual session running on that side (client-only desktop-app use doesn't count)
  const winSide = has('win_app_local') || has('win_cli_native') || has('win_vscode_local');
  const wslSide = kw || has('win_vscode_wsl');
  const macSide = has('mac_app_local') || k6 || has('mac_vscode');
  const c5 = has('code_web') || has('mac_app_web') || has('win_app_web');
  const cwRemoteProject = has('cw_remote_project');
  const cwRemoteNoproj  = has('cw_remote_noproj');
  const cwLocalProject  = has('cw_local_project');
  const cwLocalNoproj   = has('cw_local_noproj');
  const cwRemote  = cwRemoteProject || cwRemoteNoproj;
  const cwLocal   = cwLocalProject || cwLocalNoproj;
  const cwSession = cwRemote || cwLocal;
  const chatAny = has('ch_standalone') || has('ch_project');

  const blocks = [];
  const present = new Set();
  const sgs = new Set();
  const node = id => { present.add(id); return NODES[id]; };

  // chat
  if (chatAny){
    const inner = [];
    if (has('ch_standalone')) inner.push('  '+node('C1'));
    if (has('ch_project'))    inner.push('  '+node('C2'));
    sgs.add('CHAT');
    blocks.push('subgraph CHAT["Claude chat — claude.ai, mobile and desktop apps"]\ndirection TB\n'+inner.join('\n')+'\nend');
    if (has('ch_standalone')) blocks.push(node('SET'));
  }
  {
    const acct = [];
    if (has('ch_standalone')) { acct.push('  '+node('S1'), '  '+node('S2')); }
    if (has('ch_project'))    acct.push('  '+node('S3'));
    if (chatAny || cwSession) acct.push('  '+node('PRF'));
    if (cwRemote) acct.push('  '+node('S8'));
    if (acct.length){
      sgs.add('ACCT');
      blocks.push('subgraph ACCT["On your account — online, any device"]\ndirection TB\n'+acct.join('\n')+'\nend');
    }
  }

  // code sides
  function side(id, title, ids){
    const inner = ids.filter(Boolean).map(n => '  '+node(n));
    sgs.add(id);
    blocks.push(`subgraph ${id}["${title}"]\ndirection TB\n`+inner.join('\n')+'\nend');
  }
  if (macSide) side('MACSIDE','runs on your Mac',
      [has('mac_app_local')?'MAPP':null, k6?'K6':null, has('mac_vscode')?'K7':null]);
  if (winSide) side('WINSIDE','runs on the Windows side',
      [has('win_app_local')?'WAPP':null, has('win_cli_native')?'K4':null, has('win_vscode_local')?'K5':null]);
  // desktop app as client only (web launcher / remote control): standalone node outside the side groups
  if (mapp && !has('mac_app_local')) blocks.push(node('MAPP'));
  if (wapp && !has('win_app_local')) blocks.push(node('WAPP'));
  if (wslSide) side('WSLSIDE','runs on the WSL (Linux) side',
      [kw?'KW':null, has('win_vscode_wsl')?'KV':null]);
  if (c5) blocks.push(node('C5'));

  // stores
  const localCode = winSide || wslSide || macSide;
  const s4 = localCode || c5;
  if (s4){
    present.add('S4'); sgs.add('REPO');
    blocks.push('subgraph REPO["Saved with the project’s files"]\n  '+s4Node()+'\nend');
  }
  function fs(id, title, a, b){
    sgs.add(id);
    blocks.push(`subgraph ${id}["${title}"]\ndirection TB\n  `+node(a)+'\n  '+node(b)+'\nend');
  }
  if (macSide) fs('MACFS','Mac file system — ~/.claude','M1','M2');
  if (winSide) fs('WINFS','Windows file system — C:\\Users\\you\\.claude','N1','N2');
  if (wslSide) fs('WSLFS','WSL file system — ~/.claude','W1','W2');

  // cowork
  if (cwSession){
    const groups = [];
    if (cwRemote){
      const rInner = [];
      if (cwRemoteProject) rInner.push('    '+node('C6R'));
      if (cwRemoteNoproj)  rInner.push('    '+node('C7R'));
      sgs.add('CWR');
      groups.push(`  subgraph CWR["Remote sessions — run on Anthropic's servers (beta, the default)"]\n  direction TB\n`+rInner.join('\n')+'\n  end');
    }
    if (cwLocal){
      const lInner = [];
      if (cwLocalProject) lInner.push('    '+node('C6L'));
      if (cwLocalNoproj)  lInner.push('    '+node('C7L'));
      sgs.add('CWL');
      groups.push('  subgraph CWL["Local sessions — run on your computer (desktop app, isolated VM)"]\n  direction TB\n'+lInner.join('\n')+'\n  end');
    }
    sgs.add('CW');
    blocks.push('subgraph CW["Claude Cowork — chat & Cowork share one home (claude.ai · mobile · desktop)"]\ndirection TB\n'+groups.join('\n\n')+'\nend');

    blocks.push(node('GI'));
    blocks.push(node('FI'));

    if (cwLocalProject || cwRemoteProject){
      present.add('S7');
      if (cwRemoteProject){
        blocks.push(s7Node(true));
      } else {
        sgs.add('CWLOC');
        blocks.push('subgraph CWLOC["On one computer — Cowork"]\n  '+s7Node(false)+'\nend');
      }
    }
  }

  // flows
  const flows = [];
  for (const [a,b,edge] of CHAT_FLOWS_ALL)
    if (present.has(a) && present.has(b)) flows.push(edge);

  if (macSide){ flows.push(`MACSIDE <-- "${BUNDLED}" --> MACFS`); if (s4) flows.push(`MACSIDE <-- "${WRITE_READ}" --> S4`); }
  if (winSide){ flows.push(`WINSIDE <-- "${BUNDLED}" --> WINFS`); if (s4) flows.push(`WINSIDE <-- "${WRITE_READ}" --> S4`); }
  if (wslSide){ flows.push(`WSLSIDE <-- "${BUNDLED}" --> WSLFS`); if (s4) flows.push(`WSLSIDE <-- "${WRITE_READ}" --> S4`); }
  if (c5 && present.has('S4')){
    flows.push('S4 -- "read at session start" --> C5');
    flows.push('C5 -. "can update it by saving changes to the project" .-> S4');
  }
  if (has('mac_app_web')) flows.push('MAPP -. "opens web sessions (they run in the cloud)" .-> C5');
  if (has('win_app_web')) flows.push('WAPP -. "opens web sessions (they run in the cloud)" .-> C5');
  if (has('win_app_rc_wsl'))
    flows.push('WAPP -. "remote-controls it (Remote Control, /rc) · session + memory stay in WSL (observed)" .-> KW');

  if (present.has('PRF')){
    if (chatAny) flows.push('PRF -- "applied to every chat" --> CHAT');
    if (cwSession) flows.push('PRF -- "applied to Cowork sessions (per the Settings-page description)" --> CW');
  }
  if (cwSession){
    if (cwLocalProject && present.has('S7'))
      flows.push('C6L <-- "learns from tasks in the project · applied to future tasks there" --> S7');
    if (cwRemoteProject && present.has('S7'))
      flows.push('C6R <-- "learns from tasks in the project · applied to future tasks there" --> S7');
    if (cwLocal)
      flows.push('CWL <-- "you or Claude writes them · added when a session uses that folder" --> FI');
    if (cwRemote)
      flows.push(`FI -. "via the Claude Desktop app — only while it's open & the folder is connected" .-> CWR`);
    flows.push('GI -- "applied to every Cowork session" --> CW');
    if (cwRemote)
      flows.push(`CWR -- "the session + files Claude delivers are saved · working files aren't kept" --> S8`);
  }

  let noFlowIdx = -1;
  if (cwSession){
    const src = present.has('S2') ? 'S2' : (present.has('S3') ? 'S3' : (present.has('S1') ? 'S1' : null));
    if (src){
      noFlowIdx = flows.length;
      flows.push(`${src} x-. "✕ MEMORY IS CHAT-ONLY — what Claude remembers about you in chat doesn't carry into Cowork yet" .-x CW`);
    }
  }

  // node text suffixes for desktop-app nodes
  let body = blocks.join('\n\n') + '\n\n' + flows.join('\n');
  body = body.replace('__MAPP_SUFFIX__', has('mac_app_local') ? ' —\nlocal sessions' : '');
  body = body.replace('__WAPP_SUFFIX__', has('win_app_local') ? ' —\nlocal sessions (Windows side)' : '');

  // styles
  const styleLines = [CLASSDEFS];
  for (const [cls, ids] of Object.entries(NODE_CLASS)){
    const here = ids.filter(n => present.has(n));
    if (here.length) styleLines.push('class '+here.join(',')+' '+cls);
  }
  for (const [sg, st] of Object.entries(SG_STYLE))
    if (sgs.has(sg)) styleLines.push('style '+sg+' '+st);
  if (noFlowIdx >= 0) styleLines.push(`linkStyle ${noFlowIdx} stroke:#B06A4F,color:#B06A4F`);

  const code = 'flowchart LR\n\n' + body + '\n\n' + styleLines.join('\n');
  return { code, hints, empty: present.size === 0 };
}
'''
