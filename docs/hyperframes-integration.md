# HyperFrames integration

HyperFrames (github.com/heygen-com/hyperframes; npm `hyperframes`, pinned **0.9.77**) is the only composition and
rendering engine. No Remotion, no second framework.

## Project layout produced by `fvs build`

```
<project>/
  index.html               root composition: one host per scene + the audio mix + root timeline (flashes)
  compositions/sNN.html    one HyperFrames sub-composition per storyboard scene (<template>, own timeline, local time)
  components/fvs-motion.js motion interpreter: FVS_RUN({id, motion}) → paused GSAP timeline registered last
  components/fvs-blocks3d.js  Three.js scene module, drawn from the runtime's `hf-seek` time
  styles/base.css          tokens, components, local @font-face (Inter, Anton, Bebas Neue, Playfair Display, Caveat — SIL OFL)
  vendor/                  gsap.min.js, three.module.min.js, three.core.min.js (no CDN at render time)
  fonts/ assets/ audio/    media; audio/mix.wav is the film's sound
  hyperframes.json
  preview/videohub.html    generated VideoHub page (docs/videohub-integration.md)
```

## Rules followed (from the HyperFrames docs and its authoring skill)

- Timing in HTML (`data-start`, `data-duration`, `data-composition-src`); motion in scripts, at absolute seconds
  with `fromTo`; one paused timeline per composition registered in `window.__timelines[id]` **after** it is built.
- Sub-composition timing is local; scene hosts carry the absolute start.
- Deterministic: no `Date.now`, no `requestAnimationFrame`, seeded randomness (mulberry32), Three.js drawn from
  `hf-seek` (`e.detail.time`), counters via a tween's `onUpdate`.
- Text CSS matches what the compiler injects (`text-rendering: geometricPrecision`).
- One root composition file: the VideoHub page lives in `preview/` (lint error `multiple_root_compositions`).
- `npx hyperframes lint <project>`: 0 errors expected.

## Commands used

| Purpose | Command |
|---|---|
| lint | `npx hyperframes lint <project>` |
| look at frames (no render) | `npx hyperframes snapshot <project> --at 1.5,4.2 --no-end` |
| parity with the VideoHub preview | `fvs verify-preview <project>` |
| final render (after approval) | `fvs render <project>` → `hyperframes render <project> -o renders/<title>_vN.mp4 --fps 30 -q looks -w 2 --no-best-effort` |
| low-memory laptop render | `fvs render <project> --low-memory` (adds `--low-memory-mode`) |
| distributed cloud render | `npx hyperframes cloudrun …` / `lambda …` (see docs/cloud-architecture.md) |

`--no-best-effort` makes a render fail on missing or unready media instead of silently producing a broken frame.

## Measured performance (this cloud container: 4 vCPU Xeon @ 2.1 GHz, 16 GB, no GPU)

| Task | Time |
|---|---|
| `fvs build` (12 scenes, mix, preview page) | ≈ 4.7 s |
| `hyperframes snapshot` of 12 frames | ≈ 15 s |
| `hyperframes render` 6 s test film, 1080p30 (VideoHub queue) | 23 s total job |
| `renderOut` per frame in VideoHub (production film) | 4–8 ms |

The 44 s sample film was not rendered at final quality in this session: rendering needs the user's approval (see
docs/test-report.md). Laptop (i5-1335U, 16 GB) numbers must be measured there: `npx hyperframes benchmark <project>`.
