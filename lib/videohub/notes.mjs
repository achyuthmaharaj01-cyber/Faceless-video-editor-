// Read VideoHub review notes for a HyperFrames film, restore their pictures from real HyperFrames frames,
// and add the context the agent needs (scene, narration at that moment, storyboard scene id).
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { captureViaHyperframes } from './parity.mjs';
import { REPO_ROOT } from './build-preview.mjs';

const OPEN = new Set(['open', 'claude', 'reopened', 'açık', 'hâlâ var', 'hala var']);

function readJson(file, fallback) { try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return fallback; } }

export function python() { return process.env.FVS_PYTHON || (process.platform === 'win32' ? 'python' : 'python3'); }

/** Capture each live note's frame with HyperFrames and redraw the user's drawing on it (once per note). */
export function restoreNotePictures(projectDir, notes) {
  const todo = notes.filter(n => n.file === '~live' && n.images && Number.isFinite(n.frame) && n.fps &&
    !Object.values(n.images).some(p => p && fs.existsSync(String(p).replace(/\.jpg$/, '.vhblank.jpg'))));
  if (!todo.length) return [];
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'fvs-notes-'));
  try {
    const times = [...new Set(todo.map(n => +(n.frame / n.fps).toFixed(3)))];
    const shots = captureViaHyperframes(projectDir, times, tmp);
    const byTime = new Map(shots.map(s => [s.t, s.file]));
    const map = {};
    for (const n of todo) { const f = byTime.get(+(n.frame / n.fps).toFixed(3)); if (f) map[n.id] = f; }
    const notesFile = path.join(tmp, 'notes.json'); fs.writeFileSync(notesFile, JSON.stringify(todo));
    const framesFile = path.join(tmp, 'frames.json'); fs.writeFileSync(framesFile, JSON.stringify(map));
    const r = spawnSync(python(), [path.join(REPO_ROOT, 'scripts', 'videohub', 'note_pictures.py'), notesFile, framesFile], { encoding: 'utf8' });
    if (r.status !== 0) throw new Error('note_pictures.py failed: ' + (r.stderr || r.stdout).slice(-600));
    return JSON.parse(r.stdout.trim().split('\n').pop()).rebuilt;
  } finally { fs.rmSync(tmp, { recursive: true, force: true }); }
}

function narrationAt(words, t, span = 2.5) {
  if (!Array.isArray(words)) return '';
  const norm = words.map(w => Array.isArray(w) ? w : [w.s ?? w.start, w.e ?? w.end, w.w ?? w.word ?? w.text]);
  return norm.filter(([s, e]) => e >= t - span && s <= t + span).map(w => w[2]).join(' ');
}

export function readNotes(projectDir, { all = false, restore = true } = {}) {
  const dir = path.resolve(projectDir);
  const notes = readJson(path.join(dir, '.videohub', 'notes.json'), []);
  const restored = restore ? restoreNotePictures(dir, notes) : [];
  const words = readJson(path.join(dir, 'audio', 'words.json'), null);
  const story = readJson(path.join(dir, 'storyboard', 'storyboard.json'), null);
  const sceneAt = t => story?.scenes?.find(s => t >= s.start && t < s.end) || null;
  const list = notes.filter(n => all || OPEN.has(n.status)).map(n => {
    const sc = sceneAt(n.t);
    return {
      id: n.id, status: n.status, t: +n.t.toFixed(3), t2: n.t2 ?? null, frame: n.frame, kind: n.kind, text: n.text,
      scene: sc ? { id: sc.id, start: sc.start, end: sc.end, visual: sc.visual?.type } : null,
      narration: narrationAt(words, n.t),
      pictures: n.images || {}, restoredPicture: restored.includes(n.id),
    };
  });
  return { project: dir, total: notes.length, notes: list };
}
