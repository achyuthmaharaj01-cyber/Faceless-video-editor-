# Faceless Video Studio

Script + voiceover in → a professionally edited faceless YouTube video out.

- **HyperFrames** composes and renders (the only video engine).
- **VideoHub** is the mandatory review step: the real HyperFrames composition plays in VideoHub's live preview,
  frame-accurately, with its scenes, narration and sound stems; you draw notes on frames, Claude revises, the preview
  reloads, and nothing is rendered until you approve.
- **Claude** directs through the `/faceless-video-studio` skill (`.claude/skills/faceless-video-studio/SKILL.md`),
  using a style library measured from the eight reference videos.

```
script + voiceover ─► fvs new ─► fvs analyse (word-level alignment) ─► storyboard (Claude + style guide)
  ─► fvs assets (licensed, verified, registered) ─► fvs build (HyperFrames sub-compositions + audio mix)
  ─► fvs qc ─► VideoHub review ⇄ revisions ─► your approval ─► fvs render (HyperFrames) ─► fvs qc ─► delivery
```

## Status

| Area | State |
|---|---|
| HyperFrames → VideoHub adapter | ✅ built and verified in the real VideoHub UI; preview frames pixel-identical to HyperFrames' capture |
| Pipeline (ingest, alignment, storyboard, assets, build, mix, QC, versions, approval gate) | ✅ tested end to end up to approval on a sample film |
| Reference analysis (8 videos, 3,074 shots) + style library | ✅ `references/reference-analysis/` |
| Final render of the sample | ⏳ waits for your approval |
| Drive API for large files, Pexels/Pixabay | implemented, untested (need your OAuth client / free keys) |
| Cloud render backend (GCP/AWS) | designed, not deployed (needs your account + approval) |

Details: [docs/test-report.md](docs/test-report.md).

## Docs

[Installation & configuration](docs/installation.md) · [Usage](docs/usage.md) ·
[Storyboard schema](docs/storyboard-schema.md) · [HyperFrames integration](docs/hyperframes-integration.md) ·
[VideoHub integration](docs/videohub-integration.md) · [Remote review](docs/remote-review.md) ·
[Google Drive](docs/google-drive.md) · [Asset licensing](docs/asset-licensing.md) ·
[Reference analysis](docs/reference-analysis-guide.md) · [Cloud architecture](docs/cloud-architecture.md) ·
[Costs](docs/costs.md) · [Troubleshooting](docs/troubleshooting.md) · [Master style guide](references/reference-analysis/master-style-guide.md)

## Layout

```
.claude/skills/faceless-video-studio/SKILL.md   the skill (workflow Claude follows)
bin/fvs.mjs                                     command line (fvs help)
lib/                                            pipeline: ingest, analyse, storyboard, assets, compose/, audio/, qc/, videohub/, render, deliver
scripts/                                        Python: reference-analysis/, audio-analysis/, storyboard/, asset-research/, sound-design/, quality-control/, videohub/
templates/hyperframes-project/                  styles, motion interpreter, Three.js component
backend/integrations/drive.mjs                  Google Drive API (OAuth, resumable uploads)
references/                                     style library (reference-analysis/), HyperFrames + VideoHub notes
examples/box-that-changed-the-world/            the sample production's storyboard, compositions, QC report, licence register, review notes
learning/                                       production log + proposed style amendments
tests/                                          npm test
```

> This repository holds **code and text only**. Reference footage and frames, voiceovers, renders and credentials
> stay out of Git (private Drive folders, `.env`).
