// Licensed media research, download and the asset licence register.
//
// Policy (docs/asset-licensing.md): only licences that allow commercial use AND modification are accepted
// automatically: CC0, Public Domain Mark / public-domain works, US-federal works (e.g. NASA, with its
// no-endorsement rule), CC BY (attribution recorded), Pexels License, Pixabay Content License.
// CC BY-SA is refused unless FVS_ALLOW_SHARE_ALIKE=1 (share-alike can attach to the whole video);
// NC / ND / unknown licences are always refused. Every asset is verified individually from the source's own
// metadata at download time and recorded in assets/asset-licence-register.csv.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { LAYOUT, readJson, writeJson, markStage } from './project.mjs';

const UA = process.env.FVS_HTTP_USER_AGENT || 'faceless-video-studio/0.1 (licensed media research tool)';  // Wikimedia asks for contact info in the UA: set FVS_HTTP_USER_AGENT
export const REGISTER_COLUMNS = ['asset_id', 'filename', 'asset_type', 'original_url', 'landing_url', 'creator', 'source_platform', 'licence',
  'licence_url', 'commercial_use', 'attribution_required', 'attribution_text', 'modification_allowed', 'date_accessed', 'scene', 'intended_usage',
  'width', 'height', 'sha256', 'notes'];

// --------------------------------------------------------------------------------------------- licences

export function classifyLicence(raw) {
  const l = String(raw || '').toLowerCase().replace(/[_\s]+/g, '-');
  if (!l) return { ok: false, why: 'no licence information' };
  if (/(^|-)nc(-|$)|noncommercial|non-commercial/.test(l)) return { ok: false, why: 'non-commercial licence' };
  if (/(^|-)nd(-|$)|noderiv/.test(l)) return { ok: false, why: 'no-derivatives licence' };
  if (/by-sa|sharealike|share-alike/.test(l)) {
    return process.env.FVS_ALLOW_SHARE_ALIKE === '1' ? { ok: true, name: 'CC BY-SA', attribution: true, note: 'share-alike accepted by FVS_ALLOW_SHARE_ALIKE' }
      : { ok: false, why: 'share-alike (CC BY-SA) refused by default: it can attach to the whole video' };
  }
  if (/cc0|publicdomain\/zero|^zero/.test(l)) return { ok: true, name: 'CC0', attribution: false };
  if (/^pdm$|public-?domain|^pd($|-)|mark\/1\.0|no-known-copyright|us-gov|pd-usgov|pd-nasa/.test(l)) return { ok: true, name: 'Public domain', attribution: false };
  if (/^by($|-\d)|cc-by($|-\d)|attribution/.test(l)) return { ok: true, name: 'CC BY', attribution: true };
  if (/pexels/.test(l)) return { ok: true, name: 'Pexels License', attribution: false };
  if (/pixabay/.test(l)) return { ok: true, name: 'Pixabay Content License', attribution: false };
  return { ok: false, why: `unrecognised licence "${raw}"` };
}

// ---------------------------------------------------------------------------------------------- sources

async function getJson(url, headers = {}) {
  const r = await fetch(url, { headers: { 'User-Agent': UA, Accept: 'application/json', ...headers } });
  if (!r.ok) throw new Error(`${new URL(url).host}: HTTP ${r.status}`);
  return r.json();
}
const stripHtml = s => String(s || '').replace(/<[^>]+>/g, '').replace(/\s+/g, ' ').trim();

