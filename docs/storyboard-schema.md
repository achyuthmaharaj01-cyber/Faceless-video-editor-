# Storyboard schema (`storyboard/storyboard.json`)

```jsonc
{
  "version": 1,
  "duration": 44.41,                       // = voiceover length (checked)
  "style": { "tokens": { "accent": "#e8262b" } },   // CSS token overrides for this film
  "music": { "track": "procedural" | "none" | "<asset id or file>", "mood": "curious|tense|uplifting|dramatic",
             "gain_db": -20, "duck_db": 12, "offset": 0 },
  "audio": { "limiter": false, "limiterApprovedBy": null },   // limiter only with the user's approval
  "scenes": [ { …scene… } ]
}
```

## Scene

| Field | Meaning |
|---|---|
| `id`, `title` | stable id (`sc01`) and a short name (VideoHub scene lane) |
| `start`, `end` | seconds; scenes are contiguous, start at 0, end at the voiceover length |
| `sentences` | indices of the script sentences spoken in this scene (order is checked) |
| `narration` | the spoken words (for humans and QC) |
| `purpose`, `technique` | why this scene exists and which style-guide technique it uses |
| `visual` | the base picture (below) |
| `layers` | overlays (below) |
| `transition_in` | `cut` (default) · `whip-left` · `whip-right` · `whip-up` · `zoom` · `flash` · `fade` |
| `sfx` | extra cues `[{cue, at, gain_db}]` — components add their own cues automatically |
| `assets` | media this scene needs: `[{id, kind: image|video|audio, query, need, pick?, sources?, original?}]` |
| `status`, `revisions` | draft/refined and the review history |

**Times** (`at`, `until`, …): a number (absolute seconds), `"@word"` / `"@two words"` (when that word is spoken inside
the scene; `"@word+0.2"` offsets), or `"+1.5"` (scene start + 1.5 s).

**Positions** are fractions of the frame `[x, y]` (0–1).

## Visual types

| type | options |
|---|---|
| `photo` | `asset`, `move` (push-in, pull-out, pan-left, pan-right, tilt-up, tilt-down, push-fast, drift, static), `focus [x,y]`, `grade` (bw, bw-red), `vignette` |
| `inset` | `asset`, `move` — framed over a blurred dark copy (screenshots, vertical clips) |
| `video` | `asset`, `from` (seconds into the clip), `move` |
| `solid` | `background` (CSS colour/gradient) |
| `title` | `text`, `sub`, `size`, `background` |
| `kinetic` | `text` (words appear when spoken; `sync: even` to space them), `size`, `top`, `color`, `background` or `asset` |
| `stat` | `value`, `from`, `prefix`, `suffix`, `decimals`, `compact`, `money`, `sub`, `at`, `duration`, `size`, `top`, `asset`+`dim` or `background` |
| `map` | `from`/`focus` `{lat, lon, zoom}`, `zoomDuration`, `pins [{lat, lon, label, at, size}]`, `route [[lat, lon]…]`, `routeAt`, `routeDuration`, `highlight [country names]`, `labelStyle` |
| `timeline` | `events [{year, label, text, at}]`, `background` |
| `document` | `headline`, `highlight` (phrase), `highlightAt`, `source`, `lines`, `tilt`, `asset` (blurred background) |
| `ranking` | `rows ["S","A",…]`, `items [{asset, row, label, at}]` |
| `cutout` | `asset`, `shape` (round/rect), `size`, `x`, `y`, `background` |
| `collage` | `tiles [{asset, label, at}]` |
| `comparison` | `left {asset, label, grade}`, `right {asset, label, grade, at}`, `vs` |
| `blocks3d` | `count`, `cols`, `palette`, `growAt`, `growDuration`, `cameraFrom`, `cameraTo` (Three.js) |
| `custom` | `composition` (`compositions/<file>.html`, a hand-made HyperFrames sub-composition), `compositionId` |

## Layer types

| type | options |
|---|---|
| `label` | `text`, `position`, `anchor` (left/center/right), `style` (plain, money, alert, dark, pin), `size`, `at`, `until`, `reveal: words`, `rotate`, `lowercase`, `sfx` |
| `arrow` | `from [x,y]`, `to [x,y]`, `width`, `color`, `at`, `until`, `label {…label…}` |
| `captions` | `at`, `until` — the narration words of that span, each shown as spoken |
| `image` | `asset`, `position`, `width`, `aspect`, `round`, `at` |
| `pricetag` | `price`, `name`, `asset` (thumbnail), `position`, `at` |
| `hand` | `text`, `position`, `size`, `rotate`, `dark`, `at`, `to [x,y]` (adds an arrow) |
| `meter` | `fraction`, `label`, `position`, `width`, `at`, `duration` |

`fvs storyboard-check` validates all of this; `fvs build` refuses a storyboard that fails the check.
