// 3D motion-graphics toolkit (three.js, software-GL friendly: matcap materials, no shadow maps, no PBR).
// Everything here is a pure function of its inputs; scenes call update(t) with a local time and set state from it.
import * as THREE from "three";
import { Font } from "three/addons/loaders/FontLoader.js";
import { TextGeometry } from "three/addons/geometries/TextGeometry.js";
import { RoundedBoxGeometry } from "three/addons/geometries/RoundedBoxGeometry.js";
import fontData from "./font_bold.js";

export { THREE };
export const C = { cyan: 0x42d9f9, blue: 0x199aff, navy: 0x14182a, gold: 0xf5c542, red: 0xe0262b, S: 0xf57e7e, A: 0xf8bc7f, B: 0xf7dc79, Cc: 0xfefc79, D: 0xc5fd7a, F: 0x91fc79,
  white: 0xffffff, violet: 0x8f6bff, pink: 0xff5fa2, green: 0x39d98a, grey: 0x8a93a8, dark: 0x1b2036, orange: 0xff8a3d };

// ---------------- math / easing ----------------
export const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
export const lerp = (a, b, t) => a + (b - a) * t;
export const sstep = (a, b, x) => { const t = clamp((x - a) / (b - a)); return t * t * (3 - 2 * t); };
export const E = {
  lin: (t) => t, outCubic: (t) => 1 - Math.pow(1 - t, 3), outQuart: (t) => 1 - Math.pow(1 - t, 4), outExpo: (t) => (t >= 1 ? 1 : 1 - Math.pow(2, -10 * t)),
  inOutCubic: (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2), inOutSine: (t) => -(Math.cos(Math.PI * t) - 1) / 2,
  outBack: (t, s = 1.70158) => 1 + (s + 1) * Math.pow(t - 1, 3) + s * Math.pow(t - 1, 2), inCubic: (t) => t * t * t,
  outElastic: (t) => (t <= 0 ? 0 : t >= 1 ? 1 : Math.pow(2, -9 * t) * Math.sin((t * 10 - 0.75) * ((2 * Math.PI) / 3)) + 1),
};
/** progress 0..1 of an animation that starts at t0 and lasts d, shaped by ease */
export const prog = (t, t0, d, ease = E.outCubic) => ease(clamp((t - t0) / d));
export function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = (a + 0x6d2b79f5) | 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

