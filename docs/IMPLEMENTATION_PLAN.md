# Implementation Plan — Faceless Video Studio

Status: **Phase 1 complete (audit). Awaiting your decisions and Google Cloud access.**

## 1. Architecture

```
 Phone ─┬─ Claude Code (web/app) ── /faceless-video-studio skill
        │        │  HTTPS + bearer token (injected by the Claude network proxy, never in chat)
        │        ▼
        │  ┌──────────────── Google Cloud project (us-central1) ─────────────────┐
        │  │ Cloud Run SERVICE  studio-api  (FastAPI, scales to zero)            │
        │  │   • REST API: projects, start/cancel/resume, status, QC report      │
        ├──┼─► • Mobile status page (signed read-only links)                     │
        │  │   • Google OAuth start/callback → refresh token → Secret Manager    │
        │  │        │ starts executions                                          │
        │  │        ▼                                                            │
        │  │ Cloud Run JOBS (one image: Python + Node + FFmpeg + Chromium)       │
        │  │   • studio-worker   4 vCPU/16 GiB: ingest, analysis, assets, QC     │
        │  │   • studio-render   8 vCPU/32 GiB: Remotion + FFmpeg render         │
        │  │        │                                                            │
        │  │ Firestore: project + stage state · GCS bucket: private working files│
        │  │ Secret Manager: Anthropic key, OAuth client, Drive token, API token │
        │  │ Budget alerts · job timeouts · max-instances · lifecycle cleanup    │
        │  └─────────────────────────────────────────────────────────────────────┘
        │        │ resumable upload/download (Drive API v3)
        └─ Google Drive: FACELESS VIDEO STUDIO/{Reference Library, Scripts, Voiceovers,
                         Projects, Finished Videos, Thumbnails, Reports, Archived Projects}

 GitHub repo ── push to main ── GitHub Actions (keyless Workload Identity) ── Cloud Build ── deploy
```

