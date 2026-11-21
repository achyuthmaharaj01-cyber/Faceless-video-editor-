// storyboard.json → HyperFrames index.html (+ audio cues). The composition is plain HTML/CSS with the film's
// motion as data (FVS_SPEC) interpreted by components/fvs-motion.js into one seekable GSAP timeline.
// Re-running build after a storyboard change regenerates index.html; a snapshot of the previous version is
// kept in versions/ first.
import fs from 'node:fs';
import path from 'node:path';
import { LAYOUT, readJson, writeJson, markStage, snapshot, readState } from '../project.mjs';
import { buildPreview } from '../videohub/build-preview.mjs';
import { checkStoryboard } from '../storyboard.mjs';
import { readRegister } from '../assets.mjs';
import { worldMapSvg, project as projectLonLat } from './map.mjs';
import { mixProject } from '../audio/mix.mjs';

const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
const r3 = x => Math.round(x * 1000) / 1000;
const PIN_SVG = '<svg class="pin" viewBox="0 0 24 32"><path d="M12 0C5.4 0 0 5.3 0 11.9 0 20.8 12 32 12 32s12-11.2 12-20.1C24 5.3 18.6 0 12 0z" fill="#e8262b"/><circle cx="12" cy="11.5" r="4.6" fill="#fff"/></svg>';
const TIER_COLORS = ['#ff7f7f', '#ffbf7f', '#ffdf7f', '#ffff7f', '#bfff7f', '#7fff7f', '#7fbfff'];

/** Resolve a time: number (absolute s), "@word" / "@word+0.2" (spoken time of the word inside the scene), "+1.5" (scene start + 1.5). */
export function makeTimeResolver(words, warn) {
  const norm = w => String(w).toLowerCase().replace(/[^\p{L}\p{N}$%]/gu, '');
  return function at(v, scene, fallback) {
    if (v === undefined || v === null) return fallback;
    if (typeof v === 'number') return v;
    const s = String(v).trim();
    if (/^[+-]\d/.test(s)) return scene.start + parseFloat(s);
    const m = s.match(/^@(.+?)(?:([+-]\d*\.?\d+))?$/);
    if (m) {
      const want = m[1].split(/\s+/).map(norm);
      for (let i = 0; i < words.length; i++) {
        const [st] = words[i];
        if (st < scene.start - 0.05 || st > scene.end) continue;
        if (want.every((w, k) => words[i + k] && norm(words[i + k][2]) === w)) return st + (m[2] ? parseFloat(m[2]) : 0);
      }
      warn(`scene ${scene.id}: word "${m[1]}" is not spoken between ${scene.start}s and ${scene.end}s; used scene start`);
      return scene.start;
    }
    const n = parseFloat(s);
    return Number.isFinite(n) ? n : fallback;
  };
}

