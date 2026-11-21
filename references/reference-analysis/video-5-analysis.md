# Reference video 5 — measured analysis

Title (from the file name): **Billionaire House Tier List**

> The measured sections below are produced by `scripts/reference-analysis/analyze_reference.py` and
> `synthesize.py`. Qualitative observations are in the `## Observations` section, written from the contact sheets.

## Technical metadata

| Duration | Resolution | FPS | Aspect | Video | Audio | Bitrate |
|---|---|---|---|---|---|---|
| 10:38.15 | 1280×720 | 60.0 | 16:9 | h264 Main | aac 2 ch 44100 Hz | 2105 kb/s |

## Editing rhythm

- Shots: **270**, **25.29 cuts/min**
- Shot length: median **1.7 s**, mean 2.36 s, 10th pct 0.87 s, 90th pct 3.24 s, longest 123.93 s
- Distribution: <1s: 43, 1-2s: 131, 2-3s: 62, 3-5s: 24, 5-8s: 8, 8s+: 2
- Dissolve-like (soft, multi-frame) transitions: 45 — almost every change is a hard cut or a fast motion transition
- Fastest 30 s windows: 05:00.00–05:30.00 (22 cuts), 00:00.00–00:30.00 (19 cuts), 01:30.00–02:00.00 (19 cuts)
- Slowest 30 s windows: 07:30.00–08:00.00 (0 cuts), 07:00.00–07:30.00 (0 cuts), 08:00.00–08:30.00 (0 cuts)
- Longest holds: 06:48.90 (123.9 s, static), 09:29.53 (8.7 s, static), 09:44.53 (6.8 s, static), 09:58.83 (6.3 s, static), 10:05.10 (5.9 s, static)

## Camera movement (optical-flow classification per shot)

| Motion | Share of shots |
|---|---|
| static | 60.0% |
| push-in | 22.2% |
| pull-out | 7.4% |
| internal-motion | 5.2% |
| pan-right | 1.5% |
| pan-left | 1.5% |
| tilt-down | 1.1% |
| tilt-up | 1.1% |

- Example push-in: 00:00.00 (1.9 s), 00:01.87 (1.9 s), 00:07.70 (1.8 s), 00:17.87 (2.0 s)
- Example internal-motion: 01:11.47 (1.9 s), 02:19.10 (2.2 s), 02:21.33 (2.1 s), 02:41.17 (1.6 s)
- Example pull-out: 01:21.83 (2.4 s), 01:33.83 (1.8 s), 01:43.17 (1.6 s), 01:46.23 (2.6 s)
- Example pan-left: 02:02.10 (1.5 s), 06:46.73 (2.2 s)
- Example tilt-down: 02:10.70 (2.5 s)
- Example pan-right: 02:39.33 (1.8 s), 02:59.77 (3.5 s), 05:21.30 (3.2 s)
- Example tilt-up: 04:55.53 (1.8 s)

## Narration ↔ picture

- Narration pace: **156.1 words/min**; speech covers 69% of the running time; 48 pauses > 0.4 s
- **79%** of cuts fall within 0.25 s of a word boundary; 22% within 0.4 s of a sentence end
- 2.69 cuts per spoken sentence on average (100 sentences)

## Sound

- Integrated loudness **-16.3 LUFS**, LRA 4.2 LU, true peak 0.3 dBTP
- 382 transient onsets (35.9 per minute); **20%** of cuts have a transient within 100 ms (SFX / music hits on cuts)
- Average level in seconds with speech -24.0 dB vs without speech -83.0 dB (music/SFX bed level in pauses)

## Colour

- Mean brightness 132.8/255, mean saturation 74.1/255
- Dominant colours: `#625f52` 18% `#3d3835` 16% `#a8b5b5` 15% `#777c7a` 15% `#110e11` 13% `#eceff4` 12% `#b48d6c` 6% `#3f75c0` 3%

## Files

- Contact sheets and frames (private, not in Git): `reference-library/video-5/contact-sheets/`
- Shot list and per-frame metrics: `data/video-5/shots.json`

## Observations

<!-- qualitative notes for video 5 are maintained in timestamped-observations.md and the guides -->
