import { fitPx, THREE, C, E, clamp, lerp, prog, rng, mc, basic, glow, ring, disc, bar, plate, slice, card, canvasTex, wrapText, textRow, counter, fmt, coinRain, confetti, stage, crowd, coin, V3, sstep } from "./kit.js";

export const B = {};
const G = () => new THREE.Group();
const OB = (x = 0, y = 0, z = 0, parent) => { const o = new THREE.Object3D(); o.position.set(x, y, z); if (parent) parent.add(o); return o; };
const rr = (g, x, y, w, h, r) => { g.beginPath(); g.moveTo(x + r, y); g.arcTo(x + w, y, x + w, y + h, r); g.arcTo(x + w, y + h, x, y + h, r); g.arcTo(x, y + h, x, y, r); g.arcTo(x, y, x + w, y, r); g.closePath(); };
function starShape(R = 1, r = 0.45) { const s = new THREE.Shape(); for (let i = 0; i < 10; i++) { const a = Math.PI / 2 + (i * Math.PI) / 5, q = i % 2 ? r : R; const x = Math.cos(a) * q, y = Math.sin(a) * q; i ? s.lineTo(x, y) : s.moveTo(x, y); } s.closePath(); return s; }
function starMesh(R, color) { const g = new THREE.ExtrudeGeometry(starShape(R, R * 0.45), { depth: R * 0.3, bevelEnabled: true, bevelThickness: R * 0.06, bevelSize: R * 0.05, bevelSegments: 2 }); g.translate(0, 0, -R * 0.15); return new THREE.Mesh(g, mc(color, { metal: true })); }

// ---- three question cards ----
B.questions = (p) => {
  const root = G(), items = p.items, n = items.length, cards = [], at = p.at ?? items.map((_, i) => 0.15 + i * 0.9); const anchors = {}; const single = n === 1; const CW = single ? 6.4 : 3.95, CH = single ? 4.3 : 2.95, step = single ? 0 : 4.3;
  items.forEach((it, i) => {
    const c = card(CW, CH, (g, w, h) => { const lg = g.createLinearGradient(0, 0, w, h); lg.addColorStop(0, "#1a2a5c"); lg.addColorStop(1, "#0d1432"); g.fillStyle = lg; g.fillRect(0, 0, w, h);
      g.fillStyle = "#42d9f9"; g.beginPath(); g.arc(120, 120, 74, 0, 7); g.fill(); g.fillStyle = "#0b1228"; g.font = '700 104px "Arimo"'; g.textAlign = "center"; g.textBaseline = "middle"; g.fillText(String(p.nums ? p.nums[i] : i + 1), 120, 128);
      g.textAlign = "left"; g.textBaseline = "alphabetic"; g.fillStyle = "#fff"; const txt = it.toLowerCase(); let fs = single ? 84 : 62, ls; for (; fs > 30; fs -= 4) { g.font = `700 ${fs}px "Arimo"`; ls = wrapText(g, txt, w - 100); if (ls.length * fs * 1.2 <= h - 300) break; } ls.forEach((l, k) => g.fillText(l, 50, 290 + k * fs * 1.2)); }, { px: 160, depth: 0.14, edge: 0x42d9f9 });
    c.position.set((i - (n - 1) / 2) * step, 2.4, -Math.abs(i - (n - 1) / 2) * 0.5); c.rotation.y = -(i - (n - 1) / 2) * 0.16; root.add(c); cards.push(c); anchors["card" + i] = c;
  });
  const gl = glow(C.cyan, 18, 0.22); gl.position.set(0, 2.6, -3); root.add(gl);
  return { root, camD: single ? 10.5 : 12, camH: 2.8, look: [0, 2.4, 0], anchors, update(t) { cards.forEach((c, i) => { const e = E.outBack(clamp((t - at[i]) / 0.5), 1.3); c.position.y = 2.4 - (1 - e) * 4 + Math.sin(t * 1.2 + i) * 0.07; c.scale.setScalar(Math.max(0.001, e)); c.rotation.z = (1 - e) * 0.4; }); } };
};

// ---- five pedestals (the five moves) ----
B.pedestals = (p) => {
  const root = G(), n = 5, peds = [], nums = [], anchors = {}; const hs = [1.4, 2.0, 2.6, 3.2, 4.2]; const step = p.step ?? 0.32; const lastGold = p.gold !== false;
  for (let i = 0; i < n; i++) {
    const x = (i - 2) * 2.5, gold = lastGold && i === 4; const b = bar(1.9, 1.9, gold ? C.gold : [C.cyan, C.blue, C.violet, C.pink, C.gold][i], { metal: gold }); b.position.set(x, 0, 0); b.scale.y = 0.001; root.add(b); peds.push(b);
    const t3 = textRow(String(i + 1), { size: 1.3, mat: mc(gold ? 0xfff2c0 : 0xffffff, { metal: gold }), depth: 0.3 }); t3.group.position.set(x, hs[i] + 1.0, 0); t3.group.scale.setScalar(0.001); root.add(t3.group); nums.push(t3);
    anchors["ped" + i] = OB(x, hs[i] + 2.2, 0, root); anchors["base" + i] = OB(x, 0.1, 1.2, root);
  }
  const gl = glow(C.gold, 6, 0.0); gl.position.set(5, 4, -0.5); root.add(gl); const rain = coinRain(28, { area: [4, 8], seed: 4 }); rain.mesh.position.x = 5; root.add(rain.mesh);
  const base = plate(14, 0.3, 3.4, 0x0e1428, { r: 0.1 }); base.position.y = -0.15; root.add(base);
  return { root, camD: 15.5, camH: 3.6, look: [0, 2.9, 0], anchors, update(t) {
      peds.forEach((b, i) => { const t0 = 0.1 + i * step; const e = E.outBack(clamp((t - t0) / 0.5), 1.2); b.scale.y = Math.max(0.001, hs[i] * e); const ne = E.outBack(clamp((t - t0 - 0.35) / 0.4)); nums[i].group.scale.setScalar(Math.max(0.001, ne)); nums[i].group.position.y = hs[i] * e + 1.0; });
      const k = clamp((t - (p.glowAt ?? 1.8)) / 0.5); gl.material.opacity = 0.7 * k * (0.85 + 0.15 * Math.sin(t * 4)); gl.scale.setScalar(6 + 2 * k); rain.update(t, k); } };
};

