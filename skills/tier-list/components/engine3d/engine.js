// Engine: one WebGL renderer, scenes swapped per shot (hard cuts), DOM overlays projected from 3D anchors.
// render(t) is a pure function of composition time t (Hyperframes seeks frames out of order).
import { THREE, E, clamp, bgTex, motes, V3 } from "./kit.js";
import { SCENES } from "./scenes.js";

const DATA = JSON.parse(document.getElementById("shots").textContent);
const SHOTS = DATA.shots; const W = 1920, H = 1080;
const Q = new URLSearchParams(location.search);
window.__hf = window.__hf || {}; window.__hf.buildReady = window.__hf.buildReady || {};

const canvas = document.getElementById("gl");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true, powerPreference: "high-performance" });
renderer.setSize(W, H, false); renderer.setPixelRatio(1);
const scene = new THREE.Scene(); const camera = new THREE.PerspectiveCamera(36, W / H, 0.1, 400);
const dust = motes(110); scene.add(dust.points);
const KIT_CTX = {};

const AUTO = ["push", "orbit", "drift", "pull", "orbit", "push"];
// ---------- camera rigs ----------
function placeCamera(shot, inst, t, d) {
  if (inst.camera) { inst.camera(camera, t, d); camera.updateProjectionMatrix(); return; }
  const c = shot.cam || {}, u = clamp(t / d), rig = c.rig || inst.rig || AUTO[(shot.idx || 0) % AUTO.length];
  const dist = c.d ?? inst.camD ?? 11, h = c.h ?? inst.camH ?? 2.2, look = c.look || inst.look || [0, 1.5, 0], a = c.amp ?? 1;
  let x = c.x ?? 0, y = h, z = dist, lx = look[0], ly = look[1], lz = look[2]; const s = E.inOutSine(u);
  switch (rig) {
    case "push": z = dist + 1.6 * a - 3.0 * a * s; x += Math.sin(u * 1.4) * 0.5 * a; break;
    case "pull": z = dist - 1.6 * a + 3.0 * a * s; x -= Math.sin(u * 1.4) * 0.5 * a; break;
    case "orbit": { const ang = (c.a0 ?? -0.38) + (c.sweep ?? 0.76) * a * s; x = look[0] + Math.sin(ang) * dist; z = look[2] + Math.cos(ang) * dist; break; }
    case "rise": y = h - 1.3 * a + 2.6 * a * s; z = dist - u * 1.0 * a; break;
    case "fall": y = h + 1.5 * a - 3.0 * a * s; z = dist - u * 1.0 * a; break;
    case "track": x += (-2.6 + 5.2 * s) * a; lx = look[0] + x * 0.55; break;
    case "trackr": x += (2.6 - 5.2 * s) * a; lx = look[0] + x * 0.55; break;
    case "drift": x += Math.sin(t * 0.55) * 0.6 * a; y += Math.sin(t * 0.4) * 0.3 * a; z -= u * 0.8 * a; break;
    case "static": break;
  }
  camera.position.set(x, y, z); camera.lookAt(lx, ly, lz); camera.fov = c.fov ?? 36; camera.updateProjectionMatrix();
}

// ---------- shots ----------
let cur = -1, curInst = null;
const insts = new Array(SHOTS.length);
function instance(i) {
  if (!insts[i]) { const s = SHOTS[i]; const f = SCENES[s.scene]; if (!f) throw new Error("unknown scene " + s.scene + " (shot " + s.id + ")"); insts[i] = f(s.p || {}, s); }
  return insts[i];
}
function shotAt(t) { let lo = 0, hi = SHOTS.length - 1; while (lo < hi) { const m = (lo + hi + 1) >> 1; if (SHOTS[m].ps <= t) lo = m; else hi = m - 1; } return lo; }

