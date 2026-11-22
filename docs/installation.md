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
The environment's **setup script** (saved 2026-11-22) installs everything on every fresh container: `npm install`,
`pip install -r requirements.txt`, and Agent-Reach pinned to the reviewed commit `c70ae6d` (via `uv`).

## Agent-Reach (research)

github.com/Panniantong/Agent-Reach gives Claude web search (Exa) and page reading (Jina Reader), plus GitHub,
YouTube metadata/subtitles and more, as one read-only CLI with JSON output. Install (laptop or cloud):

```bash
uv tool install "git+https://github.com/Panniantong/Agent-Reach@c70ae6da5d39bc90e09ad2ae0575ccc89f31e284"
agent-reach setup
```
Notes: install from GitHub only (the PyPI package of the same name is a different project); `setup` links its skill
into `~/.claude/skills`; it never posts and never logs in for you. On a personal computer it may copy a site's login
from your Chrome when a login-walled platform is used, so prefer a secondary account for such platforms. In the
cloud environment the hosts `mcp.exa.ai` and `r.jina.ai` are allowed for it; Wikimedia rate-limits the cloud IP
(HTTP 429), so Wikimedia sourcing works from the laptop.

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