// ---- crowd of people lighting up ----
B.crowd = (p) => {
  const root = G(), n = p.n ?? 480, cols = p.cols ?? 24; const cr = crowd(n, cols, { spacing: 0.46 }); root.add(cr.group); const col0 = new THREE.Color(p.base ?? 0x4a5a8a), col1 = new THREE.Color(p.color ?? C.gold); const anchors = {};
  const order = Array.from({ length: n }, (_, i) => i); const R = rng(p.seed ?? 11); for (let i = n - 1; i > 0; i--) { const j = Math.floor(R() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; } const rank = new Array(n); order.forEach((idx, r) => (rank[idx] = r));
  anchors.front = OB(0, 2.0, 0.6, root); anchors.top = OB(0, 3.4, -2, root); const gl = glow(p.color ?? C.gold, 20, 0.18); gl.position.set(0, 1.5, -5); root.add(gl);
  return { root, camD: 10, camH: 5.2, look: [0, 0.9, -3.6], rig: "rise", anchors, update(t, d) {
      const cnt = p.cnt ?? Math.min(2.2, d * 0.75), a = p.from ?? 0.02, b = p.to ?? 1; const frac = lerp(a, b, E.inOutSine(clamp(t / cnt)));
      for (let i = 0; i < n; i++) { const lit = rank[i] < frac * n; const k = lit ? E.outBack(clamp((frac * n - rank[i]) / 8)) : 0; cr.setState(i, (1 + 0.25 * Math.min(k, 1.2) * (lit ? 1 : 0)) * (p.pscale ?? 1), lit ? col1 : col0); } cr.done(); } };
};

// ---- play button with view counter (generic, no brand) ----
B.playButton = (p) => {
  const root = G(), accent = p.color ?? C.blue; const pl = plate(5.4, 3.4, 0.5, accent, { r: 1.2 }); pl.position.y = 4.6; root.add(pl);
  const tri = new THREE.Shape(); tri.moveTo(-0.65, -0.85); tri.lineTo(-0.65, 0.85); tri.lineTo(0.95, 0); tri.closePath(); const tg = new THREE.ExtrudeGeometry(tri, { depth: 0.2, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.05, bevelSegments: 2 }); tg.translate(0, 0, -0.1);
  const tm = new THREE.Mesh(tg, mc(0xffffff)); tm.position.set(0, 4.6, 0.35); root.add(tm);
  const cn = counter({ size: p.size ?? 1.55, mat: mc(C.gold, { metal: true }), depth: 0.3, max: 12 }); cn.group.position.set(0, 1.2, 0); root.add(cn.group);
  const gl = glow(accent, 14, 0.35); gl.position.set(0, 4.6, -1.5); root.add(gl); const rg = []; for (let i = 0; i < 3; i++) { const r = ring(3.2, 0.03, 0xffffff, { mat: basic(0xffffff, { opacity: 0.4 }) }); r.position.set(0, 4.6, -0.3); root.add(r); rg.push(r); }
  root.add(stage(6, accent)); const anchors = { count: cn.group, top: OB(0, 6.4, 0, root), under: OB(0, 0.6, 1.2, root) };
  return { root, camD: 12.5, camH: 3.4, look: [0, 3, 0], anchors, update(t, d) {
      const cnt = p.cnt ?? Math.min(1.3, d * 0.65); const v = (p.from ?? 0) + (p.to - (p.from ?? 0)) * E.outExpo(clamp(t / cnt)); cn.set(fmt(v, p.dec ?? 0, p.prefix ?? "", p.suffix ?? "")); const k = Math.max(0, 1 - (t - cnt) / 0.4);
      cn.group.scale.setScalar(1 + 0.08 * E.outCubic(k) * (t >= cnt ? 1 : 0)); const e = E.outBack(clamp(t / 0.4)); pl.scale.setScalar(Math.max(0.001, e)); tm.scale.setScalar(Math.max(0.001, e)); pl.rotation.y = Math.sin(t * 0.8) * 0.15; tm.rotation.y = pl.rotation.y;
      rg.forEach((r, i) => { const u = ((t * 0.7 + i / 3) % 1); r.scale.setScalar(0.8 + u * 1.2); r.material = basic(0xffffff, { opacity: 0.35 * (1 - u) }); }); }, hitAt: p.cnt ?? 1.0 };
};

// ---- gauge (purchase intent) ----
B.gauge = (p) => {
  const root = G(), N = 36, ticks = [], mats = []; const a0 = Math.PI * 1.15, a1 = -Math.PI * 0.15; const dial = G(); dial.position.y = 3.2; root.add(dial);
  for (let i = 0; i < 12; i++) mats.push(mc(new THREE.Color().setHSL(0.52 - 0.52 * (i / 11) * 0.95 + 0.0, 0.85, 0.55).getHex()));
  const off = mc(0x252f52);
  for (let i = 0; i < N; i++) { const a = lerp(a0, a1, i / (N - 1)); const b = bar(0.26, 0.4, 0xffffff); b.material = off; b.scale.y = 0.95; b.position.set(Math.cos(a) * 3.3, Math.sin(a) * 3.3, 0); b.rotation.z = a - Math.PI / 2; dial.add(b); ticks.push(b); }
  const needle = G(); const nb = bar(0.16, 0.16, 0xffffff); nb.scale.y = 2.9; needle.add(nb); const cap = new THREE.Mesh(new THREE.SphereGeometry(0.34, 18, 14), mc(0xffffff, { metal: true })); needle.add(cap); dial.add(needle);
  const cn = counter({ size: 1.25, mat: mc(0xffffff), depth: 0.25, max: 8 }); cn.group.position.set(0, -2.1, 0.4); dial.add(cn.group); const gl = glow(C.cyan, 13, 0.28); gl.position.set(0, 3.2, -1.5); root.add(gl);
  const anchors = { dial: dial, top: OB(0, 3.8, 0, dial), end: OB(Math.cos(a1) * 4.1, Math.sin(a1) * 4.1, 0, dial) }; const full = p.full ?? false;
  return { root, camD: 12, camH: 3.2, look: [0, 3.2, 0], anchors, update(t, d) {
      const cnt = p.cnt ?? Math.min(1.6, d * 0.7), v = clamp(E.outCubic(clamp(t / cnt))) * (p.value ?? 0.29); const shown = full ? v / (p.value ?? 0.29) : v / 0.5; const a = lerp(a0, a1, clamp(shown));
      needle.rotation.z = a - Math.PI / 2 + Math.sin(t * 18) * 0.006 * (1 - clamp(t / cnt)); const lit = Math.round(clamp(shown) * N); ticks.forEach((b, i) => { b.material = i < lit ? mats[Math.min(11, Math.floor((i / N) * 12))] : off; });
      cn.set(fmt(v * 100, 0, "", "%")); dial.rotation.y = Math.sin(t * 0.7) * 0.12; gl.material.opacity = 0.2 + 0.2 * clamp((t - cnt) / 0.3); }, hitAt: p.cnt ?? 1.2 };
};

// ---- gift box (bonus pack) ----
B.giftBox = (p) => {
  const root = G(), accent = p.color ?? C.pink; const g = G(); root.add(g); const body = plate(3, 2.4, 3, accent, { r: 0.12 }); body.position.y = 1.2; g.add(body);
  const lid = G(); lid.position.y = 2.7; const lp = plate(3.3, 0.6, 3.3, accent, { r: 0.1 }); lid.add(lp); g.add(lid);
  const rib1 = plate(0.5, 2.5, 3.05, C.gold, { r: 0.04, metal: true }); rib1.position.y = 1.2; g.add(rib1); const rib2 = plate(3.05, 2.5, 0.5, C.gold, { r: 0.04, metal: true }); rib2.position.y = 1.2; g.add(rib2);
  const rl = plate(0.5, 0.62, 3.35, C.gold, { r: 0.04, metal: true }); lid.add(rl); const rl2 = plate(3.35, 0.62, 0.5, C.gold, { r: 0.04, metal: true }); lid.add(rl2);
  [-1, 1].forEach((s) => { const lp2 = new THREE.Mesh(new THREE.TorusGeometry(0.55, 0.16, 10, 24), mc(C.gold, { metal: true })); lp2.position.set(s * 0.6, 0.65, 0); lp2.rotation.set(0, 0, s * 0.5); lid.add(lp2); });
  const gl = glow(accent, 14, 0.3); gl.position.set(0, 2.5, -1.5); root.add(gl); const cf = confetti(70, { seed: 8 }); root.add(cf.mesh); root.add(stage(5.2, accent));
  const tick = []; const cd = G(); cd.position.set(0, 2.5, -1.2); root.add(cd); for (let i = 0; i < 60; i++) { const a = (i / 60) * Math.PI * 2; const b = bar(0.07, 0.07, 0xffffff); b.material = basic(C.cyan); b.scale.y = 0.35; b.position.set(Math.sin(a) * 3.6, Math.cos(a) * 3.6, 0); b.rotation.z = -a; cd.add(b); tick.push(b); }
  const anchors = { box: g, ring: OB(3.9, 2.5, 0, root), under: OB(0, 0.4, 1.8, root) };
  return { root, camD: 12.5, camH: 3.2, look: [0, 2.3, 0], anchors, update(t, d) {
      const open = E.outBack(clamp((t - 0.45) / 0.45), 1.6); lid.position.y = 2.7 + open * 1.7; lid.rotation.z = open * 0.5; lid.rotation.x = open * 0.12; g.rotation.y = Math.sin(t * 0.8) * 0.3 + 0.2; g.position.y = (1 - E.outBack(clamp(t / 0.45))) * 3; cf.mesh.visible = t > 0.5; cf.update(t - 0.5);
      const lit = Math.round(60 * (1 - clamp((t - 0.2) / (d * 0.9)))); tick.forEach((b, i) => { b.scale.y = i < lit ? 0.35 : 0.12; b.material = i < lit ? basic(C.cyan) : basic(0x2a3a66); }); }, hitAt: 0.5 };
};

// ---- claim card (viral claim) with strike ----
B.claimCard = (p) => {
  const root = G(); const c = card(6.4, 3.8, (g, w, h) => { const lg = g.createLinearGradient(0, 0, w, h); lg.addColorStop(0, "#1b2450"); lg.addColorStop(1, "#0c1230"); g.fillStyle = lg; g.fillRect(0, 0, w, h);
    g.fillStyle = "#42d9f9"; fitPx(g, (p.kicker ?? "viral claim").toLowerCase(), w - 120, 54); g.fillText((p.kicker ?? "viral claim").toLowerCase(), 60, 90); g.fillStyle = "#fff"; fitPx(g, p.big, w - 120, 150); g.fillText(p.big, 60, 290); g.fillStyle = "#f5c542"; fitPx(g, p.sub ?? "", w - 120, 76); g.fillText(p.sub ?? "", 60, 430); }, { px: 160, depth: 0.2, edge: 0x42d9f9 });
  c.position.y = 3; root.add(c); const strike = plate(7.2, 0.34, 0.1, C.red, { r: 0.1 }); strike.position.set(0, 3.1, 0.25); strike.rotation.z = -0.1; strike.scale.x = 0.001; root.add(strike);
  const gl = glow(C.cyan, 14, 0.25); gl.position.set(0, 3, -2); root.add(gl); root.add(stage(5.6, C.cyan)); const anchors = { card: c, under: OB(0, 0.4, 1.6, root) };
  return { root, camD: 12.5, camH: 3, look: [0, 3, 0], anchors, update(t, d) { const e = E.outBack(clamp(t / 0.45), 1.2); c.scale.setScalar(Math.max(0.001, e)); c.rotation.y = Math.sin(t * 0.8) * 0.12 - 0.05; c.rotation.z = (1 - e) * 0.3;
      const sa = p.strikeAt; if (sa !== undefined) { const k = E.outCubic(clamp((t - sa) / 0.22)); strike.scale.x = Math.max(0.001, k); strike.rotation.y = c.rotation.y; } }, hitAt: p.strikeAt ?? 0.4 };
};

// ---- padlock closing (lock in the money) ----
B.lock = (p) => {
  const root = G(), lk = G(); lk.position.y = 2.2; root.add(lk); const body = plate(3, 2.4, 1.2, C.gold, { r: 0.3, metal: true }); body.position.y = -0.4; lk.add(body);
  const sh = G(); const arc = new THREE.Mesh(new THREE.TorusGeometry(0.95, 0.24, 14, 28, Math.PI), mc(0xdfe6ff, { metal: true })); arc.position.y = 0; sh.add(arc); [-0.95, 0.95].forEach((x) => { const leg = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 0.7, 14), mc(0xdfe6ff, { metal: true })); leg.position.set(x, -0.35, 0); sh.add(leg); }); sh.position.y = 0.8; lk.add(sh);
  const key = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.18, 0.1, 16), basic(0x30240a)); key.rotation.x = Math.PI / 2; key.position.set(0, -0.2, 0.62); lk.add(key); const slot = plate(0.12, 0.6, 0.1, 0x30240a, { r: 0.03, flat: true }); slot.position.set(0, -0.6, 0.62); lk.add(slot);
  const gl = glow(C.gold, 12, 0.35); gl.position.set(0, 2.2, -1.5); root.add(gl); const rain = coinRain(40, { seed: 6, area: [9, 8] }); root.add(rain.mesh); root.add(stage(5, C.gold)); const anchors = { lock: lk, under: OB(0, 0.4, 1.6, root) };
  return { root, camD: 11, camH: 3, look: [0, 2.4, 0], anchors, update(t, d) { const close = E.outBounce ? 0 : 0; const c = E.outBack(clamp((t - 0.55) / 0.3), 2.2); sh.position.y = 0.8 + (1 - c) * 0.75; sh.rotation.y = (1 - c) * 1.2; lk.rotation.y = Math.sin(t * 0.8) * 0.25; lk.position.y = 2.2 + (1 - E.outBack(clamp(t / 0.4))) * 3 + Math.sin(t * 1.4) * 0.05; rain.update(t, 1); gl.material.opacity = 0.25 + 0.3 * clamp((t - 0.7) / 0.2) * Math.exp(-(t - 0.7) * 2); }, hitAt: 0.75 };
};

