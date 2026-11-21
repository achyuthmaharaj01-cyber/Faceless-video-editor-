// Generate the VideoHub live-preview page for a HyperFrames project.
//
// index.html stays the single, authoritative HyperFrames composition (it is what `hyperframes render`
// renders). videohub.html is a generated copy of it with three scripts added at the start of <head>:
//   1. window.__FVS_PREVIEW__   size / fps / duration / a hash of index.html (staleness check)
//   2. preview/hf-runtime.js    the HyperFrames browser runtime from the pinned `hyperframes` package —
//                               the same file `hyperframes preview` and the renderer inject
//   3. preview/vh-adapter.js    exposes window.renderOut(t) / window.READY for VideoHub
// It also writes .videohub/project.json (merging, never dropping keys VideoHub owns) and render.mjs, which
// lets VideoHub's Render button drive a HyperFrames render.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
export const REPO_ROOT = path.resolve(HERE, '..', '..');
export const RUNTIME_SRC = path.join(REPO_ROOT, 'node_modules', 'hyperframes', 'dist', 'hyperframe.runtime.iife.js');
const ADAPTER_SRC = path.join(HERE, 'vh-adapter.js');
const RENDER_MARK = '// fvs:videohub-render-bridge';

export function fnv1a(text) {
  const bytes = Buffer.from(text, 'utf8');
  let h = 0x811c9dc5;
  for (const b of bytes) { h ^= b; h = Math.imul(h, 0x01000193) >>> 0; }
  return h.toString(16).padStart(8, '0');
}

/** Read width/height/duration from the root composition element of index.html. */
export function readRootMeta(html) {
  const tag = html.match(/<[a-z]+\b[^>]*\bdata-composition-id\s*=\s*["'][^"']+["'][^>]*>/i)?.[0];
  if (!tag) throw new Error('index.html has no element with data-composition-id (not a HyperFrames composition)');
  const attr = name => tag.match(new RegExp(`\\b${name}\\s*=\\s*["']([^"']*)["']`, 'i'))?.[1];
  return { id: attr('data-composition-id'), width: +attr('data-width') || 1920, height: +attr('data-height') || 1080, duration: +attr('data-duration') || 0 };
}

function writeIfChanged(file, content) {
  if (fs.existsSync(file) && fs.readFileSync(file, 'utf8') === content) return false;
  fs.mkdirSync(path.dirname(file), { recursive: true });
  fs.writeFileSync(file, content);
  return true;
}

function readJson(file, fallback) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return fallback; }
}