// ---------- overlays (DOM) ----------
const ovRoot = document.getElementById("ov"); const OVS = [];
const ICON = { coin: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" fill="#f5c542"/><circle cx="12" cy="12" r="6.4" fill="none" stroke="#b8860b" stroke-width="1.6"/><text x="12" y="16" font-size="10" text-anchor="middle" fill="#8a6508" font-weight="700" font-family="Arimo">$</text></svg>',
  calendar: '<svg viewBox="0 0 24 24"><rect x="3" y="5" width="18" height="16" rx="3" fill="#fff"/><rect x="3" y="5" width="18" height="5" rx="2" fill="#e0262b"/><rect x="7" y="2.5" width="2" height="5" rx="1" fill="#ddd"/><rect x="15" y="2.5" width="2" height="5" rx="1" fill="#ddd"/><rect x="7" y="13" width="3" height="3" fill="#8a93a8"/><rect x="13" y="13" width="3" height="3" fill="#42d9f9"/></svg>',
  play: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="#fff"/><path d="M10 8l6 4-6 4z" fill="#e0262b"/></svg>', people: '<svg viewBox="0 0 24 24"><circle cx="8" cy="8" r="3" fill="#fff"/><circle cx="16.5" cy="9" r="2.5" fill="#cfe"/><path d="M2 20c0-4 3-6 6-6s6 2 6 6z" fill="#fff"/><path d="M14 20c0-3 2-5 4.5-5S22 17 22 20z" fill="#cfe"/></svg>',
  tag: '<svg viewBox="0 0 24 24"><path d="M3 12V4h8l10 10-8 8z" fill="#fff"/><circle cx="7.5" cy="8.5" r="1.8" fill="#199aff"/></svg>', lock: '<svg viewBox="0 0 24 24"><rect x="5" y="10" width="14" height="11" rx="2.5" fill="#fff"/><path d="M8 10V7a4 4 0 018 0v3" fill="none" stroke="#fff" stroke-width="2.4"/><circle cx="12" cy="15.5" r="1.7" fill="#199aff"/></svg>',
  doc: '<svg viewBox="0 0 24 24"><path d="M5 2h10l5 5v15H5z" fill="#fff"/><rect x="8" y="11" width="9" height="1.8" fill="#8a93a8"/><rect x="8" y="15" width="9" height="1.8" fill="#8a93a8"/><rect x="8" y="7" width="4" height="1.8" fill="#42d9f9"/></svg>', star: '<svg viewBox="0 0 24 24"><path d="M12 2l3 6.5 7 .8-5.2 4.8 1.5 7L12 17.6 5.7 21l1.5-7L2 9.3l7-.8z" fill="#f5c542"/></svg>' };
function esc(s) { return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }
function mkChars(text, wrap) { const sp = []; let h = ""; for (const ch of String(text)) { if (ch === "\n") h += "<br/>"; else { h += `<span class="ch">${ch === " " ? (wrap ? " " : "&nbsp;") : esc(ch)}</span>`; } } return h; }
function buildOverlay(o, si) {
  const el = document.createElement("div"); el.style.display = "none"; el.dataset.k = o.kind;
  if (o.kind === "label") { el.className = "tl-text tl-name ov-label"; el.style.fontSize = (o.size || 72) + "px"; el.style.textAlign = o.side === "left" ? "right" : o.side === "center" || o.side === "above" || o.side === "below" ? "center" : "left"; el.innerHTML = mkChars(o.text); if (o.color) el.style.color = o.color; }
  else if (o.kind === "caption") { el.className = "tl-text tl-spec ov-cap"; el.style.fontSize = (o.size || 58) + "px"; el.innerHTML = `<span class="tl-pop">${esc(o.text)}</span>`; }
  else if (o.kind === "badge") { el.className = "tl-badge ov-badge"; el.innerHTML = `${o.icon ? `<div class="ico">${ICON[o.icon] || ""}</div>` : ""}<div class="txt"><div class="price">${esc(o.price)}</div><div class="model">${esc(o.model || "")}</div></div>`; }
  else if (o.kind === "year") { el.className = "tl-text tl-year ov-year"; el.innerHTML = `<span class="tl-pop">${esc(o.text)}</span>`; }
  else if (o.kind === "quote") { el.className = "ov-quote"; el.innerHTML = `<div class="q">${mkChars(o.text, true)}</div>${o.by ? `<div class="by">${esc(o.by)}</div>` : ""}`; }
  else if (o.kind === "tracker") {
    el.className = "ov-tracker"; let h = '<div class="pips">'; for (let i = 1; i <= 5; i++) h += `<div class="pip ${i < o.n ? "done" : i === o.n ? "cur" : ""}">${i}</div>`; h += `</div><div class="tt">${esc(o.title || "")}</div>`; el.innerHTML = h;
  } else if (o.kind === "stamp") { el.className = "ov-stamp"; el.innerHTML = `<span>${esc(o.text)}</span>`; }
  ovRoot.appendChild(el);
  return { el, o, si, on: false, chars: el.querySelectorAll(".ch"), pop: el.querySelector(".tl-pop") };
}
SHOTS.forEach((s, i) => (s.idx = i));
SHOTS.forEach((s, si) => (s.ov || []).forEach((o) => OVS.push(buildOverlay(o, si))));
(DATA.ov || []).forEach((o) => OVS.push(buildOverlay(o, -1)));
const _v = new THREE.Vector3();
function updateOverlays(t) {
  for (const ov of OVS) {
    const o = ov.o, on = t >= o.t0 && t < o.t1;
    if (on !== ov.on) { ov.el.style.display = on ? "" : "none"; ov.on = on; }
    if (!on) continue; const tl = t - o.t0, el = ov.el;
    const fadeOut = o.fade ? clamp((o.t1 - t) / o.fade) : 1;
    if (o.kind === "label") {
      const cps = 35; for (let i = 0; i < ov.chars.length; i++) ov.chars[i].style.opacity = clamp(tl * cps - i, 0, 2.8) / 2.8;
      let px, py; const inst = insts[ov.si]; const a = o.anchor && inst && inst.anchors && inst.anchors[o.anchor];
      if (a) { a.updateWorldMatrix(true, false); a.getWorldPosition(_v); _v.project(camera); px = (_v.x * 0.5 + 0.5) * W + (o.dx || 0); py = (-_v.y * 0.5 + 0.5) * H + (o.dy || 0); }
      else { px = (o.x ?? 50) / 100 * W; py = (o.y ?? 50) / 100 * H; }
      const tf = o.side === "left" ? "translate(-100%,-50%)" : o.side === "above" ? "translate(-50%,-100%)" : o.side === "below" ? "translate(-50%,0)" : o.side === "center" ? "translate(-50%,-50%)" : "translate(0,-50%)";
      el.style.left = px.toFixed(1) + "px"; el.style.top = py.toFixed(1) + "px"; el.style.transform = tf + " translateX(" + ((o.side === "left" ? -1 : 1) * Math.min(tl, 4) * 8).toFixed(1) + "px)"; el.style.opacity = fadeOut;
    } else if (o.kind === "caption" || o.kind === "year") {
      const p = E.outCubic(clamp(tl / 0.18)); ov.pop.style.opacity = p * fadeOut; ov.pop.style.transform = `scale(${(0.92 + 0.08 * p).toFixed(3)})`;
    } else if (o.kind === "badge") {
      const p = E.outCubic(clamp(tl / 0.18)); el.style.opacity = p * fadeOut; el.style.transform = `scale(${(0.92 + 0.08 * p).toFixed(3)})`;
    } else if (o.kind === "quote") {
      const cps = o.cps || 38; for (let i = 0; i < ov.chars.length; i++) ov.chars[i].style.opacity = clamp(tl * cps - i, 0, 2.8) / 2.8;
      const p = E.outCubic(clamp(tl / 0.25)); el.style.opacity = p * fadeOut; const by = el.querySelector(".by"); if (by) by.style.opacity = clamp((tl - 0.6) / 0.3);
    } else if (o.kind === "tracker") { const p = E.outCubic(clamp(tl / 0.25)); el.style.opacity = p * fadeOut; el.style.transform = `translateY(${((1 - p) * -14).toFixed(1)}px)`; }
    else if (o.kind === "stamp") { const p = clamp(tl / 0.16); const sc = 2.6 - 1.6 * E.outCubic(p); el.style.opacity = clamp(tl / 0.06) * fadeOut; el.style.transform = `translate(-50%,-50%) rotate(${o.rot ?? -9}deg) scale(${sc.toFixed(3)})`; }
  }
}