// ---- guide book + laptop (the free guide) ----
B.guide = (p) => {
  const root = G(); const bookG = G(); root.add(bookG);
  const cover = canvasTex(640, 840, (g, w, h) => { const lg = g.createLinearGradient(0, 0, w, h); lg.addColorStop(0, "#1456d8"); lg.addColorStop(1, "#0a1f6b"); g.fillStyle = lg; g.fillRect(0, 0, w, h); g.fillStyle = "rgba(255,255,255,.12)"; g.beginPath(); g.arc(w * 0.85, h * 0.12, 190, 0, 7); g.fill();
    g.fillStyle = "#42d9f9"; g.font = '700 44px "Arimo"'; g.fillText("free guide", 48, 86); g.fillStyle = "#fff"; g.font = '700 74px "Arimo"'; const ls = ["guide to", "become an", "ai solopreneur", "in 90 days"]; ls.forEach((l, i) => { g.fillStyle = i === 2 ? "#f5c542" : "#fff"; g.fillText(l, 48, 300 + i * 92); }); g.fillStyle = "#42d9f9"; g.fillRect(48, 700, 220, 10); });
  const book = G(); const bb = plate(3.1, 4.1, 0.42, 0x0a1f6b, { r: 0.08 }); book.add(bb); const face = new THREE.Mesh(new THREE.PlaneGeometry(3.0, 3.99), new THREE.MeshBasicMaterial({ map: cover, toneMapped: false })); face.position.z = 0.215; book.add(face);
  const pages = plate(2.9, 3.9, 0.3, 0xf2f4fa, { r: 0.03, flat: true }); pages.position.set(0.1, 0, -0.1); book.add(pages); bookG.add(book); book.position.y = 2.3;
  const burst = G(); const bd = new THREE.Mesh(new THREE.CylinderGeometry(0.85, 0.85, 0.14, 32), mc(C.gold, { metal: true })); bd.rotation.x = Math.PI / 2; burst.add(bd); const ft = textRow("FREE", { size: 0.4, mat: mc(0x2a1a00), depth: 0.06 }); ft.group.position.set(0, -0.15, 0.1); burst.add(ft.group); burst.position.set(1.45, 4.0, 0.55); bookG.add(burst);
  const lap = G(); const lb = plate(4.6, 0.16, 3, 0x2b3352, { r: 0.08 }); lap.add(lb); const scr = G(); const sp = plate(4.6, 2.9, 0.12, 0x2b3352, { r: 0.1 }); scr.add(sp);
  const st = canvasTex(920, 580, (g, w, h) => { const lg = g.createLinearGradient(0, 0, w, h); lg.addColorStop(0, "#0b1a44"); lg.addColorStop(1, "#143a8a"); g.fillStyle = lg; g.fillRect(0, 0, w, h); g.fillStyle = "rgba(255,255,255,.16)"; for (let i = 0; i < 7; i++) { rr(g, 70 + (i % 2) * 110, 70 + i * 62, 380 + (i * 53) % 300, 34, 17); g.fill(); } g.fillStyle = "#42d9f9"; rr(g, 70, 500, 220, 46, 23); g.fill(); });
  const sf = new THREE.Mesh(new THREE.PlaneGeometry(4.3, 2.7), new THREE.MeshBasicMaterial({ map: st, toneMapped: false })); sf.position.z = 0.07; scr.add(sf); scr.position.set(0, 1.45, -1.45); scr.rotation.x = -0.28; lap.add(scr); lap.position.set(-0.2, 0, 0); lap.scale.setScalar(0.9); root.add(lap);
  const gl = glow(C.blue, 14, 0.38); gl.position.set(0, 2.6, -2); root.add(gl); const mt = glowCloud(); root.add(mt.group); root.add(stage(6, C.cyan));
  const mode = p.mode ?? "both"; const anchors = { book: bookG, laptop: lap, free: burst, under: OB(0, 0.3, 2, root) };
  return { root, camD: 12.5, camH: 3, look: [0, 2.3, 0], anchors, update(t, d) {
      const eb = E.outBack(clamp(t / 0.55), 1.3), el = E.outBack(clamp((t - 0.2) / 0.55), 1.3);
      bookG.visible = mode !== "laptop"; lap.visible = mode !== "book"; const both = mode === "both"; bookG.position.set(both ? 2.7 : 0, (1 - eb) * -3, both ? 0.8 : 0); bookG.scale.setScalar(Math.max(0.001, eb) * (both ? 0.9 : 1.05)); bookG.rotation.y = Math.sin(t * 0.9) * 0.28 - 0.3; book.position.y = 2.3 + Math.sin(t * 1.4) * 0.1;
      lap.position.set(both ? -2.6 : 0, (1 - el) * -3, both ? -0.2 : 0); lap.scale.setScalar(Math.max(0.001, el) * (both ? 0.82 : 1.0)); lap.rotation.y = Math.sin(t * 0.7 + 1) * 0.2 + 0.25; burst.rotation.z = Math.sin(t * 2) * 0.12; mt.update(t); } };
};
function glowCloud() { const g = G(); const R = rng(21); const items = []; for (let i = 0; i < 14; i++) { const s = glow(C.cyan, 0.5 + R() * 0.6, 0.8); s.position.set((R() - 0.5) * 11, R() * 6, (R() - 0.5) * 4 - 1); g.add(s); items.push(s); } return { group: g, update(t) { items.forEach((s, i) => { s.position.y += 0; s.material.opacity = 0.35 + 0.4 * Math.sin(t * 1.5 + i); }); } }; }