const SOURCES = {
  async openverse(q, { kind, limit }) {
    if (kind !== 'image' && kind !== 'audio') return [];
    const u = `https://api.openverse.org/v1/${kind === 'audio' ? 'audio' : 'images'}/?q=${encodeURIComponent(q)}&license_type=commercial,modification&page_size=${limit}&mature=false`;
    const d = await getJson(u);
    return (d.results || []).map(r => ({
      source: `openverse/${r.source}`, id: r.id, title: r.title, url: r.url, thumb: r.thumbnail, landing: r.foreign_landing_url,
      creator: r.creator || 'unknown', licenceRaw: `${r.license}${r.license === 'cc0' || r.license === 'pdm' ? '' : '-' + (r.license_version || '')}`,
      licenceUrl: r.license_url, width: r.width, height: r.height, kind, attributionText: r.attribution,
    }));
  },
  async wikimedia(q, { kind, limit }) {
    if (kind !== 'image') return [];
    const u = `https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=search&gsrnamespace=6&gsrlimit=${limit}&gsrsearch=${encodeURIComponent(q + ' filetype:bitmap')}&prop=imageinfo&iiprop=url|size|extmetadata|mime&iiurlwidth=640`;
    const d = await getJson(u);
    return Object.values(d.query?.pages || {}).map(p => {
      const ii = p.imageinfo?.[0] || {}; const m = ii.extmetadata || {};
      return { source: 'wikimedia-commons', id: p.pageid, title: p.title, url: ii.url, thumb: ii.thumburl, landing: ii.descriptionurl,
        creator: stripHtml(m.Artist?.value) || 'unknown', licenceRaw: m.LicenseShortName?.value || m.License?.value, licenceUrl: m.LicenseUrl?.value,
        width: ii.width, height: ii.height, kind, mime: ii.mime, attributionText: `${stripHtml(m.Artist?.value) || 'Unknown'}, ${m.LicenseShortName?.value || ''}, via Wikimedia Commons`,
        restrictions: stripHtml(m.Restrictions?.value) };
    }).filter(c => /^image\/(jpeg|png|webp)/.test(c.mime || ''));
  },
  async nasa(q, { kind, limit }) {
    if (kind !== 'image') return [];
    const d = await getJson(`https://images-api.nasa.gov/search?q=${encodeURIComponent(q)}&media_type=image&page_size=${limit}`);
    const items = (d.collection?.items || []).slice(0, limit);
    return items.map(it => {
      const m = it.data?.[0] || {}; const thumb = it.links?.find(l => l.rel === 'preview')?.href;
      return { source: 'nasa-images', id: m.nasa_id, title: m.title, url: thumb?.replace(/~thumb\.jpg$/, '~orig.jpg'), urlFallback: thumb?.replace(/~thumb\.jpg$/, '~large.jpg'), thumb,
        landing: `https://images.nasa.gov/details/${encodeURIComponent(m.nasa_id)}`, creator: m.secondary_creator || m.photographer || m.center || 'NASA',
        licenceRaw: m.secondary_creator ? 'needs-review' : 'pd-nasa', licenceUrl: 'https://www.nasa.gov/nasa-brand-center/images-and-media/',
        kind, notes: 'NASA media are generally not copyrighted; no NASA logos/insignia, no implied endorsement' };
    });
  },
  async pexels(q, { kind, limit }) {
    const key = process.env.PEXELS_API_KEY;
    if (!key || (kind !== 'image' && kind !== 'video')) return [];
    const u = kind === 'video' ? `https://api.pexels.com/videos/search?query=${encodeURIComponent(q)}&per_page=${limit}&orientation=landscape`
      : `https://api.pexels.com/v1/search?query=${encodeURIComponent(q)}&per_page=${limit}&orientation=landscape`;
    const d = await getJson(u, { Authorization: key });
    if (kind === 'video') return (d.videos || []).map(v => {
      const file = (v.video_files || []).filter(f => f.width && f.width <= 1920).sort((a, b) => b.width - a.width)[0];
      return { source: 'pexels', id: v.id, title: v.url, url: file?.link, thumb: v.image, landing: v.url, creator: v.user?.name || 'unknown', licenceRaw: 'pexels',
        licenceUrl: 'https://www.pexels.com/license/', width: file?.width, height: file?.height, kind, duration: v.duration };
    });
    return (d.photos || []).map(p => ({ source: 'pexels', id: p.id, title: p.alt, url: p.src?.original, thumb: p.src?.medium, landing: p.url, creator: p.photographer,
      licenceRaw: 'pexels', licenceUrl: 'https://www.pexels.com/license/', width: p.width, height: p.height, kind }));
  },
  async pixabay(q, { kind, limit }) {
    const key = process.env.PIXABAY_API_KEY;
    if (!key || (kind !== 'image' && kind !== 'video')) return [];
    const base = kind === 'video' ? 'https://pixabay.com/api/videos/' : 'https://pixabay.com/api/';
    const d = await getJson(`${base}?key=${key}&q=${encodeURIComponent(q)}&per_page=${Math.max(3, limit)}&safesearch=true`);
    return (d.hits || []).map(h => kind === 'video'
      ? { source: 'pixabay', id: h.id, title: h.tags, url: h.videos?.large?.url || h.videos?.medium?.url, thumb: h.videos?.tiny?.thumbnail, landing: h.pageURL, creator: h.user, licenceRaw: 'pixabay',
          licenceUrl: 'https://pixabay.com/service/license-summary/', width: h.videos?.large?.width, height: h.videos?.large?.height, kind, duration: h.duration }
      : { source: 'pixabay', id: h.id, title: h.tags, url: h.largeImageURL, thumb: h.webformatURL, landing: h.pageURL, creator: h.user, licenceRaw: 'pixabay',
          licenceUrl: 'https://pixabay.com/service/license-summary/', width: h.imageWidth, height: h.imageHeight, kind });
  },
};

