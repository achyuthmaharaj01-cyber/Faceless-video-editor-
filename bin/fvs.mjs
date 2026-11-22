#!/usr/bin/env node
// faceless-video-studio command line. Every stage is a separate, resumable command; `fvs help` lists them.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));

// Settings and keys: the studio folder's .env is loaded automatically (variables already set in the shell win).
const ENV_FILE = path.join(HERE, '..', '.env');
if (fs.existsSync(ENV_FILE)) {
  try { process.loadEnvFile(ENV_FILE); } catch (e) { console.error(`fvs: could not read ${ENV_FILE}: ${e.message}`); }
}

// Node's fetch ignores HTTPS_PROXY unless NODE_USE_ENV_PROXY=1 (Node >= 22.21). Behind a proxy, re-launch with it.
if ((process.env.HTTPS_PROXY || process.env.https_proxy) && !process.env.NODE_USE_ENV_PROXY) {
  const { spawnSync } = await import('node:child_process');
  const r = spawnSync(process.execPath, ['--disable-warning=UNDICI-EHPA', ...process.argv.slice(1)], { stdio: 'inherit', env: { ...process.env, NODE_USE_ENV_PROXY: '1' } });
  process.exit(r.status ?? 1);
}

function parse(argv) {
  const pos = [], opt = {};
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const [k, v] = a.slice(2).split('=');
      const key = k.replace(/-([a-z])/g, (_, c) => c.toUpperCase());
      if (v !== undefined) opt[key] = v;
      else if (argv[i + 1] && !argv[i + 1].startsWith('--')) opt[key] = argv[++i];
      else opt[key] = true;
    } else pos.push(a);
  }
  return { pos, opt };
}

const out = obj => console.log(typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2));
const need = (v, what) => { if (!v) throw new Error(`missing ${what}`); return v; };

