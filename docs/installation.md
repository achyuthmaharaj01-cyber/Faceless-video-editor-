# Installation and configuration

## Windows laptop (i5-1335U, 16 GB, integrated graphics)

```powershell
winget install -e --id OpenJS.NodeJS.LTS
winget install -e --id Gyan.FFmpeg
winget install -e --id Python.Python.3.12
git clone https://github.com/achyuthmaharaj01-cyber/Faceless-video-editor-.git
cd Faceless-video-editor-
npm install
python -m pip install -r requirements.txt
copy .env.example .env      # then fill in what you use
node bin/fvs.mjs doctor
```
- Install VideoHub (docs/videohub-integration.md) and set `FVS_WORKSPACE` to its films folder and `VIDEOHUB_DIR`
  to its install folder in `.env`.
- Make the skill available everywhere: copy or link `.claude/skills/faceless-video-studio` into
  `%USERPROFILE%\.claude\skills\` and set `FVS_HOME` to this folder (inside the repository it is found automatically).
- The first `fvs analyse` downloads the Whisper model (`small.en`, ≈ 500 MB) once.
- Render settings for this laptop: `FVS_RENDER_WORKERS=2`; add `--low-memory` to `fvs render` if Chrome runs out of
  memory. Close other browsers during renders.

## Claude Code cloud session (phone)

The repository includes the skill. The `faceless-video-editor` cloud environment allows the hosts the pipeline
needs (Whisper weights on Hugging Face, Openverse/NASA/Pexels/Pixabay/Wikimedia/Flickr/rawpixel media, jsDelivr).
A fresh container needs, once per session (or as the environment's setup script):

```bash
npm install
pip install -r requirements.txt
```

## Configuration (`.env`, never committed)

| Variable | Purpose |
|---|---|
| `PEXELS_API_KEY`, `PIXABAY_API_KEY` | free stock keys (higher-resolution photos and video) |
| `FVS_HTTP_USER_AGENT` | identify the client to Wikimedia (include a contact) |
| `FVS_WORKSPACE` | where projects are created (VideoHub films folder) |
| `VIDEOHUB_DIR` | VideoHub install folder |
| `FVS_PYTHON` | Python executable if not `python`/`python3` |
| `FVS_WHISPER_MODEL` | `small.en` (default, accurate) or `base.en` (faster) |
| `FVS_RENDER_WORKERS` | HyperFrames render workers (default 2) |
| `FVS_ALLOW_SHARE_ALIKE` | `1` accepts CC BY-SA media (off by default) |
| `FVS_MASTER_GAIN` | `off` skips the static loudness gain |
| `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, `FVS_GOOGLE_REFRESH_TOKEN` | Drive API (docs/google-drive.md) |

Load `.env` in your shell (or with a tool like `dotenv`); no secret is ever written into the project or the repo.