// ---- rumour cards flying (the $100 rumour) ----
B.rumors = (p) => {
  const root = G(), N = p.n ?? 16, texts = p.texts ?? ["$100?!", "leak", "$100", "outrage", "$100??", "thread", "$100!!", "rumor"]; const R = rng(p.seed ?? 12); const cs = [];
  for (let i = 0; i < N; i++) {
    const tx = texts[i % texts.length]; const c = card(2.2, 1.28, (g, w, h) => { g.fillStyle = i % 3 === 0 ? "#3a0f14" : "#1c1f36"; g.fillRect(0, 0, w, h); g.fillStyle = i % 3 === 0 ? "#ff6b6b" : "#c9d3ff"; g.textAlign = "center"; g.textBaseline = "middle"; fitPx(g, tx, w - 30, 118); g.fillText(tx, w / 2, h / 2 + 8); }, { px: 120, depth: 0.08, edge: i % 3 === 0 ? 0xe0262b : 0x42d9f9 });
    c.userData = { x: (R() - 0.5) * 13, y: 0.5 + R() * 5.5, z0: -9 - R() * 6, sp: 2.2 + R() * 2.2, rz: (R() - 0.5) * 0.5, ry: (R() - 0.5) * 0.7 }; root.add(c); cs.push(c);
  }
  const gl = glow(C.red, 18, 0.2); gl.position.set(0, 3, -6); root.add(gl);
  return { root, camD: 10, camH: 2.6, look: [0, 2.6, 0], rig: "drift", anchors: {}, update(t) { cs.forEach((c, i) => { const u = c.userData; const z = ((u.z0 + t * u.sp + 18) % 24) - 14; c.position.set(u.x, u.y + Math.sin(t + i) * 0.2, z); c.rotation.set(0, u.ry + t * 0.1, u.rz); const a = clamp((z + 14) / 4); c.visible = a > 0.02; c.scale.setScalar(Math.max(0.001, a)); }); } };
};