const COMMANDS = {
  async doctor() { const m = await import('../lib/doctor.mjs'); const r = await m.doctor(); out(r.text); process.exitCode = r.ok ? 0 : 1; },

  async new({ pos, opt }) {
    const m = await import('../lib/ingest.mjs');
    out(await m.createProject({ name: need(pos[0], 'project name'), script: need(opt.script, '--script'), voice: need(opt.voice, '--voice'),
      workspace: opt.workspace, format: opt.format || 'long', title: opt.title }));
  },
  async analyse({ pos, opt }) { const m = await import('../lib/analyse.mjs'); out(await m.analyse(need(pos[0], 'project'), { model: opt.model, force: !!opt.force })); },
  async 'storyboard-draft'({ pos, opt }) { const m = await import('../lib/storyboard.mjs'); out(m.draftStoryboard(need(pos[0], 'project'), { force: !!opt.force })); },
  async 'storyboard-check'({ pos }) { const m = await import('../lib/storyboard.mjs'); const r = m.checkStoryboard(need(pos[0], 'project')); out(r); process.exitCode = r.ok ? 0 : 1; },
  async assets({ pos, opt }) { const m = await import('../lib/assets.mjs'); out(await m.acquireAssets(need(pos[0], 'project'), { scene: opt.scene, dryRun: !!opt.dryRun })); },
  async 'asset-search'({ pos, opt }) {
    const m = await import('../lib/assets.mjs');
    const r = await m.search(need(opt.query, '--query'), { kind: opt.kind || 'image', sources: opt.sources, limit: +(opt.limit || 8) });
    if (opt.sheet) {   // a contact sheet of the accepted candidates, numbered, for visual review
      const { spawnSync } = await import('node:child_process');
      const { python } = await import('../lib/videohub/notes.mjs');
      const tmp = path.join(path.dirname(path.resolve(opt.sheet)), '.candidates.json');
      fs.writeFileSync(tmp, JSON.stringify(r.accepted.filter(c => c.thumb).map(c => ({ thumb: c.thumb, label: `${c.source.replace('openverse/', '')} ${c.width || '?'}x${c.height || '?'} ${c.licence.name}` }))));
      spawnSync(python(), [path.join(HERE, '..', 'scripts', 'asset-research', 'thumb_sheet.py'), tmp, opt.sheet], { stdio: 'inherit' });
      fs.rmSync(tmp, { force: true });
    }
    if (opt.save) fs.writeFileSync(opt.save, JSON.stringify(r, null, 2));
    out(opt.brief ? { query: r.query, errors: r.errors, skipped: r.skipped, refused: r.refused.length,
      accepted: r.accepted.filter(c => !opt.sheet || c.thumb).map((c, i) => `[${i}] ${c.source} | ${c.licence.name} | ${c.width || '?'}x${c.height || '?'} | ${(c.title || '').slice(0, 60)} | ${c.landing}`) } : r);
  },
  async build({ pos, opt }) { const m = await import('../lib/compose/build.mjs'); out(await m.build(need(pos[0], 'project'), { reason: opt.reason })); },
  async mix({ pos }) { const m = await import('../lib/audio/mix.mjs'); out(await m.mixProject(need(pos[0], 'project'))); },

  async preview({ pos, opt }) {
    const { buildPreview } = await import('../lib/videohub/build-preview.mjs');
    const dir = need(pos[0], 'project');
    const r = buildPreview(dir, { fps: +(opt.fps || 30) });
    out({ ...r, page: path.join(path.resolve(dir), 'preview', 'videohub.html') });
    if (opt.watch) {
      out('watching index.html; Ctrl+C to stop');
      let t = 0;
      fs.watch(path.resolve(dir), (ev, f) => {
        if (f !== 'index.html') return;
        clearTimeout(t); t = setTimeout(() => { try { const x = buildPreview(dir, { fps: +(opt.fps || 30) }); if (x.changed.length) out(`regenerated: ${x.changed.join(', ')}`); } catch (e) { console.error(e.message); } }, 150);
      });
      await new Promise(() => {});
    }
  },
  async 'verify-preview'({ pos, opt }) {
    const { verifyParity } = await import('../lib/videohub/parity.mjs');
    const { readRootMeta } = await import('../lib/videohub/build-preview.mjs');
    const dir = path.resolve(need(pos[0], 'project'));
    const { duration } = readRootMeta(fs.readFileSync(path.join(dir, 'index.html'), 'utf8'));
    const fps = +(opt.fps || 30), n = +(opt.samples || 8);
    const times = opt.at ? String(opt.at).split(',').map(Number)
      : Array.from({ length: n }, (_, i) => Math.round(((i + 0.5) * duration / n) * fps) / fps);
    const r = await verifyParity(dir, times, path.join(dir, '.fvs', 'parity'), { minPsnr: +(opt.minPsnr || 35) });
    out(r); process.exitCode = r.pass ? 0 : 1;
  },
  async notes({ pos, opt }) { const m = await import('../lib/videohub/notes.mjs'); out(m.readNotes(need(pos[0], 'project'), { all: !!opt.all })); },

  async snapshot({ pos, opt }) { const m = await import('../lib/project.mjs'); out({ snapshot: m.snapshot(path.resolve(need(pos[0], 'project')), opt.reason || 'manual') }); },
  async approve({ pos, opt }) {
    const { approve } = await import('../lib/project.mjs');
    const { indexHash } = await import('../lib/render.mjs');
    const dir = path.resolve(need(pos[0], 'project'));
    out(approve(dir, { by: opt.by, note: opt.note, hash: indexHash(dir) }));
  },
  async render({ pos, opt }) {
    const m = await import('../lib/render.mjs');
    out(await m.render(need(pos[0], 'project'), { out: opt.out, draft: !!opt.draft, fps: +(opt.fps || 30), workers: opt.workers, source: opt.source || 'agent',
      start: opt.start, end: opt.end, lowMemory: !!opt.lowMemory }));
  },
  async qc({ pos, opt }) { const m = await import('../lib/qc/qc.mjs'); const r = await m.qualityControl(need(pos[0], 'project'), { video: opt.video }); out(r.summary); process.exitCode = r.failed ? 1 : 0; },
  async deliver({ pos, opt }) { const m = await import('../lib/deliver.mjs'); out(await m.deliver(need(pos[0], 'project'), { to: opt.to })); },
  async 'drive-auth'() { const d = await import('../backend/integrations/drive.mjs'); out(await d.authorize()); },
  async 'drive-pull'({ pos, opt }) {
    // newest script + voiceover from YouTube Production/Input → a local folder (then `fvs new` with them)
    const d = await import('../backend/integrations/drive.mjs');
    const tree = await d.ensureTree(opt.root);
    const { script, voice } = await d.findInputs(tree.Input);
    if (!script || !voice) throw new Error(`Input folder needs a script and a voiceover (found script: ${script?.name || 'none'}, voice: ${voice?.name || 'none'})`);
    const dir = path.resolve(pos[0] || 'drive-input'); fs.mkdirSync(dir, { recursive: true });
    const sName = script.mimeType === 'application/vnd.google-apps.document' ? `${script.name}.txt` : script.name;
    out({ script: await d.download(script, path.join(dir, sName)), voice: await d.download(voice, path.join(dir, voice.name)) });
  },
  async 'drive-push'({ pos, opt }) {
    // upload deliverables/ (final video, QC report, register, credits) to Completed Videos/<title>/
    const d = await import('../backend/integrations/drive.mjs');
    const dir = path.resolve(need(pos[0], 'project'));
    const src = path.join(dir, 'deliverables');
    if (!fs.existsSync(src)) throw new Error('run `fvs deliver` first');
    const title = JSON.parse(fs.readFileSync(path.join(dir, 'project.fvs.json'), 'utf8')).title;
    const tree = await d.ensureTree(opt.root);
    const folder = await d.ensureFolder(title, tree['Completed Videos']);
    const res = [];
    for (const f of fs.readdirSync(src)) res.push({ file: f, ...(await d.upload(path.join(src, f), folder, { mimeType: f.endsWith('.mp4') ? 'video/mp4' : f.endsWith('.csv') ? 'text/csv' : 'text/plain' })) });
    out(res);
  },
  async status({ pos }) {
    const { readState } = await import('../lib/project.mjs');
    const st = readState(path.resolve(need(pos[0], 'project')));
    out({ stages: st.stages, revision: st.revision, approval: st.approval, renders: st.renders.slice(-3), recent: st.history.slice(-8) });
  },
  help() {
    out(`fvs — faceless-video-studio

  doctor                                   check tools (node, ffmpeg, python deps, hyperframes, browser, VideoHub)
  new <name> --script F --voice F          create a project and ingest the inputs  [--format long|short] [--workspace DIR]
  analyse <project>                        voiceover analysis + word alignment + script analysis
  storyboard-draft <project>               first-pass storyboard.json from the analysis (Claude then refines it)
  storyboard-check <project>               validate storyboard.json (timing, coverage, schema)
  asset-search --query Q [--kind image|video|audio]   search licensed sources (prints licence facts)
  assets <project>                         download every asset the storyboard asks for + licence register
  build <project>                          storyboard → HyperFrames index.html, audio mix, preview page
  mix <project>                            rebuild the audio mix (voice untouched, music ducked, SFX cues)
  preview <project> [--watch]              regenerate the VideoHub page (videohub.html) + .videohub/project.json
  verify-preview <project>                 compare VideoHub-adapter frames with HyperFrames' own frames
  notes <project> [--all]                  VideoHub notes with real frame pictures + narration context
  snapshot <project> --reason R            keep a copy of the current version before a revision
  approve <project> --by WHO               record the user's approval of the current composition
  render <project> [--draft]               HyperFrames render (final needs approval)  [--low-memory]
  qc <project> [--video F]                 quality-control report → reports/quality-control-report.md
  deliver <project> [--to DIR]             package the deliverables
  status <project>                         stages, approval, renders, history
  drive-auth                               one-time Google OAuth consent (laptop / backend; see docs/google-drive.md)
  drive-pull [dir]                         download the newest script + voiceover from YouTube Production/Input
  drive-push <project>                     upload deliverables/ to YouTube Production/Completed Videos/<title>`);
  },
};

const [cmd, ...rest] = process.argv.slice(2);
const fn = COMMANDS[cmd || 'help'];
if (!fn) { console.error(`unknown command: ${cmd}`); COMMANDS.help(); process.exit(2); }
try { await fn(parse(rest)); } catch (e) { console.error(`fvs ${cmd}: ${e.message}`); process.exit(1); }
