# VideoHub integration

VideoHub (github.com/TensaikunYT/Videohub, inspected at commit `2302ba8`) is the mandatory review step. It is a
**local** app (Node server on 127.0.0.1:7788 + MCP tools); it previews a film by loading a page in an iframe and
calling `window.renderOut(t)`.

## The compatibility problem and the adapter

| VideoHub expects (`docs/PROJECT-CONTRACT.md` §2) | HyperFrames provides |
|---|---|
| `window.renderOut(t)` draws second *t* synchronously | runtime `window.__player.renderSeek(t)` — the producer's own export-seek path (pauses the clock, seeks GSAP + frame adapters, applies clip windows, syncs media, paints VFX) |
| `window.READY = true` when loaded | `window.__playerReady` + `window.__renderReady` |
| pure function of *t* | HyperFrames' determinism contract (same) |
| page served from the project folder | `index.html` + runtime injected by the CLI at preview/render time |

They are **not directly compatible**: a HyperFrames `index.html` does not contain the runtime, and VideoHub does not
inject it. `lib/videohub/build-preview.mjs` therefore generates `preview/videohub.html` from the real `index.html`:

1. `<base href="../">` (so every relative path resolves from the project root — the page must live in `preview/`
   because a second root-level composition file makes HyperFrames lint fail with `multiple_root_compositions`);
2. the `data-hyperframes-text-rendering` rule HyperFrames' compiler injects (`text-rendering: geometricPrecision`)
   — without it glyphs land 1 px differently from the render;
3. `window.__FVS_PREVIEW__` (size, fps, duration, a hash of `index.html`, the scene list);
4. the HyperFrames runtime from the pinned package (`node_modules/hyperframes/dist/hyperframe.runtime.iife.js`, copied
   to `preview/hf-runtime.js`);
5. the adapter (`lib/videohub/vh-adapter.js`), **inlined** because VideoHub's static check looks for `renderOut` in
   the page or a script beside it (it does not honour `<base>`).

The adapter maps `renderOut(t)` → `__player.renderSeek(t)`, waits for the runtime gates, fonts and media before
`READY`, mutes page media (VideoHub plays `audio/mix.wav` itself), publishes `VH_SCENES` for the scene lane and
`VH_CONFIG` for size/fps, and **refuses to preview a stale page** (if `index.html` changed after generation it sets
`__vhError`, which VideoHub shows as an error toast).

`fvs build` and `fvs preview` also write `.videohub/project.json` (merged; keys VideoHub or the user set are kept):
`live {page, audio, dur, fps}`, `transcript {file: audio/words.json}`, `render {script: render.mjs, env.DUR, mux}`, and
a generated `render.mjs` so VideoHub's 🎬 Render button runs **HyperFrames** (`fvs render --source videohub`), hands
the MP4 back as one chunk and copies its streams (`mux`) — VideoHub never re-encodes or replaces HyperFrames.

## Verified (in this repository's test session, Linux, scratch hub on port 7799)

- `hub_live` opens the film (12 sub-compositions, 44.4 s); the UI shows the composition, the **Scenes** lane (12
  scenes), the **Text** row (word-aligned narration), and **Voice / Music / Effects** stem rows with waveforms.
- Frame stepping is exact: 300 × → = frame 300 = composition time 10.000 s; play/pause follow VideoHub's clock.
- Preview = render: frames drawn through `renderOut` are **pixel-identical** to `hyperframes snapshot` at 8 times
  across the film plus 3 inside the Three.js scene (`fvs verify-preview`).
- Notes: a drawn box note at frame 300 was read with `hub_notes` (time, frame, narration «whole trailer on board?»);
  `fvs notes` mapped it to storyboard scene `sc04`; the revision rebuilt `compositions/s04.html`; VideoHub reloaded
  in place at the same frame; `hub_note_update` marked it fixed; "Check fixes" listed it.
- Render button: VideoHub's queue ran `render.mjs` → HyperFrames → 1920×1080 30 fps H.264/AAC, registered as `v1`.

## Known limitation: note pictures

VideoHub cuts a live note's picture from the page's `<canvas>` elements. HyperFrames compositions are DOM, so the
picture VideoHub saves shows only the drawing on black. **`fvs notes` fixes this**: it captures the note's exact
frame with HyperFrames (`hyperframes snapshot`), redraws the user's shapes (stored as normalised vectors in
`notes.json`), recuts the close-up and writes them into the note's picture files (originals kept as
`*.vhblank.jpg`). VideoHub's own thumbnail may show the black version until the browser reloads it.

Other preview-only differences: a seeked `<video>` element shows its new frame a few milliseconds after
`renderOut` returns (browser decode; the export engine pre-extracts frames). DOM, images, SVG, canvas, WebGL and
GSAP motion are exact.

## Installing VideoHub (Windows laptop)

1. Download/clone github.com/TensaikunYT/Videohub to a permanent folder, e.g. `C:\Users\<you>\VideoHub`.
2. Double-click `SETUP.cmd` (or `node scripts/install.mjs setup --agents claude`). Choose the workspace; its
   `films` folder is where projects should live (`FVS_WORKSPACE`).
3. Restart Claude Code; `claude mcp list` should show `videohub`. Without MCP the same tools run as
   `node <VideoHub>\server\cli.js <tool> "<json>"`.
4. `fvs doctor` checks it (`VIDEOHUB_DIR`).

Security: VideoHub listens on 127.0.0.1 only and its render queue can run commands — **never expose port 7788**
(no port forwarding, tunnels or 0.0.0.0 proxies). Remote review: docs/remote-review.md.
