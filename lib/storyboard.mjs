// Storyboard: a first-pass draft from the aligned narration, and a strict checker.
// The draft is deliberately simple; the skill has Claude rewrite each scene with the style guide
// (references/reference-analysis/*) before building. The checker enforces the hard rules: the scenes cover
// the whole voiceover with no gaps, follow the script order, and every sentence is on screen.
import fs from 'node:fs';
import path from 'node:path';
import { LAYOUT, readJson, writeJson, markStage } from './project.mjs';

export const VISUAL_TYPES = ['photo', 'inset', 'video', 'solid', 'title', 'kinetic', 'stat', 'map', 'timeline', 'document', 'ranking', 'cutout', 'collage', 'comparison', 'blocks3d', 'custom'];
export const LAYER_TYPES = ['label', 'arrow', 'captions', 'image', 'pricetag', 'hand', 'meter'];
export const TRANSITIONS = ['cut', 'whip-left', 'whip-right', 'whip-up', 'zoom', 'flash', 'fade'];

// a small gazetteer for draft maps (Claude adds real coordinates for anything else)
export const PLACES = {
  'new york': [40.71, -74.0], newark: [40.73, -74.17], houston: [29.76, -95.37], 'los angeles': [34.05, -118.24], london: [51.5, -0.12],
  paris: [48.86, 2.35], tokyo: [35.68, 139.69], shanghai: [31.23, 121.47], singapore: [1.35, 103.82], dubai: [25.2, 55.27],
  rotterdam: [51.92, 4.48], hamburg: [53.55, 9.99], 'hong kong': [22.32, 114.17], beijing: [39.9, 116.4], moscow: [55.76, 37.62],
  berlin: [52.52, 13.4], rome: [41.9, 12.5], madrid: [40.42, -3.7], mumbai: [19.08, 72.88], sydney: [-33.87, 151.21],
  chicago: [41.88, -87.63], 'san francisco': [37.77, -122.42], seattle: [47.61, -122.33], miami: [25.76, -80.19], detroit: [42.33, -83.05],
  china: [35.0, 103.0], india: [21.0, 78.0], japan: [36.2, 138.2], germany: [51.2, 10.4], france: [46.2, 2.2], italy: [41.9, 12.6],
  'united states': [39.8, -98.6], america: [39.8, -98.6], canada: [56.1, -106.3], mexico: [23.6, -102.5], brazil: [-14.2, -51.9],
  russia: [61.5, 105.3], australia: [-25.3, 133.8], england: [52.4, -1.5], britain: [54.0, -2.0], spain: [40.5, -3.7], egypt: [26.8, 30.8],
  california: [36.8, -119.4], texas: [31.0, -100.0], florida: [27.7, -81.7], 'saudi arabia': [23.9, 45.1], korea: [36.5, 127.9], vietnam: [14.1, 108.3],
};

