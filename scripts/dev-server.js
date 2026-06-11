#!/usr/bin/env node
// Zero-dependency dev server for interactively debugging index.html.
//   - serves the repo root over HTTP (so the page runs from a real origin, not file://)
//   - injects a tiny live-reload client into index.html
//   - watches index.html + suite/ and reloads the browser on change
//   - watches src/*.py and rebuilds (python3 src/build_picker3.py) on change,
//     which rewrites index.html and triggers the reload above
//
// Usage:  node scripts/dev-server.js  [--port 8000] [--no-build]
//         npm run dev
// On WSL, open the printed http://localhost:<port>/ URL in your Windows browser.

const http = require('http');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const ROOT = path.resolve(__dirname, '..');
const argv = process.argv.slice(2);
const PORT = Number(getArg('--port')) || Number(process.env.PORT) || 8000;
const AUTO_BUILD = !argv.includes('--no-build');
const BUILD_CMD = ['python3', ['src/build_picker3.py']];

function getArg(flag){ const i = argv.indexOf(flag); return i >= 0 ? argv[i + 1] : null; }

const MIME = {
  '.html': 'text/html; charset=utf-8', '.js': 'application/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8', '.json': 'application/json; charset=utf-8',
  '.mermaid': 'text/plain; charset=utf-8', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.ico': 'image/x-icon', '.map': 'application/json',
};

// --- live-reload plumbing (Server-Sent Events) ---
const clients = new Set();
function broadcastReload(){
  for (const res of clients) res.write('data: reload\n\n');
}
const RELOAD_SNIPPET = `
<script>
(function(){
  var es = new EventSource('/__livereload');
  es.onmessage = function(e){ if (e.data === 'reload') location.reload(); };
  es.onerror = function(){ /* server restarting; EventSource auto-retries */ };
})();
</script>
`;

const server = http.createServer((req, res) => {
  const url = req.url.split('?')[0];

  if (url === '/__livereload'){
    res.writeHead(200, {
      'Content-Type': 'text/event-stream', 'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
    });
    res.write('retry: 1000\n\n');
    clients.add(res);
    req.on('close', () => clients.delete(res));
    return;
  }

  let rel = decodeURIComponent(url);
  if (rel === '/') rel = '/index.html';
  const filePath = path.join(ROOT, path.normalize(rel));
  if (!filePath.startsWith(ROOT)){ res.writeHead(403).end('Forbidden'); return; }

  fs.readFile(filePath, (err, buf) => {
    if (err){ res.writeHead(404, {'Content-Type':'text/plain'}).end('Not found: ' + rel); return; }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {'Content-Type': MIME[ext] || 'application/octet-stream', 'Cache-Control': 'no-store'});
    if (ext === '.html'){
      let html = buf.toString('utf8');
      html = html.includes('</body>')
        ? html.replace('</body>', RELOAD_SNIPPET + '</body>')
        : html + RELOAD_SNIPPET;
      res.end(html);
    } else {
      res.end(buf);
    }
  });
});

// --- watchers (debounced) ---
function debounce(fn, ms){ let t; return () => { clearTimeout(t); t = setTimeout(fn, ms); }; }

let building = false, rebuildQueued = false;
function rebuild(){
  if (building){ rebuildQueued = true; return; }
  building = true;
  const [cmd, args] = BUILD_CMD;
  const t0 = Date.now();
  const proc = spawn(cmd, args, { cwd: ROOT, stdio: ['ignore', 'inherit', 'inherit'] });
  proc.on('exit', (code) => {
    building = false;
    if (code === 0) console.log(`[build] ok (${Date.now() - t0}ms)`);
    else console.error(`[build] FAILED (exit ${code}) — fix the error above`);
    if (rebuildQueued){ rebuildQueued = false; rebuild(); }
    // index.html change is picked up by the output watcher below -> reload
  });
}

function watchDir(dir, onChange){
  try {
    fs.watch(dir, { recursive: false }, onChange);
  } catch (e) { console.warn(`[watch] cannot watch ${dir}: ${e.message}`); }
}

const onOutputChange = debounce(() => { console.log('[reload] output changed'); broadcastReload(); }, 120);
watchDir(ROOT, (_e, f) => { if (f === 'index.html') onOutputChange(); });
watchDir(path.join(ROOT, 'suite'), () => onOutputChange());

if (AUTO_BUILD){
  const onSrcChange = debounce(() => { console.log('[build] src changed -> rebuilding'); rebuild(); }, 150);
  watchDir(path.join(ROOT, 'src'), (_e, f) => { if (f && f.endsWith('.py')) onSrcChange(); });
}

server.listen(PORT, () => {
  console.log(`\n  Memory-map dev server`);
  console.log(`  → http://localhost:${PORT}/   (open in your browser; DevTools = F12)`);
  console.log(`  live-reload: on   auto-build on src/*.py change: ${AUTO_BUILD ? 'on' : 'off'}`);
  console.log(`  Ctrl-C to stop\n`);
});