class Film {
  constructor(meta, words, register, warn) {
    this.meta = meta; this.W = meta.width; this.H = meta.height;
    this.motionBy = { main: [] }; this.offset = { main: 0 }; this.cur = 'main';
    this.cues = []; this.html = []; this.rootHtml = []; this.at = makeTimeResolver(words, warn);
    this.words = words; this.register = register; this.warn = warn; this.n = 0;
  }
  uid(p) { return `${p}${++this.n}`; }
  /** Motion goes to the current scene's own timeline, in that scene's local time (HyperFrames sub-composition). */
  push(m) { const list = (this.motionBy[this.cur] ||= []); list.push({ ...m, t: r3(m.t - (this.offset[this.cur] || 0)) }); }
  on(scene, fn) { const keep = this.cur; this.cur = scene; try { fn(); } finally { this.cur = keep; } }
  ft(s, from, to, t, d, e, extra = {}) { this.push({ k: 'ft', s, from, to, t, d: r3(Math.max(0.001, d)), e, ...extra }); }
  set(s, to, t) { this.push({ k: 'set', s, to, t }); }
  get motionCount() { return Object.values(this.motionBy).reduce((a, l) => a + l.length, 0); }
  cue(name, t, gain = 0) { this.cues.push({ t: r3(t), name, gain }); }
  asset(id, sceneId) {
    if (!id) return null;
    if (/^(assets|compositions)\//.test(id) || /\.(png|jpe?g|webp|svg|gif|mp4|webm|mov)$/i.test(id)) return { file: id, kind: /\.(mp4|webm|mov)$/i.test(id) ? 'video' : 'image' };
    const a = this.register.get(id);
    if (!a) { this.warn(`scene ${sceneId}: asset "${id}" is not in the licence register (shown as a MISSING slate)`); return null; }
    return a;
  }
  media(id, sceneId, cls = 'fill', extra = '') {
    const a = this.asset(id, sceneId);
    if (!a) return `<div class="missing">missing asset: ${esc(id)}</div>`;
    if (a.kind === 'video') return `<video class="${cls}" src="${esc(a.file)}" muted playsinline ${extra}></video>`;
    return `<img class="${cls}" src="${esc(a.file)}" alt="" ${extra}/>`;
  }
}

// ---------------------------------------------------------------------------------------------- visuals

const MOVES = {
  'push-in': [{ scale: 1.0 }, { scale: 1.14 }], 'pull-out': [{ scale: 1.16 }, { scale: 1.0 }],
  'pan-left': [{ scale: 1.14, xPercent: 4 }, { scale: 1.14, xPercent: -4 }], 'pan-right': [{ scale: 1.14, xPercent: -4 }, { scale: 1.14, xPercent: 4 }],
  'tilt-up': [{ scale: 1.14, yPercent: 4 }, { scale: 1.14, yPercent: -4 }], 'tilt-down': [{ scale: 1.14, yPercent: -4 }, { scale: 1.14, yPercent: 4 }],
  'push-fast': [{ scale: 1.0 }, { scale: 1.3 }], static: null, drift: [{ scale: 1.06, xPercent: -1 }, { scale: 1.08, xPercent: 1 }],
};

function camMove(f, sel, v, sc) {
  const move = v.move || 'push-in';
  const m = MOVES[move];
  if (!m) return;
  const from = { ...m[0] }, to = { ...m[1] };
  if (v.focus) { const [fx, fy] = v.focus; f.set(sel, { transformOrigin: `${fx * 100}% ${fy * 100}%` }, sc.start); }
  f.ft(sel, from, to, sc.start, sc.end - sc.start, v.ease || 'sine.inOut');
}

const VISUALS = {
  photo(f, sc, v, id) {
    const cls = [v.grade === 'bw' || v.grade === 'bw-red' ? 'grade-bw' : '', v.vignette !== false ? 'vignette' : ''].join(' ');
    let extra = '';
    if (v.grade === 'bw-red') extra = `<div class="solid" style="background:repeating-linear-gradient(100deg, rgba(232,38,43,.0) 0 70px, rgba(232,38,43,.85) 70px 96px);mix-blend-mode:multiply"></div>`;
    f.html.push(`<div class="${cls}" style="position:absolute;inset:0"><div class="cam" id="${id}-cam">${f.media(v.asset, sc.id)}</div>${extra}</div>`);
    camMove(f, `#${id}-cam`, v, sc);
  },
  video(f, sc, v, id) {
    const a = f.asset(v.asset, sc.id);
    const start = v.from || 0;
    f.html.push(`<div class="vignette" style="position:absolute;inset:0"><div class="cam" id="${id}-cam">` +
      (a ? `<video id="${id}-v" class="fill clip" src="${esc(a.file)}" muted playsinline data-start="0" data-duration="${r3(sc.end - sc.start)}" data-media-start="${r3(start)}" data-track-index="2"></video>`
         : `<div class="missing">missing video: ${esc(v.asset)}</div>`) + `</div></div>`);
    camMove(f, `#${id}-cam`, { move: 'drift', ...v }, sc);
  },
  inset(f, sc, v, id) {
    // picture-in-picture: the image framed over a dark, blurred copy of itself (reference style for screenshots/clips)
    f.html.push(`<div class="inset-bg">${f.media(v.asset, sc.id)}</div><div class="inset" id="${id}-i"><div class="cam" id="${id}-cam">${f.media(v.asset, sc.id)}</div></div>`);
    f.ft(`#${id}-i`, { scale: 0.92, opacity: 0 }, { scale: 1, opacity: 1 }, sc.start, 0.3, 'power3.out');
    camMove(f, `#${id}-cam`, { move: v.move || 'push-in' }, sc);
  },
  solid(f, sc, v) { f.html.push(`<div class="solid" style="background:${esc(v.background || v.color || '#111')}"></div>`); },
  title(f, sc, v, id) {
    f.html.push(`<div class="solid" style="background:${esc(v.background || '#0d0d0d')}"></div>` +
      `<div class="kt" id="${id}-t" style="top:38%;font-size:${v.size || 170}px">${esc(v.text)}</div>` +
      (v.sub ? `<div class="stat-sub" id="${id}-s" style="top:60%">${esc(v.sub)}</div>` : ''));
    f.ft(`#${id}-t`, { opacity: 0, y: 40, scale: 0.96 }, { opacity: 1, y: 0, scale: 1 }, sc.start + 0.05, 0.5, 'power3.out');
    if (v.sub) f.ft(`#${id}-s`, { opacity: 0 }, { opacity: 1 }, sc.start + 0.45, 0.4, 'power2.out');
  },
  kinetic(f, sc, v, id) {
    const words = String(v.text).split(/\s+/);
    const bg = v.asset ? `<div class="cam" id="${id}-cam" style="filter:brightness(.45)">${f.media(v.asset, sc.id)}</div>` : `<div class="solid" style="background:${esc(v.background || '#101010')}"></div>`;
    f.html.push(bg + `<div class="kt" id="${id}-k" style="top:${v.top ?? 34}%;font-size:${v.size || 150}px;color:${esc(v.color || '#fff')}">` +
      words.map((w, i) => `<span class="w" id="${id}-w${i}">${esc(w)}</span>`).join(' ') + `</div>`);
    if (v.asset) camMove(f, `#${id}-cam`, { move: 'push-in' }, sc);
    // words land when they are spoken (or evenly across the first half of the scene)
    let after = sc.start - 0.05;
    words.forEach((w, i) => {
      const t = v.sync !== 'even' ? f.at('@' + w, { ...sc, start: after }, null) : null;
      const at = t !== null && t >= after ? t : sc.start + 0.1 + i * Math.min(0.35, (sc.end - sc.start) * 0.5 / words.length);
      after = at + 0.01;
      f.ft(`#${id}-w${i}`, { opacity: 0, y: 60, scale: 1.25 }, { opacity: 1, y: 0, scale: 1 }, at, 0.22, 'back.out(2)');
      if (v.sfx !== false) f.cue('click', at, -6);
    });
  },
  stat(f, sc, v, id) {
    const bg = v.asset ? `<div class="cam" id="${id}-cam" style="filter:brightness(${v.dim ?? .5})">${f.media(v.asset, sc.id)}</div>`
                       : `<div class="solid" style="background:${esc(v.background || 'radial-gradient(circle at 50% 45%, #1d2a1f, #050505 70%)')}"></div>`;
    const money = v.money ?? /[$£€]/.test(v.prefix || '');
    f.html.push(bg + `<div class="stat ${money ? 'money' : ''}" id="${id}-n" style="top:${v.top ?? 33}%;font-size:${v.size || 210}px">0</div>` +
      (v.sub ? `<div class="stat-sub" id="${id}-s" style="top:${((v.top ?? 33) + ((v.size || 210) * 1.25 + 12) / f.H * 100).toFixed(2)}%">${esc(v.sub)}</div>` : ''));
    if (v.asset) camMove(f, `#${id}-cam`, { move: 'push-in' }, sc);
    const t0 = f.at(v.at, sc, sc.start + 0.15);
    const dur = Math.min(v.duration || 1.4, Math.max(0.4, sc.end - t0 - 0.3));
    f.ft(`#${id}-n`, { opacity: 0, scale: 0.85 }, { opacity: 1, scale: 1 }, t0, 0.25, 'power2.out');
    f.push({ k: 'count', s: `#${id}-n`, from: v.from ?? 0, to: v.value, t: r3(t0), d: r3(dur), e: 'power2.out',
      f: { prefix: v.prefix || '', suffix: v.suffix || '', decimals: v.decimals || 0, compact: !!v.compact } });
    f.cue(money ? 'cash' : 'riser', t0, -3);
    f.cue('impact', t0 + dur, -4);
    if (v.sub) f.ft(`#${id}-s`, { opacity: 0, y: 20 }, { opacity: 1, y: 0 }, t0 + dur * 0.6, 0.35, 'power2.out');
  },
  map(f, sc, v, id) {
    const viewW = f.W, viewH = f.H;
    const cam = c => { if (!c) return { scale: 1, x: 0, y: 0 }; const [x, y] = projectLonLat([c.lon, c.lat], viewW, viewH); const s = c.zoom || 1;
      return { scale: s, x: (viewW / 2 - x) * s, y: (viewH / 2 - y) * s, cx: x, cy: y }; };
    const zoomMax = Math.max(v.from?.zoom || 1, v.focus?.zoom || 1);
    const view = c => { const k = cam(c); const hw = viewW / 2 / k.scale, hh = viewH / 2 / k.scale; return c ? [k.cx - hw, k.cy - hh, k.cx + hw, k.cy + hh] : [0, 0, viewW, viewH]; };
    const { svg } = worldMapSvg({ width: viewW, height: viewH, sea: v.sea, land: v.land, highlight: v.highlight, zoom: Math.min(zoomMax, Math.max(1, Math.min(v.from?.zoom || 1, v.focus?.zoom || 1)) * 1.5 + 0.01) || 1, views: [view(v.from), view(v.focus || v.from)] });
    const pins = (v.pins || []).map((p, i) => { const [x, y] = projectLonLat([p.lon, p.lat], viewW, viewH); return { ...p, x, y, i }; });
    const a = cam(v.from), b = cam(v.focus || v.from);
    const T0 = sc.start, TD = Math.min(v.zoomDuration || 2.2, sc.end - sc.start), EASE = 'power2.inOut';
    // the map zooms; pins, labels and the route stay screen-sized: they are positioned on screen from the same
    // camera values, so they track the map exactly without scaling with it
    f.html.push(`<div class="map" style="position:absolute;inset:0;background:${esc(v.sea || 'var(--sea)')}"><div class="cam" id="${id}-cam">${svg}` +
      (v.route ? `<svg viewBox="0 0 ${viewW} ${viewH}" style="position:absolute;inset:0;width:100%;height:100%;overflow:visible"><path id="${id}-route" class="route" style="stroke-width:${(7 / Math.max(1, v.focus?.zoom || 1)).toFixed(3)}" d="M${v.route.map(([lat, lon]) => projectLonLat([lon, lat], viewW, viewH).map(r3).join(',')).join(' L')}" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>` : '') +
      `</div>` + pins.map(p => `<div class="pinwrap" id="${id}-pw${p.i}" style="position:absolute;left:0;top:0;width:0;height:0">` +
        `<svg id="${id}-p${p.i}" width="40" height="40" viewBox="-20 -20 40 40" style="position:absolute;left:-20px;top:-20px;width:40px;height:40px;overflow:visible"><circle class="pin-dot" r="13"/></svg>` +
        `<div style="position:absolute;left:0;bottom:26px;transform:translateX(-50%)"><div class="label lower ${v.labelStyle || 'dark'}" id="${id}-pl${p.i}" style="position:relative;font-size:${p.size || 50}px">${esc(p.label || '')}</div></div></div>`).join('') + `</div>`);
    f.set(`#${id}-cam`, { transformOrigin: '50% 50%' }, T0);
    f.ft(`#${id}-cam`, a, b, T0, TD, EASE);
    // screen position of a map point under camera {scale,x,y}: centre + s*(p - centre) + (x, y)
    const screen = (p, c) => ({ x: f.W / 2 + c.scale * (p.x / viewW * f.W - f.W / 2) + c.x, y: f.H / 2 + c.scale * (p.y / viewH * f.H - f.H / 2) + c.y });
    for (const p of pins) {
      f.ft(`#${id}-pw${p.i}`, screen(p, a), screen(p, b), T0, TD, EASE);
      const t = f.at(p.at, sc, sc.start + 0.6 + p.i * 0.4);
      f.ft(`#${id}-p${p.i}`, { scale: 0, transformOrigin: '50% 50%' }, { scale: 1 }, t, 0.3, 'back.out(3)');
      f.ft(`#${id}-pl${p.i}`, { opacity: 0, y: 20 }, { opacity: 1, y: 0 }, t + 0.05, 0.25, 'power2.out');
      f.cue('pop', t, -6);
    }
    if (v.route) { const t = f.at(v.routeAt, sc, sc.start + 0.8); f.push({ k: 'attr', s: `#${id}-route`, from: { 'stroke-dashoffset': 1 }, to: { 'stroke-dashoffset': 0 }, t: r3(t), d: r3(v.routeDuration || 2.5), e: 'power1.inOut' }); f.cue('swish', t, -8); }
  },
  timeline(f, sc, v, id) {
    const ev = v.events || [];
    const span = [ev[0]?.year ?? 0, ev[ev.length - 1]?.year ?? 1];
    const xOf = y => 6 + 88 * ((y - span[0]) / Math.max(1, span[1] - span[0]));
    f.html.push(`<div class="solid" style="background:${esc(v.background || 'linear-gradient(180deg,#14202b,#0a0f14)')}"></div>` +
      `<div class="tline" id="${id}-l" style="top:55%;transform-origin:0 50%"></div>` +
      ev.map((e, i) => `<div class="tick" id="${id}-k${i}" style="left:${xOf(e.year)}%;top:55%"></div><div class="tyear" id="${id}-y${i}" style="left:${xOf(e.year)}%;top:${i % 2 ? 60 : 38}%">${esc(e.label ?? e.year)}</div>` +
        (e.text ? `<div class="label lower" id="${id}-x${i}" style="left:${xOf(e.year)}%;top:${i % 2 ? 72 : 30}%;transform:translateX(-50%);font-size:40px">${esc(e.text)}</div>` : '')).join(''));
    f.ft(`#${id}-l`, { scaleX: 0 }, { scaleX: 1 }, sc.start + 0.05, 0.7, 'power2.out');
    ev.forEach((e, i) => {
      const t = f.at(e.at, sc, sc.start + 0.4 + i * 0.5);
      f.ft(`#${id}-k${i}`, { scaleY: 0 }, { scaleY: 1 }, t, 0.2, 'power2.out');
      f.ft(`#${id}-y${i}`, { opacity: 0, y: 30 }, { opacity: 1, y: 0 }, t, 0.3, 'back.out(2)');
      if (e.text) f.ft(`#${id}-x${i}`, { opacity: 0 }, { opacity: 1 }, t + 0.15, 0.3);
      f.cue('click', t, -6);
    });
  },
  document(f, sc, v, id) {
    const hl = v.highlight ? esc(v.headline).replace(esc(v.highlight), `<span class="hl" id="${id}-hl">${esc(v.highlight)}</span>`) : esc(v.headline);
    f.html.push(`<div class="solid" style="background:${esc(v.background || '#2a2a2a')}"></div>` + (v.asset ? `<div class="cam" id="${id}-cam" style="filter:blur(6px) brightness(.4)">${f.media(v.asset, sc.id)}</div>` : '') +
      `<div class="doc" id="${id}-d" style="left:22%;right:22%;top:12%;transform:rotate(${v.tilt ?? -2}deg)"><h2>${hl}</h2>` +
      Array.from({ length: v.lines ?? 6 }, (_, i) => `<div class="line" style="width:${[96, 88, 93, 70, 90, 60, 84][i % 7]}%"></div>`).join('') +
      (v.source ? `<div class="src">${esc(v.source)}</div>` : '') + `</div>`);
    f.ft(`#${id}-d`, { y: 900, rotation: (v.tilt ?? -2) - 6 }, { y: 0, rotation: v.tilt ?? -2 }, sc.start, 0.55, 'power3.out');
    f.ft(`#${id}-d`, { scale: 1 }, { scale: 1.07 }, sc.start + 0.55, Math.max(0.1, sc.end - sc.start - 0.55), 'none', { i: false });
    f.cue('swish', sc.start, -6);
    if (v.highlight) { const t = f.at(v.highlightAt, sc, sc.start + 0.9); f.ft(`#${id}-hl`, { '--hlx': 0 }, { '--hlx': 1 }, t, 0.35, 'power1.out'); f.cue('marker', t, -8); }
  },
  ranking(f, sc, v, id) {
    const rows = v.rows || ['S', 'A', 'B', 'C', 'D', 'F'];
    const rh = f.H / rows.length;
    const counts = rows.map(() => 0);
    f.html.push(`<div class="board">` + rows.map((r, i) => `<div class="row" style="top:${r3(i * rh)}px;height:${r3(rh)}px"><div class="tag" style="background:${TIER_COLORS[i % TIER_COLORS.length]};font-size:${r3(rh * 0.5)}px">${esc(r)}</div></div>`).join('') +
      (v.items || []).map((it, k) => {
        const ri = Math.max(0, rows.indexOf(it.row)); const c = counts[ri]++;
        const s = rh - 18; const x = 170 + 14 + c * (s * 1.2 + 12), y = ri * rh + 9;
        return `<div class="slot" id="${id}-i${k}" style="left:${r3(x)}px;top:${r3(y)}px;width:${r3(s * 1.2)}px;height:${r3(s)}px">${f.media(it.asset, sc.id, '')}${it.label ? `<div class="cap">${esc(it.label)}</div>` : ''}</div>`;
      }).join('') + `</div>`);
    (v.items || []).forEach((it, k) => {
      const t = f.at(it.at, sc, sc.start + 0.3 + k * 0.4);
      f.ft(`#${id}-i${k}`, { x: f.W * 0.5, y: -f.H * 0.3, scale: 1.6, rotation: 8 }, { x: 0, y: 0, scale: 1, rotation: 0 }, t, 0.45, 'power3.out');
      f.cue('thud', t + 0.4, -4);
    });
  },
  cutout(f, sc, v, id) {
    const size = v.size || 0.55;
    const shape = v.shape || 'round';
    const w = shape === 'round' ? f.H * size : f.W * size * 0.6;
    f.html.push(`<div class="studio" ${v.background ? `style="background:${esc(v.background)}"` : ''}></div>` +
      `<div class="cutout ${shape === 'round' ? 'round' : ''}" id="${id}-c" style="width:${r3(w)}px;height:${r3(shape === 'round' ? w : f.H * size)}px;left:${r3((v.x ?? 0.5) * f.W - w / 2)}px;top:${r3((v.y ?? 0.45) * f.H - (shape === 'round' ? w : f.H * size) / 2)}px">${f.media(v.asset, sc.id, '')}</div>`);
    f.ft(`#${id}-c`, { scale: 0.4, opacity: 0, y: 80 }, { scale: 1, opacity: 1, y: 0 }, sc.start + 0.03, 0.45, 'back.out(1.6)');
    f.ft(`#${id}-c`, { rotation: -1.5 }, { rotation: 1.5 }, sc.start, sc.end - sc.start, 'sine.inOut', { i: false });
    f.cue('pop', sc.start + 0.05, -4);
  },
  collage(f, sc, v, id) {
    const tiles = v.tiles || [];
    const cols = tiles.length <= 4 ? 2 : 3, rows = Math.ceil(tiles.length / cols);
    const gw = f.W / cols, gh = f.H / rows;
    f.html.push(`<div class="solid" style="background:#fff"></div>` + tiles.map((t, i) => {
      const c = i % cols, r = Math.floor(i / cols);
      return `<div class="tile" id="${id}-t${i}" style="left:${r3(c * gw)}px;top:${r3(r * gh)}px;width:${r3(gw)}px;height:${r3(gh)}px">${f.media(t.asset, sc.id, '')}${t.label ? `<div class="cap">${esc(t.label)}</div>` : ''}</div>`;
    }).join(''));
    tiles.forEach((t, i) => { const at = f.at(t.at, sc, sc.start + i * 0.18); f.ft(`#${id}-t${i}`, { scale: 0.6, opacity: 0 }, { scale: 1, opacity: 1 }, at, 0.3, 'power3.out'); f.cue('pop', at, -9); });
  },
  comparison(f, sc, v, id) {
    const side = (s, k, x) => `<div style="position:absolute;top:0;bottom:0;left:${x}%;width:50%;overflow:hidden" id="${id}-${k}"><div class="cam" id="${id}-${k}c"${s.grade === 'bw' ? ' style="filter:grayscale(1) contrast(1.1)"' : ''}>${f.media(s.asset, sc.id)}</div>` +
      (s.label ? `<div class="label lower" style="left:50%;bottom:9%;transform:translateX(-50%)">${esc(s.label)}</div>` : '') + `</div>`;
    f.html.push(side(v.left || {}, 'L', 0) + side(v.right || {}, 'R', 50) + `<div id="${id}-div" style="position:absolute;left:50%;top:0;bottom:0;width:8px;background:#fff;transform:translateX(-50%);z-index:2"></div>` +
      (v.vs !== false ? `<div class="label" id="${id}-vs" style="left:50%;top:44%;transform:translate(-50%,-50%);font:400 120px var(--font-display);color:#fff">VS</div>` : ''));
    const tR = f.at(v.right?.at, sc, sc.start + 0.4);
    // the left side owns the whole frame until the right side is introduced, then the split opens
    f.set(`#${id}-R`, { xPercent: 100 }, sc.start);
    f.ft(`#${id}-L`, { width: '100%' }, { width: '50%' }, tR, 0.45, 'power3.inOut');
    f.ft(`#${id}-R`, { xPercent: 100 }, { xPercent: 0 }, tR, 0.45, 'power3.inOut', { i: false });
    f.ft(`#${id}-div`, { opacity: 0 }, { opacity: 1 }, tR, 0.2);
    f.ft(`#${id}-Lc`, { scale: 1.05 }, { scale: 1.15 }, sc.start, sc.end - sc.start, 'none', { i: false });
    f.ft(`#${id}-Rc`, { scale: 1.15 }, { scale: 1.05 }, sc.start, sc.end - sc.start, 'none', { i: false });
    if (v.vs !== false) { f.ft(`#${id}-vs`, { scale: 0 }, { scale: 1 }, tR + 0.3, 0.3, 'back.out(3)'); f.cue('impact', tR + 0.3, -6); }
    f.cue('whoosh', sc.start, -8); f.cue('whoosh', tR, -8);
  },
  blocks3d(f, sc, v, id) {
    // Three.js scene drawn from HyperFrames' hf-seek time: rows of boxes growing in, camera dolly. See components/fvs-blocks3d.js
    const cfg = { count: v.count || 24, cols: v.cols || 6, color: v.color || '#d9772b', palette: v.palette || null, start: sc.start, end: sc.end,
      growAt: f.at(v.growAt, sc, sc.start + 0.2), growDuration: v.growDuration || 1.6, label: v.label || null, cameraFrom: v.cameraFrom || null, cameraTo: v.cameraTo || null };
    f.html.push(`<div class="studio"></div><canvas id="${id}-3d" class="fvs-3d" width="${f.W}" height="${f.H}" style="position:absolute;inset:0;width:100%;height:100%" data-fvs3d='${esc(JSON.stringify(cfg))}'></canvas>`);
    f.html.push(`<script type="module">import { mount } from './components/fvs-blocks3d.js'; mount(document.getElementById('${id}-3d'));</script>`);
    f.cue('riser', cfg.growAt, -8);
  },
  custom(f, sc, v, id) {
    // a hand-made scene: a HyperFrames sub-composition in compositions/, mounted for this scene's window
    f.html.push(`<div id="${id}-cc" data-composition-id="${esc(v.compositionId || id)}" data-composition-src="${esc(v.composition)}" data-start="0" data-duration="${r3(sc.end - sc.start)}" data-track-index="3" style="position:absolute;inset:0"></div>`);
  },
};

// ---------------------------------------------------------------------------------------------- layers

const LAYERS = {
  label(f, sc, L, id) {
    const t0 = f.at(L.at, sc, sc.start + 0.1);
    const t1 = f.at(L.until, sc, sc.end);
    const style = L.style || 'plain';
    const cls = ['label', L.lowercase === false ? '' : 'lower', style === 'money' ? 'money' : style === 'alert' ? 'alert' : style === 'dark' ? 'dark' : ''].join(' ');
    const [x, y] = L.position || [0.5, 0.82];
    const anchor = L.anchor || 'center';
    const tx = anchor === 'left' ? '0' : anchor === 'right' ? '-100%' : '-50%';
    const words = String(L.text).split(/\s+/);
    const inner = L.reveal === 'words' ? words.map((w, i) => `<span class="w" id="${id}-w${i}">${esc(w)}</span>`).join(' ') : esc(L.text);
    f.html.push(`<div class="${cls}" id="${id}" style="left:${x * 100}%;top:${y * 100}%;font-size:${L.size || 64}px;transform:translate(${tx},-50%) rotate(${L.rotate || 0}deg)">${inner}${style === 'pin' ? PIN_SVG : ''}</div>`);
    if (L.reveal === 'words') {
      f.set(`#${id}`, { opacity: 1 }, t0);
      let after = t0 - 0.05;
      words.forEach((w, i) => {
        const tw = f.at('@' + w, { ...sc, start: after }, null);
        const at = tw !== null && tw > after - 0.001 && tw <= sc.end ? tw : after + 0.2;
        after = at + 0.01;
        f.ft(`#${id}-w${i}`, { opacity: 0 }, { opacity: 1 }, Math.max(t0, at), 0.04);
      });
    } else {
      f.ft(`#${id}`, { opacity: 0, scale: 0.8 }, { opacity: 1, scale: 1 }, t0, 0.16, 'back.out(2.5)');
    }
    if (t1 < sc.end - 0.05) f.ft(`#${id}`, { opacity: 1 }, { opacity: 0 }, t1, 0.12, 'none', { i: false });
    if (L.sfx !== false) f.cue(style === 'money' ? 'cash' : 'pop', t0, style === 'money' ? -6 : -9);
  },
  arrow(f, sc, L, id) {
    const t0 = f.at(L.at, sc, sc.start + 0.2);
    const [x1, y1] = L.from, [x2, y2] = L.to;
    const X1 = x1 * f.W, Y1 = y1 * f.H, X2 = x2 * f.W, Y2 = y2 * f.H;
    const ang = Math.atan2(Y2 - Y1, X2 - X1), len = Math.hypot(X2 - X1, Y2 - Y1), w = L.width || 22, head = w * 2.6;
    const col = L.color || 'var(--accent)';
    f.html.push(`<svg class="arrow" id="${id}" width="${f.W}" height="${f.H}" viewBox="0 0 ${f.W} ${f.H}" style="filter:drop-shadow(0 3px 3px rgba(0,0,0,.5))">` +
      `<g transform="translate(${r3(X1)},${r3(Y1)}) rotate(${r3(ang * 180 / Math.PI)})"><g id="${id}-g">` +
      `<rect x="0" y="${-w / 2}" width="${r3(Math.max(0, len - head))}" height="${w}" fill="${col}"/>` +
      `<polygon points="${r3(len - head)},${-head * 0.75} ${r3(len)},0 ${r3(len - head)},${head * 0.75}" fill="${col}"/></g></g></svg>`);
    f.ft(`#${id}-g`, { scaleX: 0, transformOrigin: '0px 0px' }, { scaleX: 1 }, t0, 0.18, 'power3.out');
    if (L.until) f.ft(`#${id}`, { opacity: 1 }, { opacity: 0 }, f.at(L.until, sc, sc.end), 0.1, 'none', { i: false });
    if (L.label) LAYERS.label(f, sc, { ...L.label, at: L.label.at ?? t0 + 0.05, position: L.label.position || [x1, y1], sfx: false }, `${id}-lb`);
    f.cue('pop', t0, -8);
  },
  captions(f, sc, L, id) {
    // narration words as a lower caption strip, each word appearing as it is spoken (for quotes / key lines)
    const t0 = f.at(L.at, sc, sc.start), t1 = f.at(L.until, sc, sc.end);
    const ws = f.words.filter(([s]) => s >= t0 - 0.01 && s < t1);
    f.html.push(`<div class="cap-strip" id="${id}" style="${L.color ? `color:${esc(L.color)};` : ''}">` + ws.map((w, i) => `<span class="w" id="${id}-w${i}">${esc(w[2])}</span>`).join(' ') + `</div>`);
    ws.forEach((w, i) => f.ft(`#${id}-w${i}`, { opacity: 0 }, { opacity: 1 }, w[0], 0.05));
  },
  pricetag(f, sc, L, id) {
    const t0 = f.at(L.at, sc, sc.start + 0.15);
    const [x, y] = L.position || [0.03, 0.05];
    f.html.push(`<div class="pricetag" id="${id}" style="left:${x * 100}%;top:${y * 100}%">${L.asset ? f.media(L.asset, sc.id, '') : ''}<div><b>${esc(L.price)}</b>${L.name ? `<span>${esc(L.name)}</span>` : ''}</div></div>`);
    f.ft(`#${id}`, { opacity: 0, x: -40 }, { opacity: 1, x: 0 }, t0, 0.25, 'power3.out');
    f.cue('ding', t0, -10);
  },
  hand(f, sc, L, id) {
    // handwritten annotation with an optional arrow drawn toward the subject
    const t0 = f.at(L.at, sc, sc.start + 0.2);
    const [x, y] = L.position || [0.2, 0.3];
    f.html.push(`<div class="hand ${L.dark ? 'dark' : ''}" id="${id}" style="left:${x * 100}%;top:${y * 100}%;font-size:${L.size || 72}px;transform:rotate(${L.rotate ?? -4}deg)">${esc(L.text)}</div>`);
    f.ft(`#${id}`, { opacity: 0, clipPath: 'inset(0 100% 0 0)' }, { opacity: 1, clipPath: 'inset(0 0% 0 0)' }, t0, 0.35, 'power1.out');
    if (L.to) LAYERS.arrow(f, sc, { from: L.from || [x + 0.02, y + 0.06], to: L.to, at: t0 + 0.2, width: 10, color: L.dark ? '#111' : '#fff' }, `${id}-a`);
    f.cue('marker', t0, -10);
  },
  meter(f, sc, L, id) {
    const t0 = f.at(L.at, sc, sc.start + 0.3), d = L.duration || 1.2;
    const [x, y] = L.position || [0.2, 0.2]; const w = (L.width || 0.6) * 100; const frac = Math.max(0, Math.min(1, L.fraction ?? 1));
    f.html.push(`<div class="meter" id="${id}" style="left:${x * 100}%;top:${y * 100}%;width:${w}%"><div class="fill" id="${id}-f"></div>${L.label ? `<div class="val" id="${id}-v" style="left:${frac * 100}%">${esc(L.label)}</div>` : ''}</div>`);
    f.ft(`#${id}`, { opacity: 0 }, { opacity: 1 }, t0 - 0.15, 0.15);
    f.ft(`#${id}-f`, { scaleX: 0 }, { scaleX: frac }, t0, d, 'power2.out');
    if (L.label) f.ft(`#${id}-v`, { opacity: 0, y: 10 }, { opacity: 1, y: 0 }, t0 + d * 0.8, 0.25, 'back.out(2)');
    f.cue('riser', t0 + d, -12);
  },
  image(f, sc, L, id) {
    const t0 = f.at(L.at, sc, sc.start + 0.1);
    const [x, y] = L.position || [0.5, 0.5]; const w = (L.width || 0.3) * f.W;
    f.html.push(`<div class="cutout ${L.round ? 'round' : ''}" id="${id}" style="left:${r3(x * f.W - w / 2)}px;top:${r3(y * f.H - w * (L.aspect || 1) / 2)}px;width:${r3(w)}px;height:${r3(w * (L.aspect || 1))}px">${f.media(L.asset, sc.id, '')}</div>`);
    f.ft(`#${id}`, { scale: 0, opacity: 0 }, { scale: 1, opacity: 1 }, t0, 0.35, 'back.out(2)');
    f.cue('pop', t0, -8);
  },
};

// ---------------------------------------------------------------------------------------------- transitions

function transitionIn(f, sc, prev, sid) {
  const t = sc.transition_in || sc.transition || 'cut';
  const type = typeof t === 'string' ? t : t.type;
  const d = (typeof t === 'object' && t.duration) || 0.16;
  if (!prev || type === 'cut') return;
  const T = sc.start;
  const IN = `#${sid}-in`, OUT = `#${prev}-in`;
  if (type.startsWith('whip')) {
    const dir = type.endsWith('right') ? -1 : type.endsWith('up') ? 0 : 1;
    const ax = dir ? 'x' : 'y', dist = (dir || 1) * (dir ? f.W : f.H) * 0.35;
    f.on(prev, () => f.ft(OUT, { [ax]: 0, filter: 'blur(0px)' }, { [ax]: -dist, filter: 'blur(28px)' }, T - d, d, 'power2.in', { i: false }));
    f.ft(IN, { [ax]: dist, filter: 'blur(28px)' }, { [ax]: 0, filter: 'blur(0px)' }, T, d, 'power2.out');
    f.cue('whoosh', T - d, -4);
  } else if (type === 'zoom') {
    f.on(prev, () => f.ft(OUT, { scale: 1, filter: 'blur(0px)' }, { scale: 1.35, filter: 'blur(14px)' }, T - d, d, 'power2.in', { i: false }));
    f.ft(IN, { scale: 0.8, filter: 'blur(14px)' }, { scale: 1, filter: 'blur(0px)' }, T, d * 1.4, 'power2.out');
    f.cue('whoosh', T - d, -6);
  } else if (type === 'flash') {
    const fid = f.uid('flash');
    f.rootHtml.push(`<div class="flash clip" id="${fid}" data-start="${r3(T - 0.1)}" data-duration="0.35" data-track-index="6"></div>`);
    f.on('main', () => { f.ft(`#${fid}`, { opacity: 0 }, { opacity: 1 }, T - 0.1, 0.1, 'power1.in'); f.ft(`#${fid}`, { opacity: 1 }, { opacity: 0 }, T, 0.25, 'power1.out', { i: false }); });
    f.cue('impact', T, -5);
  } else if (type === 'fade' || type === 'dissolve') {
    f.ft(IN, { opacity: 0 }, { opacity: 1 }, T, Math.max(d, 0.3), 'power1.inOut');
  }
}

// ---------------------------------------------------------------------------------------------- build

export async function build(projectDir, { reason } = {}) {
  const dir = path.resolve(projectDir);
  const meta = readJson(path.join(dir, 'project.fvs.json'));
  const sb = readJson(path.join(dir, LAYOUT.storyboard, 'storyboard.json'));
  if (!sb) throw new Error('no storyboard/storyboard.json (run storyboard-draft, then refine it)');
  const check = checkStoryboard(dir);
  if (!check.ok) throw new Error('storyboard check failed:\n- ' + check.errors.join('\n- '));
  const words = readJson(path.join(dir, LAYOUT.audio, 'words.json'), []);
  const register = readRegister(dir);
  const warnings = [];
  const f = new Film(meta, words, register, w => warnings.push(w));

  if (fs.existsSync(path.join(dir, 'index.html'))) snapshot(dir, reason || 'rebuild from storyboard');

  const duration = r3(meta.duration);
  const scenes = sb.scenes;
  const compDir = path.join(dir, 'compositions');
  fs.mkdirSync(compDir, { recursive: true });
  for (const old of fs.readdirSync(compDir)) if (/^s\d+\.html$/.test(old)) fs.rmSync(path.join(compDir, old));   // generated scene files only
  const sids = scenes.map((_, i) => `s${String(i + 1).padStart(2, '0')}`);
  scenes.forEach((sc, i) => { f.offset[sids[i]] = sc.start; f.motionBy[sids[i]] = []; });
  const bodies = {};
  for (const [i, sc] of scenes.entries()) {
    const sid = sids[i];
    f.cur = sid; f.html = [];
    const v = sc.visual || { type: 'solid' };
    const fn = VISUALS[v.type];
    if (!fn) throw new Error(`scene ${sc.id}: unknown visual type "${v.type}" (known: ${Object.keys(VISUALS).join(', ')})`);
    fn(f, sc, v, sid);
    (sc.layers || []).forEach((L, k) => {
      const lf = LAYERS[L.type];
      if (!lf) throw new Error(`scene ${sc.id}: unknown layer type "${L.type}" (known: ${Object.keys(LAYERS).join(', ')})`);
      lf(f, sc, L, `${sid}-L${k}`);
    });
    for (const c of sc.sfx || []) f.cue(c.cue, f.at(c.at, sc, sc.start), c.gain_db ?? 0);
    transitionIn(f, sc, i ? sids[i - 1] : null, sid);
    bodies[sid] = f.html;
  }
  f.cur = 'main';
  // one HyperFrames sub-composition per scene: its own file, its own timeline in local time
  const hosts = [];
  for (const [i, sc] of scenes.entries()) {
    const sid = sids[i];
    const label = `${String(i + 1).padStart(2, '0')} · ${sc.title || sc.id}`;
    const file = `compositions/${sid}.html`;
    fs.writeFileSync(path.join(dir, file), `<!-- ${esc(label)} — scene ${esc(sc.id)} (${sc.start}s–${sc.end}s). Generated by \`fvs build\` from storyboard/storyboard.json.
     Narration: ${esc(sc.narration || '')}
     Technique: ${esc(sc.technique || '')} -->
<template id="${sid}-template">
  <div data-composition-id="${sid}" data-width="${meta.width}" data-height="${meta.height}" data-duration="${r3(sc.end - sc.start)}">
  <div class="scene" id="${sid}-in">
    ${bodies[sid].join('\n    ')}
  </div>
  <script>FVS_RUN(${JSON.stringify({ id: sid, motion: f.motionBy[sid] })});</script>
  </div>
</template>
`);
    hosts.push(`  <div id="${sid}" data-composition-id="${sid}" data-composition-src="${file}" data-fvs-scene="${esc(label)}" data-fvs-id="${esc(sc.id)}" data-start="${r3(sc.start)}" data-duration="${r3(sc.end - sc.start)}" data-track-index="1" style="position:absolute;inset:0;z-index:${i + 1}"></div>`);
  }
  const tokens = Object.entries(sb.style?.tokens || {}).map(([k, v]) => `--${k}:${v};`).join('');
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=${meta.width}, height=${meta.height}" />
<!-- Generated by faceless-video-studio \`fvs build\` from storyboard/storyboard.json. Each scene is a HyperFrames
     sub-composition in compositions/sNN.html. Small fixes can be made there directly; a later \`fvs build\`
     regenerates them (the previous version is kept in versions/). -->
<title>${esc(meta.title)}</title>
<link rel="stylesheet" href="styles/base.css" />
<style>:root{--W:${meta.width}px;--H:${meta.height}px;${tokens}}</style>
<script src="vendor/gsap.min.js"></script>
<script src="components/fvs-motion.js"></script>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-duration="${duration}" data-width="${meta.width}" data-height="${meta.height}">
${hosts.join('\n')}
${f.rootHtml.map(h => '  ' + h).join('\n')}
  <audio id="mix" src="audio/mix.wav" data-start="0" data-duration="${duration}" data-track-index="9" data-volume="1"></audio>
</div>
<script>
FVS_RUN(${JSON.stringify({ id: 'main', motion: f.motionBy.main })});
</script>
</body>
</html>
`;
  fs.writeFileSync(path.join(dir, 'index.html'), html);
  // sound cues for the mix (and VideoHub's cue marks)
  f.cues.sort((a, b) => a.t - b.t);
  writeJson(path.join(dir, LAYOUT.audio, 'cues.json'), { cues: f.cues.filter(c => c.t >= 0 && c.t < meta.duration) });
  const mix = await mixProject(dir);
  const preview = buildPreview(dir, { fps: meta.fps, title: meta.title });
  markStage(dir, 'build', 'done', { scenes: scenes.length, tweens: f.motionCount, cues: f.cues.length, warnings: warnings.length });
  return { project: dir, scenes: scenes.length, tweens: f.motionCount, cues: f.cues.length, warnings, mix, preview: preview.changed, revision: readState(dir).revision };
}
