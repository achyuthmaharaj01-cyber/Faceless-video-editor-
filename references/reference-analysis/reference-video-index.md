# Reference video index

Eight reference videos (Jack Pockets channel), analysed locally from the copies in the user's Google Drive
reference folder. Numbering follows the Drive upload order and **may differ from the numbering of the local
Windows copies** (`video 1.mp4` … `video 8.mp4`), which were not reachable from the cloud session.

| # | Title (from file name) | Duration | Format | Shots | Cuts/min | Median shot | Words/min | Loudness |
|---|---|---|---|---|---|---|---|---|
| [1](video-1-analysis.md) | What Happens When You Win The Lottery | 12:39.32 | 1280×720 @ 60.0 | 315 | 24.81 | 1.83 s | 204.8 | -14.1 LUFS |
| [2](video-2-analysis.md) | Could You Spend 1 Trillion | 09:28.66 | 1280×720 @ 60.0 | 220 | 23.11 | 1.98 s | 176.9 | -14.2 LUFS |
| [3](video-3-analysis.md) | Celebrity Car Tier List | 19:35.30 | 1280×720 @ 60.0 | 641 | 32.67 | 1.4 s | 153.6 | -15.3 LUFS |
| [4](video-4-analysis.md) | Billionaires Who Hate Each Other | 31:25.13 | 1280×720 @ 60.0 | 657 | 20.88 | 1.97 s | 160.4 | -14.5 LUFS |
| [5](video-5-analysis.md) | Billionaire House Tier List | 10:38.15 | 1280×720 @ 60.0 | 270 | 25.29 | 1.7 s | 156.1 | -16.3 LUFS |
| [6](video-6-analysis.md) | Billionaire Yacht Tier List | 16:15.68 | 1280×720 @ 60.0 | 382 | 23.43 | 1.78 s | 160.7 | -13.8 LUFS |
| [7](video-7-analysis.md) | Every Level Of Watches | 11:55.31 | 1280×720 @ 60.0 | 332 | 27.76 | 1.77 s | 165.2 | -16.1 LUFS |
| [8](video-8-analysis.md) | Billionaire Car Tier List | 08:08.97 | 1280×720 @ 60.0 | 257 | 31.41 | 1.47 s | 176.1 | -13.0 LUFS |

**All videos:** 3074 shots; median shot **1.7 s** (10th–90th pct 0.63–4.0 s); 20% of shots under 1 s, 6% over 5 s.
## File integrity

All eight files were downloaded byte-for-byte (sizes match Google Drive) and are readable, but a full decode
(`ffmpeg -v error -i <file> -f null -`) reports corrupted H.264 data in four of them:

| Video | Decode-error lines | Effect on the analysis |
|---|---|---|
| 1, 2, 7, 8 | 0 | none |
| 3 | 49,995 | some frames show blocky garbage (e.g. around 14:23–14:27); a few detected cuts there may be false |
| 4 | 65,776 | as above; statistics are dominated by clean sections |
| 5 | 36,772 | as above |
| 6 | 45,227 | as above |

The corruption is in the source files (they came from a downloader site), not introduced by the analysis. Clean
copies from the original channel would make the per-video cut statistics of 3–6 exact; the style conclusions do
not depend on them (the clean videos show the same ranges).