// ---------------- materials ----------------
const hexOf = (c) => "#" + c.getHexString();
const mcCache = new Map();
/** matcap material: one texture lookup = cheap fake of glossy/metal lighting. */
export function mc(color, o = {}) {
  const key = `${color}|${o.metal ? 1 : 0}|${o.flat ? 1 : 0}|${o.tint ?? ""}`;
  if (mcCache.has(key)) return mcCache.get(key);
  const S = 256, cv = document.createElement("canvas"); cv.width = cv.height = S; const g = cv.getContext("2d");
  const base = new THREE.Color(color);
  const mix = (c, k, w) => c.clone().lerp(new THREE.Color(k), w);
  const r = g.createRadialGradient(S * 0.36, S * 0.28, S * 0.01, S * 0.5, S * 0.5, S * 0.58);
  if (o.flat) { r.addColorStop(0, hexOf(mix(base, 0xffffff, 0.25))); r.addColorStop(0.6, hexOf(base)); r.addColorStop(1, hexOf(base.clone().multiplyScalar(0.7))); }
  else {
    r.addColorStop(0, hexOf(mix(base, 0xffffff, 0.92))); r.addColorStop(0.09, hexOf(mix(base, 0xffffff, 0.55))); r.addColorStop(0.32, hexOf(base));
    r.addColorStop(0.72, hexOf(base.clone().multiplyScalar(0.45))); r.addColorStop(1, hexOf(base.clone().multiplyScalar(0.14)));
  }
  g.fillStyle = r; g.fillRect(0, 0, S, S);
  if (o.metal) { // horizon / studio-strip reflection bands
    const lg = g.createLinearGradient(0, 0, 0, S);
    lg.addColorStop(0, "rgba(255,255,255,.55)"); lg.addColorStop(0.38, "rgba(255,255,255,.05)"); lg.addColorStop(0.47, "rgba(0,0,0,.55)"); lg.addColorStop(0.58, "rgba(0,0,0,.15)");
    lg.addColorStop(0.7, "rgba(255,230,160,.25)"); lg.addColorStop(1, "rgba(255,255,255,.1)");
    g.fillStyle = lg; g.fillRect(0, 0, S, S);
  }
  const rr = g.createRadialGradient(S * 0.84, S * 0.88, 0, S * 0.84, S * 0.88, S * 0.34);
  rr.addColorStop(0, "rgba(130,200,255,.5)"); rr.addColorStop(1, "rgba(130,200,255,0)"); g.fillStyle = rr; g.fillRect(0, 0, S, S);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace;
  const m = new THREE.MeshMatcapMaterial({ matcap: t }); mcCache.set(key, m); return m;
}
const basicCache = new Map();
export function basic(color, o = {}) {
  const key = `${color}|${o.opacity ?? 1}|${o.add ? 1 : 0}|${o.side ?? 0}`; if (basicCache.has(key)) return basicCache.get(key);
  const m = new THREE.MeshBasicMaterial({ color, transparent: (o.opacity ?? 1) < 1 || !!o.add, opacity: o.opacity ?? 1, depthWrite: !o.add && (o.opacity ?? 1) >= 1, side: o.side ?? THREE.FrontSide,
    blending: o.add ? THREE.AdditiveBlending : THREE.NormalBlending, toneMapped: false });
  basicCache.set(key, m); return m;
}
let _glowTex = null;
function glowTex() {
  if (_glowTex) return _glowTex; const S = 128, cv = document.createElement("canvas"); cv.width = cv.height = S; const g = cv.getContext("2d");
  const r = g.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S / 2); r.addColorStop(0, "rgba(255,255,255,1)"); r.addColorStop(0.25, "rgba(255,255,255,.45)"); r.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = r; g.fillRect(0, 0, S, S); _glowTex = new THREE.CanvasTexture(cv); _glowTex.colorSpace = THREE.SRGBColorSpace; return _glowTex;
}
/** additive billboard glow (fake bloom) */
export function glow(color = 0x42d9f9, size = 3, opacity = 0.9) {
  const m = new THREE.SpriteMaterial({ map: glowTex(), color, transparent: true, opacity, blending: THREE.AdditiveBlending, depthWrite: false, toneMapped: false });
  const s = new THREE.Sprite(m); s.scale.set(size, size, 1); s.userData.base = opacity; return s;
}
/** canvas texture helper: draw(ctx,w,h) */
export function canvasTex(w, h, draw) {
  const cv = document.createElement("canvas"); cv.width = w; cv.height = h; const g = cv.getContext("2d"); draw(g, w, h);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 4; return t;
}
/** largest font px (<= px) at which text fits maxW on canvas context g */
export function fitPx(g, text, maxW, px, weight = "700") { let p = px; g.font = `${weight} ${p}px "Arimo"`; while (g.measureText(text).width > maxW && p > 18) { p -= 2; g.font = `${weight} ${p}px "Arimo"`; } return p; }
export function wrapText(g, text, maxW) { const words = text.split(" "), lines = []; let cur = ""; for (const w of words) { const t = cur ? cur + " " + w : w; if (g.measureText(t).width > maxW && cur) { lines.push(cur); cur = w; } else cur = t; } if (cur) lines.push(cur); return lines; }

