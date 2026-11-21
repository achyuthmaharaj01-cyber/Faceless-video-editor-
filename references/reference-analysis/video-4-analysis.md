# Reference video 4 — measured analysis

Title (from the file name): **Billionaires Who Hate Each Other**

> The measured sections below are produced by `scripts/reference-analysis/analyze_reference.py` and
> `synthesize.py`. Qualitative observations are in the `## Observations` section, written from the contact sheets.

## Technical metadata

| Duration | Resolution | FPS | Aspect | Video | Audio | Bitrate |
|---|---|---|---|---|---|---|
| 31:25.13 | 1280×720 | 60.0 | 16:9 | h264 Main | aac 2 ch 44100 Hz | 1561 kb/s |

## Editing rhythm

- Shots: **657**, **20.88 cuts/min**
- Shot length: median **1.97 s**, mean 2.87 s, 10th pct 0.5 s, 90th pct 5.1 s, longest 114.43 s
- Distribution: <1s: 126, 1-2s: 208, 2-3s: 139, 3-5s: 114, 5-8s: 50, 8s+: 20
- Dissolve-like (soft, multi-frame) transitions: 131 — almost every change is a hard cut or a fast motion transition
- Fastest 30 s windows: 02:00.00–02:30.00 (25 cuts), 19:00.00–19:30.00 (21 cuts), 07:00.00–07:30.00 (20 cuts)
- Slowest 30 s windows: 11:00.00–11:30.00 (0 cuts), 10:00.00–10:30.00 (0 cuts), 10:30.00–11:00.00 (0 cuts)
- Longest holds: 09:37.50 (114.4 s, static), 20:22.33 (105.2 s, static), 25:01.67 (19.0 s, static), 29:18.43 (19.0 s, static), 13:47.87 (16.0 s, static)

## Camera movement (optical-flow classification per shot)

| Motion | Share of shots |
|---|---|
| static | 65.9% |
| internal-motion | 14.0% |
| push-in | 7.6% |
| pull-out | 6.8% |
| pan-right | 2.3% |
| pan-left | 2.1% |
| tilt-down | 0.9% |
| tilt-up | 0.3% |

- Example pull-out: 00:00.00 (2.3 s), 02:10.80 (3.1 s), 02:49.93 (1.6 s), 09:00.60 (1.9 s)
- Example pan-right: 00:20.80 (3.5 s), 01:28.77 (1.9 s), 02:06.47 (4.3 s), 03:24.03 (2.8 s)
- Example internal-motion: 00:27.50 (1.7 s), 01:26.97 (1.8 s), 01:36.63 (3.2 s), 01:56.37 (1.9 s)
- Example tilt-down: 00:48.73 (1.9 s), 05:15.40 (3.7 s), 15:27.20 (1.6 s)
- Example push-in: 00:52.67 (1.9 s), 02:44.47 (2.4 s), 04:49.10 (4.4 s), 05:34.53 (2.0 s)
- Example pan-left: 04:27.17 (1.8 s), 15:32.53 (1.6 s), 30:07.40 (2.1 s)
- Example tilt-up: 05:45.13 (2.4 s)

## Narration ↔ picture

- Narration pace: **160.4 words/min**; speech covers 71% of the running time; 231 pauses > 0.4 s
- **79%** of cuts fall within 0.25 s of a word boundary; 18% within 0.4 s of a sentence end
- 1.88 cuts per spoken sentence on average (349 sentences)

## Sound

- Integrated loudness **-14.5 LUFS**, LRA 4.1 LU, true peak -0.0 dBTP
- 1940 transient onsets (61.7 per minute); **23%** of cuts have a transient within 100 ms (SFX / music hits on cuts)
- Average level in seconds with speech -21.7 dB vs without speech -27.1 dB (music/SFX bed level in pauses)

## Colour

- Mean brightness 103.4/255, mean saturation 104.4/255
- Dominant colours: `#0a070a` 30% `#31282c` 19% `#56535c` 11% `#9d887c` 11% `#f0edee` 10% `#c5b7ba` 9% `#8a4d38` 5% `#4377bd` 4%

## Files

- Contact sheets and frames (private, not in Git): `reference-library/video-4/contact-sheets/`
- Shot list and per-frame metrics: `data/video-4/shots.json`

## Observations

<!-- qualitative notes for video 4 are maintained in timestamped-observations.md and the guides -->
