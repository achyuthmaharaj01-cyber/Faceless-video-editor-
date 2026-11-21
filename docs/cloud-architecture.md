# Cloud architecture

Goal: run productions from the phone without the laptop staying on for hours.

## Recommendation

**Use Claude Code on the web (a cloud session on this repository) as the production backend, and add a paid render
backend only when videos get long or frequent.** The cloud session already provides everything the pipeline needs:
a Linux container (4 vCPU, 16 GB in testing), Node 22, Python, FFmpeg, Chromium, network access through the
`faceless-video-editor` environment, the Google Drive connector, and Claude itself as the orchestrator that makes
the creative decisions. A separate API/queue/database service would duplicate what the session + the project's
own state already do, at extra cost and complexity.

| Option | Setup | Cost | Fits |
|---|---|---|---|
| **A. Claude Code cloud session** (recommended) | done (repo + environment); add the setup script | included in the Claude plan | production orchestration, analysis, build, QC, renders of short/medium videos |
| B. Laptop + VideoHub | install (docs/installation.md) | electricity | detailed frame review; renders when the laptop is on anyway |
| C. Google Cloud Run Jobs via HyperFrames' built-in `hyperframes cloudrun` | GCP project + billing + `cloudrun deploy` | pay per use (below) | long videos rendered in parallel, fully phone-driven |
| D. AWS Lambda via `hyperframes lambda` | AWS account | pay per use | same as C |
| E. HeyGen's hosted render (`hyperframes cloud`) | HeyGen plan | subscription/credits | if you already pay for HeyGen |

## How the pieces fit (option A + B)

```
Phone (Claude app)
  └─ Claude Code cloud session on this repo  ── /faceless-video-studio skill
       ├─ Drive connector: find inputs, create folders, small files
       ├─ fvs pipeline in the container: ingest → analyse → storyboard (Claude) → assets → build → QC
       ├─ review:
       │    at the desk: VideoHub on the laptop (local only)    → notes → Claude revises
       │    on the phone: scene snapshots + short clips in chat → replies → Claude revises
       ├─ approval (the user, in their words) → fvs render (HyperFrames in the container)
       └─ delivery: Drive API (OAuth refresh token) → Completed Videos/<title>/
```

**Resilience.** Every stage records its status in `.fvs/state.json`; `fvs build` snapshots the previous version into
`versions/rNNN/`; every artefact is regenerated deterministically from the inputs + storyboard. The container is
temporary, so after each milestone the project folder (without large media) should be saved to Drive
`Project Files/` with the Drive API path (the connector's 4 MB limit is too small for media).

**Review security.** VideoHub binds to 127.0.0.1 and can run commands; it is never exposed. Remote review uses
snapshots/clips sent through Claude (already authenticated), or — when the laptop is on — Claude's Remote Control
attachment of the VideoHub films folder, which keeps VideoHub local (docs/remote-review.md).

## What is implemented vs. not

| Part | Status |
|---|---|
| Pipeline commands, resumable stage state, versions, approval gate | ✅ implemented and tested |
| Cloud session environment (network allowlist for models and media sources) | ✅ created (`faceless-video-editor`) |
| Environment setup script (installs Python packages + npm deps on a fresh container) | to save once you approve it (it is the commands in docs/installation.md) |
| Drive API module (OAuth, resumable upload, inputs pull) | ✅ implemented, ⚠️ untested (needs your OAuth client) |
| GCP Cloud Run render backend | ❌ not deployed: needs your GCP project, billing and approval; HyperFrames ships the deploy (`npx hyperframes cloudrun --help`) |
| Job API / database / queue | ❌ deliberately not built (option A makes it unnecessary) |

## Cost estimates (verify current prices before enabling anything paid)

Assumptions to replace with a benchmark (`npx hyperframes benchmark`): DOM capture of these compositions on one
vCPU ≈ 3–6 frames/s; a 10-minute 1080p30 video = 18,000 frames.

| Item | Estimate |
|---|---|
| Option A per video | no extra charge beyond the Claude plan; render time ≈ 18,000 frames / (≈ 8–15 fps on 4 vCPU) ≈ 20–40 min — measure first |
| Option C compute per 10-min video | ≈ 3,000–6,000 vCPU-s + memory ≈ **$0.10–0.30** at Cloud Run's on-demand rates (≈ $0.000018/vCPU-s, $0.000002/GiB-s); likely inside the monthly free tier at low volume |
| Cloud Storage | ≈ $0.02/GB-month; delete render chunks after delivery |
| Drive | your existing storage |
| Stock media | free (Openverse, NASA, Pexels, Pixabay) |
| Music | free if from your own licensed library; paid AI music only with approval |

Set a GCP budget alert before deploying option C.