// ---- quote slab: huge 3D quote marks (DOM overlay carries the words) ----
B.quoteSlab = (p) => {
  const root = G(); const accent = p.color ?? C.cyan; const q1 = textRow("“".replace("“", '"'), { size: 1, mat: mc(accent, { metal: true }), depth: 0.5, center: true }); q1.group.position.set(-5.2, 3.6, -1); root.add(q1.group);
  const q2 = textRow('"', { size: 1, mat: mc(accent, { metal: true }), depth: 0.5, center: true }); q2.group.position.set(5.2, 0.4, -1); q2.group.rotation.z = Math.PI; root.add(q2.group);
  const gl = glow(accent, 18, 0.25); gl.position.set(0, 3, -3); root.add(gl); const mt = glowCloud(); root.add(mt.group);
  return { root, camD: 12, camH: 2.8, look: [0, 2.6, 0], rig: "drift", anchors: {}, update(t) { const e = E.outBack(clamp(t / 0.5)); q1.group.scale.setScalar(Math.max(0.001, 5.2 * e)); q2.group.scale.setScalar(Math.max(0.001, 5.2 * E.outBack(clamp((t - 0.15) / 0.5)))); q1.group.rotation.y = Math.sin(t * 0.8) * 0.25; q2.group.rotation.y = Math.sin(t * 0.8 + 1) * 0.25 + 0; mt.update(t); } };
};

// ---- score badge (99) with orbiting stars ----
B.score = (p) => {
  const root = G(), accent = p.color ?? C.green; const bd = G(); bd.position.y = 3; root.add(bd); const pl = plate(4.2, 4.2, 0.6, accent, { r: 0.9 }); bd.add(pl); const inner = plate(3.5, 3.5, 0.2, 0x0b3a26, { r: 0.7 }); inner.position.z = 0.32; bd.add(inner);
  const cn = counter({ size: 2.1, mat: mc(0xffffff), depth: 0.3, max: 4 }); cn.group.position.set(0, -0.78, 0.55); bd.add(cn.group); const stars = []; for (let i = 0; i < 8; i++) { const s = starMesh(0.34, C.gold); root.add(s); stars.push(s); }
  const gl = glow(accent, 14, 0.4); gl.position.set(0, 3, -1.5); root.add(gl); root.add(stage(5.4, accent)); const anchors = { badge: bd, under: OB(0, 0.4, 1.8, root), side: OB(3.4, 3, 0, root) };
  return { root, camD: 12, camH: 3, look: [0, 3, 0], anchors, update(t, d) { const cnt = p.cnt ?? 1.0; cn.set(fmt((p.value ?? 99) * E.outExpo(clamp(t / cnt)), 0, p.prefix ?? "")); const e = E.outBack(clamp(t / 0.4), 1.5); bd.scale.setScalar(Math.max(0.001, e)); bd.rotation.y = Math.sin(t * 0.9) * 0.2;
      stars.forEach((s, i) => { const a = t * 0.9 + (i / 8) * Math.PI * 2; s.position.set(Math.cos(a) * 3.9, 3 + Math.sin(a) * 1.0, Math.sin(a) * 1.6); s.rotation.set(0, t * 2 + i, 0); s.scale.setScalar(Math.max(0.001, E.outBack(clamp((t - 0.3 - i * 0.05) / 0.4)))); }); }, hitAt: p.cnt ?? 1.0 };
};

// ---- shelf of game boxes (count visible / slots) ----
B.shelf = (p) => {
  const root = G(), slots = p.slots ?? 10, cols = p.cols ?? 5, rows = Math.ceil(slots / cols), shown = p.count ?? slots; const boxes = [], ghost = []; const cs = [C.cyan, C.pink, C.violet, C.orange, C.green, C.blue, C.red, C.gold, C.B, C.D];
  for (let r = 0; r < rows; r++) { const board = plate(cols * 1.5 + 0.6, 0.18, 1.5, 0x1c2540, { r: 0.05 }); board.position.set(0, 1.6 + (rows - 1 - r) * 2.6 - 0.1, 0); root.add(board); }
  for (let i = 0; i < slots; i++) { const r = Math.floor(i / cols), c = i % cols; const x = (c - (cols - 1) / 2) * 1.5, y = 1.6 + (rows - 1 - r) * 2.6 + 0.85;
    const gh = plate(1.0, 1.55, 0.24, 0x232c4c, { r: 0.06, flat: true }); gh.position.set(x, y, 0); gh.material = basic(0x1a2240, { opacity: 0.55 }); root.add(gh); ghost.push(gh);
    const b = plate(1.0, 1.55, 0.24, cs[i % cs.length], { r: 0.07 }); b.position.set(x, y, 0); b.visible = i < shown; b.userData = { x, y }; root.add(b); boxes.push(b); }
  const anchors = { shelf: OB(0, 1.6 + rows * 1.3, 0, root), first: boxes[0], under: OB(0, 0.2, 1.8, root) }; const gl = glow(C.cyan, 16, 0.15); gl.position.set(0, 3, -3); root.add(gl);
  return { root, camD: 9.5, camH: 3.2, look: [0, 1.6 + (rows - 1) * 1.3 + 0.9, 0], rig: "drift", anchors, update(t, d) { boxes.forEach((b, i) => { if (i >= shown) return; let e = E.outBack(clamp((t - 0.1 - i * (p.step ?? 0.11)) / 0.35), 1.4); if (p.vanish && i >= (p.vanish.keep ?? 1)) { const v = E.inCubic(clamp((t - p.vanish.at - i * 0.06) / 0.4)); e *= 1 - v; b.rotation.z = v * 1.2; b.position.x = b.userData.x + v * (i % 2 ? 1.5 : -1.5); } b.scale.setScalar(Math.max(0.001, e)); b.position.y = b.userData.y + (1 - e) * 0.8; b.rotation.y = Math.sin(t + i) * 0.08; }); } };
};

