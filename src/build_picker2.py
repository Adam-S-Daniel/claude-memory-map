#!/usr/bin/env python3
"""Build the interactive memory-map picker v2: checkbox tree -> runtime-composed Mermaid chart."""
import pathlib

JS_GENERATOR = r'''
// ---------- canonical text blocks (single source of truth) ----------
const Q = '&quot;';
const NODES = {
  C1:  `C1["Chats not inside a Project\n  (${Q}standalone${Q} chats)"]`,
  C2:  `C2["Chats inside a Project"]`,
  S1:  `S1["Saved facts (${Q}memory edits${Q})\n  (kept word-for-word)"]`,
  S2:  `S2["Nightly chat summary\n  (${Q}memory summary${Q})"]`,
  S3:  `S3["Project memory (${Q}project-scoped\n  memory${Q}) — one per Project"]`,
  PRF: `PRF["Instructions for Claude — Settings → Profile\n  (${Q}Instructions${Q} in the app)\n  (kept in mind across chats & Cowork)"]`,
  SET: `SET["Settings → Memory page\n(${Q}Manage memory${Q} · home of the\n${Q}Generate memory from chat history${Q} toggle)"]`,
  MAPP:`MAPP["Claude Desktop app__MAPP_SUFFIX__"]`,
  K6:  `K6["CLI on Mac — Terminal"]`,
  K7:  `K7["VS Code with the\nClaude Code extension — Mac"]`,
  WAPP:`WAPP["Claude Desktop app__WAPP_SUFFIX__"]`,
  K4:  `K4["CLI in Windows — native"]`,
  K5:  `K5["VS Code with the\nClaude Code extension —\nlocal (not WSL)"]`,
  KW:  `KW["CLI in WSL"]`,
  KV:  `KV["VS Code on Windows,\nconnected to WSL\n(the ${Q}WSL${Q} extension,\nformerly ${Q}Remote - WSL${Q})"]`,
  C5:  `C5["On the web\n(fresh cloud sandbox per task)"]`,
  YOU: `YOU["You, in the Claude Desktop app"]`,
  C6:  `C6["Session inside a project"]`,
  C7:  `C7["One-off session (${Q}standalone\n  session${Q}) — keeps nothing afterward"]`,
  S7:  `S7["Cowork project memory"]`,
  W1:  `W1["User CLAUDE.md — WSL\n  (${Q}user instructions${Q})\n  (all projects on this side)"]`,
  W2:  `W2["Claude's own notes — WSL\n  (${Q}auto memory${Q})\n  (one set per project, on this side only)"]`,
  N1:  `N1["User CLAUDE.md — Windows\n  (${Q}user instructions${Q})\n  (all projects on this side)"]`,
  N2:  `N2["Claude's own notes — Windows\n  (${Q}auto memory${Q})\n  (one set per project, on this side only)"]`,
  M1:  `M1["User CLAUDE.md — Mac\n  (${Q}user instructions${Q})\n  (all projects on this Mac)"]`,
  M2:  `M2["Claude's own notes — Mac\n  (${Q}auto memory${Q})\n  (one set per project)"]`,
};

function s4Node(term){
  return `S4["Project notes file — CLAUDE.md\n  (${Q}project instructions${Q})\n  (one per ${term},\n  read by whatever opens it)"]`;
}

const BUNDLED = `you write the user file · it jots notes, incl. \u201Cremember this\u201D · all read at session start`;
const WRITE_READ = `you write it · read at session start`;

const CHAT_FLOWS_ALL = [
  ['C1','S2', 'C1 -- "summarized overnight" --> S2'],
  ['C1','S1', 'C1 -- "saying \u201Cremember this\u201D" --> S1'],
  ['S1','S2', 'S1 -. "feeds" .-> S2'],
  ['S2','C1', 'S2 -- "loaded into every new standalone chat" --> C1'],
  ['S1','C1', 'S1 --> C1'],
  ['C2','S3', 'C2 <-- "chatting · saying \u201Cremember this\u201D · recalled in that Project\u2019s chats" --> S3'],
  ['S2','SET','S2 -. "displayed here, regenerated nightly · export" .-> SET'],
  ['SET','S1','SET -. "your edits · imports" .-> S1'],
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
  ctx: ['C1','C2','MAPP','K6','K7','WAPP','K4','K5','KW','KV','C5','C6','YOU','SET'],
  quiet: ['C7'],
  acct: ['S1','S2','S3','PRF'], repo: ['S4'],
  wsl: ['W1','W2'], win: ['N1','N2'], mac: ['M1','M2'], cwloc: ['S7'],
};
const SG_STYLE = {
  CHAT:'fill:#FDFBF7,stroke:#C9C3B6,stroke-width:1px,color:#6B675E',
  CW:'fill:#FDFBF7,stroke:#C9C3B6,stroke-width:1px,color:#6B675E',
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
    hints.push('Remote-controlling a WSL CLI session implies a CLI session in WSL \u2014 added to the map.');
  const k6  = has('mac_cli');

  const wapp = has('win_app_local') || has('win_app_web') || has('win_app_rc_wsl');
  const mapp = has('mac_app_local') || has('mac_app_web');
  // side = an actual session running on that side (client-only desktop-app use doesn't count)
  const winSide = has('win_app_local') || has('win_cli_native') || has('win_vscode_local');
  const wslSide = kw || has('win_vscode_wsl');
  const macSide = has('mac_app_local') || k6 || has('mac_vscode');
  const c5 = has('code_web') || has('mac_app_web') || has('win_app_web');
  const codeAny = winSide || wslSide || macSide || c5;
  const cwSession = has('cw_project') || has('cw_standalone');
  const cwAny = cwSession || has('cw_desktop');
  const chatAny = has('ch_standalone') || has('ch_project');


  if (has('cw_desktop') && !cwSession)
    hints.push('You picked a way into Cowork but no session type \u2014 check \u201Cinside a project\u201D or \u201Cstandalone\u201D to see where the work lands.');

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
  const s4 = localCode || c5 || cwSession;
  if (s4){
    const term = (codeAny && cwSession) ? 'repo/project folder' : (codeAny ? 'repo' : 'project folder');
    present.add('S4'); sgs.add('REPO');
    blocks.push('subgraph REPO["Saved with the project\u2019s files"]\n  '+s4Node(term)+'\nend');
  }
  function fs(id, title, a, b){
    sgs.add(id);
    blocks.push(`subgraph ${id}["${title}"]\ndirection TB\n  `+node(a)+'\n  '+node(b)+'\nend');
  }
  if (macSide) fs('MACFS','Mac file system — ~/.claude','M1','M2');
  if (winSide) fs('WINFS','Windows file system — C:\\Users\\you\\.claude','N1','N2');
  if (wslSide) fs('WSLFS','WSL file system — ~/.claude','W1','W2');

  // cowork
  if (cwAny){
    const inner = [];
    if (has('cw_desktop'))  inner.push('  '+node('YOU'));
    if (has('cw_project'))  inner.push('  '+node('C6'));
    if (has('cw_standalone')) inner.push('  '+node('C7'));
    sgs.add('CW');
    blocks.push('subgraph CW["Claude Cowork — via the Claude Desktop app"]\ndirection TB\n'+inner.join('\n')+'\nend');
    if (has('cw_project')){
      sgs.add('CWLOC');
      blocks.push('subgraph CWLOC["On one computer — Cowork"]\n  '+node('S7')+'\nend');
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
    if (cwSession) flows.push('PRF -- "applied to Cowork sessions" --> CW');
  }
  if (cwAny){
    if (present.has('C6') && present.has('S7'))
      flows.push('C6 <-- "remembers as you work · recalled when you reopen it" --> S7');
    if (present.has('YOU')){
      if (present.has('C6')) flows.push('YOU -- "work in it directly" --> C6');
      if (present.has('C7')) flows.push('YOU --> C7');
    }
    if (cwSession && present.has('S4'))
      flows.push('CW <-- "you or Claude writes it (e.g. /init) · read at session start" --> S4');
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

  const code = 'flowchart LR\n\n' + body + '\n\n' + styleLines.join('\n');
  return { code, hints, empty: present.size === 0 };
}
'''

