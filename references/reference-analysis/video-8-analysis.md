# Reference video 8 — measured analysis

Title (from the file name): **Billionaire Car Tier List**

> The measured sections below are produced by `scripts/reference-analysis/analyze_reference.py` and
> `synthesize.py`. Qualitative observations are in the `## Observations` section, written from the contact sheets.

## Technical metadata

| Duration | Resolution | FPS | Aspect | Video | Audio | Bitrate |
|---|---|---|---|---|---|---|
| 08:08.97 | 1280×720 | 60.0 | 16:9 | h264 Main | aac 2 ch 44100 Hz | 1722 kb/s |

## Editing rhythm

- Shots: **257**, **31.41 cuts/min**
- Shot length: median **1.47 s**, mean 1.9 s, 10th pct 0.49 s, 90th pct 3.83 s, longest 11.83 s
- Distribution: <1s: 68, 1-2s: 106, 2-3s: 45, 3-5s: 24, 5-8s: 11, 8s+: 3
- Dissolve-like (soft, multi-frame) transitions: 79 — almost every change is a hard cut or a fast motion transition
- Fastest 30 s windows: 00:30.00–01:00.00 (22 cuts), 01:00.00–01:30.00 (22 cuts), 04:00.00–04:30.00 (20 cuts)
- Slowest 30 s windows: 07:00.00–07:30.00 (9 cuts), 06:30.00–07:00.00 (12 cuts), 05:30.00–06:00.00 (12 cuts)
- Longest holds: 04:55.63 (11.8 s, static), 02:21.83 (9.1 s, internal-motion), 07:34.37 (9.0 s, push-in), 00:00.03 (7.3 s, static), 03:24.10 (6.6 s, static)

## Camera movement (optical-flow classification per shot)

| Motion | Share of shots |
|---|---|
| static | 42.0% |
| push-in | 21.4% |
| internal-motion | 20.6% |
| pull-out | 8.6% |
| pan-left | 3.9% |
| pan-right | 1.6% |
| tilt-up | 1.2% |
| tilt-down | 0.8% |

- Example pull-out: 00:07.37 (1.9 s), 01:43.53 (1.9 s), 03:15.90 (1.9 s), 04:03.30 (2.6 s)
- Example pan-left: 00:10.30 (1.7 s), 00:56.97 (2.4 s), 05:10.43 (2.0 s), 06:38.80 (3.0 s)
- Example push-in: 00:12.87 (2.2 s), 00:43.43 (2.0 s), 00:45.40 (1.6 s), 01:00.97 (3.9 s)
- Example pan-right: 00:22.80 (2.8 s), 00:53.40 (1.8 s), 06:24.37 (3.1 s)
- Example internal-motion: 00:36.60 (2.1 s), 00:55.23 (1.7 s), 01:17.80 (4.9 s), 01:58.33 (1.8 s)
- Example tilt-up: 06:14.43 (2.1 s)

## Narration ↔ picture

- Narration pace: **176.1 words/min**; speech covers 79% of the running time; 71 pauses > 0.4 s
- **79%** of cuts fall within 0.25 s of a word boundary; 32% within 0.4 s of a sentence end
- 2.13 cuts per spoken sentence on average (120 sentences)

## Sound

- Integrated loudness **-13.0 LUFS**, LRA 3.7 LU, true peak -0.6 dBTP
- 598 transient onsets (73.4 per minute); **32%** of cuts have a transient within 100 ms (SFX / music hits on cuts)
- Average level in seconds with speech -19.6 dB vs without speech -31.2 dB (music/SFX bed level in pauses)

## Colour

- Mean brightness 122.9/255, mean saturation 76.1/255
- Dominant colours: `#0d0c0e` 21% `#302b2d` 15% `#584d49` 14% `#7d7370` 13% `#a79c95` 13% `#f7f4f6` 12% `#cec6bc` 10% `#cc5b38` 3%

## Files

- Contact sheets and frames (private, not in Git): `reference-library/video-8/contact-sheets/`
- Shot list and per-frame metrics: `data/video-8/shots.json`

## Observations

<!-- qualitative notes for video 8 are maintained in timestamped-observations.md and the guides -->