const DEFAULT_SOURCES = { image: ['pexels', 'pixabay', 'openverse', 'wikimedia', 'nasa'], video: ['pexels', 'pixabay'], audio: ['openverse'] };

function score(c, query) {
  const w = +c.width || 0, h = +c.height || 1, ar = w / h;
  const terms = String(query).toLowerCase().split(/\s+/).filter(t => t.length > 2);
  const text = `${c.title || ''} ${c.tags || ''}`.toLowerCase();
  const hits = terms.filter(t => text.includes(t.replace(/s$/, ''))).length;
  let s = 4 * hits / Math.max(1, terms.length);           // relevance: query words in the title/tags
  s += 1.5 * (1 - (c.rank || 0) / 10);                    // the source's own relevance order
  s += Math.min(1, w / 1920) * 2;                         // resolution
  s -= Math.min(1.5, Math.abs(ar - 16 / 9));             // shape close to 16:9
  if (/watermark|logo|stamp|sample/i.test(`${c.title} ${c.url}`)) s -= 5;
  if (w < 1000) s -= 2;
  return +s.toFixed(3);
}

/** Search all configured sources; returns licence-checked candidates, best first. */
export async function search(query, { kind = 'image', sources, limit = 8 } = {}) {
  const list = sources ? String(sources).split(',') : DEFAULT_SOURCES[kind] || [];
  const out = [], errors = [];
  await Promise.all(list.map(async name => {
    try { (await SOURCES[name](query, { kind, limit })).forEach((c, rank) => out.push({ ...c, rank })); } catch (e) { errors.push(`${name}: ${e.message}`); }
  }));
  const results = out.filter(c => c.url).map(c => ({ ...c, licence: classifyLicence(c.licenceRaw), score: score(c, query) }))
    .sort((a, b) => (b.licence.ok - a.licence.ok) || (b.score - a.score));
  return { query, kind, sources: list, skipped: list.filter(n => (n === 'pexels' && !process.env.PEXELS_API_KEY) || (n === 'pixabay' && !process.env.PIXABAY_API_KEY)).map(n => `${n} (no API key)`),
    errors, accepted: results.filter(c => c.licence.ok), refused: results.filter(c => !c.licence.ok).map(c => ({ source: c.source, title: c.title, why: c.licence.why })) };
}

// ----------------------------------------------------------------------------------------------- register

