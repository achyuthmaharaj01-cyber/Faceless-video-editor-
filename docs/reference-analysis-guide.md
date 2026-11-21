# Reference analysis

Run once per set of reference videos; the results are the permanent style library in `references/reference-analysis/`.

```bash
python scripts/reference-analysis/analyze_reference.py "<video>" --out <library>/video-N --id N
python scripts/reference-analysis/synthesize.py <library> references/reference-analysis --titles manifest.tsv
```

Per video (one video at a time, flat memory ≈ 150 MB): one FFmpeg decode at 320×180 / 30 fps gives cut detection
(HSV content difference, fixed + adaptive thresholds, 0.25 s minimum shot), dissolve-like transitions, fades,
dense optical flow per shot (push-in / pull-out / pan / tilt / internal motion), brightness, saturation and the
palette; a second pass measures EBU R128 loudness, true peak and transients; faster-whisper gives word timings to
relate cuts to words and sentences and speech to music levels. Frames are grabbed only where useful: one per shot
(≤ 240), regular samples, and 6-frame strips around cuts and soft transitions; contact sheets are built from them.
Every stage is cached as JSON and skipped on re-run (`--force` to redo).

Measured on the cloud container (4 vCPU): ≈ 9 s of video pass + 5 s of transcription per minute of footage;
the eight references (2 h) took ≈ 45 min sequentially. On the i5-1335U laptop expect a similar order of magnitude
(benchmark with a 60 s excerpt first, as was done here).

Then the analyst (Claude) reads the contact sheets and writes the qualitative guides and timestamped observations.
Frames and contact sheets are copies of third-party footage: keep them private (Drive `Reference Library/`), never
in the public repository; the repository holds only measurements and written guidance.

The 2026-11-21 run used the eight videos from the Drive reference folder (the Windows paths in the brief were not
reachable from the cloud session). Four of the files contain corrupted H.264 data — see
`references/reference-analysis/reference-video-index.md`.
