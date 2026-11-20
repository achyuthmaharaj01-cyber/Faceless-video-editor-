# Phase 1 — Environment Audit

First audit: 2026-11-20 (session `…44zcevNm7bNUQWua`). **Re-verified and extended: 2026-11-20 (session `…gH9cMoi6j8rEEypNNt`).**
Every row below was checked by running a command in a session. Nothing is assumed.

## 1. Claude Code session (this container)

| Item | Result |
|---|---|
| Machine | Ubuntu 24.04, 4 vCPU, 15 GiB RAM, ~60 GB free disk. **Temporary**: reclaimed when the session goes idle |
| FFmpeg / ffprobe | 6.1.1 ✅ |
| Node / npm | 22.23 / 10.9 ✅ |
| Python | 3.13 ✅. OpenCV 5.1, PySceneDetect and faster-whisper 1.2.1 **install and import from PyPI** ✅ |
| Chromium | Playwright headless shell at `/opt/pw-browsers/chromium_headless_shell-1243/…` ✅ |
| Docker | CLI only, **no daemon** (`/var/run/docker.sock` absent). Images are built with **Cloud Build** |
| gcloud / gsutil / bq | SDK 570 installed, **no usable credentials**. `CLOUDSDK_AUTH_ACCESS_TOKEN` is present in the environment but Google rejects it (`invalid_token`), so it is a placeholder, not access |
| Google Drive | **No Drive connector** (only an unconnected Google Calendar connector). `drive.google.com` is blocked; the Drive API answers `401` without a token |
| GitHub | Push access to `achyuthmaharaj01-cyber/Faceless-video-editor-` ✅. The repo is still **PUBLIC** ⚠️. Its default branch is a stale session branch (`ccr-e58a7e6f-b0jpkx`) and should become `main` |
| Claude environment | "Default", limited network: package registries + MCP servers only, no extra hosts, no setup script |

## 2. Proven by actual test runs in this session

| Test | Result |
|---|---|
| **Remotion 4.0.545 render** (spring and interpolate animation, 1920×1080, 90 frames) | ✅ 5.2 s → **≈17 fps on 4 vCPU**. ffprobe: h264, 1920×1080, 30/1, 3.000 s. The frame was inspected visually and is correct |
| **Remotion + Three.js** (`@remotion/three`, lit rotating mesh, software GL `gl: 'swangle'`, 60 frames) | ✅ 5.1 s → **≈12 fps without a GPU**. The frame was inspected visually and is correct |
| **Scene detection** on a synthetic clip with cuts at 2.0 s and 5.0 s | ⚠️ PySceneDetect `ContentDetector` at its default threshold **missed the 5.0 s cut** (hue change, similar luma). `AdaptiveDetector`, `HistogramDetector` and `ContentDetector(threshold=15)` found both. **Design consequence:** the reference analysis uses an ensemble of detectors plus frame-difference confirmation, not one default detector |
| Remotion's own Chrome download | Blocked here (Remotion CDN). Solved by passing `browserExecutable`. The cloud image installs Chrome at build time on Cloud Build, which has open internet |

## 3. Network reach from this session (allowlist proxy, re-probed)

| Reachable ✅ | Blocked ❌ |
|---|---|
| `*.googleapis.com` (Drive API, OAuth token, Cloud Run, Cloud Build, Firestore, Secret Manager, Storage) | `drive.google.com`, `youtube.com` |
| `accounts.google.com`, `api.anthropic.com` | Wikimedia (`commons`, `upload`), Openverse, archive.org, NASA, LoC |
| npm, PyPI | Pexels, Pixabay, Unsplash, Freesound |
| | `huggingface.co` (Whisper weights), `us-docker.pkg.dev`, Remotion CDN, `*.run.app` |

These blocks apply **only to this Claude session**. The Cloud Run backend has normal outbound internet, so media research, model downloads and rendering work there. The Skill needs exactly one extra host in the Claude environment, the deployed backend's `*.run.app` hostname. I'll propose that through the environment approval prompt after deployment, plus the API token through the secure credential form.

## 4. Constraints and their consequences

1. **The Claude session is temporary.** State lives in GCS, Firestore and Drive; code lives in GitHub.
2. **No Docker daemon.** Images build on Cloud Build.
3. **No Google credentials exist anywhere yet.** **Phase 2 (reference inventory) is blocked.** I have not accessed your Drive folder, and the reference videos have not been seen.
4. **Drive through user OAuth.** A service account can read a folder shared with it, but it cannot own uploads in a personal My Drive (no storage quota). Uploads need *your* OAuth refresh token, which goes in Secret Manager.
5. **Public repo.** No frames, media or credentials ever go into Git. Making it private is recommended.
6. **Mobile-only operator.** Every human step must work in a phone browser: Cloud Console, Cloud Shell, Drive, Claude.

## 5. Licensing notes

- **Remotion** is free for individuals and companies with ≤3 employees.
- **Google OAuth "Testing" mode** expires refresh tokens after **7 days**. The consent screen must be set to *In production* (unverified, personal use).
- **CC BY-SA** is excluded by default (share-alike risk for a monetised work). **NC and ND are never allowed.** Default allowlist: CC0, Public Domain Mark, US-Gov PD, CC BY, Pexels License, Pixabay Content License.
- **GitHub-hosted Actions runners were considered as free render compute and rejected.** GitHub's Actions terms restrict hosted runners to work related to the repository's software project, and logs and artifacts would sit next to a public repo.
