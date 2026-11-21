# Reference video 6 — measured analysis

Title (from the file name): **Billionaire Yacht Tier List**

> The measured sections below are produced by `scripts/reference-analysis/analyze_reference.py` and
> `synthesize.py`. Qualitative observations are in the `## Observations` section, written from the contact sheets.

## Technical metadata

| Duration | Resolution | FPS | Aspect | Video | Audio | Bitrate |
|---|---|---|---|---|---|---|
| 16:15.68 | 1280×720 | 60.0 | 16:9 | h264 Main | aac 2 ch 44100 Hz | 1931 kb/s |

## Editing rhythm

- Shots: **382**, **23.43 cuts/min**
- Shot length: median **1.78 s**, mean 2.55 s, 10th pct 0.93 s, 90th pct 3.83 s, longest 79.7 s
- Distribution: <1s: 46, 1-2s: 172, 2-3s: 101, 3-5s: 40, 5-8s: 16, 8s+: 7
- Dissolve-like (soft, multi-frame) transitions: 82 — almost every change is a hard cut or a fast motion transition
- Fastest 30 s windows: 01:30.00–02:00.00 (21 cuts), 02:00.00–02:30.00 (21 cuts), 00:00.00–00:30.00 (20 cuts)
- Slowest 30 s windows: 05:30.00–06:00.00 (0 cuts), 11:30.00–12:00.00 (0 cuts), 11:00.00–11:30.00 (2 cuts)
- Longest holds: 05:07.43 (79.7 s, static), 11:02.33 (76.8 s, static), 10:02.63 (13.2 s, static), 07:30.47 (10.3 s, internal-motion), 10:42.77 (10.0 s, static)

## Camera movement (optical-flow classification per shot)

| Motion | Share of shots |
|---|---|
| static | 58.1% |
| internal-motion | 16.2% |
| push-in | 11.8% |
| pull-out | 6.8% |
| pan-left | 3.1% |
| pan-right | 2.4% |
| tilt-up | 1.3% |
| tilt-down | 0.3% |

- Example internal-motion: 00:00.00 (1.8 s), 00:15.33 (2.5 s), 00:27.30 (1.7 s), 00:32.67 (1.8 s)
- Example pan-right: 00:03.73 (1.8 s), 01:27.53 (6.0 s), 06:40.77 (2.4 s), 07:58.63 (2.3 s)
- Example push-in: 00:20.10 (1.8 s), 00:28.97 (2.1 s), 01:00.50 (3.0 s), 01:33.50 (1.6 s)
- Example pull-out: 01:19.70 (1.7 s), 01:43.20 (2.5 s), 02:10.63 (1.7 s), 04:00.17 (1.6 s)
- Example tilt-up: 06:50.33 (1.6 s)
- Example pan-left: 12:27.67 (4.0 s), 13:04.93 (1.7 s), 13:27.03 (1.5 s), 13:48.53 (1.8 s)

## Narration ↔ picture

- Narration pace: **160.7 words/min**; speech covers 70% of the running time; 85 pauses > 0.4 s
- **79%** of cuts fall within 0.25 s of a word boundary; 14% within 0.4 s of a sentence end
- 2.54 cuts per spoken sentence on average (150 sentences)

## Sound

- Integrated loudness **-13.8 LUFS**, LRA 3.6 LU, true peak -0.7 dBTP
- 870 transient onsets (53.5 per minute); **25%** of cuts have a transient within 100 ms (SFX / music hits on cuts)
- Average level in seconds with speech -20.3 dB vs without speech -24.1 dB (music/SFX bed level in pauses)

## Colour

- Mean brightness 120.7/255, mean saturation 84.2/255
- Dominant colours: `#0b0a0d` 19% `#323136` 17% `#625550` 13% `#8e8380` 12% `#b8bbc1` 11% `#849db7` 10% `#e3e6ed` 9% `#4a6c8c` 8%

## Files

- Contact sheets and frames (private, not in Git): `reference-library/video-6/contact-sheets/`
- Shot list and per-frame metrics: `data/video-6/shots.json`

## Observations

<!-- qualitative notes for video 6 are maintained in timestamped-observations.md and the guides -->