// ---------------- 3D text (glyph-pooled) ----------------
const font = new Font(fontData);
const gcache = new Map();
export function charGeo(ch, depth = 0.28) {
  const k = ch + "|" + depth; if (gcache.has(k)) return gcache.get(k);
  const g = new TextGeometry(ch, { font, size: 1, depth, curveSegments: 5, bevelEnabled: depth > 0.04, bevelThickness: depth * 0.14, bevelSize: depth * 0.1, bevelSegments: 2 });
  gcache.set(k, g); return g;
}
export const adv = (ch) => { if (ch === " ") return 0.32; const gl = font.data.glyphs[ch]; return gl ? gl.ha / font.data.resolution : 0.55; };
const DIGIT_ADV = adv("0");
export const advTab = (ch) => (ch >= "0" && ch <= "9" ? DIGIT_ADV : adv(ch));
/** static row of 3D chars; returns {group, width, chars[]} (chars are Meshes at their rest x). origin = left, centered if center */
export function textRow(str, { size = 1, mat = mc(0xffffff), depth = 0.28, center = true, tab = false } = {}) {
  const group = new THREE.Group(), chars = []; let pen = 0;
  for (const ch of str) { const a = (tab ? advTab : adv)(ch); if (ch !== " ") { const m = new THREE.Mesh(charGeo(ch, depth), mat); m.position.x = pen; group.add(m); chars.push(m); m.userData.x = pen; } pen += a; }
  chars.forEach((m) => { if (center) { m.position.x -= pen / 2; m.userData.x = m.position.x; } m.userData.w = 0; });
  group.scale.setScalar(size); group.userData.width = pen * size; return { group, width: pen * size, chars };
}
/** counter: a pool of char meshes you can re-text each frame (tabular digits so nothing jitters) */
export function counter({ size = 1, mat = mc(0xffffff), depth = 0.28, max = 12 } = {}) {
  const group = new THREE.Group(), pool = []; for (let i = 0; i < max; i++) { const m = new THREE.Mesh(charGeo("0", depth), mat); m.visible = false; group.add(m); pool.push(m); }
  group.scale.setScalar(size); let last = "", width = 0;
  return { group, get width() { return width * size; },
    set(str, center = true) {
      if (str === last) return; last = str; let pen = 0; const xs = [];
      for (let i = 0; i < pool.length; i++) { const ch = str[i]; if (ch === undefined) { pool[i].visible = false; continue; } pool[i].visible = ch !== " "; if (ch !== " ") pool[i].geometry = charGeo(ch, depth); xs.push(pen); pool[i].position.x = pen; pen += advTab(ch); }
      width = pen; if (center) pool.forEach((m) => (m.position.x -= pen / 2));
    } };
}
export function fmt(n, dec = 0, prefix = "", suffix = "") { const s = n.toFixed(dec); const [a, b] = s.split("."); const withComma = a.replace(/\B(?=(\d{3})+(?!\d))/g, ","); return prefix + withComma + (b ? "." + b : "") + suffix; }

