| metric | reference (video-3) | this video | tolerance | result |
|---|---|---|---|---|
| cuts_per_minute | 33.09 | 37.03 | ±15% | PASS |
| shot_median | 1.56 | 1.516 | ±15% | PASS |
| shot_mean | 1.814 | 1.62 | ±20% | PASS |
| shot_p10 | 0.833 | 0.8 | ±30% | PASS |
| shot_p90 | 2.866 | 2.467 | ±30% | PASS |
| price_badge_share | 0.257 | 0.478 | ±0.12 | warn |
| vignette_share | 0.101 | 0.087 | ±0.12 | PASS |
| tier_chart_share | 0.014 | 0.13 | ±0.1 | warn |
| luma_mean | 104.0 | 103.9 | ±25% | PASS |
| sat_mean | 29.5 | 25.2 | ±35% | PASS |
| vo_share | 0.845 | 0.823 | ±0.08 | PASS |
| integrated_lufs | -15.4 | -15.0 | ±1.0 | PASS |
| lufs_vo_on | -15.2 | -14.9 | ±1.5 | PASS |
| breath_gaps_per_min | 3.57 | 10.46 | ±50% | warn |
| breath_gap_median_s | 0.46 | 0.42 | ±50% | PASS |
| vo_pauses_per_min | 3.2 | 4.8 | ±50% | PASS |
| vo_pause_median_s | 0.61 | 0.52 | ±35% | PASS |
| clip_audio_per_min | 0.3 | 1.61 | ±0.6 | warn |
| label_h_pct | 6.11 | 7.08 | ±20% | PASS |
| label_cy_pct | 37.0 | 31.95 | ±8 | PASS |
| bottom_h_pct | 8.12 | None | n/a |  |
| bottom_cy_pct | 84.1 | None | n/a |  |
| sfx_per_min | 5.5 | 8.9 | ±60% | warn |
| sfx_per_badge | 0.49 | 0.5 | ±0.15 | PASS |
| sfx_per_verdict | 0.75 | 0.8 | ±0.15 | PASS |

## Test video (Phase 3)
"Presidential Car Tier List" - 70.5 s, Kokoro TTS voiceover (am_michael, tightened with tighten_vo.py), 46 shots,
5 entries + hook chart, 1 VO-off clip (public-domain JFK inaugural excerpt), CC BY-SA music bed (Jahzzar "Trap").
0 hard fails. Warnings are content-density effects of a 70 s test that packs 5 verdicts: badge share, chart share,
clip-audio and SFX per minute (per-event SFX rates match: 0.50 per badge vs 0.49, 0.80 per verdict vs 0.75).
Whisper-based "breath_gaps_per_min" over-counts on synthetic speech (word ends are cut early); the hard metric is
vo_pauses_per_min measured on the demucs vocal stem (reference 3.2/min, test 4.8/min).

## Holdout (Billionaire Car Tier List, not used for the style)
median shot 1.633 s (video-3 1.56 s), 27.4 cuts/min; same text grammar; different tier chart variant (rows) and no
price badge - see style.json holdout_validation.
