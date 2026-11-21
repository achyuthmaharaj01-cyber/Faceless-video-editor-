# Reference video 7 — measured analysis

Title (from the file name): **Every Level Of Watches**

> The measured sections below are produced by `scripts/reference-analysis/analyze_reference.py` and
> `synthesize.py`. Qualitative observations are in the `## Observations` section, written from the contact sheets.

## Technical metadata

| Duration | Resolution | FPS | Aspect | Video | Audio | Bitrate |
|---|---|---|---|---|---|---|
| 11:55.31 | 1280×720 | 60.0 | 16:9 | h264 Main | aac 2 ch 44100 Hz | 1787 kb/s |

## Editing rhythm

- Shots: **332**, **27.76 cuts/min**
- Shot length: median **1.77 s**, mean 2.15 s, 10th pct 0.93 s, 90th pct 3.69 s, longest 10.9 s
- Distribution: <1s: 40, 1-2s: 151, 2-3s: 83, 3-5s: 41, 5-8s: 14, 8s+: 3
- Dissolve-like (soft, multi-frame) transitions: 124 — almost every change is a hard cut or a fast motion transition
- Fastest 30 s windows: 06:30.00–07:00.00 (21 cuts), 07:00.00–07:30.00 (21 cuts), 04:30.00–05:00.00 (19 cuts)
- Slowest 30 s windows: 11:00.00–11:30.00 (8 cuts), 07:30.00–08:00.00 (9 cuts), 03:30.00–04:00.00 (10 cuts)
- Longest holds: 03:55.80 (10.9 s, static), 10:15.50 (9.8 s, static), 03:47.40 (8.4 s, static), 03:01.20 (7.5 s, static), 11:22.37 (7.4 s, static)

## Camera movement (optical-flow classification per shot)

| Motion | Share of shots |
|---|---|
| static | 63.0% |
| internal-motion | 13.9% |
| push-in | 13.3% |
| pull-out | 4.5% |
| pan-right | 3.0% |
| pan-left | 1.2% |
| tilt-up | 0.6% |
| tilt-down | 0.6% |

- Example push-in: 00:15.87 (2.0 s), 02:01.37 (2.2 s), 02:17.33 (2.0 s), 03:08.67 (2.1 s)
- Example internal-motion: 00:33.13 (1.8 s), 00:53.83 (2.3 s), 01:08.63 (3.0 s), 01:55.90 (2.1 s)
- Example pull-out: 00:48.67 (2.7 s), 01:49.03 (1.6 s), 05:52.47 (3.2 s), 06:11.10 (2.1 s)
- Example pan-right: 01:28.30 (2.2 s), 05:55.63 (3.0 s), 05:58.67 (2.6 s)
- Example tilt-down: 04:54.27 (1.7 s)
- Example pan-left: 06:58.57 (2.0 s), 09:44.33 (1.9 s)

## Narration ↔ picture

- Narration pace: **165.2 words/min**; speech covers 75% of the running time; 146 pauses > 0.4 s
- **84%** of cuts fall within 0.25 s of a word boundary; 28% within 0.4 s of a sentence end
- 1.82 cuts per spoken sentence on average (182 sentences)

## Sound

- Integrated loudness **-16.1 LUFS**, LRA 5.6 LU, true peak 0.4 dBTP
- 745 transient onsets (62.5 per minute); **30%** of cuts have a transient within 100 ms (SFX / music hits on cuts)
- Average level in seconds with speech -25.1 dB vs without speech -49.2 dB (music/SFX bed level in pauses)

## Colour

- Mean brightness 126.6/255, mean saturation 64.5/255
- Dominant colours: `#110c0f` 18% `#352d2e` 17% `#fbf9fb` 16% `#59504f` 15% `#7e797b` 10% `#aea199` 10% `#ccc8c8` 8% `#a66647` 4%

## Files

- Contact sheets and frames (private, not in Git): `reference-library/video-7/contact-sheets/`
- Shot list and per-frame metrics: `data/video-7/shots.json`

## Observations

<!-- qualitative notes for video 7 are maintained in timestamped-observations.md and the guides -->
