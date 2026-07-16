// Test suite for picker v3: live rendering, redesigned selection UI, mobile friendliness.
// Run BEFORE implementation (red) and AFTER (green).
const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');
const TARGET = 'file://' + path.resolve(__dirname, '../index.html');
const MERMAID_BUNDLE = path.resolve(__dirname, '../node_modules/mermaid/dist/mermaid.min.js');

// Browser launch resolution.
//   CI / serverless: CHROMIUM_PATH unset (or /tmp/chromium) -> @sparticuz/chromium args, headless shell.
//   Local: auto-detect a Chrome-for-Testing under ~/.cache/puppeteer (or CHROMIUM_PATH) -> desktop args.
//   Claude Code web: a Playwright-managed Chromium under $PLAYWRIGHT_BROWSERS_PATH
//   (/opt/pw-browsers there) -> desktop args, same as local.
//   Debug knobs (local only): HEADED=1 visible window, DEVTOOLS=1 open devtools, SLOWMO=<ms> per-step delay.
function detectLocalChrome(){
  const root = path.join(os.homedir(), '.cache', 'puppeteer', 'chrome');
  try {
    for (const d of fs.readdirSync(root).filter(n => n.startsWith('linux-')).sort().reverse()){
      const exe = path.join(root, d, 'chrome-linux64', 'chrome');
      if (fs.existsSync(exe)) return exe;
    }
  } catch {}
  return null;
}
function detectPlaywrightChromium(){
  const root = process.env.PLAYWRIGHT_BROWSERS_PATH;
  if (!root) return null;
  const link = path.join(root, 'chromium');            // env-provided symlink, if any
  if (fs.existsSync(link)) return link;
  try {
    for (const d of fs.readdirSync(root).filter(n => /^chromium-\d+$/.test(n)).sort().reverse()){
      for (const exe of [path.join(root, d, 'chrome-linux64', 'chrome'),
                         path.join(root, d, 'chrome-linux', 'chrome')]){
        if (fs.existsSync(exe)) return exe;
      }
    }
  } catch {}
  return null;
}
function launchOptions(){
  const exe = process.env.CHROMIUM_PATH || detectLocalChrome() || detectPlaywrightChromium();
  const serverless = !exe || exe === '/tmp/chromium';
  if (serverless){
    return { executablePath: exe || '/tmp/chromium',
      args: require('@sparticuz/chromium').default.args, headless: 'shell' };
  }
  return {
    executablePath: exe,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    headless: process.env.HEADED ? false : 'new',
    devtools: !!process.env.DEVTOOLS,
    slowMo: process.env.SLOWMO ? Number(process.env.SLOWMO) : 0,
  };
}

let failures = [], passes = 0;
function check(cond, name){
  if (cond) { passes++; console.log('  PASS', name); }
  else { failures.push(name); console.log('  FAIL', name); }
}