export function buildPreview(projectDir, { fps = 30, title, audio = 'audio/mix.wav', words = 'audio/words.json' } = {}) {
  const dir = path.resolve(projectDir);
  const indexFile = path.join(dir, 'index.html');
  if (!fs.existsSync(indexFile)) throw new Error(`No index.html in ${dir}`);
  if (!fs.existsSync(RUNTIME_SRC)) throw new Error(`HyperFrames runtime not found at ${RUNTIME_SRC}. Run npm install in the studio folder.`);
  const html = fs.readFileSync(indexFile, 'utf8');
  const meta = readRootMeta(html);
  // Scene lane for VideoHub: read from the scene hosts in index.html (the runtime replaces those hosts when it
  // mounts the sub-compositions, so the page cannot rediscover them later)
  const scenes = [...html.matchAll(/<[a-z]+\b[^>]*\bdata-fvs-scene="([^"]*)"[^>]*>/gi)].map(m => {
    const a = k => m[0].match(new RegExp(`\\b${k}="([^"]*)"`))?.[1];
    const t0 = +a('data-start'), d = +a('data-duration');
    return Number.isFinite(t0) && Number.isFinite(d) ? { name: m[1].replace(/&amp;/g, '&').replace(/&quot;/g, '"'), t0, t1: +(t0 + d).toFixed(3) } : null;
  }).filter(Boolean);
  const cfg = { width: meta.width, height: meta.height, fps, duration: meta.duration, sourceFile: 'index.html', sourceHash: fnv1a(html), scenes };
  // Mirror the CSS rule HyperFrames' own compiler injects before capture (producer htmlCompiler.ts /
  // core htmlBundler.ts injectTextRenderingRule): without it glyph positions differ by up to 1 px.
  const textRule = /data-hyperframes-text-rendering/.test(html) ? ''
    : '<style data-hyperframes-text-rendering="true">html,body,*{text-rendering:geometricPrecision}</style>';
  // The page lives in preview/ (a second root-level composition file would be picked up by HyperFrames as
  // another entry point); <base href="../"> keeps every relative path resolving from the project root.
  // The adapter is inlined: VideoHub looks for renderOut in the page itself (or a script beside it, resolved
  // without <base>), so an inline definition is found however the page is opened.
  const adapter = fs.readFileSync(ADAPTER_SRC, 'utf8').replace(/<\/script/gi, '<\\/script');
  const inject = '<base href="../">' + textRule + `<script>window.__FVS_PREVIEW__=${JSON.stringify(cfg)};</script>` +
    `<script src="preview/hf-runtime.js"></script><script>\n${adapter}\n</script>`;
  if (!/<head[^>]*>/i.test(html)) throw new Error('index.html has no <head>');
  const page = '<!-- GENERATED from index.html by faceless-video-studio for the VideoHub live preview. Do not edit: edit index.html. -->\n' +
    html.replace(/<head[^>]*>/i, m => m + inject);

  const changed = [];
  if (writeIfChanged(path.join(dir, 'preview', 'hf-runtime.js'), fs.readFileSync(RUNTIME_SRC, 'utf8'))) changed.push('preview/hf-runtime.js');
  if (writeIfChanged(path.join(dir, 'preview', 'videohub.html'), page)) changed.push('preview/videohub.html');
  const legacy = path.join(dir, 'videohub.html');   // older layout: page at the root (a second root composition)
  if (fs.existsSync(legacy) && fs.readFileSync(legacy, 'utf8').startsWith('<!-- GENERATED from index.html')) fs.rmSync(legacy);

  // .videohub/project.json: merge; keep keys VideoHub or the user set (status, notes settings, ...)
  const pjFile = path.join(dir, '.videohub', 'project.json');
  const pj = readJson(pjFile, {});
  pj.title = pj.title || title || path.basename(dir);
  pj.status = pj.status || 'review';
  pj.live = { ...(pj.live || {}), page: 'preview/videohub.html', audio, dur: meta.duration, fps };
  if (fs.existsSync(path.join(dir, words))) pj.transcript = { ...(pj.transcript || {}), file: words, offset: pj.transcript?.offset ?? 0 };
  pj.render = {
    ...(pj.render || {}),
    script: 'render.mjs',
    env: { ...(pj.render?.env || {}), DUR: String(meta.duration) },
    // HyperFrames already muxed narration + music + effects: VideoHub only copies the streams
    mux: ['-v', 'error', '-y', '-i', '{video}', '-map', '0:v:0', '-map', '0:a:0?', '-c', 'copy', '-movflags', '+faststart', '{out}'],
  };
  if (writeIfChanged(pjFile, JSON.stringify(pj, null, 2) + '\n')) changed.push('.videohub/project.json');

  const renderFile = path.join(dir, 'render.mjs');
  const existing = fs.existsSync(renderFile) ? fs.readFileSync(renderFile, 'utf8') : null;
  if (existing === null || existing.includes(RENDER_MARK)) {
    const fvs = path.join(REPO_ROOT, 'bin', 'fvs.mjs').split(path.sep).join('/');
    const script = `${RENDER_MARK}  (generated; VideoHub's Render button runs this)
// VideoHub runs \`node render.mjs <workers>\` and joins render/chunks/c_*.mp4. The authoritative renderer is
// HyperFrames: this asks faceless-video-studio to render index.html with it and hands the MP4 back as one
// chunk. PREVIEW=1 makes a fast draft into render/preview/video.mp4 instead.
import { spawnSync } from 'node:child_process';
const FPS = +(process.env.FPS || ${fps});
const preview = process.env.PREVIEW === '1';
const out = preview ? 'render/preview/video.mp4' : 'render/chunks/c_000.mp4';
const args = [${JSON.stringify(fvs)}, 'render', '.', '--out', out, '--fps', String(FPS), '--workers', String(+process.argv[2] || 1), '--source', 'videohub'];
if (preview) args.push('--draft');
console.log('0/1 chunks to render');
const r = spawnSync(process.execPath, args, { stdio: 'inherit' });
if (r.status === 0) console.log('[w0] chunk 0 ok — 1 done');
process.exit(r.status ?? 1);
`;
    if (writeIfChanged(renderFile, script)) changed.push('render.mjs');
  }
  return { ...cfg, changed };
}
