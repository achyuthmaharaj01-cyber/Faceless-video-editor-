// Real-photo scenes (tier-list look): the licensed photo fills the frame, slow eased push/pull, labels/captions/badges
// come from the shared overlay system. Images are decoded before the first render (engine.js preload) so render(t) stays pure.
import { THREE, E, clamp } from "./kit.js";
export const Cx = {};
const FOV = 36, DIST = 10, VH = 2 * DIST * Math.tan((FOV / 2) * Math.PI / 180), VW = VH * 16 / 9;   // plane that exactly fills the frame at z=0

Cx.photo = (p, shot) => {
  const root = new THREE.Group(); const img = window.__imgs && window.__imgs[p.src];
  if (!img) throw new Error("photo not preloaded: " + p.src + " (shot " + shot.id + ")");
  const tex = new THREE.Texture(img); tex.colorSpace = THREE.SRGBColorSpace; tex.generateMipmaps = false; tex.minFilter = THREE.LinearFilter; tex.magFilter = THREE.LinearFilter; tex.needsUpdate = true;
  const mat = new THREE.MeshBasicMaterial({ map: tex, toneMapped: false, depthWrite: false });
  const plane = new THREE.Mesh(new THREE.PlaneGeometry(VW, VH), mat); root.add(plane);
  const zoom = p.zoom ?? 0.11, mode = p.motion || "push", panx = p.pan ?? 0;   // push: 1 -> 1+zoom, pull: 1+zoom -> 1
  return { root, noDust: true,
    camera(cam, t, d) {
      const u = E.inOutSine(clamp(t / Math.max(d, 0.1))), k = mode === "pull" ? 1 + zoom * (1 - u) : mode === "static" ? 1 : 1 + zoom * u;
      cam.position.set(panx * (u - 0.5) * VW * zoom * 0.5, 0, DIST / k); cam.lookAt(cam.position.x, 0, 0); cam.fov = FOV;
    },
    update() {} };
};
