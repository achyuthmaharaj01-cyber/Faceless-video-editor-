# VideoHub contract notes (agent reference)

From VideoHub (commit 2302ba8) `docs/PROJECT-CONTRACT.md`, `ui/review/live.js`, `server/notes.js`, `server/jobs.js`:
- Live page: `renderOut(t)` synchronous + `READY`; the iframe itself is displayed (DOM content is visible);
  note pictures copy only `<canvas>` elements → restore them with `fvs notes`.
- Page / fps / size / length / sound from `.videohub/project.json` `live` (we write it); `__config`/`VH_CONFIG`
  override size/fps/duration; `VH_SCENES` = scene lane; `__vhError` = error toast.
- `renderOut` must be found in the page or a script next to it (no `<base>` resolution) → adapter is inlined.
- Narration row from `words.json` (`[[s, e, "w"], …]`) via `project.json` `transcript`.
- Stems: `audio/vo.wav`, `audio/music.wav`, `audio/sfx.wav`; cues `audio/cues.json` `{cues:[{t,name,gain}]}`.
- Render queue: `node render.mjs <workers>` with env `DUR, WK, ONLY, PREVIEW, FPS, VIDEOHUB_ENCODER`; joins
  `render/chunks/c_NNN.mp4`; sound via `project.json` `render.mux` ({video}/{out}).
- Tools: hub_live, hub_notes, hub_note_update, hub_project, hub_render, hub_job, hub_register_version, hub_workspace,
  hub_cleanup, hub_thumb_*; CLI fallback `node server/cli.js <tool> '<json>'`.
- Never expose port 7788; dev/test hubs use VIDEOHUB_PORT=7799 with scratch data/base dirs.
User-facing guide: docs/videohub-integration.md.
