import { fitPx, advTab, THREE, C, E, clamp, lerp, prog, rng, mc, basic, glow, ring, disc, bar, plate, slice, card, canvasTex, wrapText, textRow, counter, fmt, coinRain, confetti, stage, crowd, V3, sstep } from "./kit.js";

export const A = {};
const G = () => new THREE.Group();
const place = (o, x = 0, y = 0, z = 0) => { o.position.set(x, y, z); return o; };

// ---- 1. big counting number with coins / confetti ----
A.bigNumber = (p) => {
  const root = G(), gold = p.color === "gold"; const _fs = fmt(p.to, p.dec ?? 0, p.prefix ?? "", p.suffix ?? ""); let _w = 0; for (const ch of _fs) _w += advTab(ch); const size = Math.min(p.size ?? 1.9, 2.4, 10.4 / _w);
  const mat = gold ? mc(C.gold, { metal: true }) : mc(p.hex ?? 0xffffff, { metal: !!p.metal });
  const cn = counter({ size, mat, depth: 0.34, max: 14 }); cn.group.position.set(0, 1.9, 0); root.add(cn.group); const cy = 1.9 + size * 0.5;
  const accent = p.glow ?? C.cyan; const gl = glow(accent, 15, 0.5); gl.position.set(0, cy, -2.4); root.add(gl);
  const g1 = ring(4.4, 0.045, accent), g2 = ring(5.2, 0.03, accent, { mat: basic(accent, { opacity: 0.5 }) }); g1.position.set(0, cy, -1.8); g2.position.set(0, cy, -2.2); root.add(g1, g2);
  const st = stage(6.2, accent); root.add(st);
  let rain = null; if (p.particles === "coins") { rain = coinRain(60, { seed: p.seed ?? 3 }); root.add(rain.mesh); } else if (p.particles === "confetti") { rain = confetti(110, { seed: p.seed ?? 5 }); root.add(rain.mesh); }
  const under = new THREE.Object3D(); under.position.set(0, 0.55, 1.2); root.add(under); const above = new THREE.Object3D(); above.position.set(0, 1.9 + size + 0.5, 0); root.add(above);
  const left = new THREE.Object3D(); left.position.set(-5.2, 2.5, 0); root.add(left);
  return { root, camD: 11, camH: 2.8, look: [0, 2.2, 0], anchors: { num: cn.group, under, above, left },
    update(t, d) {
      const cnt = p.cnt ?? Math.min(1.25, d * 0.62), from = p.from ?? 0, to = p.to; const v = from + (to - from) * E.outExpo(clamp(t / cnt));
      cn.set(fmt(v, p.dec ?? 0, p.prefix ?? "", p.suffix ?? "")); const enter = E.outBack(clamp(t / 0.3)); const k = Math.max(0, 1 - (t - cnt) / 0.45);
      cn.group.scale.setScalar(size * (0.55 + 0.45 * enter) * (1 + 0.09 * E.outCubic(k) * (t >= cnt ? 1 : 0))); cn.group.rotation.y = Math.sin(t * 0.9) * 0.16 - 0.08;
      g1.rotation.set(t * 0.4, 0, t * 0.25); g2.rotation.set(-t * 0.3, t * 0.2, 0); gl.material.opacity = 0.35 + 0.2 * Math.sin(t * 2) + 0.35 * k;
      if (rain) rain.update(t, clamp((t - cnt * 0.6) / 0.4)); },
    hitAt: (p.cnt ?? 1.0) };
};