// ---- fine-print document with magnifier and highlights ----
B.fineprint = (p) => {
  const root = G(); const rows = p.rows ?? ["Day One Retail Sales", "unaudited estimate", "includes pre-orders"]; const lineY = [3.7, 2.6, 1.5];
  const doc = card(5.6, 6.6, (g, w, h) => { g.fillStyle = "#f6f7fb"; g.fillRect(0, 0, w, h); g.fillStyle = "#222a44"; g.font = '700 46px "Arimo"'; g.fillText("financial results", 60, 90); g.fillStyle = "#c8cde0"; for (let i = 0; i < 4; i++) { rr(g, 60, 130 + i * 40, w - 120 - (i % 2) * 120, 16, 8); g.fill(); }
    rows.forEach((r, i) => { const y = 330 + i * 170; g.fillStyle = "#14192e"; g.font = '700 54px "Arimo"'; g.fillText(r, 70, y + 8); g.fillStyle = "#c8cde0"; rr(g, 70, y + 36, w - 150 - (i * 60), 14, 7); g.fill(); rr(g, 70, y + 62, w - 220, 14, 7); g.fill(); });
    g.fillStyle = "#c8cde0"; for (let i = 0; i < 3; i++) { rr(g, 60, 860 + i * 34, w - 120 - (i % 2) * 200, 14, 7); g.fill(); } }, { px: 150, depth: 0.12, edge: 0xdfe3ee, r: 0.08 });
  doc.position.y = 3.4; doc.rotation.y = -0.18; root.add(doc); const his = [];
  rows.forEach((r, i) => { const hy = hyOf(i); const h = plate(5.0, 0.62, 0.04, i === 0 ? 0xffe14d : 0x42d9f9, { r: 0.05, flat: true }); h.material = basic(i === 0 ? 0xffe14d : 0x42d9f9, { opacity: 0.55 }); h.position.set(0, hy, 0.1); h.scale.x = 0.001; doc.add(h); his.push(h); });
  const mag = G(); const lens = ring(0.8, 0.1, 0xdfe6ff, { mat: mc(0xdfe6ff, { metal: true }) }); mag.add(lens); const handle = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.13, 1.3, 12), mc(0x39455f)); handle.position.set(0.85, -0.85, 0); handle.rotation.z = Math.PI / 4; mag.add(handle); const lg = new THREE.Mesh(new THREE.CircleGeometry(0.76, 30), basic(0xffffff, { opacity: 0.12 })); mag.add(lg); mag.position.z = 0.4; doc.add(mag);
  const gl = glow(C.cyan, 14, 0.2); gl.position.set(0, 3.4, -2); root.add(gl); const anchors = { doc, row0: OB(2.9, hyOf(0), 0.2, doc), row1: OB(2.9, hyOf(1), 0.2, doc), row2: OB(2.9, hyOf(2), 0.2, doc) }; function hyOf(i) { return 3.3 - (318 + i * 170) / 150; }
  const hs = p.hs ?? rows.map((_, i) => 0.7 + i * 1.5);
  return { root, camD: 12, camH: 3.2, look: [0, 3.4, 0], anchors, update(t, d) { const e = E.outBack(clamp(t / 0.45), 1.1); doc.scale.setScalar(Math.max(0.001, e)); doc.rotation.y = -0.18 + Math.sin(t * 0.7) * 0.06;
      let cur = -1; rows.forEach((r, i) => { const k = E.outCubic(clamp((t - hs[i]) / 0.35)); his[i].scale.x = Math.max(0.001, k); if (k > 0) cur = i; }); const ti = Math.max(0, cur); const ty = hyOf(ti); mag.position.set(lerp(mag.position.x, 1.6, 1) + Math.sin(t * 2) * 0.06, ty + 0.0, 0.4); mag.position.x = 1.2 + Math.sin(t * 1.5) * 0.2; mag.scale.setScalar(Math.max(0.001, E.outBack(clamp((t - 0.35) / 0.3)))); } };
};

// ---- range bar (cost between two values) ----
B.range = (p) => {
  const root = G(), L = 11, ax = p.axisMax ?? 4; const track = plate(L + 0.6, 0.34, 0.5, 0x1b2444, { r: 0.12 }); track.position.y = 2; root.add(track);
  const fill = new THREE.Mesh(new THREE.BoxGeometry(1, 0.4, 0.55), mc(p.color ?? C.gold, { metal: true })); fill.position.y = 2; root.add(fill); const xo = (v) => -L / 2 + (v / ax) * L;
  const ticks = []; for (let v = 0; v <= ax; v++) { const tr = textRow(String(v) + (p.unit ?? "B"), { size: 0.5, mat: mc(0x9fb0e0), depth: 0.12 }); tr.group.position.set(xo(v), 0.9, 0.3); root.add(tr.group); const tk = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.5, 0.05), basic(0x5a6da8)); tk.position.set(xo(v), 1.6, 0.25); root.add(tk); ticks.push(tr); }
  const h1 = new THREE.Mesh(new THREE.SphereGeometry(0.42, 20, 16), mc(0xffffff)), h2 = new THREE.Mesh(new THREE.SphereGeometry(0.42, 20, 16), mc(0xffffff)); h1.position.y = h2.position.y = 2; root.add(h1, h2);
  const q = textRow("?", { size: 1.6, mat: mc(C.gold, { metal: true }), depth: 0.3 }); q.group.position.set(xo(ax) + 0.2, 3.8, 0); root.add(q.group); const gl = glow(p.color ?? C.gold, 15, 0.22); gl.position.set(0, 2.6, -2.5); root.add(gl);
  const anchors = { lo: OB(xo(p.min), 2.9, 0.3, root), hi: OB(xo(p.max), 2.9, 0.3, root), mid: OB(xo((p.min + p.max) / 2), 3.3, 0.3, root) };
  return { root, camD: 12.5, camH: 3, look: [0, 2.2, 0], rig: "drift", anchors, update(t, d) { const a = E.outCubic(clamp((t - 0.1) / 0.45)), b = E.outCubic(clamp((t - 0.5) / 1.0)); const lo = xo(p.min), hi = lerp(lo, xo(p.max), b); fill.scale.x = Math.max(0.001, (hi - lo)); fill.position.x = (lo + hi) / 2; h1.position.x = lo; h2.position.x = hi; h1.scale.setScalar(Math.max(0.001, a)); h2.scale.setScalar(Math.max(0.001, a)); q.group.scale.setScalar(Math.max(0.001, E.outBack(clamp((t - 1.5) / 0.4)))); q.group.position.y = 3.8 + Math.sin(t * 2.4) * 0.12; } };
};

