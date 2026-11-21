// faceless-video-studio 3D blocks: a set of boxes (shipping containers, crates, bars...) that land one by one,
// with a slow camera dolly. Pure function of composition time: every frame is drawn from the `hf-seek`
// event's time (HyperFrames runtime contract), with seeded per-box variation. No clock, no rAF.
import * as THREE from '../vendor/three.module.min.js';

function mulberry32(a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
const ease = x => 1 - Math.pow(1 - Math.min(1, Math.max(0, x)), 3);
const PALETTE = ['#b5462f', '#2f5d8a', '#3c7a4a', '#d9772b', '#7a7f87', '#a33a3a', '#c9a227', '#2e7f86'];

const scenes = [];
// Each 3D scene's sub-composition calls mount(canvas) from its own module script once it is mounted.
export function mount(canvas) {
  if (!canvas || canvas.__fvs3d) return;
  canvas.__fvs3d = true;
  const cfg = JSON.parse(canvas.getAttribute('data-fvs3d'));
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: true });
  renderer.setPixelRatio(1);
  renderer.setSize(canvas.width, canvas.height, false);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(32, canvas.width / canvas.height, 0.1, 200);
  scene.add(new THREE.HemisphereLight(0xffffff, 0xb8b0a0, 1.6));
  const key = new THREE.DirectionalLight(0xfff1dd, 2.2); key.position.set(6, 12, 8); scene.add(key);
  const rim = new THREE.DirectionalLight(0xbcd4ff, 0.8); rim.position.set(-8, 5, -6); scene.add(rim);
  // studio floor that fades into the page's studio background (no visible horizon)
  const bg = new THREE.Color(cfg.background || '#ecebe8');
  scene.fog = new THREE.Fog(bg, 30, 90);
  const floor = new THREE.Mesh(new THREE.CircleGeometry(400, 64), new THREE.MeshLambertMaterial({ color: bg }));
  floor.rotation.x = -Math.PI / 2; scene.add(floor);
  renderer.setClearColor(bg, 1);

  const rnd = mulberry32(cfg.seed || 58);
  const geo = new THREE.BoxGeometry(2.35, 1, 1.05);
  const edges = new THREE.EdgesGeometry(geo);
  const boxes = [];
  const cols = cfg.cols, layers = Math.max(1, Math.ceil(cfg.count / (cols * 3)));
  const perLayer = Math.ceil(cfg.count / layers), rows = Math.ceil(perLayer / cols);
  for (let i = 0; i < cfg.count; i++) {
    const layer = Math.floor(i / perLayer), k = i % perLayer, r = Math.floor(k / cols), c = k % cols;
    const color = (cfg.palette || PALETTE)[Math.floor(rnd() * (cfg.palette || PALETTE).length)];
    const m = new THREE.Mesh(geo, new THREE.MeshLambertMaterial({ color }));
    m.add(new THREE.LineSegments(edges, new THREE.LineBasicMaterial({ color: 0x1a1a1a, transparent: true, opacity: 0.35 })));
    const target = new THREE.Vector3((c - (cols - 1) / 2) * 2.5, 0.5 + layer * 1.02, (r - (rows - 1) / 2) * 1.15);
    scene.add(m);
    boxes.push({ m, target, delay: (i / cfg.count) * 0.85 + rnd() * 0.08, spin: (rnd() - 0.5) * 0.6 });
  }
  // auto framing: fit the grid's footprint in the lower two-thirds of the frame (room for a title above)
  const span = Math.max(cols * 2.5, rows * 1.15 * 1.6, 6);
  const dist = span / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2))) / camera.aspect * 1.2;
  const from = new THREE.Vector3(...(cfg.cameraFrom || [dist * 0.32, dist * 0.6, dist * 1.0]));
  const to = new THREE.Vector3(...(cfg.cameraTo || [dist * 0.18, dist * 0.48, dist * 0.86]));
  const look = new THREE.Vector3(0, 1.6 + layers * 0.4, 0);

  function draw(t) {
    const span = Math.max(0.001, cfg.end - cfg.start);
    const u = (t - cfg.start) / span;
    camera.position.copy(from).lerp(to, ease(u * 0.9));
    camera.lookAt(look);
    const g = (t - cfg.growAt) / cfg.growDuration;
    for (const b of boxes) {
      const p = ease((g - b.delay) / 0.18);
      b.m.visible = p > 0;
      b.m.position.set(b.target.x, b.target.y + (1 - p) * 7, b.target.z);
      b.m.rotation.y = (1 - p) * b.spin;
    }
    renderer.render(scene, camera);
  }
  scenes.push({ cfg, draw });
  const now = window.__player && typeof window.__player.getTime === 'function' ? window.__player.getTime() : cfg.start;
  draw(Math.min(cfg.end, Math.max(cfg.start, now)));
}

// HyperFrames dispatches `hf-seek` with the composition time on every seek (preview, VideoHub adapter, render).
window.addEventListener('hf-seek', e => {
  const t = e.detail && typeof e.detail.time === 'number' ? e.detail.time : 0;
  for (const s of scenes) if (t >= s.cfg.start - 0.05 && t <= s.cfg.end + 0.05) s.draw(t);
});
