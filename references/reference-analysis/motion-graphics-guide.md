# Motion graphics guide

## Principles

- Graphics serve the narration: they appear **on the spoken word** and get out of the way.
- Entrances are short and springy (0.15–0.3 s, `back.out` / `power3.out`); exits are cuts, not animations.
- Motion inside a held shot keeps it alive: a slow camera push (≈ 10–15% over the shot), a counter, an appearing
  layer. Measured: 40–64% of reference shots are static frames, but most of them carry an appearing layer.
- Everything is deterministic (seekable): GSAP timelines at absolute times, seeded randomness, Three.js drawn
  from HyperFrames' seek time. See `references/hyperframes/` and the HyperFrames determinism docs.

## Component reference (fvs)

| Component | Motion | Timing default | Use |
|---|---|---|---|
| `label` | scale 0.8→1 + fade, 0.16 s `back.out(2.5)`; or `reveal: words` (each word when spoken) | at `@word` | names, places, money on objects |
| `arrow` | grows from its tail, 0.18 s `power3.out` | at `@word` | point at the detail that matters |
| `pricetag` | slides in 40 px + fade, 0.25 s | at `@price` | price + name of an object |
| `hand` | handwriting wipe (clip-path) 0.35 s, optional arrow | at `@word` | asides, jokes, small facts |
| `meter` | fill scaleX 0→fraction over 1–1.2 s `power2.out` | at `@figure` | progress, share, "how much of" |
| `stat` | count-up 1.1–1.4 s `power2.out` (tabular figures), impact at the end | at `@figure` | the hero number |
| `kinetic` | words drop in on speech, 0.22 s `back.out(2)` | each word | hooks, questions, punchlines |
| `map` | camera zoom 2–3 s `power2.inOut`; pins pop `back.out(3)`; route draws `power1.inOut` | pins at `@place` | locations, journeys |
| `timeline` | line draws, ticks pop per event | per event | dates, eras |
| `document` | card slides up with a slight rotation, highlighter wipe on the phrase | highlight at `@word` | quotes, claims |
| `ranking` | items fly in and land in their row with a thud | per item | list videos' home base |
| `cutout` | spring scale-in + gentle sway | scene start | studio product/person shots |
| `collage` | tiles pop in sequence (0.18 s apart) | | enumerations |
| `comparison` | left owns the frame, split opens on the contrasting word | right at `@word` | before/after, refused/adapted |
| `inset` | frame scales in over a blurred, darkened copy | | screenshots, vertical clips |
| `blocks3d` | Three.js: boxes land in sequence, slow camera dolly | grow at `@figure` | quantity you can count |

## Camera movement

| Move | Reference share | When |
|---|---|---|
| static | 40–64% | screenshots, documents, boards, talking moments, punchlines |
| push-in | 10–22% | reveals, tension, focusing on a detail (set `focus: [x, y]`) |
| pull-out | 5–13% | context ("and this is just one of…"), endings |
| pan / tilt | 2–8% | wide landscapes, tall buildings (tilt-up for scale) |

fvs camera presets: `push-in`, `pull-out`, `pan-left`, `pan-right`, `tilt-up`, `tilt-down`, `push-fast`, `drift`,
`static` (storyboard `visual.move`).

## 3D

Use Three.js only when the third dimension carries information: counting physical objects, scale, an object's
form. The references use simple white-studio 3D (big extruded number block, money stacks); `blocks3d` follows
that look: soft studio floor fading into the background, warm key + cool rim light, no orbiting.

## Parallax and layering

- Background photo with camera move + foreground labels that do *not* move with the camera.
- Cutouts on a studio gradient get drop shadows (depth) and a slight independent sway.