// ---- dotted globe with pulsing pins ----
B.globe = (p) => {
  const root = G(), N = p.n ?? 1100; const gg = G(); gg.position.y = 3.2; root.add(gg); const core = new THREE.Mesh(new THREE.SphereGeometry(2.9, 36, 28), mc(0x0d1a3d, { flat: true })); gg.add(core);
  const dots = new THREE.InstancedMesh(new THREE.SphereGeometry(0.05, 6, 5), basic(0x6fd8ff), N); const d = new THREE.Object3D(); const ga = Math.PI * (3 - Math.sqrt(5)); for (let i = 0; i < N; i++) { const y = 1 - (i / (N - 1)) * 2, r = Math.sqrt(1 - y * y), th = ga * i; d.position.set(Math.cos(th) * r * 3.0, y * 3.0, Math.sin(th) * r * 3.0); d.updateMatrix(); dots.setMatrixAt(i, d.matrix); } gg.add(dots);
  const pins = []; const R = rng(p.seed ?? 31); for (let i = 0; i < 9; i++) { const y = (R() - 0.5) * 1.5, th = R() * 6.28, r = Math.sqrt(1 - y * y); const g = glow(C.gold, 0.9, 1); g.position.set(Math.cos(th) * r * 3.1, y * 3.1, Math.sin(th) * r * 3.1); gg.add(g); pins.push(g); }
  const ar = ring(3.7, 0.03, C.cyan); ar.rotation.x = 1.2; ar.position.y = 3.2; root.add(ar); const gl = glow(C.blue, 14, 0.3); gl.position.set(0, 3.2, -2); root.add(gl); const anchors = { globe: gg, under: OB(0, 0.2, 1.8, root), right: OB(4.4, 3.2, 0, root) };
  return { root, camD: 12, camH: 3.2, look: [0, 3.2, 0], anchors, update(t) { const e = E.outBack(clamp(t / 0.5)); gg.scale.setScalar(Math.max(0.001, e)); gg.rotation.y = t * 0.45; gg.rotation.z = 0.2; ar.rotation.z = t * 0.5; pins.forEach((g, i) => { g.material.opacity = 0.5 + 0.5 * Math.sin(t * 3 + i * 1.3); g.scale.setScalar(0.7 + 0.5 * Math.abs(Math.sin(t * 3 + i * 1.3))); }); } };
};

// ---- two "coming later" locked cards ----
B.comingLater = (p) => {
  const root = G(), items = p.items ?? ["online mode", "pc version"]; const cs = []; const anchors = {};
  items.forEach((it, i) => { const c = card(4.4, 2.8, (g, w, h) => { const lg = g.createLinearGradient(0, 0, w, h); lg.addColorStop(0, "#1b2450"); lg.addColorStop(1, "#0c1230"); g.fillStyle = lg; g.fillRect(0, 0, w, h); g.fillStyle = "#fff"; g.textAlign = "center"; fitPx(g, it, w - 80, 96); g.fillText(it, w / 2, h / 2 + 30); g.fillStyle = "#42d9f9"; fitPx(g, p.sub ?? "coming later", w - 80, 50); g.fillText(p.sub ?? "coming later", w / 2, h / 2 + 130); }, { px: 150, depth: 0.14, edge: 0x42d9f9 });
    const x = (i - (items.length - 1) / 2) * 5.4; c.position.set(x, 3, 0); root.add(c); cs.push(c); const lk = G(); const lb = plate(0.9, 0.75, 0.3, C.gold, { r: 0.15, metal: true }); lk.add(lb); const la = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.07, 10, 20, Math.PI), mc(0xdfe6ff, { metal: true })); la.position.y = 0.37; lk.add(la); lk.position.set(0, 1.5, 0.3); c.add(lk); anchors["card" + i] = c; anchors["lock" + i] = lk; });
  const gl = glow(C.cyan, 16, 0.22); gl.position.set(0, 3, -3); root.add(gl);
  return { root, camD: 13, camH: 2.8, look: [0, 3, 0], rig: "drift", anchors, update(t) { cs.forEach((c, i) => { const e = E.outBack(clamp((t - 0.1 - i * 0.35) / 0.5), 1.3); const sx = (i - (items.length - 1) / 2) * 5.4; c.position.x = sx + (1 - e) * (i ? 7 : -7); c.position.y = 3 + Math.sin(t * 1.2 + i) * 0.1; c.rotation.y = (1 - e) * 0.8 + Math.sin(t * 0.7 + i) * 0.1 - (i ? 0.1 : -0.1); }); } };
};

// ---- funnel: people in, customers out ----
B.funnel = (p) => {
  const root = G(), N = 70; const cone = new THREE.Mesh(new THREE.CylinderGeometry(3.2, 0.9, 3.2, 40, 1, true), new THREE.MeshMatcapMaterial({ matcap: mc(C.cyan).matcap, transparent: true, opacity: 0.5, side: THREE.DoubleSide, depthWrite: false })); cone.position.y = 3.6; root.add(cone);
  const rimr = ring(3.2, 0.06, C.cyan); rimr.rotation.x = Math.PI / 2; rimr.position.y = 5.2; root.add(rimr); const spout = new THREE.Mesh(new THREE.CylinderGeometry(0.9, 0.9, 1.2, 28, 1, true), new THREE.MeshMatcapMaterial({ matcap: mc(C.cyan).matcap, transparent: true, opacity: 0.45, side: THREE.DoubleSide, depthWrite: false })); spout.position.y = 1.4; root.add(spout);
  const im = new THREE.InstancedMesh(new THREE.SphereGeometry(0.16, 10, 8), new THREE.MeshBasicMaterial({ toneMapped: false }), N); const R = rng(p.seed ?? 17); const P = []; for (let i = 0; i < N; i++) P.push({ x: (R() - 0.5) * 5.4, z: (R() - 0.5) * 3, ph: R() * 8, sp: 0.9 + R() * 0.5 });
  root.add(im); const d = new THREE.Object3D(); const cA = new THREE.Color(0xe4ecff), cB = new THREE.Color(C.gold); const coins = coinRain(16, { area: [1.2, 3], seed: 2, speed: 1.6, size: 0.3 }); coins.mesh.position.set(0, -0.6, 0.4); root.add(coins.mesh);
  const gl = glow(C.gold, 6, 0.0); gl.position.set(0, 0.8, 0.5); root.add(gl); const anchors = { top: OB(0, 6.4, 0, root), out: OB(0, 0.2, 1.4, root) }; root.add(stage(4.6, C.cyan));
  return { root, camD: 12, camH: 4, look: [0, 3, 0], anchors, update(t) { for (let i = 0; i < N; i++) { const q = P[i]; const u = ((t * q.sp * 0.38 + q.ph) % 8) / 8; const y = lerp(8.2, 0.4, u); const f = clamp((6.0 - y) / 3.2); const x = q.x * (1 - 0.85 * f), z = q.z * (1 - 0.85 * f); d.position.set(x, y, z); d.scale.setScalar(1 - 0.4 * f); d.updateMatrix(); im.setMatrixAt(i, d.matrix); im.setColorAt(i, cA.clone().lerp(cB, clamp((3.4 - y) / 1.8))); } im.instanceMatrix.needsUpdate = true; if (im.instanceColor) im.instanceColor.needsUpdate = true; coins.update(t, clamp((t - 0.6) / 0.5)); gl.material.opacity = 0.5 * clamp((t - 0.4) / 0.6); } };
};