**Why this shape (vs. the brief's suggested stack):** It is the brief's stack, with two adjustments.
1. **No separate orchestrator.** Cloud Workflows or Pub/Sub would add moving parts. Instead, each job runs the stage list for one project and checkpoints every stage to Firestore and GCS. A retry or resume skips completed stages.
2. **Keyless CI/CD.** After a one-time bootstrap, no Google credential ever has to exist in a Claude session. Code deploys through GitHub Actions with Workload Identity Federation. I debug through Actions logs and an authenticated `/admin/logs` API endpoint.

## 2. Production pipeline (resumable stages)

| # | Stage (status) | What runs | Output (GCS `projects/<id>/`) |
|---|---|---|---|
| 1 | Validating files | Drive download (resumable) → ffprobe, text decode, script↔VO sanity | `input/`, `validation.json` |
| 2 | Analysing voiceover | loudness, pauses (silencedetect), faster-whisper word timestamps | `audio/analysis.json` |
| 3 | Analysing script | script↔transcript alignment (script text is authoritative, VO controls timing); beats, entities, emphasis, mismatch report | `script/beats.json`, `mismatch.md` |
| 4 | Creating storyboard | Claude (Opus 5.5) with Style Bible + reference-library retrieval → schema-validated JSON storyboard | `storyboard.json`, `STORYBOARD.md` |
| 5 | Researching media | Openverse, Wikimedia Commons, NASA, LoC, Smithsonian, Internet Archive (PD only), Pexels, Pixabay; Claude vision ranks candidates | `assets/candidates.json` |
| 6 | Downloading assets | download + per-asset licence verification against the allowlist → `ASSET_LICENSE_REGISTER.csv` | `assets/`, register |
| 7 | Creating graphics | Remotion components (typography, charts, maps, timelines), Three.js via `@remotion/three` only where flagged, Python image treatments | `graphics/` |
| 8 | Editing | build Remotion timeline props from storyboard; SFX placement; music bed with ducking | `edit/timeline.json` |
| 9 | Rendering | Remotion `renderMedia` (H.264/AAC, 1080p30 or 1080×1920) + FFmpeg final mix (loudnorm) | `render/final.mp4` |
| 10 | Quality control | ffprobe spec check, blackdetect, freezedetect, ebur128 loudness and true peak, VO-sync cross-correlation, OCR of on-screen text vs. storyboard, contact sheet + Claude vision review, licence register completeness → auto-fix and re-render (max 2) | `QUALITY_CONTROL_REPORT.md` |
| 11 | Uploading | Drive resumable upload: video, storyboard, register, QC report, contact sheet | Drive links |
| 12 | Completed / Failed | learning-log entry, notification, project status page | — |

Long-form and short-form are **separate storyboards** from the same beats. Shorts are composed for 9:16, not cropped.

## 3. Reference analysis (one-off, re-runnable)

Per video: download → PySceneDetect (content + adaptive) → shot list → representative frames, contact sheets and short sequential frame strips around cuts → OpenCV optical flow (zoom/pan/static classification) → audio: ebur128, Demucs separation (voice vs. music/SFX), onset detection for SFX hits relative to cuts → Claude vision via **Batch API (50% off)** on sheets and strips. Results go into the searchable reference library (Firestore + JSONL in GCS, frames in the private bucket). Claude then synthesises `STYLE_BIBLE.md` and the five companion guides. **No frames or media go into the public repo**, only derived text.

## 4. Phases — what I do vs. what you do

| Phase | I do (autonomously) | You do (phone) | Blocked by |
|---|---|---|---|
| 1 Audit | ✅ done | — | — |
| 4/5 Build Skill + backend code | write all code, Dockerfile, infra scripts, CI; local tests here (FFmpeg, Remotion render, scene detection on synthetic clips) | — | nothing, **can start now** |
| 6a Bootstrap GCP | write `infra/bootstrap.sh` | create GCP project + billing; paste one command into **Cloud Shell**; create the OAuth client (≈10 taps, exact guide provided); put the Anthropic key into Secret Manager via Cloud Shell | your Google account, billing approval |
| 6b Deploy | push → Actions → Cloud Build → Cloud Run; verify health | approve the Claude environment host + API token form | 6a |
| 2 Reference access | Drive inventory: count, names, sizes, formats, durations, nested folders, test download | open one OAuth link and consent | 6b |
| 3 Reference analysis | run analysis jobs, build Style Bible + guides + library | approve the one-off analysis cost | 2 |
| 7 Testing | component tests with a 30–60 s sample project | — | 3 |
| 8 Pilot | full video, evaluate against the Style Bible, improve | supply a real script + VO | 7 |
| 9 Handover | final docs, links, costs, limitations | — | 8 |

Phases 2–3 come after a minimal deploy because Drive access goes through the cloud backend's OAuth callback. That keeps your refresh token out of chat and out of temporary sessions.

## 5. Cost estimate (approximate — confirm in the GCP pricing calculator before approval)

Assumed rates: Cloud Run Jobs ≈ $0.000018/vCPU-s + $0.000002/GiB-s (Tier 1) with a monthly free tier ≈ 180k vCPU-s / 360k GiB-s; GCS Standard ≈ $0.02/GB-month; internet egress ≈ $0.12/GB; Claude Opus 5.5 $4 / $20 per M input/output tokens (Batch −50%).

| Item | Estimate |
|---|---|
| **Fixed monthly** (API scaled to zero, Firestore free tier, ~6 secrets, ~5 GB container image, Cloud Build free minutes) | **≈ $1–3 / month** |
| **One-off reference analysis** (~10 videos; compute ≈ $2–5, Claude via Batch ≈ $10–25) | **≈ $15–30 once** |
| **Per 10-min long-form video**: compute ≈ $1–1.50 (largely covered by the free tier at low volume), Claude ≈ $3–6, storage ≈ $0.20, Drive egress ≈ $0.25 | **≈ $5–8** |
| **Per Short (≤60 s)** | **≈ $1–2** |
| Remotion licence (individual) / stock APIs (Pexels, Pixabay, Freesound, Openverse) | $0 |
| Optional paid music generation (e.g. an AI music API) | only with your approval |

**Guards:** GCP budget alerts (e.g. 50/90/100% of a monthly cap you choose), a code-enforced Claude spend cap per project, job timeouts (worker 2 h, render 4 h), one concurrent production, max-instances caps, GCS lifecycle (temp files 7 days, project working files 30 days after delivery).

## 6. Known limitations, stated up front

- **No GPU.** Three.js scenes render with software GL in Chromium: slower but functional. That's one more reason to use 3D only where it earns its place.
- **Licensed background music is the weakest link for full automation.** There are few high-quality, API-accessible, monetisation-safe music sources. See decision D4.
- **Facts in the script are your responsibility.** QC checks that on-screen names, dates and numbers match the script and voiceover, and flags implausible ones. It cannot guarantee historical accuracy.
- **Company logos and product imagery** are trademarks. Use is limited to editorial/nominative contexts and recorded in the register.

## 7. Decisions needed from you

- **D1 GCP access:** Cloud Shell bootstrap (recommended) vs. signing gcloud into this Claude session.
- **D2 Monthly budget alert** for GCP + Claude API.
- **D3 Repo visibility:** make it private (recommended).
- **D4 Music source:** your own licensed library in a Drive folder (e.g. tracks from the YouTube Audio Library) + generated beds, vs. a paid AI-music API.
- **Accounts you'll need:** a Google Cloud project with billing; an Anthropic API key (paid, prepaid credits); free API keys for Pexels, Pixabay and Freesound (can come later).