const csvCell = v => { const s = v === undefined || v === null ? '' : String(v); return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s; };
function parseCsv(text) {
  const rows = []; let row = [], cell = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"' && text[i + 1] === '"') { cell += '"'; i++; } else if (c === '"') q = false; else cell += c; }
    else if (c === '"') q = true; else if (c === ',') { row.push(cell); cell = ''; } else if (c === '\n') { row.push(cell); rows.push(row); row = []; cell = ''; } else if (c !== '\r') cell += c;
  }
  if (cell || row.length) { row.push(cell); rows.push(row); }
  return rows;
}
export const registerFile = dir => path.join(dir, LAYOUT.assets, 'asset-licence-register.csv');
export function readRegisterRows(dir) {
  const f = registerFile(dir);
  if (!fs.existsSync(f)) return [];
  const [head, ...rows] = parseCsv(fs.readFileSync(f, 'utf8'));
  return rows.filter(r => r.length > 1).map(r => Object.fromEntries(head.map((h, i) => [h, r[i] ?? ''])));
}
export function readRegister(dir) {
  const map = new Map();
  for (const r of readRegisterRows(dir)) map.set(r.asset_id, { file: r.filename, kind: r.asset_type, licence: r.licence });
  return map;
}
export function addToRegister(dir, row) {
  const rows = readRegisterRows(dir).filter(r => r.asset_id !== row.asset_id);
  rows.push(row);
  fs.mkdirSync(path.dirname(registerFile(dir)), { recursive: true });
  fs.writeFileSync(registerFile(dir), [REGISTER_COLUMNS.join(','), ...rows.map(r => REGISTER_COLUMNS.map(k => csvCell(r[k])).join(','))].join('\n') + '\n');
}

/** Register a file made for this project (code-drawn illustration, synthesized sound...). */
export function registerOriginal(dir, { id, file, kind, scene, usage, how }) {
  const abs = path.join(dir, file);
  addToRegister(dir, { asset_id: id, filename: file, asset_type: kind, original_url: '', landing_url: '', creator: 'faceless-video-studio (original)', source_platform: 'original',
    licence: 'Original work', licence_url: '', commercial_use: 'yes', attribution_required: 'no', attribution_text: '', modification_allowed: 'yes',
    date_accessed: new Date().toISOString().slice(0, 10), scene: scene || '', intended_usage: usage || '', width: '', height: '',
    sha256: fs.existsSync(abs) ? crypto.createHash('sha256').update(fs.readFileSync(abs)).digest('hex') : '', notes: how || '' });
}

// ----------------------------------------------------------------------------------------------- download

async function download(url, dst) {
  const r = await fetch(url, { headers: { 'User-Agent': UA } });
  if (!r.ok) throw new Error(`HTTP ${r.status} for ${url}`);
  const buf = Buffer.from(await r.arrayBuffer());
  if (buf.length < 2000) throw new Error(`suspiciously small file (${buf.length} bytes)`);
  fs.writeFileSync(dst, buf);
  return buf;
}