// ---- 2. bars / stacks comparison ----
A.compare = (p) => {
  const root = G(), items = p.items, n = items.length; const bw = p.bw ?? (n <= 2 ? 2.2 : n <= 4 ? 1.7 : 1.3), gap = p.gap ?? (n <= 2 ? 1.7 : n <= 4 ? 1.4 : 0.8), Hmax = p.h ?? 3.9; const max = p.max ?? Math.max(...items.map((i) => i.value));
  const bars = [], texts = [], anchors = {}; const total = n * bw + (n - 1) * gap;
  const base = plate(total + 2, 0.3, 3, 0x0e1428, { r: 0.1 }); base.position.set(0, -0.15, 0); root.add(base);
  const edge = new THREE.Mesh(new THREE.BoxGeometry(total + 2, 0.04, 0.04), basic(C.cyan)); edge.position.set(0, 0.01, 1.5); root.add(edge);
  items.forEach((it, i) => {
    const x = -total / 2 + bw / 2 + i * (bw + gap); const b = bar(bw, bw * 0.9, it.color ?? C.cyan, { metal: it.metal }); b.position.set(x, 0, 0); b.scale.y = 0.001; root.add(b); bars.push(b);
    const _vw = textRow(it.vlabel ?? "", { size: 1 }).width || 0.01; const tr = textRow(it.vlabel ?? "", { size: Math.min(it.vsize ?? 0.62, (bw + gap) * 0.92 / _vw), mat: mc(0xffffff), depth: 0.2 }); tr.group.position.set(x, 0, bw * 0.45 + 0.1); root.add(tr.group); texts.push(tr.group);
    const top = new THREE.Object3D(); top.position.set(x, 0, bw * 0.5); root.add(top); anchors["top" + i] = top; const bs = new THREE.Object3D(); bs.position.set(x, 0.1, bw * 0.55); root.add(bs); anchors["base" + i] = bs;
    if (it.glow) { const gl = glow(it.color ?? C.cyan, bw * 3.2, 0.35); gl.position.set(x, Hmax * 0.5, -1); root.add(gl); it._gl = gl; }
  });
  const dust = G(); root.add(dust);
  return { root, camD: p.camD ?? 15, camH: 3.2, look: [0, Hmax * 0.52, 0], anchors,
    update(t, d) {
      items.forEach((it, i) => { const t0 = 0.15 + i * (p.stagger ?? 0.35), gd = p.grow ?? 0.9; const h = Math.max(0.001, (it.value / max) * Hmax * E.outCubic(clamp((t - t0) / gd)));
        bars[i].scale.y = h; const tg = texts[i]; tg.position.y = h + 0.55; const sc = E.outBack(clamp((t - t0 - gd * 0.75) / 0.3)); tg.scale.setScalar(Math.max(0.001, sc)); anchors["top" + i].position.y = h + 0.1; if (it._gl) it._gl.position.y = h * 0.6; }); } };
};

// ---- 3. timeline with travelling playhead ----
A.timeline = (p) => {
  const root = G(), nodes = p.nodes, n = nodes.length, sp = p.spacing ?? 4.2; const x0 = -((n - 1) * sp) / 2; const anchors = {};
  const beam = plate((n - 1) * sp + 6, 0.16, 0.16, 0x1a2a55, { r: 0.05 }); beam.position.y = 1; root.add(beam);
  const lit = new THREE.Mesh(new THREE.BoxGeometry(1, 0.1, 0.1), basic(C.cyan)); lit.position.y = 1; root.add(lit);
  const discs = [], labels = [];
  nodes.forEach((nd, i) => {
    const x = x0 + i * sp; const dsk = new THREE.Mesh(new THREE.SphereGeometry(0.34, 20, 16), mc(0x3a4566)); dsk.position.set(x, 1, 0); root.add(dsk); discs.push(dsk);
    const tr = textRow(nd.year ?? "", { size: nd.size ?? 1.1, mat: mc(nd.color ?? 0xffffff), depth: 0.3 }); tr.group.position.set(x, 2.5, 0); root.add(tr.group); labels.push(tr.group);
    const a = new THREE.Object3D(); a.position.set(x, 0.1, 0.5); root.add(a); anchors["node" + i] = a; const a2 = new THREE.Object3D(); a2.position.set(x, 3.6, 0); root.add(a2); anchors["top" + i] = a2;
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, 1.1, 6), basic(0x2a3a66)); pole.position.set(x, 1.75, 0); root.add(pole);
  });
  const head = glow(C.cyan, 2.4, 0.95); head.position.set(x0, 1, 0.3); root.add(head); const headBall = new THREE.Mesh(new THREE.SphereGeometry(0.2, 14, 12), basic(0xffffff)); root.add(headBall);
  const xs = nodes.map((_, i) => x0 + i * sp); const colorOf = (nd) => nd.color ?? C.cyan;
  return { root, anchors, camera(cam, t, d) { const u = E.inOutSine(clamp(t / d)); const hx = lerp(xs[0], xs[n - 1], u); cam.position.set(hx, 2.6, (p.camD ?? 12.5) - u * 1.2); cam.lookAt(hx, 1.9, 0); cam.fov = 38; },
    update(t, d) { const lead = p.lead ?? 0.12; const u = clamp((t - lead) / (d - lead - 0.1)); const hx = lerp(xs[0], xs[n - 1], E.inOutSine(u)); head.position.x = hx; headBall.position.set(hx, 1, 0.3);
      lit.scale.x = Math.max(0.01, hx - xs[0] + 0.3); lit.position.x = (xs[0] - 0.3 + hx) / 2 + 0.0;
      nodes.forEach((nd, i) => { const reached = hx >= xs[i] - 0.05 || n === 1; const k = reached ? 1 : 0; const pulse = reached ? E.outBack(clamp((hx - xs[i] + 0.05) / 0.5)) : 0;
        discs[i].material = reached ? mc(colorOf(nd)) : mc(0x3a4566); discs[i].scale.setScalar(1 + 0.45 * pulse * (1 - 0.35 * pulse)); labels[i].scale.setScalar(Math.max(0.001, E.outBack(clamp((hx - xs[i] + 0.9) / 0.5))) * (nd.size ? 1 : 1)); labels[i].position.y = 2.5 + 0.12 * Math.sin(t * 2 + i); }); } };
};