const UNITS = Object.fromEntries('zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split(' ').map((w, i) => [w, i]));
const TENS = { twenty: 20, thirty: 30, forty: 40, fifty: 50, sixty: 60, seventy: 70, eighty: 80, ninety: 90 };
const SCALES = { thousand: 1e3, million: 1e6, billion: 1e9, trillion: 1e12 };
export function numberValue(text) {
  let t = String(text).toLowerCase().replace(/[$£€,]/g, ' ').replace(/-/g, ' ');
  const toks = t.match(/[a-z]+|\d+(?:\.\d+)?/g) || [];
  let total = 0, cur = 0, seen = false;
  for (const x of toks) {
    if (/^\d/.test(x)) { cur += +x; seen = true; } else if (x in UNITS) { cur += UNITS[x]; seen = true; } else if (x in TENS) { cur += TENS[x]; seen = true; }
    else if (x === 'hundred') { cur = (cur || 1) * 100; seen = true; } else if (x in SCALES) { total += (cur || 1) * SCALES[x]; cur = 0; seen = true; }
    else if (seen) break;
  }
  return seen ? total + cur : null;
}

const STOP = new Set('the a an and or but of to in on at by for with from as is was were be been it its this that these those he she they we you his her their our your my me him them us there here so if then than one more most when why what how who which while into onto about over under after before just only also very much many some any all each every could would should can will had has have did does do not no yes up down out off'.split(' '));

function keywords(text, n = 4) {
  const ws = text.replace(/[^\p{L}\p{N}\s'-]/gu, ' ').split(/\s+/).filter(w => w.length > 2 && !STOP.has(w.toLowerCase()));
  const caps = ws.filter(w => /^[A-Z]/.test(w));
  const rest = ws.filter(w => !/^[A-Z]/.test(w)).sort((a, b) => b.length - a.length);
  return [...new Set([...caps, ...rest].map(w => w.toLowerCase()))].slice(0, n).join(' ');
}

/** Split long sentences at a comma near the middle, merge very short ones. Returns beats with times. */
function beats(al) {
  const out = [];
  for (const s of al.sentences) {
    const ws = al.words.filter(w => w.sentence === s.index);
    if (s.duration > 5.5 && ws.length > 6) {
      const mid = (s.start + s.end) / 2;
      const commas = ws.map((w, k) => ({ k, w })).filter(({ w, k }) => /[,;:—–]$/.test(w.w) && k < ws.length - 2);
      const cut = commas.sort((a, b) => Math.abs(a.w.e - mid) - Math.abs(b.w.e - mid))[0];
      if (cut) {
        out.push({ sentences: [s.index], start: s.start, end: ws[cut.k + 1].s, text: ws.slice(0, cut.k + 1).map(w => w.w).join(' '), paragraph: s.paragraph });
        out.push({ sentences: [s.index], start: ws[cut.k + 1].s, end: s.end, text: ws.slice(cut.k + 1).map(w => w.w).join(' '), paragraph: s.paragraph });
        continue;
      }
    }
    out.push({ sentences: [s.index], start: s.start, end: s.end, text: s.text, paragraph: s.paragraph });
  }
  // merge beats shorter than 1.3 s into the next one (same paragraph)
  const merged = [];
  for (const b of out) {
    const last = merged[merged.length - 1];
    if (last && last.end - last.start < 1.3 && last.paragraph === b.paragraph) {
      last.end = b.end; last.text += ' ' + b.text; last.sentences = [...new Set([...last.sentences, ...b.sentences])];
    } else merged.push({ ...b });
  }
  return merged;
}

export function draftStoryboard(projectDir, { force = false } = {}) {
  const dir = path.resolve(projectDir);
  const file = path.join(dir, LAYOUT.storyboard, 'storyboard.json');
  if (fs.existsSync(file) && !force) throw new Error(`${path.relative(dir, file)} already exists (use --force to replace the draft; the refined storyboard would be lost)`);
  const meta = readJson(path.join(dir, 'project.fvs.json'));
  const al = readJson(path.join(dir, LAYOUT.analysis, 'alignment.json'));
  if (!al) throw new Error('run `fvs analyse` first');
  const D = meta.duration;
  const bs = beats(al);
  const moves = ['push-in', 'pan-left', 'pull-out', 'pan-right', 'tilt-up', 'push-in', 'drift'];
  let lastPara = 0, mv = 0;
  const scenes = bs.map((b, i) => {
    const start = i === 0 ? 0 : Math.max(0, b.start - 0.08);
    const end = i === bs.length - 1 ? D : Math.max(start + 0.3, bs[i + 1].start - 0.08);
    const text = b.text;
    const id = `sc${String(i + 1).padStart(2, '0')}`;
    const sc = { id, title: keywords(text, 3), start: +start.toFixed(3), end: +end.toFixed(3), sentences: b.sentences, narration: text,
      purpose: '', technique: '', visual: null, layers: [], sfx: [], assets: [], transition_in: 'cut', status: 'draft' };
    const money = text.match(/[$£€]\s?[\d.,]+(?:\s?(?:thousand|million|billion|trillion))?|\b[\d.,]+\s?(?:dollars|pounds|euros)\b|\b(?:[a-z]+[\s-])*(?:thousand|million|billion|trillion)\b/i);
    const year = text.match(/\b(1[5-9]\d\d|20\d\d)\b/);
    const place = Object.keys(PLACES).find(p => new RegExp(`\\b${p}\\b`, 'i').test(text));
    if (money && numberValue(money[0]) !== null && numberValue(money[0]) > 0) {
      const val = numberValue(money[0]);
      const isMoney = /[$£€]|dollar|pound|euro|cent/i.test(money[0] + text);
      sc.visual = { type: 'stat', value: val, prefix: isMoney && /[$]|dollar/i.test(money[0]) ? '$' : '', decimals: val % 1 ? 2 : 0, compact: val >= 1e6, sub: keywords(text, 3), at: '@' + money[0].split(/\s+/)[0].replace(/[$£€]/, '') };
      sc.technique = 'number as the hero: count-up on the spoken figure';
    } else if (place && i > 0) {
      const [lat, lon] = PLACES[place];
      sc.visual = { type: 'map', focus: { lat, lon, zoom: 2.2 }, pins: [{ lat, lon, label: place, at: '@' + place.split(' ')[0] }] };
      sc.technique = 'map establishes the location';
    } else if (/\?$/.test(text.trim()) && text.split(/\s+/).length <= 12) {
      sc.visual = { type: 'kinetic', text: text.replace(/[?,.]/g, '').toLowerCase() };
      sc.technique = 'question as kinetic text';
    } else {
      const q = keywords(text, 4);
      sc.visual = { type: 'photo', asset: `${id}-a1`, move: moves[mv++ % moves.length] };
      sc.assets.push({ id: `${id}-a1`, kind: 'image', query: q, need: `photo that shows: ${text}` });
      sc.technique = 'photo with slow camera move';
      if (year) sc.layers.push({ type: 'label', text: year[1], style: 'plain', position: [0.12, 0.14], anchor: 'left', at: '@' + year[1], size: 72 });
    }
    if (b.paragraph !== lastPara && i > 0) sc.transition_in = 'whip-left';
    lastPara = b.paragraph;
    return sc;
  });
  const sb = { version: 1, generated: 'draft', format: { width: meta.width, height: meta.height, fps: meta.fps }, duration: D,
    style: { guide: 'references/reference-analysis/master-style-guide.md', tokens: {} },
    music: { track: 'procedural', mood: 'curious', gain_db: -20, duck_db: -12 }, scenes };
  writeJson(file, sb);
  fs.writeFileSync(path.join(dir, LAYOUT.storyboard, 'storyboard.md'), storyboardMarkdown(sb));
  markStage(dir, 'storyboard', 'draft', { scenes: scenes.length });
  return { file, scenes: scenes.length, note: 'DRAFT: refine every scene (visual, layers, assets, transitions, sfx) with the style guide, then run storyboard-check and build.' };
}

export function storyboardMarkdown(sb) {
  const fmt = t => `${Math.floor(t / 60)}:${(t % 60).toFixed(2).padStart(5, '0')}`;
  const rows = sb.scenes.map((s, i) => `| ${i + 1} | ${fmt(s.start)} | ${fmt(s.end)} | ${(s.end - s.start).toFixed(2)} | ${s.narration.replace(/\|/g, '/')} | ${s.visual?.type}${s.visual?.move ? ` (${s.visual.move})` : ''} | ${(s.layers || []).map(l => `${l.type}${l.text ? `: ${l.text}` : ''}`).join('; ')} | ${typeof s.transition_in === 'string' ? s.transition_in : s.transition_in?.type || 'cut'} | ${(s.sfx || []).map(x => x.cue).join(', ')} | ${s.technique || ''} | ${(s.assets || []).map(a => a.id).join(', ')} | ${s.status || ''} |`);
  return `# Storyboard\n\nDuration ${fmt(sb.duration)} · ${sb.scenes.length} scenes · music: ${sb.music?.track} (${sb.music?.mood || ''})\n\n| # | Start | End | Dur | Narration | Visual | Layers | In | SFX | Technique | Assets | Status |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n${rows.join('\n')}\n`;
}

export function checkStoryboard(projectDir) {
  const dir = path.resolve(projectDir);
  const sb = readJson(path.join(dir, LAYOUT.storyboard, 'storyboard.json'));
  const al = readJson(path.join(dir, LAYOUT.analysis, 'alignment.json'));
  const meta = readJson(path.join(dir, 'project.fvs.json'));
  const errors = [], warnings = [];
  if (!sb) return { ok: false, errors: ['storyboard/storyboard.json is missing'], warnings };
  const fps = meta?.fps || 30, frame = 1 / fps + 1e-6, D = meta?.duration ?? sb.duration;
  const sc = sb.scenes || [];
  if (!sc.length) errors.push('no scenes');
  const ids = new Set();
  sc.forEach((s, i) => {
    if (!s.id) errors.push(`scene ${i + 1} has no id`);
    if (ids.has(s.id)) errors.push(`duplicate scene id ${s.id}`); ids.add(s.id);
    if (!(s.end > s.start)) errors.push(`${s.id}: end must be after start`);
    if (s.end - s.start < 0.3) errors.push(`${s.id}: ${(s.end - s.start).toFixed(2)} s is shorter than 0.3 s`);
    if (i > 0 && Math.abs(s.start - sc[i - 1].end) > frame) errors.push(`${s.id}: gap/overlap of ${(s.start - sc[i - 1].end).toFixed(3)} s after ${sc[i - 1].id} (scenes must be contiguous)`);
    if (!s.visual || !VISUAL_TYPES.includes(s.visual.type)) errors.push(`${s.id}: visual.type must be one of ${VISUAL_TYPES.join(', ')}`);
    if (['photo', 'inset', 'video', 'cutout'].includes(s.visual?.type) && !s.visual.asset) errors.push(`${s.id}: ${s.visual.type} needs visual.asset`);
    for (const L of s.layers || []) if (!LAYER_TYPES.includes(L.type)) errors.push(`${s.id}: unknown layer type ${L.type}`);
    const t = typeof s.transition_in === 'object' ? s.transition_in?.type : s.transition_in;
    if (t && !TRANSITIONS.includes(t)) errors.push(`${s.id}: transition_in must be one of ${TRANSITIONS.join(', ')}`);
    if (s.end - s.start > 9 && ['photo', 'solid'].includes(s.visual?.type) && !(s.layers || []).length) warnings.push(`${s.id}: ${(s.end - s.start).toFixed(1)} s on one ${s.visual.type} with no layers — consider splitting or adding motion`);
    if (i > 0 && s.visual?.type === sc[i - 1].visual?.type && s.visual?.move && s.visual.move === sc[i - 1].visual?.move) warnings.push(`${s.id}: same visual type and camera move as the previous scene (repetitive)`);
  });
  if (sc.length) {
    if (sc[0].start > frame) errors.push(`first scene starts at ${sc[0].start}s (must start at 0)`);
    if (Math.abs(sc[sc.length - 1].end - D) > frame) errors.push(`last scene ends at ${sc[sc.length - 1].end}s but the voiceover is ${D}s (the film length must equal the voiceover)`);
  }
  if (al) {
    // every sentence must be on screen while it is spoken, in script order
    let lastSent = -1;
    for (const s of sc) for (const k of s.sentences || []) { if (k < lastSent) errors.push(`${s.id}: sentence ${k} comes after sentence ${lastSent} (scene order must follow the script)`); lastSent = Math.max(lastSent, k); }
    const covered = new Set(sc.flatMap(s => s.sentences || []));
    const missing = al.sentences.filter(s => !covered.has(s.index));
    if (missing.length) errors.push(`sentences not assigned to any scene: ${missing.map(s => s.index).join(', ')}`);
  }
  const d = sc.map(s => s.end - s.start);
  if (d.length > 6) {
    const mean = d.reduce((a, b) => a + b, 0) / d.length, sd = Math.sqrt(d.reduce((a, b) => a + (b - mean) ** 2, 0) / d.length);
    if (sd < 0.15 * mean) warnings.push(`scene lengths barely vary (mean ${mean.toFixed(2)} s, sd ${sd.toFixed(2)} s): pacing will feel mechanical`);
  }
  const types = sc.map(s => s.visual?.type);
  const share = types.filter(t => t === 'photo').length / Math.max(1, types.length);
  if (types.length >= 8 && share > 0.75) warnings.push(`${Math.round(share * 100)}% of scenes are plain photos: vary the formats (maps, stats, documents, cutouts, kinetic text...)`);
  return { ok: errors.length === 0, errors, warnings, scenes: sc.length };
}