// ---------- render ----------
let lastBg = "";
function renderAt(t) {
  t = Math.max(0, Math.min(t, DATA.total - 1e-3)); const i = shotAt(t); const s = SHOTS[i]; const inst = instance(i);
  if (i !== cur) { if (curInst) scene.remove(curInst.root); scene.add(inst.root); cur = i; curInst = inst; if (s.bg !== lastBg) { scene.background = bgTex(s.bg || "navy"); lastBg = s.bg; } }
  const local = t - s.ps, d = s.pe - s.ps; dust.update(t);
  dust.points.visible = !inst.noDust; inst.update(local, d); placeCamera(s, inst, local, d); camera.updateMatrixWorld();
  renderer.render(scene, camera); updateOverlays(t);
}
window.__renderAt = renderAt; window.__shots = SHOTS; window.__insts = insts; window.__renderer = renderer;
window.addEventListener("hf-seek", (e) => { renderAt(e.detail.time); });

window.__hf.buildReady["gl"] = (async () => {
  if (document.fonts) { await Promise.all([document.fonts.load('700 64px "Arimo"'), document.fonts.load('400 64px "Arimo"'), document.fonts.load('700 64px "Kalam"')]); await document.fonts.ready; }
  // decode every photo before the first render so photo scenes can build textures synchronously
  window.__imgs = {}; const srcs = [...new Set(SHOTS.filter((x) => x.p && x.p.src).map((x) => x.p.src))];
  await Promise.all(srcs.map(async (u) => { const im = new Image(); im.src = u; await im.decode(); window.__imgs[u] = im; }));
  if (Q.get("eager") === "1") for (let i = 0; i < SHOTS.length; i++) instance(i);
  renderAt(Q.get("t") ? +Q.get("t") : 0); return true;
})();