// ---- 4. calendar page ----
A.calendar = (p) => {
  const root = G(); const accent = p.accent ?? C.red; const pg = G(); root.add(pg);
  const body = plate(4.6, 5.0, 0.3, 0xf4f6fb, { r: 0.18, flat: true }); body.position.y = 2.5; pg.add(body);
  const head = plate(4.6, 1.25, 0.34, accent, { r: 0.16 }); head.position.set(0, 4.37, 0.02); pg.add(head);
  const mo = textRow(p.month ?? "JUN", { size: 0.7, mat: mc(0xffffff), depth: 0.18 }); mo.group.position.set(0, 4.02, 0.28); pg.add(mo.group);
  const dayTxt = textRow(p.day ?? "25", { size: p.daySize ?? 1.75, mat: mc(0x151a2e), depth: 0.3 }); dayTxt.group.position.set(0, 1.25, 0.3); pg.add(dayTxt.group);
  if (p.year) { const yr = textRow(p.year, { size: 0.5, mat: mc(0x6a7390), depth: 0.12 }); yr.group.position.set(0, 0.32, 0.22); pg.add(yr.group); }
  [-1.2, 1.2].forEach((x) => { const rg = ring(0.2, 0.06, 0xdfe3ee); rg.position.set(x, 5.05, 0.1); rg.rotation.x = Math.PI / 2; pg.add(rg); });
  const gl = glow(accent, 11, 0.32); gl.position.set(0, 2.6, -1.5); root.add(gl); root.add(stage(5.4, accent === C.red ? C.cyan : accent));
  const anchors = { card: pg }; const side = new THREE.Object3D(); side.position.set(3.2, 3, 0); pg.add(side); anchors.side = side; const sl = new THREE.Object3D(); sl.position.set(-3.2, 3, 0); pg.add(sl); anchors.sideL = sl;
  return { root, camD: 11.5, camH: 3, look: [0, 2.6, 0], anchors, update(t, d) { const e = clamp(t / 0.5); pg.rotation.x = (1 - E.outBack(e, 1.2)) * -1.2; pg.position.y = (1 - E.outCubic(e)) * 3; pg.rotation.y = Math.sin(t * 0.9) * 0.12 - 0.05; pg.position.y += Math.sin(t * 1.3) * 0.06; }, hitAt: 0.35 };
};