// ---------------- primitives ----------------
export function plate(w, h, d, color, { r = 0.12, metal = false, flat = false } = {}) { const m = new THREE.Mesh(new RoundedBoxGeometry(w, h, d, 3, Math.min(r, d / 2, w / 2, h / 2)), mc(color, { metal, flat })); return m; }
export function ring(rad, tube, color, { arc = Math.PI * 2, seg = 64, mat } = {}) { return new THREE.Mesh(new THREE.TorusGeometry(rad, tube, 12, seg, arc), mat || basic(color)); }
export function disc(r, h, color, { metal = false, seg = 40 } = {}) { return new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), mc(color, { metal })); }
export function coinGeo() { return new THREE.CylinderGeometry(0.5, 0.5, 0.12, 28); }
export function coin(r = 0.5) { const g = new THREE.Group(); const m = new THREE.Mesh(coinGeo(), mc(C.gold, { metal: true })); m.rotation.x = Math.PI / 2; g.add(m); g.scale.setScalar(r * 2); return g; }
export function bar(w, d, color, { metal = false } = {}) { const g = new THREE.BoxGeometry(w, 1, d); g.translate(0, 0.5, 0); const m = new THREE.Mesh(g, mc(color, { metal })); return m; }
/** donut slice from angle a0 to a1 (radians, 0 = +x, CCW) */
export function slice(r0, r1, a0, a1, depth, color, { metal = false } = {}) {
  const s = new THREE.Shape(); const seg = Math.max(6, Math.ceil(Math.abs(a1 - a0) / 0.08));
  s.moveTo(Math.cos(a0) * r1, Math.sin(a0) * r1); for (let i = 1; i <= seg; i++) { const a = lerp(a0, a1, i / seg); s.lineTo(Math.cos(a) * r1, Math.sin(a) * r1); }
  for (let i = seg; i >= 0; i--) { const a = lerp(a0, a1, i / seg); s.lineTo(Math.cos(a) * r0, Math.sin(a) * r0); }
  const g = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: true, bevelThickness: depth * 0.1, bevelSize: 0.03, bevelSegments: 2, curveSegments: 4 }); g.translate(0, 0, -depth / 2);
  return new THREE.Mesh(g, mc(color, { metal }));
}
/** flat labelled card (canvas text): draw(g,w,h) */
export function card(w, h, draw, { px = 160, depth = 0.08, edge = 0x1b2036, r = 0.12 } = {}) {
  const g = new THREE.Group(); const body = plate(w, h, depth, edge, { r, flat: true }); g.add(body);
  const tex = canvasTex(Math.round(w * px), Math.round(h * px), draw);
  const face = new THREE.Mesh(new THREE.PlaneGeometry(w - 0.02, h - 0.02), new THREE.MeshBasicMaterial({ map: tex, toneMapped: false })); face.position.z = depth / 2 + 0.002; g.add(face); g.userData.face = face; g.userData.tex = tex; return g;
}
/** instanced people (capsule body + sphere head) */
export function crowd(n, cols, { spacing = 0.5, colorFn = () => 0x8a93a8 } = {}) {
  const bodyG = new THREE.CapsuleGeometry(0.14, 0.26, 3, 10); const headG = new THREE.SphereGeometry(0.13, 12, 10);
  const body = new THREE.InstancedMesh(bodyG, new THREE.MeshMatcapMaterial({ matcap: mc(0xffffff, { flat: true }).matcap }), n);
  const head = new THREE.InstancedMesh(headG, new THREE.MeshMatcapMaterial({ matcap: mc(0xffffff).matcap }), n);
  const dummy = new THREE.Object3D(); const pos = [];
  for (let i = 0; i < n; i++) { const x = (i % cols - (cols - 1) / 2) * spacing, z = -Math.floor(i / cols) * spacing * 0.9; pos.push([x, 0, z]); }
  const g = new THREE.Group(); g.add(body, head);
  const api = { group: g, n, pos, body, head,
    setState(i, scale, color) { const [x, y, z] = pos[i]; dummy.position.set(x, y + 0.27 * scale, z); dummy.scale.setScalar(scale); dummy.updateMatrix(); body.setMatrixAt(i, dummy.matrix);
      dummy.position.set(x, y + 0.67 * scale, z); dummy.updateMatrix(); head.setMatrixAt(i, dummy.matrix); const c = new THREE.Color(color); body.setColorAt(i, c); head.setColorAt(i, c); },
    done() { body.instanceMatrix.needsUpdate = head.instanceMatrix.needsUpdate = true; if (body.instanceColor) { body.instanceColor.needsUpdate = true; head.instanceColor.needsUpdate = true; } } };
  return api;
}
/** coin rain: InstancedMesh with closed-form motion (seeded) */
export function coinRain(n, { area = [10, 8], seed = 3, speed = 2.2, size = 0.34 } = {}) {
  const im = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.5, 0.5, 0.12, 16), mc(C.gold, { metal: true }), n); const R = rng(seed); const P = [];
  for (let i = 0; i < n; i++) P.push({ x: (R() - 0.5) * area[0], z: -R() * 5 + 1.5, ph: R() * area[1], sp: speed * (0.7 + R() * 0.6), rx: R() * 6.28, rs: 2 + R() * 4 });
  const d = new THREE.Object3D();
  return { mesh: im, update(t, on = 1) { for (let i = 0; i < n; i++) { const p = P[i]; const y = area[1] - ((p.ph + t * p.sp) % area[1]); d.position.set(p.x, y - 1, p.z); d.rotation.set(p.rx + t * p.rs, 0, t * 0.7 + i); d.scale.setScalar(size * on); d.updateMatrix(); im.setMatrixAt(i, d.matrix); } im.instanceMatrix.needsUpdate = true; } };
}
export function confetti(n, { area = [12, 9], seed = 5, colors = [C.S, C.A, C.B, C.D, C.F, C.cyan, C.pink] } = {}) {
  const geo = new THREE.PlaneGeometry(0.22, 0.12); const im = new THREE.InstancedMesh(geo, new THREE.MeshBasicMaterial({ side: THREE.DoubleSide, toneMapped: false }), n); const R = rng(seed); const P = []; const col = new THREE.Color();
  for (let i = 0; i < n; i++) { P.push({ x: (R() - 0.5) * area[0], z: -R() * 4 + 1, ph: R() * area[1], sp: 1.2 + R() * 1.6, rs: 3 + R() * 6, sw: R() * 6.28 }); col.setHex(colors[i % colors.length]); im.setColorAt(i, col); }
  const d = new THREE.Object3D();
  return { mesh: im, update(t) { for (let i = 0; i < n; i++) { const p = P[i]; const y = area[1] - ((p.ph + t * p.sp) % area[1]); d.position.set(p.x + Math.sin(t * 1.3 + p.sw) * 0.4, y - 1, p.z); d.rotation.set(t * p.rs, t * p.rs * 0.7, p.sw); d.updateMatrix(); im.setMatrixAt(i, d.matrix); } im.instanceMatrix.needsUpdate = true; } };
}
/** drifting dust motes for depth */
export function motes(n, { area = [16, 9, 8], seed = 9, color = 0x9fc8ff, size = 0.05 } = {}) {
  const geo = new THREE.BufferGeometry(); const R = rng(seed); const pos = new Float32Array(n * 3); const base = [];
  for (let i = 0; i < n; i++) { const p = [(R() - 0.5) * area[0], R() * area[1] - 1, (R() - 0.5) * area[2] - 1]; base.push(p); pos.set(p, i * 3); }
  geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
  const pts = new THREE.Points(geo, new THREE.PointsMaterial({ color, size, sizeAttenuation: true, transparent: true, opacity: 0.55, depthWrite: false, blending: THREE.AdditiveBlending, toneMapped: false }));
  return { points: pts, update(t) { const a = geo.attributes.position; for (let i = 0; i < n; i++) { const b = base[i]; a.setXYZ(i, b[0] + Math.sin(t * 0.25 + i) * 0.3, b[1] + ((t * 0.12 + i * 0.37) % 1) * 0.8, b[2]); } a.needsUpdate = true; } };
}
/** glowing stage platform */
export function stage(r = 5, color = C.cyan) {
  const g = new THREE.Group(); const d = disc(r, 0.2, 0x0c1022); d.position.y = -0.1; g.add(d);
  const rg = ring(r, 0.035, color); rg.rotation.x = Math.PI / 2; rg.position.y = 0.01; g.add(rg);
  const rg2 = ring(r * 0.62, 0.02, color, { mat: basic(color, { opacity: 0.45 }) }); rg2.rotation.x = Math.PI / 2; rg2.position.y = 0.012; g.add(rg2);
  const gl = glow(color, r * 3.2, 0.28); gl.position.y = 0.3; g.add(gl); return g;
}