// ---- coin stack (grows) / split (a share slides away) ----
B.stack = (p) => {
  const root = G(), N = p.n ?? 36, hc = 0.14; const piles = N >= 30 ? 3 : 1; const cnt = piles === 3 ? [Math.ceil(N * 0.42), Math.ceil(N * 0.33), 0] : [N]; if (piles === 3) cnt[2] = N - cnt[0] - cnt[1]; const px = piles === 3 ? [-2.1, 0.1, 2.2] : [0]; const zs = piles === 3 ? [0, 0.6, -0.4] : [0];
  const order = []; const maxL = Math.max(...cnt); for (let l = 0; l < maxL; l++) for (let k = 0; k < piles; k++) if (l < cnt[k]) order.push({ k, l });
  const im = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.5, 0.5, 0.12, 28), mc(C.gold, { metal: true }), N); root.add(im); const d = new THREE.Object3D(); const cs = p.scale ?? 5.0; const away = Math.round(N * (p.pct ?? 0) / 100); const topH = maxL * hc * 0.9;
  const gl = glow(C.gold, 14, 0.3); gl.position.set(0, 2.4, -2.5); root.add(gl); root.add(stage(piles === 3 ? 6.4 : 5.2, C.gold)); const rain = piles === 3 ? coinRain(24, { area: [8, 8], seed: 12, size: 0.3 }) : null; if (rain) root.add(rain.mesh);
  const anchors = { top: OB(px[0], topH + 0.8, 0, root), gone: OB(5.4, 3.0, 0, root), under: OB(0, 0.3, 1.8, root) };
  return { root, camD: p.camD ?? 13, camH: 3.4, look: [0, Math.min(3, topH * 0.5), 0], rig: p.rig ?? "rise", anchors, update(t, d_) {
      const gt = p.growT ?? 1.3; for (let i = 0; i < N; i++) { const o = order[i]; const t0 = (i / N) * gt, e = E.outBack(clamp((t - t0) / 0.3), 1.1); let x = px[o.k] + Math.sin(i * 1.7) * 0.03, y = 0.1 + o.l * hc * 0.9 + (1 - e) * 2.5, z = zs[o.k] + Math.cos(i * 1.3) * 0.03, sc = cs * 0.34 * Math.max(0.001, e);
        if (i >= N - away) { const k = E.inOutCubic(clamp((t - (p.splitAt ?? 1.6) - (N - 1 - i) * 0.04) / 0.9)); x += k * (5.4 - px[o.k]); y += Math.sin(k * Math.PI) * 2.6 - k * 0.4; sc *= 1 - 0.3 * k; }
        d.position.set(x, y, z); d.rotation.set(0, i * 0.4, 0); d.scale.setScalar(sc); d.updateMatrix(); im.setMatrixAt(i, d.matrix); } im.instanceMatrix.needsUpdate = true; if (rain) rain.update(t, clamp((t - 0.5) / 0.5)); }, hitAt: p.splitAt ?? 1.2 };
};

// ---- 24-hour clock ----
B.clock24 = (p) => {
  const root = G(), cg = G(); cg.position.y = 3.2; root.add(cg); const face = disc(3.4, 0.3, 0x0e1530); face.rotation.x = Math.PI / 2; cg.add(face); const ticks = [];
  for (let i = 0; i < 24; i++) { const a = (i / 24) * Math.PI * 2; const b = bar(0.12, 0.12, 0xffffff); b.material = basic(0x3a4a80); b.scale.y = i % 6 === 0 ? 0.55 : 0.32; b.position.set(Math.sin(a) * 2.95, Math.cos(a) * 2.95, 0.2); b.rotation.z = -a; cg.add(b); ticks.push(b); }
  const hand = G(); const hb = bar(0.16, 0.12, C.cyan); hb.scale.y = 2.6; hand.add(hb); const cap = new THREE.Mesh(new THREE.SphereGeometry(0.25, 14, 12), mc(0xffffff)); hand.add(cap); hand.position.z = 0.3; cg.add(hand);
  const rg = ring(3.5, 0.08, C.cyan); cg.add(rg); const cn = counter({ size: 1.1, mat: mc(0xffffff), depth: 0.2, max: 6 }); cn.group.position.set(0, -1.2, 0.35); cg.add(cn.group); const gl = glow(C.cyan, 14, 0.3); gl.position.set(0, 3.2, -1.5); root.add(gl);
  const anchors = { clock: cg, under: OB(0, 0.4, 1.8, root) };
  return { root, camD: 12, camH: 3.2, look: [0, 3.2, 0], anchors, update(t, d) { const sw = p.sweep ?? Math.min(2.0, d * 0.85); const u = E.inOutCubic(clamp(t / sw)); hand.rotation.z = -u * Math.PI * 2; const lit = Math.round(u * 24); ticks.forEach((b, i) => { b.material = i < lit ? basic(C.cyan) : basic(0x3a4a80); }); cn.set(fmt(24 * u, 0, "", "h")); const e = E.outBack(clamp(t / 0.4)); cg.scale.setScalar(Math.max(0.001, e)); cg.rotation.y = Math.sin(t * 0.8) * 0.14; }, hitAt: p.sweep ?? 1.6 };
};

// ---- gold torus knot (loop / endless run) ----
B.loop = (p) => {
  const root = G(); const knot = new THREE.Mesh(new THREE.TorusKnotGeometry(2.1, 0.55, 140, 14, 2, 3), mc(C.gold, { metal: true })); knot.position.y = 3.2; root.add(knot);
  const gl = glow(C.gold, 15, 0.35); gl.position.set(0, 3.2, -2); root.add(gl); const rain = coinRain(36, { seed: 9 }); root.add(rain.mesh); root.add(stage(5.6, C.gold)); const anchors = { knot, under: OB(0, 0.4, 1.8, root) };
  return { root, camD: 12, camH: 3.2, look: [0, 3.2, 0], anchors, update(t) { const e = E.outBack(clamp(t / 0.5)); knot.scale.setScalar(Math.max(0.001, e)); knot.rotation.set(t * 0.5, t * 0.8, 0); rain.update(t, 1); } };
};
