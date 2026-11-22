# Quality-control report

Project: **The Box That Changed the World** · 1920×1080 @ 30 fps · voiceover 0:44.41
Checked: 2026-11-22T06:59:38.829Z · video: renders/box-that-changed-the-world_v1.mp4 · composition 241382fa

**Result: no failed checks, 9 warnings, 4 manual-review items.**

## Failed (0)
- none

## Warnings (9)
- ⚠️ Integrated loudness -18.7 LUFS (YouTube reference about −14; quieter is not turned up by YouTube).
- ⚠️ Asset truck is 1024px wide: upscaled on a 1920px frame (softer). A higher-resolution licensed source would look better.
- ⚠️ Asset longshoremen is 1024px wide: upscaled on a 1920px frame (softer). A higher-resolution licensed source would look better.
- ⚠️ Asset warehouse is 1024px wide: upscaled on a 1920px frame (softer). A higher-resolution licensed source would look better.
- ⚠️ Asset terminal is 1024px wide: upscaled on a 1920px frame (softer). A higher-resolution licensed source would look better.
- ⚠️ Asset ship-aerial is 1024px wide: upscaled on a 1920px frame (softer). A higher-resolution licensed source would look better.
- ⚠️ Asset ship-harbor is 1024px wide: upscaled on a 1920px frame (softer). A higher-resolution licensed source would look better.
- ⚠️ Audio: music is the procedural placeholder bed: replace it with a licensed track for publishing quality (storyboard.music.track)
- ⚠️ Audio: loudness target -14 LUFS needs +8.0 dB but the true peak allows only 3.3 dB: mix lands at -18.7 LUFS (no limiter is applied to the narration; approve limiting if you want it louder)

## Manual review required (4)
- 👁 Look at reports/qc-frames/begin.jpg, middle.jpg, end.jpg (taken from the rendered file).
- 👁 Fact check: names, dates and figures come from your script; this system checks they match the narration, not that the script is historically correct.
- 👁 Watch every scene once: do the visuals show what the narration says (no unrelated or misleading images)?
- 👁 Credits needed in the video description (CC BY): 5 assets — see reports/attributions.txt.

## Passed (32)
- ✅ Resolution 1920×1080 (expected 1920×1080).
- ✅ Aspect ratio 1.7778.
- ✅ Frame rate 30 fps (expected 30).
- ✅ Video codec h264 (High, yuv420p).
- ✅ Audio codec aac, 2 ch, 48000 Hz.
- ✅ Video duration 44.433 s vs voiceover 44.410 s (difference 23 ms; allowed one frame, 33 ms).
- ✅ Audio duration 44.433 s vs voiceover (difference 23 ms; AAC priming allowance 50 ms).
- ✅ Frame count 1333 (expected 1332).
- ✅ No black frames (blackdetect, 0.2 s minimum, luma threshold 8%).
- ✅ No frozen picture longer than 2 s (freezedetect).
- ✅ True peak -1.1 dBTP (ceiling −1 dBTP; above 0 = clipping).
- ✅ No silence longer than 1.5 s inside the film (−50 dB).
- ✅ Audio sync: rendered audio vs approved mix offset 0 ms, correlation 1 (needs ≤ 33 ms and > 0.5).
- ✅ Audio ending: last 50 ms at -78.4 dB (fades out).
- ✅ Render matches the approved composition (approved 241382fa, rendered 241382fa).
- ✅ Layout at 24 sampled moments (two per scene): no text outside the frame, no overlapping text, no broken images, no missing-asset slates.
- ✅ No script errors while seeking the composition.
- ✅ Every file the composition requested was served (no broken asset paths).
- ✅ Storyboard: 12 contiguous scenes cover the whole voiceover; every sentence is on screen in script order.
- ✅ Narration alignment: 93.1% of script words matched in the voiceover.
- ✅ Every script/voiceover difference is a formatting or transcription variant (no omitted or changed narration detected).
- ✅ On-screen figure "1950s (in "1950s trucking")" in sc02 is stated elsewhere in the script.
- ✅ On-screen figure "26 (in "april 26, 1956")" in sc05 is stated in that scene's narration.
- ✅ On-screen figure "1956 (in "april 26, 1956")" in sc05 is stated elsewhere in the script.
- ✅ On-screen figure "58 (in "58 boxes")" in sc06 is stated in that scene's narration.
- ✅ On-screen figure "5 (in "5 days")" in sc07 is stated in that scene's narration.
- ✅ On-screen figure "$5.86" in sc08 is stated in that scene's narration.
- ✅ On-screen figure "$0.16" in sc09 is stated in that scene's narration.
- ✅ On-screen figure "24000+" in sc11 is stated in that scene's narration.
- ✅ All 6 media files used by the composition are in the licence register.
- ✅ Licence register: 8 rows complete (licence, source URL, attribution where required, commercial use and modification allowed).
- ✅ Sound design: 36 SFX cues placed; music source: procedural (curious); narration processing: none (static master gain only).

## Not checked
- nothing skipped
