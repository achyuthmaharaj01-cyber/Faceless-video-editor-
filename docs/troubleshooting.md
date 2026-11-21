# Troubleshooting

| Symptom | Cause / fix |
|---|---|
| VideoHub: "Preview is out of date: index.html changed…" | the preview page is generated from index.html: run `fvs preview <project>` (or `fvs build`) |
| VideoHub: "does not define window.renderOut" | old preview layout: run `fvs preview <project>` (the adapter is inlined into `preview/videohub.html`) |
| VideoHub note picture is black with only the drawing | expected for DOM compositions: `fvs notes <project>` rebuilds it from a HyperFrames frame |
| Scene lane empty in VideoHub | regenerate the preview (`fvs preview`); scene names come from `data-fvs-scene` on the hosts in index.html |
| `hyperframes lint`: `multiple_root_compositions` | a stray root-level HTML with `data-composition-id` (old `videohub.html`): `fvs preview` removes the generated one |
| 3D scene blank | `vendor/three.core.min.js` missing (Three r16x+ module build imports it): re-run `fvs new` template copy or copy it from `node_modules/three/build/` |
| Map pins invisible | an SVG with zero size: keep explicit `width/height` (fixed in the builder) |
| `fetch failed` when downloading assets | the media host is not allowed by the network (cloud environment allowlist) or offline |
| Wikimedia HTTP 429 | set `FVS_HTTP_USER_AGENT` with a contact; shared cloud IPs may still be rate-limited |
| Whisper model download fails | Hugging Face hosts blocked; on the cloud environment `huggingface.co`, `us.aws.cdn.hf.co`, `cas-server.xethub.hf.co` must be allowed; `HF_HUB_DISABLE_XET=1` is set by fvs |
| `open() got an unexpected keyword argument 'metadata_errors'` | PyAV incompatibility inside faster-whisper's decoder; fvs decodes with FFmpeg instead (update the repo) |
| Mix lands below −14 LUFS with a warning | the voice's peaks limit the static gain; approve limiting (`storyboard.audio.limiter: true` + who approved) or accept |
| `fvs render`: "Not approved" / "changed after approval" | by design: review in VideoHub and record the user's approval of the current version |
| Renders run out of memory on the laptop | `fvs render <project> --low-memory`, `FVS_RENDER_WORKERS=1`, close other browsers |
| Node `fetch` ignores the proxy | fvs relaunches itself with `NODE_USE_ENV_PROXY=1` when `HTTPS_PROXY` is set |