// ---- 5. hanging price tag ----
A.priceTag = (p) => {
  const root = G(); const accent = p.color ?? C.cyan; const pivot = G(); pivot.position.y = 6; root.add(pivot);
  const s = new THREE.Shape(); s.moveTo(-1.9, -1.35); s.lineTo(1.9, -1.35); s.lineTo(1.9, 0.7); s.lineTo(1.0, 1.55); s.lineTo(-1.0, 1.55); s.lineTo(-1.9, 0.7); s.closePath();
  const hole = new THREE.Path(); hole.absarc(0, 1.05, 0.2, 0, Math.PI * 2, true); s.holes.push(hole);
  const geo = new THREE.ExtrudeGeometry(s, { depth: 0.22, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.06, bevelSegments: 3, curveSegments: 12 }); geo.translate(0, 0, -0.11);
  const tag = new THREE.Mesh(geo, mc(accent, { metal: !!p.metal })); const tg = G(); tg.position.y = -3.6; tg.add(tag); pivot.add(tg);
  const _pw = textRow(p.price, { size: 1 }).width; const price = textRow(p.price, { size: Math.min(p.size ?? 1.25, 3.2 / _pw), mat: mc(0x0b1228), depth: 0.2 }); price.group.position.set(0, -0.15, 0.2); tg.add(price.group);
  if (p.sub) { const _sw = textRow(p.sub, { size: 1 }).width; const sub = textRow(p.sub, { size: Math.min(0.42, 3.3 / _sw), mat: mc(0x0b1228), depth: 0.1 }); sub.group.position.set(0, -0.95, 0.2); tg.add(sub.group); }
  const string = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 2.6, 6), basic(0xdfe6ff)); string.position.set(0, -1.3, 0); pivot.add(string);
  const gl = glow(accent, 12, 0.35); gl.position.set(0, 2.5, -2); root.add(gl); const anchors = { tag: tg, below: place(new THREE.Object3D(), 0, 0.5, 1) }; root.add(anchors.below); const sd = new THREE.Object3D(); sd.position.set(2.3, 0, 0); tg.add(sd); anchors.side = sd; const sl = new THREE.Object3D(); sl.position.set(-2.3, 0, 0); tg.add(sl); anchors.sideL = sl;
  return { root, camD: 12, camH: 2.4, look: [0, 2.6, 0], anchors, update(t, d) { const e = clamp(t / 0.55); pivot.position.y = 6 + (1 - E.outBack(e, 1.4)) * 5; const amp = 0.5 * Math.exp(-t * 0.9); pivot.rotation.z = amp * Math.cos(t * 4.6); pivot.rotation.y = Math.sin(t * 0.8) * 0.18; gl.material.opacity = 0.25 + 0.1 * Math.sin(t * 2); }, hitAt: 0.35 };
};

// ---- 6. donut with highlighted share ----
A.donut = (p) => {
  const root = G(), N = 60, lit = Math.round((p.pct / 100) * N), r0 = 1.9, r1 = 3.2; const segs = []; const a0 = Math.PI / 2; const col = p.color ?? C.cyan, rest = p.rest ?? 0x26304f;
  const g = G(); g.rotation.x = -0.35; root.add(g);
  for (let i = 0; i < N; i++) { const aa = a0 - (i / N) * Math.PI * 2, bb = a0 - ((i + 0.94) / N) * Math.PI * 2; const s = slice(r0, r1, bb, aa, 0.7, i < lit ? col : rest, { metal: false }); s.userData.mid = (aa + bb) / 2; s.userData.lit = i < lit; g.add(s); segs.push(s); }
  const cn = counter({ size: 1.05, mat: mc(0xffffff), depth: 0.2, max: 6 }); cn.group.position.set(0, -0.35, 0.55); g.add(cn.group);
  const gl = glow(col, 12, 0.3); gl.position.set(0, 0, -2); root.add(gl); const anchors = {}; const mid = a0 - (lit / N) * Math.PI;
  const am = new THREE.Object3D(); am.position.set(Math.cos(mid) * (r1 + 0.9), Math.sin(mid) * (r1 + 0.9), 0.3); g.add(am); anchors.slice = am; const ar = new THREE.Object3D(); ar.position.set(-(r1 + 0.6), 0, 0.3); g.add(ar); anchors.rest = ar;
  root.position.y = 3.2;
  return { root, camD: 12.5, camH: 3.2, look: [0, 3.2, 0], anchors, update(t, d) {
      const rev = clamp((t - 0.1) / 1.0); const shown = Math.floor(N * E.outCubic(rev));
      segs.forEach((s, i) => { const on = i < shown || !s.userData.lit && rev > 0.1; const k = E.outBack(clamp((rev * N - i * (s.userData.lit ? 1 : 0.25) + 3) / 6)); s.scale.setScalar(Math.max(0.001, s.userData.lit ? k : 1)); const out = s.userData.lit && p.explode ? 0.5 * E.outCubic(clamp((t - 0.9) / 0.5)) : 0; s.position.set(Math.cos(s.userData.mid) * out, Math.sin(s.userData.mid) * out, 0); });
      cn.set(fmt(p.pct * E.outCubic(rev), p.dec ?? 0, "", "%")); g.rotation.y = Math.sin(t * 0.7) * 0.2; }, hitAt: 1.0 };
};