(async () => {
  const opts = launchOptions();
  console.log(`Browser: ${path.basename(opts.executablePath)}  headless=${opts.headless}` +
    `${opts.devtools ? ' +devtools' : ''}${opts.slowMo ? ` slowMo=${opts.slowMo}ms` : ''}`);
  const browser = await puppeteer.launch(opts);

  async function freshPage(viewport, blockCdn=false, expandAll=true){
    const page = await browser.newPage();
    await page.setViewport(viewport);
    await page.setRequestInterception(true);
    page.on('request', r => {
      if (!r.url().includes('cdnjs')) return r.continue();
      if (blockCdn) return r.abort();
      r.respond({contentType:'application/javascript',
        body: fs.readFileSync(MERMAID_BUNDLE,'utf8')});
    });
    await page.goto(TARGET);
    if (expandAll) await page.evaluate(() =>
      document.querySelectorAll('#panel details').forEach(d => d.open = true));
    return page;
  }
  const DESKTOP = {width:1400, height:900};
  const MOBILE  = {width:390, height:844};
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  async function waitSvg(page, ms=3000){
    try { await page.waitForSelector('#diagram svg', {timeout: ms}); return true; }
    catch { return false; }
  }
  const diagText = page => page.$eval('#diagram', el => el.textContent).catch(()=> '');
  const setScope = async (page, v) => { try { await page.select('#scope', v); await sleep(250); } catch {} };

  // ---------- DESKTOP: live behavior ----------
  console.log('D1-D2: live layout at load');
  let p = await freshPage(DESKTOP);
  check(await p.$('#go') === null, 'D1 no Show-my-map button (rendering is live)');
  const bothVisible = await p.evaluate(() => {
    const vis = el => el && el.offsetParent !== null;
    return vis(document.getElementById('panel')) && vis(document.getElementById('diagram'));
  });
  check(bothVisible, 'D2 selection panel and diagram area visible together at load');
  const emptyState = await diagText(p);
  check(/check|select/i.test(emptyState), 'D2b empty state invites action');

  console.log('D3-D5: live re-render on change');
  await p.click('#ch_standalone');
  check(await waitSvg(p), 'D3 svg appears after checking a box (no button press)');
  let t = await diagText(p);
  check(t.includes('standalone'), 'D3b chart reflects selection');
  await p.click('#cw_remote_project');
  await sleep(900);
  t = await diagText(p);
  check(t.includes('Cowork'), 'D4 chart live-updates when another box is checked');
  await p.click('#ch_standalone');  // uncheck
  await sleep(900);
  t = await diagText(p);
  check(!t.includes('Manage memory'), 'D5 chart live-updates on uncheck');

  console.log('D6: live cowork/chat interplay');
  await p.close(); p = await freshPage(DESKTOP);
  await p.click('#cw_remote_project'); await p.click('#ch_standalone');
  await sleep(900);
  t = await diagText(p);
  check(/chat-only/i.test(t) && !t.includes('Could not render'),
        'D6 chat+remote-cowork selection renders the chat-only note (no render error)');

  console.log('D7-D8: clear-all and live count');
  await p.close(); p = await freshPage(DESKTOP);
  await p.click('#ch_standalone'); await p.click('#cw_remote_project');
  await sleep(900);
  const countTxt = await p.$eval('#selcount', el => el.textContent).catch(()=> '');
  check(/2/.test(countTxt), 'D8 selection count shows 2');
  const clearBtn = await p.$('#clearall');
  check(clearBtn !== null, 'D7a Clear-all control exists');
  if (clearBtn){
    await p.click('#clearall'); await sleep(900);
    const anyChecked = await p.evaluate(() =>
      [...document.querySelectorAll('input[type=checkbox]')].some(c => c.checked));
    check(!anyChecked, 'D7b Clear-all unchecks everything');
    check(/check|select/i.test(await diagText(p)), 'D7c empty state returns after clear');
  } else { failures.push('D7b (skipped)', 'D7c (skipped)'); }
  await p.close();

  // ---------- MOBILE ----------
  console.log('M1-M5: mobile (390x844)');
  p = await freshPage(MOBILE);
  const noOverflow = await p.evaluate(() =>
    document.scrollingElement.scrollWidth <= window.innerWidth + 1);
  check(noOverflow, 'M1 no horizontal page overflow');
  const stacked = await p.evaluate(() => {
    const a = document.getElementById('panel').getBoundingClientRect();
    const cEl = document.getElementById("canvas"); if (!cEl) return false; const b = cEl.getBoundingClientRect();
    return b.top >= a.top && a.width > window.innerWidth * 0.85 && b.width > window.innerWidth * 0.85;
  });
  check(stacked, 'M2 panel and map stack full-width on mobile');
  const rowOk = await p.evaluate(() => {
    const vis = [...document.querySelectorAll('label')].filter(l => l.getBoundingClientRect().height > 0);
    return vis.length >= 8 && vis.every(l => l.getBoundingClientRect().height >= 40);
  });
  check(rowOk, 'M4 every visible checkbox row is a >=40px touch target');
  await p.click('#ch_standalone');
  await sleep(1200);
  const barVisible = await p.evaluate(() => {
    const el = document.getElementById('mobilebar');
    if (!el) return false;
    const r = el.getBoundingClientRect();
    return getComputedStyle(el).display !== 'none' && r.height > 0 && r.bottom <= window.innerHeight + 1;
  });
  check(barVisible, 'M3a sticky bottom bar appears after first selection');
  if (barVisible){
    await p.click('#viewmap'); await sleep(700);
    const inView = await p.evaluate(() => {
      const r = document.getElementById('diagram').getBoundingClientRect();
      return r.top >= -20 && r.top < window.innerHeight;
    });
    check(inView, 'M3b View-map scrolls the chart into view');
  } else failures.push('M3b (skipped)');
  const fitDefault = await p.evaluate(() => {
    const svg = document.querySelector('#diagram svg'); if (!svg) return false;
    return svg.getBoundingClientRect().width <= document.getElementById('diagram').clientWidth + 2
      && document.getElementById('fitbtn').textContent.includes('Actual');
  });
  check(fitDefault, 'M5a mobile defaults to fit-width (overview first)');
  const toggleWorks = await p.evaluate(async () => {
    document.getElementById('fitbtn').click();
    await new Promise(r => setTimeout(r, 300));
    return document.getElementById('fitbtn').textContent.includes('Fit');
  });
  check(toggleWorks, 'M5b toggle switches to actual size');
  await p.close();

  // ---------- regressions (must hold in v3) ----------
  console.log('R: semantics regressions');
  p = await freshPage(DESKTOP);
  await p.click('#win_app_rc_wsl'); await sleep(900);
  t = await diagText(p);
  check(t.includes('CLI in WSL') && !t.includes('User CLAUDE.md — Windows'),
        'R1 client-only desktop app keeps Windows home out');
  await p.close();
  p = await freshPage(DESKTOP);
  await p.click('#cw_local_noproj'); await p.click('#win_cli_native');
  await sleep(900); t = await diagText(p);
  check(t.includes('Folder instructions') && t.includes('CLAUDE.md') && !t.includes('repo/project folder'),
        'R2 folder instructions + repo-only CLAUDE.md term');
  check(await p.evaluate(() => !document.getElementById('cw_desktop') && !document.getElementById('cw_standalone')),
        'R2b old Cowork checkboxes removed');
  check((await p.$eval('.cnt[data-grp="cw"]', el => el.textContent)).includes('of 4'),
        'R2c Cowork badge counts 4');
  await p.close();
  p = await freshPage(DESKTOP, true);
  await p.click('#ch_standalone'); await sleep(1500);
  t = await diagText(p);
  check(t.includes('failed to load') && t.includes('flowchart LR'),
        'R3 CDN failure falls back to banner + source');
  await p.close();

  // ---------- N: RC propagation + sync summary + iPhone 17 viewport ----------
  console.log('N1: remote-control checkbox propagation');
  p = await freshPage(DESKTOP);
  await p.click('#win_app_rc_wsl'); await sleep(300);
  check(await p.$eval('#win_cli_wsl', el => el.checked), 'N1a checking RC-WSL checks the WSL CLI box');
  await p.click('#win_cli_wsl'); await sleep(300);
  check(await p.$eval('#win_app_rc_wsl', el => !el.checked), 'N1b unchecking the host unchecks dependent RC box');
  const gone = await p.evaluate(() => !document.getElementById('mac_app_rc'));
  check(gone, 'N1c Mac remote-control checkbox removed');
  const cwSubgrps = await p.evaluate(() =>
    [...document.querySelectorAll('.card[data-tint="cw"] .subgrp')].map(el => el.textContent));
  check(cwSubgrps.some(t => t.includes('Remote sessions')) && cwSubgrps.some(t => t.includes('Local sessions')),
        'N1d Cowork card has Remote sessions and Local sessions subgroups');
  await p.close();

  console.log('N2: live sync summary above the chart');
  p = await freshPage(DESKTOP);
  await setScope(p, 'both');
  const syncAboveChart = await p.evaluate(() => {
    const s = document.getElementById('syncdesk'), d = document.getElementById('diagram');
    return s && d && s.getBoundingClientRect().top < d.getBoundingClientRect().top;
  });
  check(syncAboveChart, 'N2a sync panel exists above the chart');
  await p.click('#win_cli_wsl'); await p.click('#win_vscode_wsl'); await sleep(900);
  let sync = await p.$eval('#syncdesk', el => el.textContent);
  check(sync.includes('WSL home') && sync.includes('CLAUDE.md'),
        'N2b two WSL contexts: WSL home + project notes in sync');
  await p.click('#win_cli_native'); await sleep(900);
  sync = await p.$eval('#syncdesk', el => el.textContent);
  const inSyncPart = await p.$eval('#syncdesk .insync', el => el.textContent);
  const notSyncPart = await p.$eval('#syncdesk .notsync', el => el.textContent);
  check(inSyncPart.includes('CLAUDE.md') && !inSyncPart.includes('WSL home'),
        'N2c adding native Windows: only project notes stay fully in sync');
  check(notSyncPart.includes('WSL home') && notSyncPart.includes('Windows home'),
        'N2d homes listed as not shared');
  await p.click('#ch_standalone'); await sleep(900);
  check((await p.$eval('#syncdesk .insync', el => el.textContent)).toLowerCase().includes('none'),
        'N2e chat + code: nothing spans the whole selection');
  sync = await p.$eval('#syncdesk', el => el.textContent);
  check(sync.includes('Memory from chat history') && sync.includes('every standalone chat')
        && !sync.includes('Chat memory'),
        'N2f official term with cross-chat scope, no invented term');
  await p.close();

  console.log('L: one-item-per-line + brief/full label modes');
  p = await freshPage(DESKTOP);
  await setScope(p, 'both');
  await p.click('#win_cli_wsl'); await p.click('#win_vscode_wsl'); await sleep(900);
  const lineLayout = await p.evaluate(() => {
    const items = [...document.querySelectorAll('#syncdesk .insync .syncitem')];
    if (items.length !== 3) return {ok:false, n:items.length};
    const [a,b] = items.map(i => i.getBoundingClientRect());
    return {ok: Math.abs(a.top - b.top) > 8, n:items.length};
  });
  check(lineLayout.ok, 'L1 in-sync items render one per line (3 split stores)');
  let txt = await p.$eval('#syncdesk', el => el.textContent);
  check(txt.includes('WSL home') && txt.includes('Legend'),
        'L2a brief mode is default and a legend exists');
  check(txt.includes('auto memory') && txt.includes('~/.claude'),
        'L2b legend defines the jargon (auto memory, ~/.claude)');
  await p.click('#labelmode'); await sleep(400);
  txt = await p.$eval('#syncdesk', el => el.textContent);
  check(txt.includes('WSL file system'), 'L3 full mode spells out the store');
  await p.click('#labelmode'); await sleep(400);
  txt = await p.$eval('#syncdesk .insync', el => el.textContent);
  check(txt.includes('CLAUDE.md (repo)'), 'L4a repo term in brief label (code-only)');
  await p.click('#cw_local_project'); await sleep(900);
  txt = await p.$eval('#syncdesk', el => el.textContent);
  check(txt.includes('CLAUDE.md (repo)') && !txt.includes('CLAUDE.md (repo/project folder)')
        && txt.includes('Cowork folder instructions'),
        'L4b adding Cowork keeps the repo-only term and lists Cowork folder instructions');
  await p.click('#win_cli_native'); await sleep(900);   // a Windows-home context so winhome is listed
  await p.click('#labelmode'); await sleep(300);
  txt = await p.$eval('#syncdesk', el => el.textContent);
  check(txt.includes('C:\\Users\\you\\.claude') && !txt.includes('C:\\\\Users'),
        'L5 Windows path renders with single backslashes in full labels');
  await p.close();

  console.log('N3: iPhone 17 — sync summary stays in viewport during selection');
  p = await freshPage({width:393, height:852});
  await p.click('#ch_standalone'); await sleep(900);
  await p.evaluate(() => window.scrollTo(0, document.body.scrollHeight * 0.4));
  await sleep(400);
  const glanceable = await p.evaluate(() => {
    const s = document.getElementById('syncmob');
    if (!s) return false;
    const r = s.getBoundingClientRect();
    const visible = getComputedStyle(s).display !== 'none' && r.top >= 0 && r.bottom <= window.innerHeight;
    const someRow = [...document.querySelectorAll('label')].some(l => {
      const lr = l.getBoundingClientRect();
      return lr.top > r.bottom && lr.bottom < window.innerHeight;
    });
    return visible && someRow;
  });
  check(glanceable, 'N3 sync summary and checkbox rows share the iPhone 17 viewport mid-scroll');
  await p.close();

  console.log('S: I\u2019m-interested-in scope selector');
  p = await freshPage(DESKTOP);
  const s1 = await p.evaluate(() => {
    const el = document.getElementById('scope');
    return el && el.closest('header') !== null ? el.value : null;
  });
  check(s1 === 'across', 'S1 selector exists in header, defaults to across-projects');
  await p.click('#win_cli_wsl'); await p.click('#win_vscode_wsl'); await sleep(900);
  let stxt = await p.$eval('#syncdesk', el => el.textContent);
  let sin = await p.$eval('#syncdesk .insync', el => el.textContent);
  check(sin.includes('User CLAUDE.md'), 'S2a across: user CLAUDE.md in sync');
  let sitems = await p.$$eval('#syncdesk .syncitem', els => els.map(e => e.textContent).join('|'));
  check(!sitems.includes('Auto memory') && !sitems.includes('CLAUDE.md (repo'),
        'S2b across: per-project stores filtered out of the lists');
  await setScope(p, 'within');
  sin = await p.$eval('#syncdesk .insync', el => el.textContent);
  stxt = await p.$eval('#syncdesk', el => el.textContent);
  check(sin.includes('Auto memory') && sin.includes('CLAUDE.md (repo)'),
        'S3a within: auto memory + repo CLAUDE.md in sync');
  sitems = await p.$$eval('#syncdesk .syncitem', els => els.map(e => e.textContent).join('|'));
  check(!sitems.includes('User CLAUDE.md'), 'S3b within: cross-project stores filtered out of the lists');
  await setScope(p, 'both');
  stxt = await p.$eval('#syncdesk', el => el.textContent);
  check(stxt.includes('User CLAUDE.md') && stxt.includes('Auto memory'),
        'S4 both: every store class shown');
  await p.close();

  console.log('P/T: profile preferences + umbrella terminology');
  p = await freshPage(DESKTOP);
  await p.click('#ch_standalone'); await sleep(900);
  let pitems = await p.$$eval('#syncdesk .syncitem', els => els.map(e => e.textContent).join('|'));
  check(pitems.includes('Instructions for Claude'), 'P1 chat context surfaces Instructions for Claude under across-lens');
  let ptxt = await diagText(p);
  check(ptxt.includes('Instructions for Claude'), 'P3 chart shows the Instructions-for-Claude store');
  await p.close();
  p = await freshPage(DESKTOP);
  await p.click('#cw_remote_noproj'); await sleep(900);
  pitems = await p.$$eval('#syncdesk .syncitem', els => els.map(e => e.textContent).join('|'));
  check(pitems.includes('Instructions for Claude') && pitems.includes('Cowork global instructions'),
        'P2 Cowork sessions also receive Instructions for Claude and Cowork global instructions');
  const trm = await p.evaluate(() => ({
    h2: document.querySelector('.canvasbar h2').textContent,
    opts: [...document.querySelectorAll('#scope option')].map(o => o.textContent).join('|'),
  }));
  check(trm.h2.includes('What Claude remembers'), 'T1 heading uses the umbrella phrase, not generic memory');
  check(trm.opts.includes('remembered across') && trm.opts.includes('remembered within'),
        'T2 scope options use remembered-across/within phrasing');
  await p.close();

  console.log('E: profile-preferences field elaboration');
  p = await freshPage(DESKTOP);
  await p.click('#ch_standalone'); await sleep(900);
  let etxt = await p.$eval('#syncdesk', el => el.textContent);
  check(!etxt.includes('call you') && etxt.includes('keep these in mind'),
        'E1 legend quotes the official description, fields demoted');
  const foot = await p.$$eval('.fine', els => els.map(e => e.textContent).join(' '));
  check(foot.includes('call you') && foot.includes('describes your work'),
        'E1b lightweight Profile fields live in the footnote');
  let echart = await diagText(p);
  check(echart.includes('Instructions for Claude') && !echart.includes('call you'),
        'E2 chart node carries the shipping label only');
  await p.evaluate(() => document.getElementById('labelmode').click()); await sleep(300);
  etxt = await p.$$eval('#syncdesk .syncitem', els => els.map(e => e.textContent).join('|'));
  check(etxt.includes('free-text'), 'E3 full label mentions the free-text field');
  await p.close();

  console.log('SC: scope-dependent checkbox disabling');
  const rowOf = id => { const el = document.getElementById(id); return el ? el.closest('label') : null; };
  p = await freshPage(DESKTOP);
  let sc = await p.evaluate(() => ({
    web: document.getElementById('code_web').disabled,
    appweb: document.getElementById('win_app_web').disabled,
    chat: document.getElementById('ch_standalone').disabled,
    note: (document.getElementById('code_web')?.closest('label')?.querySelector('.scopenote')?.textContent) || '',
  }));
  check(sc.web && sc.appweb && !sc.chat, 'SC1 across-lens disables web sessions only');
  check(sc.note.includes('across'), 'SC1b disabled row explains why');
  await setScope(p, 'within');
  sc = await p.evaluate(() => ({
    web: document.getElementById('code_web').disabled,
    chat: document.getElementById('ch_standalone').disabled,
    note: (document.getElementById('ch_standalone')?.closest('label')?.querySelector('.scopenote')?.textContent) || '',
  }));
  check(!sc.web && sc.chat, 'SC2 within-lens disables standalone chats only');
  check(sc.note.includes('project'), 'SC2b note explains the within gap');
  await setScope(p, 'both');
  sc = await p.evaluate(() =>
    ['code_web','win_app_web','mac_app_web','ch_standalone'].every(i => !document.getElementById(i).disabled));
  check(sc, 'SC3 both-lens disables nothing');
  await p.click('#code_web'); await sleep(400);
  await setScope(p, 'across');
  sc = await p.evaluate(() => ({
    disabled: document.getElementById('code_web').disabled,
    dimmed: !!document.getElementById('code_web')?.closest('label')?.classList.contains('scopedim'),
  }));
  check(!sc.disabled && sc.dimmed, 'SC4 a checked box stays operable when scope turns against it');
  await p.click('#code_web'); await sleep(400);
  check(await p.$eval('#code_web', el => el.disabled), 'SC4b once unchecked it disables');
  await p.close();

  console.log('CW: Cowork remote/local split + chat-only note');
  p = await freshPage(DESKTOP);
  await p.click('#ch_standalone'); await p.click('#cw_remote_project'); await sleep(900);
  t = await diagText(p);
  check(/chat-only/i.test(t) && t.includes('Cowork'), 'CW1a chat + remote Cowork project renders the chat-only headline');
  let cwSync = await p.$eval('#syncdesk', el => el.textContent);
  check(cwSync.includes('Memory is chat-only'), 'CW1b sync notes cite the chat-only line');
  await p.close();

  p = await freshPage(DESKTOP);
  await p.click('#cw_remote_noproj'); await sleep(900);
  t = await diagText(p);
  check(t.includes("Anthropic's servers") && t.includes('files Claude delivers'),
        'CW2a remote-noproj diagram names Anthropic’s servers and delivered files');
  let cwItems = await p.$$eval('#syncdesk .syncitem', els => els.map(e => e.textContent).join('|'));
  check(cwItems.includes('Cowork global instructions'), 'CW2b remote-noproj sync lists Cowork global instructions');
  await p.close();

  p = await freshPage(DESKTOP);
  await p.click('#cw_local_project'); await sleep(900);
  t = await diagText(p);
  check(t.includes('On one computer — Cowork'), 'CW3a local project memory sits in the on-one-computer group');
  await p.click('#cw_remote_project'); await sleep(900);
  t = await diagText(p);
  check(!t.includes('On one computer — Cowork') && t.includes('not yet documented'),
        'CW3b adding a remote project makes project memory bare and undocumented for remote');
  await p.close();

  p = await freshPage(DESKTOP);
  await setScope(p, 'within');
  const cw4 = await p.evaluate(() => ({
    disabled: document.getElementById('cw_remote_noproj').disabled,
    note: document.getElementById('cw_remote_noproj').closest('label').querySelector('.scopenote').textContent,
  }));
  check(cw4.disabled && cw4.note.length > 0, 'CW4a within-scope disables remote-noproj with a scopenote');
  await setScope(p, 'across');
  const cw4b = await p.evaluate(() => ['cw_remote_project','cw_remote_noproj','cw_local_project','cw_local_noproj']
    .every(id => !document.getElementById(id).disabled));
  check(cw4b, 'CW4b across-scope leaves all cw contexts enabled');
  await p.close();

  p = await freshPage(DESKTOP);
  await p.click('#ch_standalone'); await p.click('#cw_remote_noproj'); await sleep(900);
  const cwLegend = await p.$eval('#syncdesk', el => el.textContent);
  check(cwLegend.includes('chat-only'), 'CW5 legend mentions memory being chat-only');
  await p.close();

  console.log('WM: Cowork web + mobile remote-session notes');
  p = await freshPage(DESKTOP);
  const wmSub = await p.$eval('.card[data-tint="cw"] .cardsub', el => el.textContent);
  check(wmSub.includes('claude.ai') && wmSub.includes('mobile app'),
        'WM1 Cowork card names the web and mobile surfaces');
  const wmFoot = await p.$$eval('.fine', els => els.map(e => e.textContent).join(' '));
  check(wmFoot.includes('laptop closed') && wmFoot.includes('no device online'),
        'WM2 footnote: work continues laptop-closed, scheduled tasks need no device online');
  check(wmFoot.includes('projects and artifacts'),
        'WM3 shared home spans projects and artifacts');
  check(wmFoot.includes('local files and browser') && wmFoot.includes('Max plan'),
        'WM4 desktop full-experience and Max-first rollout stay footnote-level');
  await p.close();

  console.log('SETX: chat memory Settings node correction');
  p = await freshPage(DESKTOP);
  await p.click('#ch_standalone'); await sleep(900);
  t = await diagText(p);
  check(t.includes('Capabilities') && !t.includes('Settings → Memory page'),
        'SETX chat-memory Settings node points at Capabilities, not the old Memory page');
  await p.close();

  console.log('C: collapsible sections with X-of-Y badges');
  p = await freshPage(DESKTOP, false, false);   // keep natural collapsed state
  const c1 = await p.evaluate(() => ({
    macHidden: document.getElementById('mac_cli').getBoundingClientRect().height === 0,
    winHidden: document.getElementById('win_cli_wsl').getBoundingClientRect().height === 0,
    chatVisible: document.getElementById('ch_standalone').getBoundingClientRect().height > 0,
  }));
  check(c1.macHidden && c1.winHidden && c1.chatVisible,
        'C1 Mac and Windows groups collapsed by default; chat leaves visible');
  const badges = await p.evaluate(() => ({
    mac: document.querySelector('.cnt[data-grp="mac"]').textContent,
    win: document.querySelector('.cnt[data-grp="win"]').textContent,
  }));
  check(badges.mac.includes('0 of 4') && badges.win.includes('0 of 7'),
        'C2 collapsed groups show 0-of-Y indicators');
  await p.click('summary.plat[data-grp="win"]'); await sleep(300);
  await p.click('#win_cli_wsl'); await p.click('#win_cli_native'); await sleep(400);
  await p.click('summary.plat[data-grp="win"]'); await sleep(300);
  const after = await p.evaluate(() => ({
    badge: document.querySelector('.cnt[data-grp="win"]').textContent,
    hidden: document.getElementById('win_cli_wsl').getBoundingClientRect().height === 0,
    codeBadge: document.querySelector('.cnt[data-grp="code"]').textContent,
  }));
  check(after.badge.includes('2 of 7') && after.hidden,
        'C3 re-collapsed group still reports 2 of 7');
  check(after.codeBadge.includes('2 of 12'), 'C4 product card rolls up 2 of 12');
  const order = await p.evaluate(() => {
    const cards = [...document.querySelectorAll('#panel details.card')].map(d => d.dataset.tint);
    return { cards: cards.join(','), noRc: !document.getElementById('code_rc'),
             noIncog: !document.getElementById('ch_incognito') };
  });
  check(order.cards === 'chat,cw,code', 'O1 card order is chat, cowork, code');
  check(order.noRc && order.noIncog, 'O2 generic Remote Control and Incognito boxes removed');
  await p.click('#clearall'); await sleep(400);
  check((await p.$eval('.cnt[data-grp="win"]', el => el.textContent)).includes('0 of 7'),
        'C5 Clear all resets badges');
  await p.close();

  await browser.close();
  console.log(`\n${passes} passed, ${failures.length} failed`);
  if (failures.length){ console.log('FAILED:', failures.join(' | ')); process.exit(1); }
})().catch(e => { console.error('HARNESS ERROR:', e.message); process.exit(1); });
