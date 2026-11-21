# Transitions guide

Measured: only **1–2% of picture changes are soft (dissolve-like, multi-frame)**. Everything else is a hard cut
or a very short motion transition (2–5 frames of motion blur). Transition strips (`contact-sheets/transitions-*.jpg`)
show the typical whip: the outgoing frame smears sideways for 2–3 frames and the incoming frame arrives smeared
(e.g. video 8 at 00:00.10 → 00:00.13, 00:12.90).

| Transition | Share (est.) | Use | fvs |
|---|---|---|---|
| Hard cut | ≈ 90% | default, on the word | `cut` |
| Whip (directional blur 0.12–0.2 s) | ≈ 5–8% | new segment, new list item, change of place | `whip-left`, `whip-right`, `whip-up` (+ whoosh) |
| Zoom-through | rare | into a detail / into a graphic (map, number) | `zoom` (+ whoosh) |
| Flash | rare | reveal, shock, verdict | `flash` (+ impact) |
| Fade from black | very rare | chapter break, ending | `fade` |
| Slow dissolve | ~never | — | not offered |

Rules:
1. Default to `cut`. Use a motion transition **only at segment boundaries** (paragraph change, new list item,
   change of place/time) — the draft storyboard uses `whip-left` at paragraph changes.
2. Every motion transition gets a sound (whoosh/swish); hard cuts mostly don't.
3. Don't chain motion transitions: two whips in a row read as a slideshow.
4. Graphic-to-graphic changes (map → map, board → board) can morph instead of cut: animate within one scene.
