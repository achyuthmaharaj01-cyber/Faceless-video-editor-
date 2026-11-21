> **Superseded (2026-11-21):** this plan used Remotion and a custom GCP backend. The current system uses HyperFrames + VideoHub; see README.md and docs/cloud-architecture.md.

# Phase 1 — Environment Audit

Date: 2026-11-20 · Every item below was checked by running a command in this session, not assumed.

## 1. Claude Code session (this container)

| Item | Result |
|---|---|
| Machine | Ubuntu 24.04, 4 vCPU, 15 GiB RAM, ~60 GB free disk. Temporary: reclaimed when the session goes idle |
| FFmpeg / ffprobe | 6.1.1 ✅ |
| Node / npm | 22.23 / 10.9 ✅ (Remotion 4.0.545 is available from npm) |
| Python | 3.13 ✅ numpy is installed; OpenCV, PySceneDetect and faster-whisper are not installed yet (all available from PyPI) |
| Chromium | Playwright Chromium + headless shell in `/opt/pw-browsers` ✅, so Remotion can render here for local tests |
| Docker | CLI only, **no daemon**. Images can't be built here → use **Cloud Build** |
| gcloud / gsutil / bq | SDK 570 installed, **no credentials** (`gcloud auth list` is empty) |
| GitHub | Push access to `achyuthmaharaj01-cyber/Faceless-video-editor-` ✅. The repo is **PUBLIC** ⚠️ |
| Google Drive connector | **Not installed** (only an unconnected Google Calendar connector exists). Drive access must use our own OAuth client |
| Repository | Empty (no commits) on branch `ccr-e58a7e6f-b0jpkx` |

## 2. Network reach from this session (allowlist proxy)

| Reachable ✅ | Blocked ❌ (proxy 403) |
|---|---|
| `*.googleapis.com`: Drive, OAuth token, Cloud Run, Cloud Build, Firestore, Secret Manager, Artifact Registry API, Storage, IAM, Logging, Billing | `drive.google.com` (web UI), `youtube.com` |
| `accounts.google.com` | `*.run.app`, the deployed backend (until its exact host is allowed) |
| `api.anthropic.com` | Wikimedia (`commons`/`upload`), Openverse, NASA, LoC, archive.org |
| npm, PyPI, Docker Hub, GitHub | Pexels, Pixabay, Unsplash, Freesound, ElevenLabs |
| | `huggingface.co` (Whisper model weights), `us-docker.pkg.dev` (image pushes), Remotion CDN |

**What this means:** these blocks apply only to this Claude session. The deployed Cloud Run backend has normal outbound internet access, so production media research, model downloads and rendering are unaffected. For local tests of the research scripts, I'll propose a repo-specific Claude environment that allows those exact hosts. I'll do that when a test actually needs it, and I won't change your Default environment.

## 3. Constraints and their consequences

1. **The Claude session is temporary.** Nothing important can live only here. State goes to GCS, Firestore and Drive; code goes to GitHub.
2. **No Docker daemon.** Images are built with Cloud Build (triggered from GitHub Actions or `gcloud builds submit`).
3. **No Google credentials anywhere yet.** Nothing in GCP or Drive can be verified until you provide access. **Phase 2 (reference inventory) is blocked on this.** I have not accessed your Drive folder and will not claim to have done so.
4. **Drive access through OAuth.** A service account can read a folder shared with it, but it **cannot own uploads in a personal My Drive** (service accounts have no Drive storage quota). Uploads therefore need *your* OAuth refresh token, stored in Secret Manager.
5. **Public repo.** Reference frames, voiceovers, renders and credentials must never be committed. I recommend making the repo private. Only code, docs and the text Style Bible belong in Git.
6. **Mobile-only operator.** Every human step must be doable from a phone browser: Google Cloud Console, Cloud Shell (works in a mobile browser), Drive, and Claude.

## 4. Licensing notes found during the audit

- **Remotion** is free for individuals and companies with ≤3 employees. A company license is needed beyond that.
- **Google OAuth "Testing" mode** expires refresh tokens after **7 days**. The consent screen must be set to *In production* (unverified, personal use, you accept the warning screen once) so the pipeline doesn't break weekly.
- **CC BY-SA** media is risky in a monetised video (share-alike can apply to the whole work). NC and ND licences are not allowed. Default allowlist: CC0, Public Domain Mark, US-Gov PD, CC BY, Pexels License, Pixabay Content License.
