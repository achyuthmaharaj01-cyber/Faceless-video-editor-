# Reference video 2 — measured analysis

Title (from the file name): **Could You Spend 1 Trillion**

> The measured sections below are produced by `scripts/reference-analysis/analyze_reference.py` and
> `synthesize.py`. Qualitative observations are in the `## Observations` section, written from the contact sheets.

## Technical metadata

| Duration | Resolution | FPS | Aspect | Video | Audio | Bitrate |
|---|---|---|---|---|---|---|
| 09:28.66 | 1280×720 | 60.0 | 16:9 | h264 Main | aac 2 ch 44100 Hz | 2058 kb/s |

## Editing rhythm

- Shots: **220**, **23.11 cuts/min**
- Shot length: median **1.98 s**, mean 2.58 s, 10th pct 0.6 s, 90th pct 5.0 s, longest 27.17 s
- Distribution: <1s: 46, 1-2s: 64, 2-3s: 45, 3-5s: 42, 5-8s: 16, 8s+: 7
- Dissolve-like (soft, multi-frame) transitions: 82 — almost every change is a hard cut or a fast motion transition
- Fastest 30 s windows: 00:00.00–00:30.00 (25 cuts), 05:30.00–06:00.00 (21 cuts), 00:30.00–01:00.00 (15 cuts)
- Slowest 30 s windows: 08:00.00–08:30.00 (2 cuts), 07:00.00–07:30.00 (7 cuts), 06:00.00–06:30.00 (8 cuts)
- Longest holds: 08:03.13 (27.2 s, static), 09:13.47 (15.1 s, static), 06:36.43 (12.5 s, static), 06:59.67 (11.2 s, static), 04:16.30 (8.6 s, static)

## Camera movement (optical-flow classification per shot)

| Motion | Share of shots |
|---|---|
| static | 63.6% |
| internal-motion | 14.1% |
| push-in | 10.0% |
| pull-out | 5.5% |
| pan-left | 3.6% |
| pan-right | 1.8% |
| tilt-up | 0.9% |
| tilt-down | 0.5% |

- Example pull-out: 00:19.47 (1.7 s), 00:26.20 (3.4 s), 00:34.20 (2.5 s), 00:41.33 (2.2 s)
- Example push-in: 00:49.37 (3.1 s), 01:19.23 (2.4 s), 01:58.20 (4.8 s), 03:28.07 (4.9 s)
- Example pan-right: 00:52.50 (1.9 s), 05:50.87 (5.0 s), 06:04.70 (4.5 s)
- Example internal-motion: 01:09.17 (2.9 s), 01:22.70 (3.6 s), 01:30.67 (6.7 s), 01:55.10 (3.1 s)
- Example pan-left: 02:08.57 (1.8 s), 04:43.90 (2.3 s), 05:35.00 (2.6 s), 06:14.40 (2.5 s)
- Example tilt-up: 02:10.37 (2.2 s), 05:32.00 (3.0 s)
- Example tilt-down: 07:23.97 (2.4 s)

## Narration ↔ picture

- Narration pace: **176.9 words/min**; speech covers 80% of the running time; 83 pauses > 0.4 s
- **94%** of cuts fall within 0.25 s of a word boundary; 27% within 0.4 s of a sentence end
- 1.58 cuts per spoken sentence on average (139 sentences)

## Sound

- Integrated loudness **-14.2 LUFS**, LRA 4.4 LU, true peak -0.4 dBTP
- 565 transient onsets (59.6 per minute); **30%** of cuts have a transient within 100 ms (SFX / music hits on cuts)
- Average level in seconds with speech -22.9 dB vs without speech -28.0 dB (music/SFX bed level in pauses)

## Colour

- Mean brightness 153.7/255, mean saturation 65.5/255
- Dominant colours: `#f4f3f5` 21% `#bdc0c8` 17% `#3c3f44` 16% `#6d6765` 14% `#121013` 13% `#a99485` 10% `#6e8fb4` 6% `#ba453a` 3%

## Files

- Contact sheets and frames (private, not in Git): `reference-library/video-2/contact-sheets/`
- Shot list and per-frame metrics: `data/video-2/shots.json`

## Observations

<!-- qualitative notes for video 2 are maintained in timestamped-observations.md and the guides -->
