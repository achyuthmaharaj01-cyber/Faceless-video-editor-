# Reference video 1 — measured analysis

Title (from the file name): **What Happens When You Win The Lottery**

> The measured sections below are produced by `scripts/reference-analysis/analyze_reference.py` and
> `synthesize.py`. Qualitative observations are in the `## Observations` section, written from the contact sheets.

## Technical metadata

| Duration | Resolution | FPS | Aspect | Video | Audio | Bitrate |
|---|---|---|---|---|---|---|
| 12:39.32 | 1280×720 | 60.0 | 16:9 | h264 Main | aac 2 ch 44100 Hz | 2078 kb/s |

## Editing rhythm

- Shots: **315**, **24.81 cuts/min**
- Shot length: median **1.83 s**, mean 2.41 s, 10th pct 0.68 s, 90th pct 4.69 s, longest 16.47 s
- Distribution: <1s: 61, 1-2s: 112, 2-3s: 61, 3-5s: 53, 5-8s: 24, 8s+: 4
- Dissolve-like (soft, multi-frame) transitions: 113 — almost every change is a hard cut or a fast motion transition
- Fastest 30 s windows: 06:00.00–06:30.00 (22 cuts), 00:30.00–01:00.00 (19 cuts), 03:30.00–04:00.00 (17 cuts)
- Slowest 30 s windows: 04:00.00–04:30.00 (6 cuts), 05:30.00–06:00.00 (7 cuts), 05:00.00–05:30.00 (7 cuts)
- Longest holds: 12:22.80 (16.5 s, static), 03:58.50 (16.0 s, static), 05:45.97 (11.7 s, static), 05:05.17 (10.3 s, static), 10:00.93 (8.0 s, static)

## Camera movement (optical-flow classification per shot)

| Motion | Share of shots |
|---|---|
| static | 60.6% |
| internal-motion | 13.3% |
| push-in | 9.5% |
| pull-out | 7.0% |
| pan-left | 5.4% |
| pan-right | 2.2% |
| tilt-down | 1.3% |
| tilt-up | 0.6% |

- Example pull-out: 00:04.50 (5.0 s), 00:33.33 (2.2 s), 05:35.37 (4.9 s), 06:01.87 (1.6 s)
- Example push-in: 00:21.40 (1.8 s), 00:27.30 (1.5 s), 00:42.67 (1.8 s), 01:55.53 (1.6 s)
- Example internal-motion: 00:23.23 (2.5 s), 00:40.37 (1.6 s), 01:20.67 (3.4 s), 01:33.60 (3.5 s)
- Example pan-right: 01:29.40 (1.9 s), 06:06.70 (1.6 s), 09:51.37 (6.7 s), 10:48.03 (3.3 s)
- Example pan-left: 02:50.03 (2.7 s), 05:40.30 (2.5 s), 06:59.20 (2.2 s), 07:54.93 (2.3 s)
- Example tilt-up: 09:27.10 (2.6 s), 12:07.87 (3.1 s)

## Narration ↔ picture

- Narration pace: **204.8 words/min**; speech covers 82% of the running time; 110 pauses > 0.4 s
- **88%** of cuts fall within 0.25 s of a word boundary; 27% within 0.4 s of a sentence end
- 1.74 cuts per spoken sentence on average (180 sentences)

## Sound

- Integrated loudness **-14.1 LUFS**, LRA 3.9 LU, true peak -0.3 dBTP
- 763 transient onsets (60.3 per minute); **24%** of cuts have a transient within 100 ms (SFX / music hits on cuts)
- Average level in seconds with speech -21.1 dB vs without speech -36.1 dB (music/SFX bed level in pauses)

## Colour

- Mean brightness 132.9/255, mean saturation 72.7/255
- Dominant colours: `#151113` 20% `#413733` 17% `#f4f2f5` 15% `#98938e` 14% `#6a6360` 14% `#c8c0bd` 12% `#ac6838` 5% `#2e6192` 3%

## Files

- Contact sheets and frames (private, not in Git): `reference-library/video-1/contact-sheets/`
- Shot list and per-frame metrics: `data/video-1/shots.json`

## Observations

<!-- qualitative notes for video 1 are maintained in timestamped-observations.md and the guides -->
