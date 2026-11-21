# HyperFrames implementation notes (agent reference)

Facts established by reading the HyperFrames source (commit 7fcc490, CLI 0.9.77) and testing:
- `index.html` does not contain the runtime; preview/render inject `hyperframe.runtime.iife.js` at head start.
- In-page API after load: `window.__player` (`renderSeek`, `seek`, `getTime`, `getDuration`, …), `__playerReady`,
  `__renderReady`, `__timelines`. `__hf.seek` exists only inside the producer's render bridge.
- `__player.renderSeek(t)` = the export capture path: synchronous, deterministic, snaps to the composition fps.
- The compiler injects `<style data-hyperframes-text-rendering>html,body,*{text-rendering:geometricPrecision}</style>`.
- Sub-compositions: `<template>` files mounted from `data-composition-src`; the host element is replaced on mount
  (attributes on the host are not visible to page scripts later); timing inside is local.
- `hf-seek` events carry the composition time (`e.detail.time`) on every seek — use them for Three.js/canvas.
- Lint: one root composition file per project; nested DOM in timeline elements should be sub-compositions.
- Capture browser flags: `--font-render-hinting=none --disable-lcd-text --force-color-profile=srgb`, SwiftShader GL.
- Three.js r16x+ `three.module.min.js` imports `./three.core.min.js` — vendor both.
User-facing guide: docs/hyperframes-integration.md.