// ---------------- backgrounds ----------------
const bgCache = new Map();
export const BG = { navy: ["#0d1530", "#0a0f22", "#05070f"], violet: ["#241447", "#150c30", "#07040f"], ember: ["#3a1410", "#1f0b0c", "#080304"], teal: ["#0b3340", "#0a1f2c", "#04090f"],
  night: ["#10131c", "#0a0c12", "#030407"], gold: ["#3a2a0c", "#1f1608", "#080603"], green: ["#0c3a2a", "#0a2219", "#030a07"], slate: ["#1c2336", "#121726", "#05070d"] };
export function bgTex(name) {
  if (bgCache.has(name)) return bgCache.get(name); const [a, b, c] = BG[name] || BG.navy; const W = 512, H = 288; const cv = document.createElement("canvas"); cv.width = W; cv.height = H; const g = cv.getContext("2d");
  const lg = g.createLinearGradient(0, 0, 0, H); lg.addColorStop(0, a); lg.addColorStop(0.55, b); lg.addColorStop(1, c); g.fillStyle = lg; g.fillRect(0, 0, W, H);
  const rg = g.createRadialGradient(W * 0.5, H * 0.42, 10, W * 0.5, H * 0.5, W * 0.62); rg.addColorStop(0, "rgba(255,255,255,.07)"); rg.addColorStop(1, "rgba(0,0,0,.55)"); g.fillStyle = rg; g.fillRect(0, 0, W, H);
  const t = new THREE.CanvasTexture(cv); t.colorSpace = THREE.SRGBColorSpace; bgCache.set(name, t); return t;
}
/** infinite-ish floor grid */
export function grid(size = 40, div = 40, color = 0x2a3a66) {
  const g = new THREE.GridHelper(size, div, color, color); g.material.transparent = true; g.material.opacity = 0.35; g.material.depthWrite = false; g.material.toneMapped = false; return g;
}
export const V3 = (x = 0, y = 0, z = 0) => new THREE.Vector3(x, y, z);