CHECKBOX_TREE = '''
<div class="grp">Claude chat <span class="grpsub">claude.ai &middot; the Claude mobile app &middot; the Claude Desktop app</span></div>
<label><input type="checkbox" id="ch_standalone"> Chats not inside a Project (&ldquo;standalone&rdquo; chats)</label>
<label><input type="checkbox" id="ch_project"> Chats inside a Project</label>
<label><input type="checkbox" id="ch_incognito"> Incognito chats</label>

<div class="grp">Claude Code</div>
<div class="sub1lbl">On your Mac</div>
  <div class="sub2lbl">In the Claude Desktop app</div>
    <label class="i3"><input type="checkbox" id="mac_app_local"> Local sessions</label>
    <label class="i3"><input type="checkbox" id="mac_app_web"> Claude Code on the web sessions</label>
  <label class="i2"><input type="checkbox" id="mac_cli"> In the terminal &mdash; the Claude Code CLI (command-line interface)</label>
  <label class="i2"><input type="checkbox" id="mac_vscode"> In VS Code with the Claude Code extension</label>
<div class="sub1lbl">On your Windows computer</div>
  <div class="sub2lbl">In the Claude Desktop app</div>
    <label class="i3"><input type="checkbox" id="win_app_local"> Local sessions (run on the Windows side)</label>
    <label class="i3"><input type="checkbox" id="win_app_web"> Claude Code on the web sessions</label>
    <label class="i3"><input type="checkbox" id="win_app_rc_wsl"> Remote-controlling a CLI session running in WSL (Remote Control, /rc)</label>
  <div class="sub2lbl">In the terminal &mdash; the Claude Code CLI (command-line interface)</div>
    <label class="i3"><input type="checkbox" id="win_cli_native"> Native Windows</label>
    <label class="i3"><input type="checkbox" id="win_cli_wsl"> In WSL</label>
  <div class="sub2lbl">In VS Code with the Claude Code extension</div>
    <label class="i3"><input type="checkbox" id="win_vscode_wsl"> Connected to WSL (with the &ldquo;WSL&rdquo; extension, formerly &ldquo;Remote - WSL&rdquo;)</label>
    <label class="i3"><input type="checkbox" id="win_vscode_local"> Local &mdash; not WSL</label>
<label><input type="checkbox" id="code_web"> On the web &mdash; claude.ai/code in any browser</label>
<label><input type="checkbox" id="code_rc"> From your phone or browser &mdash; Remote Control of a running session</label>

<div class="grp">Claude Cowork <span class="grpsub">runs via the Claude Desktop app</span></div>
<label><input type="checkbox" id="cw_desktop"> At your desktop, in the Claude Desktop app</label>
<label><input type="checkbox" id="cw_dispatch"> From your phone, via Dispatch (requires the Claude mobile app)</label>
<label><input type="checkbox" id="cw_project"> Sessions inside a project</label>
<label><input type="checkbox" id="cw_standalone"> Standalone sessions</label>

<p class="fine">Notes: a Cowork project is not the same thing as a project on claude.ai. Standalone Cowork sessions can also &ldquo;Work in a Folder&rdquo; &mdash; what a project adds is the bundle of folders, standing instructions, and a dedicated memory store. Dispatch from a phone requires the Claude mobile app (a phone browser isn&rsquo;t a documented path). The Desktop app can also host sessions inside WSL via its SSH feature (niche; not mapped here).</p>
'''

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Which ways do you use Claude?</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/11.12.0/mermaid.min.js"></script>
<style>
  :root { --paper:#FDFBF7; --ink:#3D3A34; --muted:#6B675E; --line:#E4DFD4;
          --blue:#4A6B8F; --amber:#9A6F33; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--paper); color:var(--ink);
         font-family:Helvetica, Arial, sans-serif; padding:32px 20px 60px; }
  .wrap { max-width:1100px; margin:0 auto; }
  h1 { font-family:Georgia, 'Times New Roman', serif; font-size:30px; font-weight:normal; }
  .sub { color:var(--muted); margin:10px 0 22px; font-size:15px; }
  .grp { font-size:12px; letter-spacing:1.5px; color:var(--amber);
         margin:24px 0 8px; text-transform:uppercase; }
  .grpsub { letter-spacing:0; text-transform:none; color:var(--muted); font-size:12px; }
  .sub1lbl { font-size:14px; color:var(--ink); margin:10px 0 4px 14px; font-weight:bold; }
  .sub2lbl { font-size:13.5px; color:var(--muted); margin:8px 0 3px 32px; font-style:italic; }
  label { display:block; font-size:14.5px; margin:5px 0 5px 14px; cursor:pointer; }
  label.i2 { margin-left:32px; }
  label.i3 { margin-left:52px; }
  input[type=checkbox] { accent-color:var(--blue); margin-right:7px; transform:scale(1.1); }
  .fine { font-size:12px; color:var(--muted); font-style:italic; margin:18px 0 0 14px; max-width:760px; }
  button.go { margin-top:26px; border:1.2px solid var(--blue); border-radius:10px;
              background:#EEF3F8; color:var(--ink); font-size:15px;
              padding:11px 22px; cursor:pointer; }
  #result { display:none; }
  #result h2 { font-family:Georgia, serif; font-weight:normal; font-size:22px; margin-bottom:6px; }
  .bar { display:flex; gap:14px; align-items:center; margin:14px 0 12px; flex-wrap:wrap; }
  .bar a { color:var(--blue); font-size:13.5px; cursor:pointer; text-decoration:underline; }
  #hints { font-size:13px; color:var(--amber); margin-bottom:10px; }
  #hints div { margin:3px 0; }
  #diagram { background:#FFFFFF; border:1px solid var(--line); border-radius:12px;
             padding:14px; overflow:auto; }
  #diagram svg { max-width:none !important; }
  .err { color:#A0552F; }
</style>
</head>
<body>
<div class="wrap">
  <div id="quiz">
    <h1>Which ways do you use Claude?</h1>
    <p class="sub">Check every context you use &mdash; the map is composed from your selection. Claude keeps separate memories in different places; this shows what gets in, where it lives, and how it comes back out.</p>
__TREE__
    <button class="go" id="go">Show my map</button>
    <p class="fine" id="emptymsg" style="display:none; color:#A0552F">Check at least one box first.</p>
  </div>

  <div id="result">
    <h2>Claude memory map &mdash; your selection</h2>
    <div class="bar"><a id="back">&larr; Change selection</a></div>
    <div id="hints"></div>
    <div id="diagram"></div>
  </div>
</div>

<script>
window.addEventListener('error', e => {
  const d = document.getElementById('diagram');
  if (d) d.insertAdjacentHTML('afterbegin', '<p class="err">Page error: '+(e.message||'unknown')+'</p>');
});
__GENERATOR__
const MERMAID_OK = typeof mermaid !== 'undefined';
if (MERMAID_OK) mermaid.initialize({ startOnLoad:false, securityLevel:'loose', theme:'neutral',
                                     flowchart:{ useMaxWidth:false } });
let renderCount = 0;
const $ = id => document.getElementById(id);
const IDS = ['ch_standalone','ch_project','ch_incognito',
  'win_app_local','win_app_web','win_app_rc_wsl','win_cli_native','win_cli_wsl',
  'win_vscode_wsl','win_vscode_local','code_web','code_rc',
  'cw_desktop','cw_dispatch','cw_project','cw_standalone'];

$('go').addEventListener('click', async () => {
  const sel = {}; IDS.forEach(i => sel[i] = $(i).checked);
  const { code, hints, empty } = compose(sel);
  if (empty){ $('emptymsg').style.display='block'; return; }
  $('emptymsg').style.display='none';
  $('quiz').style.display='none'; $('result').style.display='block';
  $('hints').innerHTML = hints.map(h => '<div>&#9432; '+h+'</div>').join('');
  if (!MERMAID_OK){
    $('diagram').innerHTML = '<p class="err">The diagram renderer (mermaid, from cdnjs.cloudflare.com) failed to load. Check the console/network for the script request, then reload.</p>'
      + '<details style="margin-top:10px"><summary style="cursor:pointer;color:#4A6B8F">Show this map&rsquo;s Mermaid source instead</summary><pre style="white-space:pre-wrap;font-size:12px;margin-top:8px">'
      + code.replace(/&/g,'&amp;').replace(/</g,'&lt;') + '</pre></details>';
    return;
  }
  $('diagram').innerHTML = '<span style="color:#6B675E">Rendering&hellip;</span>';
  try{
    const { svg } = await mermaid.render('m'+(++renderCount), code);
    $('diagram').innerHTML = svg;
  }catch(err){
    $('diagram').innerHTML = '<p class="err">Could not render: '+err.message+'</p><pre style="white-space:pre-wrap;font-size:11px">'+code.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</pre>';
  }
});
$('back').addEventListener('click', () => { $('result').style.display='none'; $('quiz').style.display='block'; });
</script>
</body>
</html>
'''

html = HTML.replace('__TREE__', CHECKBOX_TREE).replace('__GENERATOR__', JS_GENERATOR)
pathlib.Path('/mnt/user-data/outputs/claude-memory-map-picker.html').write_text(html)
print('picker v2 written:', len(html), 'bytes')
