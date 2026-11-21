# Reference video 3 — measured analysis

Title (from the file name): **Celebrity Car Tier List**

> The measured sections below are produced by `scripts/reference-analysis/analyze_reference.py` and
> `synthesize.py`. Qualitative observations are in the `## Observations` section, written from the contact sheets.

## Technical metadata

| Duration | Resolution | FPS | Aspect | Video | Audio | Bitrate |
|---|---|---|---|---|---|---|
| 19:35.30 | 1280×720 | 60.0 | 16:9 | h264 Main | aac 2 ch 44100 Hz | 2303 kb/s |

## Editing rhythm

- Shots: **641**, **32.67 cuts/min**
- Shot length: median **1.4 s**, mean 1.83 s, 10th pct 0.53 s, 90th pct 2.67 s, longest 94.2 s
- Distribution: <1s: 173, 1-2s: 314, 2-3s: 106, 3-5s: 37, 5-8s: 6, 8s+: 5
- Dissolve-like (soft, multi-frame) transitions: 339 — almost every change is a hard cut or a fast motion transition
- Fastest 30 s windows: 14:00.00–14:30.00 (27 cuts), 15:00.00–15:30.00 (26 cuts), 04:30.00–05:00.00 (24 cuts)
- Slowest 30 s windows: 06:30.00–07:00.00 (0 cuts), 07:00.00–07:30.00 (0 cuts), 13:30.00–14:00.00 (0 cuts)
- Longest holds: 06:04.23 (94.2 s, static), 12:47.63 (72.8 s, static), 01:34.53 (12.2 s, internal-motion), 16:23.53 (8.7 s, static), 16:01.60 (8.4 s, internal-motion)

## Camera movement (optical-flow classification per shot)

| Motion | Share of shots |
|---|---|
| static | 40.4% |
| push-in | 19.5% |
| internal-motion | 15.6% |
| pull-out | 12.9% |
| pan-right | 4.8% |
| pan-left | 3.1% |
| tilt-up | 1.9% |
| tilt-down | 1.7% |

- Example push-in: 00:00.00 (1.6 s), 00:09.43 (2.6 s), 00:22.63 (1.6 s), 00:28.20 (1.7 s)
- Example pull-out: 00:36.10 (1.6 s), 00:37.70 (1.6 s), 02:53.77 (2.1 s), 03:13.83 (2.7 s)
- Example internal-motion: 00:47.60 (1.7 s), 01:19.57 (1.5 s), 01:34.53 (12.2 s), 02:08.10 (1.7 s)
- Example tilt-down: 01:21.10 (1.8 s), 05:46.13 (2.0 s), 08:36.53 (1.8 s)
- Example pan-left: 01:32.53 (2.0 s), 02:58.60 (2.0 s), 03:39.33 (2.0 s), 07:44.00 (1.8 s)
- Example pan-right: 02:27.67 (1.7 s), 03:09.03 (4.8 s), 04:55.70 (1.6 s), 05:03.37 (1.7 s)
- Example tilt-up: 02:39.63 (2.5 s), 05:16.63 (1.7 s), 11:16.73 (2.8 s), 14:55.77 (2.0 s)

## Narration ↔ picture

- Narration pace: **153.6 words/min**; speech covers 69% of the running time; 99 pauses > 0.4 s
- **75%** of cuts fall within 0.25 s of a word boundary; 16% within 0.4 s of a sentence end
- 3.39 cuts per spoken sentence on average (189 sentences)

## Sound

- Integrated loudness **-15.3 LUFS**, LRA 4.2 LU, true peak -0.1 dBTP
- 1123 transient onsets (57.3 per minute); **20%** of cuts have a transient within 100 ms (SFX / music hits on cuts)
- Average level in seconds with speech -22.2 dB vs without speech -42.6 dB (music/SFX bed level in pauses)

## Colour

- Mean brightness 123.5/255, mean saturation 77.5/255
- Dominant colours: `#2f2b2f` 17% `#bbb0ae` 16% `#564b41` 14% `#8d8d8d` 13% `#67676d` 13% `#0d0a0d` 13% `#e3e4e8` 9% `#b26941` 5%

## Files

- Contact sheets and frames (private, not in Git): `reference-library/video-3/contact-sheets/`
- Shot list and per-frame metrics: `data/video-3/shots.json`

## Observations

<!-- qualitative notes for video 3 are maintained in timestamped-observations.md and the guides -->
