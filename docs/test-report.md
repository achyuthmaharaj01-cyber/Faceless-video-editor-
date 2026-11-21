# Test report — 2026-11-21 (cloud session, Linux container: 4 vCPU Xeon 2.1 GHz, 16 GB, no GPU)

Everything below was run in this session. "Simulated" marks inputs a human would normally provide.

## Automated tests
`npm test` → 7 Node tests (licence policy, register CSV, number parsing, `@word` timing, storyboard rules,
preview page generation, in-page hash = Node hash) and 6 Python tests (number/mismatch classification,
alignment interpolation, cut detection incl. minimum shot, motion labels). **All pass.**

## End-to-end sample ("The Box That Changed the World", 44.4 s)
Inputs: an original 102-word script (`examples/box-that-changed-the-world/script.md`) voiced with HyperFrames' local
Kokoro TTS (test material only; real productions use your voiceover).

| Step | Result |
|---|---|
| 1. Script ingestion (.md) | ✅ 5 paragraphs, 10 sentences; entities: 1956, $5.86, Malcom McLean, Newark, Houston |
| 2. Voiceover analysis + alignment (faster-whisper small.en) | ✅ 93.1% of words matched; 6 differences, all classified as formatting/spelling (number value equal); a wrong number (1956 vs 1965) is flagged in unit tests; 139 wpm; −23.8 LUFS |
| 3. Storyboard | ✅ draft generated, then rewritten by Claude with the style guide (12 scenes, 9 formats); `storyboard-check` passes |
| 4. Assets | ✅ 6 licensed images found via Openverse, looked at on contact sheets, downloaded, verified (5 CC BY + 1 CC0), registered with attribution text |
| 5. HyperFrames composition | ✅ 12 sub-compositions, 75+ tweens, Three.js scene, maps from Natural Earth; `hyperframes lint`: 0 errors |
| 6. Sound | ✅ 34 synthesised SFX cues on visual events, procedural music bed ducked under the voice, stems for VideoHub |
| 7. Visual review by Claude (snapshots) | ✅ found and fixed: blank 3D (missing three.core), map labels scaling with zoom, black half-frame in the comparison, word order in word-synced labels, invisible map pins, thick map strokes, 3D framing |
| 8. VideoHub live preview | ✅ real composition in the real VideoHub UI (scratch hub); scenes lane, narration text row, voice/music/effects stems; frame-accurate stepping (frame 300 = 10.000 s) |
| 9. Preview = render | ✅ `fvs verify-preview`: 11/11 sampled frames **pixel-identical** to HyperFrames' own capture (incl. 3 in the Three.js scene) |
| 10. Feedback | ✅ (simulated note) drawn box at frame 300 via the VideoHub UI → `hub_notes` → `fvs notes` mapped it to scene sc04, restored the note picture from a real frame |
| 11. Revision + refresh | ✅ storyboard change → rebuild (previous version kept in `versions/`) → VideoHub reloaded in place at the same frame → verified visually → `hub_note_update` fixed |
| 12. Pre-render QC | ✅ 0 failed; it caught (and the pipeline fixed) overlapping text and an unsupported on-screen figure ("−97%") |
| 13. Approval | ⛔ **not done**: approval must come from you; the session's safety check (correctly) refused to record one on your behalf |
| 14. Final render + final QC + delivery | ⛔ **pending your approval** of this sample (or of your first real video). The render path itself was exercised on a 6 s test film through VideoHub's Render button → HyperFrames → 1080p30 H.264/AAC; QC signal checks on that file: 180 frames, no black/frozen frames, audio sync 0.9 ms (corr. 0.998) |

Mistake noted: during the first run the note was marked fixed before the fix was verified; it was verified
immediately after, and SKILL.md now requires verification before `hub_note_update`.

## Reference analysis
All 8 Drive reference videos downloaded (sizes match Drive), analysed (3,074 shots, 2 h 00 m) in ≈ 45 min; four files
contain corrupted H.264 data (reported in the index). Windows paths from the brief were not reachable (no computer
attached to the cloud session).

## Not tested (needs your accounts or approval)
- Drive API module (`drive-auth/pull/push`) — needs your OAuth client.
- Pexels / Pixabay search — needs free API keys.
- VideoHub on Windows with its MCP tools registered in Claude Code — tested here through its CLI and UI on Linux.
- GCP/AWS distributed rendering — not deployed.
- Laptop performance — measure with `npx hyperframes benchmark` on the i5-1335U.
