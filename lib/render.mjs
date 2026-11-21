// Final rendering through HyperFrames (the authoritative renderer).
import fs from 'node:fs';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { REPO_ROOT, fnv1a } from './videohub/build-preview.mjs';
import { readState, writeState, LAYOUT, slugify } from './project.mjs';

export function hyperframesBin() {
  return path.join(REPO_ROOT, 'node_modules', '.bin', process.platform === 'win32' ? 'hyperframes.cmd' : 'hyperframes');
}

export function indexHash(dir) { return fnv1a(fs.readFileSync(path.join(dir, 'index.html'), 'utf8')); }

function nextVersion(dir, base) {
  const rdir = path.join(dir, LAYOUT.renders);
  if (!fs.existsSync(rdir)) return 1;
  return fs.readdirSync(rdir).reduce((m, f) => { const x = f.match(new RegExp(`^${base}_v(\\d+)\\.mp4$`)); return x ? Math.max(m, +x[1] + 1) : m; }, 1);
}

/**
 * Render index.html with HyperFrames.
 *  draft   – fast low-quality render (allowed any time; never a deliverable)
 *  source  – 'agent' (default) needs a recorded approval that matches the current index.html;
 *            'videohub' = the user pressed Render in VideoHub (their explicit action), recorded as such.
 */
export async function render(dir, { out, draft = false, fps = 30, workers = process.env.FVS_RENDER_WORKERS || 2, source = 'agent', start, end, lowMemory } = {}) {
  dir = path.resolve(dir);
  const st = readState(dir);
  const hash = indexHash(dir);
  if (!draft && source === 'agent') {
    if (!st.approval) throw new Error('Not approved: the final render runs only after the user approves the VideoHub preview (record it with `fvs approve`).');
    if (st.approval.indexHash !== hash) throw new Error(`index.html changed after approval (approved ${st.approval.indexHash}, now ${hash}). Show the change in VideoHub and get approval again.`);
  }
  const title = slugify(readJsonSafe(path.join(dir, '.videohub', 'project.json'))?.title || path.basename(dir));
  const output = path.resolve(dir, out || path.join(LAYOUT.renders, draft ? `${title}_draft.mp4` : `${title}_v${nextVersion(dir, title)}.mp4`));
  fs.mkdirSync(path.dirname(output), { recursive: true });
  const args = ['render', dir, '-o', output, '--fps', String(fps), '-q', draft ? 'draft' : 'looks', '-w', String(workers), '--no-best-effort'];
  if (start != null) args.push('--start', String(start));
  if (end != null) args.push('--end', String(end));
  if (lowMemory) args.push('--low-memory-mode');
  const t0 = Date.now();
  const code = await new Promise((resolve, reject) => {
    const p = spawn(hyperframesBin(), args, { stdio: 'inherit', shell: process.platform === 'win32', env: { ...process.env, HYPERFRAMES_NO_UPDATE_CHECK: '1' } });
    p.on('error', reject); p.on('exit', resolve);
  });
  const rec = { at: new Date().toISOString(), source, draft, file: path.relative(dir, output), indexHash: hash, seconds: Math.round((Date.now() - t0) / 1000), exitCode: code, args };
  const st2 = readState(dir);
  st2.renders.push(rec);
  st2.history.push({ at: rec.at, event: draft ? 'render:draft' : 'render:final', source, file: rec.file, exitCode: code });
  writeState(dir, st2);
  if (code !== 0 || !fs.existsSync(output)) throw new Error(`hyperframes render failed (exit ${code})`);
  return { ...rec, output };
}

function readJsonSafe(f) { try { return JSON.parse(fs.readFileSync(f, 'utf8')); } catch { return null; } }