function probeMedia(file) {
  const r = spawnSync('ffprobe', ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,codec_name', '-of', 'json', file], { encoding: 'utf8' });
  const s = JSON.parse(r.stdout || '{}').streams?.[0];
  if (!s?.width) throw new Error(`not a readable image/video: ${path.basename(file)}`);
  return s;
}

/** Download one accepted candidate as asset `id`. Re-verifies the licence; normalises images to JPEG ≤ 2560 px. */
export async function fetchCandidate(dir, id, c, { scene = '', usage = '' } = {}) {
  const lic = classifyLicence(c.licenceRaw);
  if (!lic.ok) throw new Error(`licence refused for ${c.landing || c.url}: ${lic.why}`);
  const adir = path.join(dir, LAYOUT.assets);
  fs.mkdirSync(adir, { recursive: true });
  const ext = c.kind === 'video' ? '.mp4' : c.kind === 'audio' ? '.mp3' : (path.extname(new URL(c.url).pathname).toLowerCase().match(/\.(jpe?g|png|webp)$/)?.[0] || '.jpg');
  const raw = path.join(adir, `${id}.src${ext}`);
  let buf;
  try { buf = await download(c.url, raw); } catch (e) { if (!c.urlFallback) throw e; buf = await download(c.urlFallback, raw); }
  let file = raw, info;
  if (c.kind === 'image') {
    info = probeMedia(raw);
    file = path.join(adir, `${id}.jpg`);
    const r = spawnSync('ffmpeg', ['-v', 'error', '-y', '-i', raw, '-vf', "scale='min(2560,iw)':-2", '-q:v', '3', file], { encoding: 'utf8' });
    if (r.status !== 0) throw new Error('image conversion failed: ' + r.stderr.slice(-300));
    info = probeMedia(file);
  } else if (c.kind === 'video') {
    info = probeMedia(raw);
    file = path.join(adir, `${id}.mp4`); fs.renameSync(raw, file);
  }
  addToRegister(dir, {
    asset_id: id, filename: path.relative(dir, file).split(path.sep).join('/'), asset_type: c.kind, original_url: c.url, landing_url: c.landing || '',
    creator: c.creator || 'unknown', source_platform: c.source, licence: lic.name + (c.licenceRaw && !/^(pexels|pixabay)$/i.test(c.licenceRaw) ? ` (${c.licenceRaw})` : ''),
    licence_url: c.licenceUrl || '', commercial_use: 'yes', attribution_required: lic.attribution ? 'yes' : 'no',
    attribution_text: lic.attribution ? (c.attributionText || `${c.creator}, ${lic.name}, via ${c.source}`) : '', modification_allowed: 'yes',
    date_accessed: new Date().toISOString().slice(0, 10), scene, intended_usage: usage, width: info?.width || c.width || '', height: info?.height || c.height || '',
    sha256: crypto.createHash('sha256').update(buf).digest('hex'), notes: [c.notes, c.restrictions ? `restrictions: ${c.restrictions}` : '', lic.note].filter(Boolean).join('; '),
  });
  return { id, file: path.relative(dir, file), licence: lic.name, source: c.source, landing: c.landing };
}

/** Download every asset the storyboard asks for that is not in the register yet. */
export async function acquireAssets(projectDir, { scene, dryRun = false } = {}) {
  const dir = path.resolve(projectDir);
  const sbFile = path.join(dir, LAYOUT.storyboard, 'storyboard.json');
  const sb = readJson(sbFile);
  if (!sb) throw new Error('no storyboard');
  const have = readRegister(dir);
  const done = [], failed = [], skipped = [];
  for (const sc of sb.scenes) {
    if (scene && sc.id !== scene) continue;
    for (const a of sc.assets || []) {
      if (have.has(a.id)) { skipped.push(a.id); continue; }
      if (a.original) { failed.push({ id: a.id, scene: sc.id, why: 'marked original: make it (code/illustration) and register it with registerOriginal' }); continue; }
      try {
        let cand = a.pick;   // a specific candidate Claude chose from asset-search (with its licence metadata)
        if (!cand) {
          const res = await search(a.query, { kind: a.kind || 'image', sources: a.sources, limit: 10 });
          cand = res.accepted[0];
          if (!cand) { failed.push({ id: a.id, scene: sc.id, query: a.query, why: 'no candidate with an accepted licence', errors: res.errors, skipped: res.skipped }); continue; }
          a.candidates = res.accepted.slice(0, 5).map(c => ({ source: c.source, title: c.title, landing: c.landing, url: c.url, thumb: c.thumb, licence: c.licence.name, width: c.width, height: c.height }));
        }
        if (dryRun) { done.push({ id: a.id, would: cand.landing || cand.url }); continue; }
        done.push(await fetchCandidate(dir, a.id, cand, { scene: sc.id, usage: a.need || sc.narration }));
      } catch (e) { failed.push({ id: a.id, scene: sc.id, why: e.message }); }
    }
  }
  if (!dryRun) writeJson(sbFile, sb);   // keeps the candidate lists for review / swapping
  markStage(dir, 'assets', failed.length ? 'partial' : 'done', { downloaded: done.length, failed: failed.length });
  return { downloaded: done, failed, alreadyRegistered: skipped, register: path.relative(dir, registerFile(dir)) };
}
