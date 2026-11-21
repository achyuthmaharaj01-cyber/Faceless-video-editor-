# Colour and composition guide

## Colour

Measured per video (`video-N-analysis.md` → Colour): mean brightness and saturation are moderate; palettes are
dominated by the source photography, with graphics adding a small set of signal colours.

| Signal colour | Meaning | Token |
|---|---|---|
| Red `#e8262b` | attention: arrows, highlights, warnings, emphasis words | `--accent` |
| Green `#3ee060` (+ glow) | money, gains | `--money` |
| White | neutral information (labels) | `--ink` |
| Studio white/grey gradient | cutouts, 3D objects | `--studio` |
| Map: sky-blue sea, flat green land | geography (a recognisable channel look; fvs uses its own tints) | `--sea`, `--land` |
| Tier colours (red → orange → yellow → green) | ranking boards | built into `ranking` |

Grades: **B&W** for the past / negative turns, **B&W + red graphic** for "failed/forbidden", vignette on almost
every photo, heavy vignette or blurred surround for insets.

## Composition

- Subject on a third; the label sits in the negative space next to it; the arrow points from the label to the
  subject.
- Full-bleed photography is the default; insets (picture-in-picture) for screenshots, vertical clips and
  low-resolution sources.
- Foreground/background separation: cutouts with drop shadows on studio gradients; labels above everything.
- Visual hierarchy per frame: 1 subject, 1 text element (2 at most), 1 pointer.
- Home-base graphics (map, ranking board) use flat colours and a clear grid: they are the calm frames between
  busy photographic sequences.
- Vertical sources (phone clips) are never stretched: centred inset with a dark/blurred surround.
