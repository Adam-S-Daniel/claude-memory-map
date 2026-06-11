#!/usr/bin/env python3
"""Picker v3: live-rendering memory map instrument. Reuses the tested compose() generator from v2."""
import pathlib, re

# extract the canonical generator verbatim from v2 (single source of truth)
v2 = (pathlib.Path(__file__).parent / 'build_picker2.py').read_text()
m = re.search(r"JS_GENERATOR = r'''(.*?)'''", v2, re.S)
JS_GENERATOR = m.group(1)

TREE = '''
<details open class="card" data-tint="chat">
  <summary class="cardhead"><span class="chip chip-chat"></span>Claude chat <span class="cnt" data-grp="chat"></span>
    <span class="cardsub">claude.ai &middot; the Claude mobile app &middot; the Claude Desktop app</span></summary>
  <label><input type="checkbox" id="ch_standalone"><span class="tick tick-acct"></span><span class="lbl">Chats not inside a Project (&ldquo;standalone&rdquo; chats) <span class="scopenote"></span></span></label>
  <label><input type="checkbox" id="ch_project"><span class="tick tick-acct"></span><span class="lbl">Chats inside a Project</span></label>
</details>

<details open class="card" data-tint="cw">
  <summary class="cardhead"><span class="chip chip-cw"></span>Claude Cowork <span class="cnt" data-grp="cw"></span>
    <span class="cardsub">runs via the Claude Desktop app</span></summary>
  <label><input type="checkbox" id="cw_desktop"><span class="tick tick-cw"></span><span class="lbl">In the Claude Desktop app</span></label>
  <label><input type="checkbox" id="cw_project"><span class="tick tick-cw"></span><span class="lbl">Sessions inside a project</span></label>
  <label><input type="checkbox" id="cw_standalone"><span class="tick tick-cw"></span><span class="lbl">Standalone sessions</span></label>
</details>

<details open class="card" data-tint="code">
  <summary class="cardhead"><span class="chip chip-code"></span>Claude Code <span class="cnt" data-grp="code"></span></summary>
  <details class="platd"><summary class="plat" data-grp="mac">On your Mac <span class="cnt" data-grp="mac"></span></summary>
    <div class="subgrp">In the Claude Desktop app</div>
      <label class="i2"><input type="checkbox" id="mac_app_local"><span class="tick tick-mac"></span><span class="lbl">Local sessions</span></label>
      <label class="i2"><input type="checkbox" id="mac_app_web"><span class="tick tick-web"></span><span class="lbl">Claude Code on the web sessions <span class="scopenote"></span></span></label>
    <label class="i1"><input type="checkbox" id="mac_cli"><span class="tick tick-mac"></span><span class="lbl">In the terminal &mdash; the Claude Code CLI (command-line interface)</span></label>
    <label class="i1"><input type="checkbox" id="mac_vscode"><span class="tick tick-mac"></span><span class="lbl">In VS Code with the Claude Code extension</span></label>
  </details>
<details class="platd"><summary class="plat" data-grp="win">On your Windows computer <span class="cnt" data-grp="win"></span></summary>
    <div class="subgrp">In the Claude Desktop app</div>
      <label class="i2"><input type="checkbox" id="win_app_local"><span class="tick tick-win"></span><span class="lbl">Local sessions (run on the Windows side)</span></label>
      <label class="i2"><input type="checkbox" id="win_app_web"><span class="tick tick-web"></span><span class="lbl">Claude Code on the web sessions <span class="scopenote"></span></span></label>
      <label class="i2"><input type="checkbox" id="win_app_rc_wsl"><span class="tick tick-wsl"></span><span class="lbl">Remote-controlling a CLI session running in WSL <span style="white-space:nowrap">(Remote Control, <code>/rc</code>)</span></span></label>
    <div class="subgrp">In the terminal &mdash; the Claude Code CLI (command-line interface)</div>
      <label class="i2"><input type="checkbox" id="win_cli_native"><span class="tick tick-win"></span><span class="lbl">Native Windows</span></label>
      <label class="i2"><input type="checkbox" id="win_cli_wsl"><span class="tick tick-wsl"></span><span class="lbl">In WSL</span></label>
    <div class="subgrp">In VS Code with the Claude Code extension</div>
      <label class="i2"><input type="checkbox" id="win_vscode_wsl"><span class="tick tick-wsl"></span><span class="lbl">Connected to WSL (with the &ldquo;WSL&rdquo; extension, formerly &ldquo;Remote&nbsp;-&nbsp;WSL&rdquo;)</span></label>
      <label class="i2"><input type="checkbox" id="win_vscode_local"><span class="tick tick-win"></span><span class="lbl">Local &mdash; not WSL</span></label>
  </details>
<label><input type="checkbox" id="code_web"><span class="tick tick-web"></span><span class="lbl">On the web &mdash; <code>claude.ai/code</code> in any browser <span class="scopenote"></span></span></label>
</details>

<p class="fine">A Cowork project is not the same thing as a project on claude.ai. Standalone Cowork sessions can also &ldquo;Work in a Folder&rdquo; &mdash; a project adds the bundle of folders, standing instructions, and a dedicated memory store. The Desktop app can also host sessions inside WSL via its SSH feature (niche; not mapped). Settings \u2192 Profile also holds your name, what Claude should call you, and what best describes your work \u2014 lighter-weight context Claude sees account-wide. The colored tick before each context shows which memory home it touches: <span class="tick tick-mac inlinetick"></span>Mac, <span class="tick tick-win inlinetick"></span>Windows, <span class="tick tick-wsl inlinetick"></span>WSL, <span class="tick tick-web inlinetick"></span>cloud, <span class="tick tick-acct inlinetick"></span>your account, <span class="tick tick-cw inlinetick"></span>Cowork.</p>
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
          --blue:#4A6B8F; --amber:#9A6F33; --wsl:#54805C; --win:#B06A4F;
          --mac:#5B6B7F; --plum:#8F5C82; --web:#8A8478; }
  * { box-sizing:border-box; margin:0; padding:0; }
  html { scroll-behavior:smooth; }
  body { background:var(--paper); color:var(--ink);
         font-family:Helvetica, Arial, sans-serif; }
  code { font-family:ui-monospace, 'Cascadia Code', Menlo, Consolas, monospace;
         font-size:0.92em; background:#F3EFE6; border-radius:4px; padding:0 4px; }

  header { position:sticky; top:0; z-index:30; background:var(--paper);
           pointer-events:none; }
  header > * { pointer-events:auto; }
  header { 
           border-bottom:1px solid var(--line); padding:14px 22px;
           display:flex; align-items:baseline; gap:16px; flex-wrap:wrap; }
  h1 { font-family:Georgia, 'Times New Roman', serif; font-weight:normal;
       font-size:22px; margin-right:auto; }
  .scopewrap { font-size:13px; color:var(--muted); display:flex; align-items:center; gap:6px; }
  .scopewrap select { border:1px solid var(--line); border-radius:8px; background:#FFF;
                      color:var(--ink); font-size:12.5px; padding:4px 6px; max-width:280px; }
  #selcount { font-size:13px; color:var(--muted); }
  #clearall { font-size:13px; color:var(--blue); cursor:pointer;
              text-decoration:underline; background:none; border:none; padding:4px; }

  .layout { display:grid; grid-template-columns:430px 1fr; gap:22px;
            max-width:1500px; margin:0 auto; padding:20px 22px 60px; }
  #panel { min-width:0; }
  .lede { font-size:14px; color:var(--muted); margin:2px 2px 16px; }

  .card { background:#FFFFFF; border:1px solid var(--line); border-radius:12px;
          padding:12px 12px 10px; margin-bottom:16px; }
  .card[data-tint="chat"] { border-left:3px solid var(--blue); }
  .card[data-tint="code"] { border-left:3px solid var(--amber); }
  .card[data-tint="cw"]   { border-left:3px solid var(--plum); }
  .cardhead { font-size:12px; letter-spacing:1.6px; text-transform:uppercase;
              color:var(--ink); margin:2px 4px 8px; display:flex;
              align-items:center; gap:8px; flex-wrap:wrap; }
  .cardsub { letter-spacing:0; text-transform:none; color:var(--muted);
             font-size:12px; font-weight:normal; }
  .chip { width:10px; height:10px; border-radius:3px; display:inline-block; }
  .chip-chat { background:var(--blue); } .chip-code { background:var(--amber); }
  .chip-cw { background:var(--plum); }
  summary { cursor:pointer; list-style:none; }
  details:not([open]) > *:not(summary) { display:none !important; }
  summary::-webkit-details-marker { display:none; }
  summary:focus-visible { outline:2px solid var(--blue); outline-offset:2px; border-radius:6px; }
  summary.plat::before, summary.cardhead::before {
    content:'▸'; display:inline-block; margin-right:6px; color:var(--muted);
    transition:transform 120ms ease; }
  details[open] > summary.plat::before, details[open] > summary.cardhead::before {
    transform:rotate(90deg); }
  @media (prefers-reduced-motion: reduce){ summary.plat::before, summary.cardhead::before { transition:none; } }
  .cnt { font-size:11px; color:var(--muted); background:#F3EFE6; border-radius:9px;
         padding:1px 8px; margin-left:4px; font-weight:normal; letter-spacing:0; text-transform:none; }
  .platd { margin:6px 0; }
  .plat { font-size:13.5px; font-weight:bold; margin:12px 6px 2px; }
  .subgrp { font-size:12.5px; font-style:italic; color:var(--muted); margin:8px 6px 2px 18px; }

  label { display:flex; align-items:center; gap:9px; min-height:44px;
          scroll-margin-top:110px;
          padding:8px 10px; margin:1px 0; border-radius:9px; cursor:pointer;
          font-size:14px; line-height:1.35; }
  label:hover { background:#F7F4EC; }
  label:has(input:checked) { background:#F2F6F2; }
  label.i1 { margin-left:14px; } label.i2 { margin-left:30px; }
  input[type=checkbox] { accent-color:var(--blue); width:17px; height:17px;
                         flex:0 0 auto; cursor:pointer; scroll-margin-top:120px; }
  input[type=checkbox]:focus-visible { outline:2px solid var(--blue); outline-offset:2px; }
  .lbl { flex:1; min-width:0; }
  .tick { width:3px; align-self:stretch; border-radius:2px; flex:0 0 auto; }
  .tick-mac{background:var(--mac);} .tick-win{background:var(--win);}
  .tick-wsl{background:var(--wsl);} .tick-web{background:var(--web);}
  .tick-acct{background:var(--blue);} .tick-quiet{background:#C9C3B6;}
  .tick-cw{background:var(--plum);}
  .inlinetick { display:inline-block; width:8px; height:11px; vertical-align:-1px; margin-right:2px; }
  label.scopedim { opacity:.55; }
  .scopenote { color:var(--amber); font-size:11.5px; font-style:italic; }
  .fine { font-size:12px; color:var(--muted); font-style:italic; margin:4px 4px 0; }

  #canvas { position:sticky; top:64px; height:calc(100vh - 86px);
            display:flex; flex-direction:column; min-width:0; }
  .canvasbar { display:flex; align-items:center; gap:12px; margin-bottom:8px; }
  .canvasbar h2 { font-family:Georgia, serif; font-weight:normal; font-size:17px;
                  margin-right:auto; }
  #fitbtn { border:1px solid var(--line); background:#FFFFFF; color:var(--ink);
            font-size:12.5px; border-radius:8px; padding:6px 12px; cursor:pointer; }
  #fitbtn:hover { border-color:var(--blue); }
  #hints { font-size:12.5px; color:var(--amber); margin-bottom:6px; min-height:0; }
  #hints div { margin:2px 0; }
  #diagram { background:#FFFFFF; border:1px solid var(--line); border-radius:12px;
             padding:12px; overflow:auto; flex:1; min-height:280px;
             -webkit-overflow-scrolling:touch; transition:opacity 120ms ease; }
  #diagram.dim { opacity:0.35; }
  #diagram svg { max-width:none !important; }
  #diagram.fit svg { width:100% !important; height:auto !important; max-width:100% !important; }
  .emptystate { color:var(--muted); font-size:14px; padding:28px 18px; }
  .emptystate b { font-family:Georgia, serif; font-weight:normal; font-size:17px;
                  display:block; margin-bottom:6px; color:var(--ink); }
  .err { color:#A0552F; font-size:13.5px; }

  .syncpanel { font-size:12.5px; background:#FFFFFF; border:1px solid var(--line);
               border-radius:10px; padding:8px 12px; margin-bottom:8px; line-height:1.45; }
  .syncpanel .insync b { color:var(--wsl); font-weight:bold; }
  .syncpanel .notsync b { color:var(--win); font-weight:bold; }
  .syncpanel .syncnote { color:var(--muted); font-style:italic; font-size:11.5px; margin-top:2px; }
  .syncitem { display:block; padding:1px 0 1px 12px; }
  .syncitem .swho { color:var(--muted); font-size:11.5px; }
  .syncctl { float:right; }
  .syncctl button { border:1px solid var(--line); background:#FFF; color:var(--blue);
                    font-size:11px; border-radius:7px; padding:3px 9px; cursor:pointer; }
  .legend { margin-top:5px; font-size:11.5px; color:var(--muted); }
  .legend summary { cursor:pointer; color:var(--blue); }
  .legend dl { margin:4px 0 0 4px; }
  .legend dt { font-weight:bold; color:var(--ink); margin-top:3px; }
  .legend dd { margin:0 0 0 12px; }
  #syncmob { display:none; }

  #mobilebar { display:none; }

  @media (prefers-reduced-motion: reduce){
    html { scroll-behavior:auto; }
    #diagram { transition:none; }
  }
  @media (max-width: 900px){
    .layout { grid-template-columns:1fr; padding:16px 12px 90px; gap:14px; }
    h1 { font-size:19px; }
    #canvas { position:static; height:auto; }
    #syncdesk { display:none; }
    #syncmob { display:block; flex-basis:100%; font-size:11.5px; padding:6px 10px;
               margin:6px 0 0; max-height:96px; overflow-y:auto; }
    #diagram { min-height:240px; max-height:70vh; }
    #mobilebar.show { display:flex; position:fixed; left:0; right:0; bottom:0; z-index:40;
      background:#FFFFFF; border-top:1px solid var(--line); padding:10px 16px;
      align-items:center; gap:12px;
      padding-bottom:calc(10px + env(safe-area-inset-bottom)); }
    #mobilebar .barcount { font-size:13px; color:var(--muted); margin-right:auto; }
    #viewmap { border:1.2px solid var(--blue); background:#EEF3F8; color:var(--ink);
               font-size:14px; border-radius:9px; padding:9px 16px; cursor:pointer; }
  }
</style>
</head>
<body>
<header>
  <h1>Which ways do you use Claude?</h1>
  <label class="scopewrap">I&rsquo;m interested in
    <select id="scope">
      <option value="across" selected>remembered across projects/repos</option>
      <option value="within">remembered within one project/repo</option>
      <option value="both">both</option>
    </select>
  </label>
  <span id="selcount">0 contexts</span>
  <button id="clearall">Clear all</button>
  <div id="syncmob" class="syncpanel"></div>
</header>

<div class="layout">
  <div id="panel">
    <p class="lede">Check every way you use Claude. The map of what Claude remembers assembles as you go &mdash; what gets in, where it lives, and how it comes back out.</p>
__TREE__
  </div>

  <div id="canvas">
    <div class="canvasbar">
      <h2>What Claude remembers &mdash; your selection</h2>
      <button id="fitbtn">Fit width</button>
    </div>
    <div id="syncdesk" class="syncpanel"></div>
    <div id="hints"></div>
    <div id="diagram"></div>
  </div>
</div>

<div id="mobilebar">
  <span class="barcount" id="barcount"></span>
  <button id="viewmap">View map</button>
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
const $ = id => document.getElementById(id);
const IDS = ['ch_standalone','ch_project',
  'mac_app_local','mac_app_web','mac_cli','mac_vscode',
  'win_app_local','win_app_web','win_app_rc_wsl','win_cli_native','win_cli_wsl',
  'win_vscode_wsl','win_vscode_local','code_web',
  'cw_desktop','cw_project','cw_standalone'];

const EMPTY_HTML = '<div class="emptystate"><b>Nothing mapped yet.</b>Check a context on the left and what Claude remembers there appears here. Add more and watch the stores and flows connect.</div>';

let renderCount = 0, timer = null, renderSeq = 0;

function selection(){ const s = {}; IDS.forEach(i => s[i] = $(i).checked); return s; }
function countChecked(){ return IDS.filter(i => $(i).checked).length; }

const GROUPS = {
  chat:['ch_standalone','ch_project'],
  mac:['mac_app_local','mac_app_web','mac_cli','mac_vscode'],
  win:['win_app_local','win_app_web','win_app_rc_wsl','win_cli_native','win_cli_wsl','win_vscode_wsl','win_vscode_local'],
  cw:['cw_desktop','cw_project','cw_standalone'],
};
GROUPS.code = [...GROUPS.mac, ...GROUPS.win, 'code_web'];

function updateBadges(){
  document.querySelectorAll('.cnt').forEach(el => {
    const ids = GROUPS[el.dataset.grp];
    const n = ids.filter(i => $(i).checked).length;
    el.textContent = n + ' of ' + ids.length + ' selected';
  });
}

const SCOPE_LACKS = {
  across: ['code_web','mac_app_web','win_app_web'],
  within: ['ch_standalone'],
  both: [],
};
const SCOPE_NOTE = {
  across: '\u2014 remembers nothing across repos',
  within: '\u2014 remembers nothing project-scoped',
};
function updateScopeUI(){
  const scope = $('scope').value;
  ['code_web','mac_app_web','win_app_web','ch_standalone'].forEach(id => {
    const el = $(id), row = el.closest('label'), note = row.querySelector('.scopenote');
    const lacks = SCOPE_LACKS[scope].includes(id);
    el.disabled = lacks && !el.checked;
    row.classList.toggle('scopedim', lacks);
    note.textContent = lacks ? SCOPE_NOTE[scope] : '';
  });
}

function updateChrome(){
  updateScopeUI();
  updateBadges();
  const n = countChecked();
  $('selcount').textContent = n + (n === 1 ? ' context' : ' contexts');
  $('barcount').textContent = n + (n === 1 ? ' context mapped' : ' contexts mapped');
  $('mobilebar').classList.toggle('show', n > 0);
}

async function renderNow(){
  const seq = ++renderSeq;
  const { code, hints, empty } = compose(selection());
  $('hints').innerHTML = hints.map(h => '<div>&#9432; '+h+'</div>').join('');
  const d = $('diagram');
  if (empty){ d.classList.remove('dim'); d.innerHTML = EMPTY_HTML; return; }
  if (!MERMAID_OK){
    d.innerHTML = '<p class="err">The diagram renderer (mermaid, from cdnjs.cloudflare.com) failed to load. Check the console/network for the script request, then reload.</p>'
      + '<details style="margin-top:10px"><summary style="cursor:pointer;color:#4A6B8F">Show this map&rsquo;s Mermaid source instead</summary><pre style="white-space:pre-wrap;font-size:12px;margin-top:8px">'
      + code.replace(/&/g,'&amp;').replace(/</g,'&lt;') + '</pre></details>';
    return;
  }
  d.classList.add('dim');
  try{
    const { svg } = await mermaid.render('m'+(++renderCount), code);
    if (seq !== renderSeq) return;            // a newer selection superseded this render
    d.innerHTML = svg;
  }catch(err){
    if (seq !== renderSeq) return;
    d.innerHTML = '<p class="err">Could not render: '+err.message+'</p><pre style="white-space:pre-wrap;font-size:11px">'+code.replace(/&/g,'&amp;').replace(/</g,'&lt;')+'</pre>';
  }
  d.classList.remove('dim');
}

function scheduleRender(){
  updateChrome();
  updateSync();
  clearTimeout(timer);
  timer = setTimeout(renderNow, 220);
}

// checking a Remote-controlling box checks its host CLI; unchecking the host releases the RC box
const IMPLIES = { win_app_rc_wsl:'win_cli_wsl' };
function propagate(id){
  if (IMPLIES[id] && $(id).checked) $(IMPLIES[id]).checked = true;
  for (const [rc, host] of Object.entries(IMPLIES))
    if (host === id && !$(id).checked) $(rc).checked = false;
}

// ----- glanceable sync summary -----
const SESSIONS = [
  ['ch_standalone','Standalone chats',['chatmem','prefs']],
  ['ch_project','Project chats',['projmem','prefs']],
  ['mac_app_local','Desktop app (Mac)',['macumd','macauto','repo']],
  ['mac_cli','CLI (Mac)',['macumd','macauto','repo']],
  ['mac_vscode','VS Code (Mac)',['macumd','macauto','repo']],
  ['win_app_local','Desktop app (Windows)',['winumd','winauto','repo']],
  ['win_cli_native','CLI (Windows)',['winumd','winauto','repo']],
  ['win_vscode_local','VS Code (Windows)',['winumd','winauto','repo']],
  ['win_cli_wsl','CLI (WSL)',['wslumd','wslauto','repo']],
  ['win_vscode_wsl','VS Code (WSL)',['wslumd','wslauto','repo']],
  ['cw_project','Cowork project sessions',['cwmem','repo','prefs']],
  ['cw_standalone','Cowork standalone sessions',['repo','prefs']],
];
const SCOPE_OF = {
  chatmem:'across', prefs:'across', macumd:'across', winumd:'across', wslumd:'across',
  projmem:'within', repo:'within', macauto:'within', winauto:'within', wslauto:'within', cwmem:'within',
};
const WINPATH = ['C:','Users','you','.claude'].join(String.fromCharCode(92));
const STORE_BRIEF = {
  chatmem:'Memory from chat history',
  prefs:'Instructions for Claude',
  projmem:'Project memory',
  repo:t => 'CLAUDE.md ('+t+')',
  macumd:'Mac home \u2014 User CLAUDE.md', winumd:'Windows home \u2014 User CLAUDE.md', wslumd:'WSL home \u2014 User CLAUDE.md',
  macauto:'Mac home \u2014 Auto memory', winauto:'Windows home \u2014 Auto memory', wslauto:'WSL home \u2014 Auto memory',
  cwmem:'Cowork memory',
};
const STORE_FULL = {
  chatmem:'Memory from chat history: nightly chat summary + saved facts, spanning every standalone chat',
  prefs:'Instructions for Claude (Settings \\u2192 Profile; \\u201CInstructions\\u201D in the app): free-text standing instructions kept in mind across chats and Cowork',
  projmem:'Project memory: one per claude.ai Project',
  repo:t => 'Project notes file \u2014 CLAUDE.md, saved in the '+t,
  macumd:'Mac file system (~/.claude) \u2014 user CLAUDE.md: your instructions, all projects on this Mac',
  winumd:'Windows file system (' + WINPATH + ') \u2014 user CLAUDE.md: your instructions, all projects on this side',
  wslumd:'WSL file system (~/.claude) \u2014 user CLAUDE.md: your instructions, all projects on this side',
  macauto:'Mac file system (~/.claude) \u2014 auto memory: Claude\u2019s own notes, one set per project',
  winauto:'Windows file system (' + WINPATH + ') \u2014 auto memory: Claude\u2019s own notes, one set per project',
  wslauto:'WSL file system (~/.claude) \u2014 auto memory: Claude\u2019s own notes, one set per project',
  cwmem:'Cowork project memory: one per Cowork project, on that computer',
};
const LEGEND_HTML = '<details class="legend"><summary>Legend</summary><dl>'
  + '<dt>Memory from chat history</dt><dd>Claude\u2019s account-level memory \u2014 the nightly chat summary plus saved facts \u2014 applied to every standalone chat on any device. Cross-project.</dd>'
  + '<dt>Instructions for Claude</dt><dd>The free-text box at Settings \\u2192 Profile (labeled \\u201CInstructions\\u201D in the app). Anthropic: \\u201CClaude will keep these in mind across chats and Cowork within Anthropic\\u2019s guidelines.\\u201D</dd>'
  + '<dt>Project memory</dt><dd>A separate memory for each claude.ai Project.</dd>'
  + '<dt>CLAUDE.md</dt><dd>The project notes file saved with the repo/project folder, read at session start by whatever opens it.</dd>'
  + '<dt>User CLAUDE.md (Mac / Windows / WSL)</dt><dd>In that side\u2019s <code>~/.claude</code> (Windows: <code>' + WINPATH + '</code>): your instructions for every project on that side. Cross-project, but each side keeps its own file.</dd>'
  + '<dt>Auto memory (Mac / Windows / WSL)</dt><dd>Claude\u2019s own notes (auto memory) in the same folder \u2014 one set per project, per side.</dd>'
  + '<dt>Cowork memory</dt><dd>Per-Cowork-project memory, kept on that computer.</dd>'
  + '</dl></details>';
let labelMode = 'brief';
function storeLabel(s, term){
  const map = labelMode === 'brief' ? STORE_BRIEF : STORE_FULL;
  const v = map[s];
  return typeof v === 'function' ? v(term) : v;
}
function updateSync(){
  const ctxs = SESSIONS.filter(([id]) => $(id).checked).map(([,name,st]) => ({name, st}));
  if ($('code_web').checked || $('mac_app_web').checked || $('win_app_web').checked)
    ctxs.push({name:'Claude Code on the web', st:['repo']});
  const scope = $('scope').value;
  if (scope !== 'both')
    ctxs.forEach(c => { c.st = c.st.filter(s => SCOPE_OF[s] === scope); });
  const notes = [];
  const codeSel = GROUPS.code.some(i => $(i).checked);
  const cwSel = $('cw_project').checked || $('cw_standalone').checked;
  const term = (codeSel && cwSel) ? 'repo/project folder' : (codeSel ? 'repo' : 'project folder');
  const item = (s, who) => '<div class="syncitem">' + storeLabel(s, term)
    + (who ? ' <span class="swho">— only in: ' + who.join(', ') + '</span>' : '') + '</div>';
  let html;
  if (ctxs.length === 0){
    html = '<div class="insync"><b>In sync across your selection:</b> —</div>'
         + '<div class="notsync"><b>Kept separate:</b> —</div>';
  } else {
    const cover = {};
    ctxs.forEach(c => c.st.forEach(s => { (cover[s] = cover[s] || []).push(c.name); }));
    const inSync = [], notSync = [];
    for (const [s, who] of Object.entries(cover))
      (who.length === ctxs.length ? inSync : notSync).push([s, who]);
    if (ctxs.length === 1) notes.push('Only one context selected — nothing to sync across yet.');
    if (cover.repo) notes.push('CLAUDE.md sync assumes the contexts open the same repo/project folder.');
    html = '<div class="insync"><b>In sync across your selection:</b>'
      + (inSync.length ? inSync.map(([s]) => item(s)).join('') : ' None') + '</div>'
      + '<div class="notsync"><b>Kept separate:</b>'
      + (notSync.length ? notSync.map(([s,who]) => item(s, who)).join('') : ' None') + '</div>';
  }
  html += notes.map(n => '<div class="syncnote">'+n+'</div>').join('');
  const controls = '<div class="syncctl"><button id="labelmode">'
    + (labelMode === 'brief' ? 'Full labels' : 'Brief labels') + '</button></div>';
  const legend = labelMode === 'brief' ? LEGEND_HTML : '';
  $('syncdesk').innerHTML = controls + html + legend;
  $('syncmob').innerHTML = html + legend;

}

IDS.forEach(i => $(i).addEventListener('change', () => { propagate(i); scheduleRender(); }));
$('clearall').addEventListener('click', () => {
  IDS.forEach(i => { $(i).checked = false; });
  scheduleRender();
});
$('fitbtn').addEventListener('click', () => {
  const fit = $('diagram').classList.toggle('fit');
  $('fitbtn').textContent = fit ? 'Actual size' : 'Fit width';
});
$('scope').addEventListener('change', () => { updateScopeUI(); updateSync(); });
document.addEventListener('click', e => {
  if (e.target && e.target.id === 'labelmode'){
    labelMode = labelMode === 'brief' ? 'full' : 'brief';
    updateSync();
  }
});
$('viewmap').addEventListener('click', () =>
  $('canvas').scrollIntoView({ block:'start', behavior:'smooth' }));

if (window.matchMedia('(max-width: 900px)').matches){
  $('diagram').classList.add('fit');
  $('fitbtn').textContent = 'Actual size';
}
updateChrome();
updateSync();
$('diagram').innerHTML = EMPTY_HTML;
</script>
</body>
</html>
'''

html = HTML.replace('__TREE__', TREE).replace('__GENERATOR__', JS_GENERATOR)
(pathlib.Path(__file__).parent.parent / 'index.html').write_text(html)
print('index.html written:', len(html), 'bytes')
