# Faceless Video Studio

A cloud video-production system driven by a Claude Skill (`/faceless-video-studio`). You provide a script and voiceover in Google Drive; a Google Cloud backend analyses them, storyboards, sources licensed media, builds motion graphics with Remotion/FFmpeg, renders, runs quality control, and delivers the finished video to Drive.

- Phase 1 audit: [docs/PHASE1_ENVIRONMENT_AUDIT.md](docs/PHASE1_ENVIRONMENT_AUDIT.md)
- Implementation plan: [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md)

**Status:** Phase 1 (environment audit) is complete. Phases 4–5 (Skill and backend code) can start now. Phases 2–3 (reference access and analysis) need Google Cloud and Drive access first.

> This repository contains **code and text only**. Reference footage, voiceovers, renders and credentials live in private Google Cloud Storage, Google Drive and Secret Manager, never in Git.