// ---- 7. takeaway statement (3D text lines, letters fly in) ----
A.statement = (p) => {
  const root = G(), lines = p.lines, n = lines.length; const accent = p.accent ?? C.cyan; const maxW = p.maxW ?? 9.6; const rows = []; const size0 = p.size ?? 0.95; const lh = p.lh ?? 1.25;
  lines.forEach((ln, i) => {
    const probe = textRow(ln, { size: 1, mat: mc(0xffffff), depth: 0.25 }); const sc = Math.min(size0, maxW / probe.width); const tr = textRow(ln, { size: sc, mat: mc(i === (p.hi ?? -1) ? C.gold : 0xffffff, { metal: i === (p.hi ?? -1) }), depth: 0.25 });
    tr.group.position.y = ((n - 1) / 2 - i) * lh * 1.18 * (size0 / 0.95) + 2.6; root.add(tr.group); rows.push({ tr, sc, i });
  });
  const bw = 0.001; const underline = new THREE.Mesh(new THREE.BoxGeometry(1, 0.07, 0.07), basic(accent)); underline.position.set(0, 2.6 - (n / 2) * lh * 1.18 * (size0 / 0.95) - 0.15, 0); root.add(underline);
  const strike = p.strike ? plate(1, 0.16, 0.12, C.red, { r: 0.05 }) : null; if (strike) { strike.position.set(0, rows[p.strike.line].tr.group.position.y + 0.32, 0.4); strike.rotation.z = -0.03; root.add(strike); }
  const gl = glow(accent, 16, 0.28); gl.position.set(0, 2.6, -3); root.add(gl); root.add(stage(7, accent)); const widest = Math.max(...rows.map((r) => r.tr.width));
  return { root, camD: 12.5, camH: 2.8, look: [0, 2.6, 0], anchors: {}, rig: "drift", update(t, d) {
      rows.forEach((r) => { r.tr.chars.forEach((m, k) => { const t0 = (p.lineAt ? p.lineAt[r.i] : 0.1 + r.i * 0.4) + k * 0.022; const e = E.outCubic(clamp((t - t0) / 0.38)); m.position.y = (1 - e) * -1.2 / r.sc * 0.4; m.rotation.x = (1 - e) * -1.1; m.scale.setScalar(Math.max(0.001, 0.4 + 0.6 * e)); }); r.tr.group.position.x = Math.sin(t * 0.5 + r.i) * 0.06; });
      underline.scale.x = Math.max(0.001, widest * E.outCubic(clamp((t - 0.5) / 0.7))); gl.material.opacity = 0.2 + 0.08 * Math.sin(t * 1.8);
      if (strike) { const k = E.outCubic(clamp((t - p.strike.at) / 0.25)); strike.scale.x = Math.max(0.001, rows[p.strike.line].tr.width * 1.08 * k); rows[p.strike.line].tr.chars.forEach((m) => (m.material = k > 0.5 ? mc(0x6a7390) : m.material)); } } };
};
