// Preview ↔ render parity check: frames drawn by VideoHub's contract (renderOut(t) on videohub.html) must
// match frames captured by HyperFrames itself (`hyperframes snapshot --at t`). Used by `fvs verify-preview`
// and by the tests. Uses the Chromium that Playwright provides.
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { REPO_ROOT } from './build-preview.mjs';

const MIME = { '.html': 'text/html', '.js': 'text/javascript', '.mjs': 'text/javascript', '.css': 'text/css', '.svg': 'image/svg+xml',
  '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.webp': 'image/webp', '.wav': 'audio/wav', '.mp3': 'audio/mpeg',
  '.mp4': 'video/mp4', '.json': 'application/json', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf' };

export function staticServer(root) {
  const srv = http.createServer((req, res) => {
    const rel = decodeURIComponent(new URL(req.url, 'http://x').pathname).replace(/^\/+/, '');
    const file = path.resolve(root, rel || 'index.html');
    if (!file.startsWith(path.resolve(root)) || !fs.existsSync(file) || fs.statSync(file).isDirectory()) { res.writeHead(404); return res.end(); }
    res.writeHead(200, { 'content-type': MIME[path.extname(file).toLowerCase()] || 'application/octet-stream' });
    fs.createReadStream(file).pipe(res);
  });
  return new Promise(r => srv.listen(0, '127.0.0.1', () => r({ srv, url: `http://127.0.0.1:${srv.address().port}` })));
}

export async function loadChromium() {
  for (const spec of ['playwright-core', 'playwright', '/opt/node-tools/node_modules/playwright/index.js']) {
    try { const m = await import(spec); return (m.default || m).chromium; } catch { /* next */ }
  }
  throw new Error('Playwright is not installed (npm install playwright-core, or use the system Playwright)');
}

const BROWSER_CANDIDATES = [
  process.env.FVS_CHROME,
  '/opt/pw-browsers/chromium-1243/chrome-linux/chrome', '/opt/pw-browsers/chromium/chrome-linux/chrome',
  '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser',
  'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', 'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
  'C:/Program Files/Google/Chrome/Application/chrome.exe',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
].filter(Boolean);

/** Launch Chromium: Playwright's own build if present, else the first installed Chrome/Edge/Chromium. */
// The rasterisation flags HyperFrames' capture browser uses (packages/engine/src/services/browserManager.ts),
// so a parity comparison measures the composition, not font hinting or GPU differences.
export const CAPTURE_ARGS = ['--font-render-hinting=none', '--disable-lcd-text', '--force-color-profile=srgb',
  '--force-device-scale-factor=1', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader'];

export async function launchBrowser({ args = CAPTURE_ARGS } = {}) {
  const chromium = await loadChromium();
  try { return await chromium.launch({ args }); } catch (first) {
    for (const exe of BROWSER_CANDIDATES) {
      if (!fs.existsSync(exe)) continue;
      try { return await chromium.launch({ executablePath: exe, args: ['--no-sandbox', ...args] }); } catch { /* next */ }
    }
    throw first;
  }
}

/** Open videohub.html, wait for READY, then renderOut(t) + screenshot for each time. */
export async function captureViaAdapter(projectDir, times, outDir) {
  const { srv, url } = await staticServer(projectDir);
  const browser = await launchBrowser();
  const errors = [];
  try {
    const cfg = JSON.parse(fs.readFileSync(path.join(projectDir, 'preview', 'videohub.html'), 'utf8').match(/__FVS_PREVIEW__=(\{.*?\});/)[1]);
    const page = await browser.newPage({ viewport: { width: cfg.width, height: cfg.height } });
    page.on('pageerror', e => errors.push(e.message));
    await page.goto(`${url}/preview/videohub.html`);
    await page.waitForFunction(() => window.READY === true || window.__vhError, null, { timeout: 120000 });
    const err = await page.evaluate(() => window.__vhError || null);
    if (err) throw new Error(err);
    const out = [];
    fs.mkdirSync(outDir, { recursive: true });
    for (const t of times) {
      const ms = await page.evaluate(t => { const a = performance.now(); window.renderOut(t); return performance.now() - a; }, t);
      await page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
      const file = path.join(outDir, `adapter-${t.toFixed(3)}.png`);
      await page.screenshot({ path: file });
      out.push({ t, file, renderOutMs: +ms.toFixed(2) });
    }
    const scenes = await page.evaluate(() => window.VH_SCENES || []);
    return { frames: out, scenes, errors };
  } finally {
    await browser.close();
    srv.close();
  }
}

export function captureViaHyperframes(projectDir, times, outDir) {
  fs.mkdirSync(outDir, { recursive: true });
  const bin = path.join(REPO_ROOT, 'node_modules', '.bin', process.platform === 'win32' ? 'hyperframes.cmd' : 'hyperframes');
  const r = spawnSync(bin, ['snapshot', projectDir, '--at', times.join(','), '--no-end', '--keep', '-o', outDir, '--json'],
    { encoding: 'utf8', shell: process.platform === 'win32', env: { ...process.env, HYPERFRAMES_NO_UPDATE_CHECK: '1' } });
  if (r.status !== 0) throw new Error(`hyperframes snapshot failed: ${(r.stderr || r.stdout).slice(-800)}`);
  // `--keep` names each still at-<seconds>s.png without trailing zeros (at-0s, at-1.5s, at-12.25s)
  return times.map(t => {
    const file = path.join(outDir, `at-${+t.toFixed(3)}s.png`);
    return { t, file: fs.existsSync(file) ? file : null };
  });
}

/** PSNR (dB) between two images with FFmpeg; Infinity when identical. */
export function psnr(a, b) {
  const r = spawnSync('ffmpeg', ['-v', 'info', '-i', a, '-i', b, '-lavfi', '[0:v]scale=1920:1080,format=rgb24[x];[1:v]scale=1920:1080,format=rgb24[y];[x][y]psnr', '-f', 'null', '-'], { encoding: 'utf8' });
  const m = r.stderr.match(/average:(inf|[\d.]+)/);
  if (!m) throw new Error('psnr failed: ' + r.stderr.slice(-400));
  return m[1] === 'inf' ? Infinity : +m[1];
}

export async function verifyParity(projectDir, times, workDir, { minPsnr = 35 } = {}) {
  const a = await captureViaAdapter(projectDir, times, workDir);
  const h = captureViaHyperframes(projectDir, times, path.join(workDir, 'hyperframes'));
  const rows = a.frames.map((f, i) => {
    const ref = h[i].file;
    const db = ref ? psnr(f.file, ref) : null;
    return { t: f.t, psnr: db === Infinity ? 'identical' : db, pass: db !== null && db >= minPsnr, renderOutMs: f.renderOutMs, adapter: f.file, hyperframes: ref };
  });
  return { pass: rows.every(r => r.pass), minPsnr, rows, scenes: a.scenes, pageErrors: a.errors };
}
