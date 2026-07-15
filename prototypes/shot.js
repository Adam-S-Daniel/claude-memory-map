#!/usr/bin/env node
// Screenshot harness for HTML prototype files (prototypes/*.html).
//   - loads file://<abs-path>?demo in puppeteer-core
//   - waits for window.__PROTO_READY === true (5s timeout, non-fatal) + 600ms settle
//   - captures desktop (1400x900) and mobile (390x844) viewport screenshots
//     into prototypes/screenshots/, both at deviceScaleFactor 2 for crisp text
//
// Usage:  node prototypes/shot.js prototypes/<name>.html [more.html ...]

const puppeteer = require('puppeteer-core');
const fs = require('fs');
const path = require('path');
const os = require('os');

const SCREENSHOT_DIR = path.resolve(__dirname, 'screenshots');

// Browser launch resolution (mirrors tests/tests_picker.js).
//   CI / serverless: CHROMIUM_PATH unset (or /tmp/chromium) -> @sparticuz/chromium args, headless shell.
//   Local: auto-detect a Chrome-for-Testing under ~/.cache/puppeteer (or CHROMIUM_PATH) -> desktop args.
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
function launchOptions(){
  const exe = process.env.CHROMIUM_PATH || detectLocalChrome();
  const serverless = !exe || exe === '/tmp/chromium';
  if (serverless){
    return { executablePath: exe || '/tmp/chromium',
      args: require('@sparticuz/chromium').default.args, headless: 'shell' };
  }
  return {
    executablePath: exe,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage'],
    headless: 'new',
  };
}

const VIEWPORTS = {
  desktop: { width: 1400, height: 900, deviceScaleFactor: 2 },
  mobile: { width: 390, height: 844, deviceScaleFactor: 2 },
};

async function shootOne(browser, htmlPath){
  const absPath = path.resolve(htmlPath);
  if (!fs.existsSync(absPath)) throw new Error(`not found: ${absPath}`);
  const basename = path.basename(absPath, path.extname(absPath));
  const url = 'file://' + absPath + '?demo';

  const page = await browser.newPage();
  try {
    await page.goto(url, { waitUntil: 'load' });
    try {
      await page.waitForFunction('window.__PROTO_READY === true', { timeout: 5000 });
    } catch {} // demo may not signal readiness; fall through to the settle delay
    await new Promise(r => setTimeout(r, 600));

    for (const [name, viewport] of Object.entries(VIEWPORTS)){
      await page.setViewport(viewport);
      const outPath = path.join(SCREENSHOT_DIR, `${basename}-${name}.png`);
      await page.screenshot({ path: outPath, fullPage: false });
      console.log('wrote', outPath);
    }
  } finally {
    await page.close();
  }
}

async function main(){
  const files = process.argv.slice(2);
  if (files.length === 0){
    console.error('Usage: node prototypes/shot.js prototypes/<name>.html [more.html ...]');
    process.exit(1);
  }
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

  const browser = await puppeteer.launch(launchOptions());
  let failed = false;
  try {
    for (const file of files){
      try {
        await shootOne(browser, file);
      } catch (err){
        console.error('FAILED', file, '-', err.message);
        failed = true;
      }
    }
  } finally {
    await browser.close();
  }
  process.exit(failed ? 1 : 0);
}

main().catch(err => {
  console.error(err);
  process.exit(1);
});
