// Project folder layout, resumable stage state, approvals and version snapshots.
import fs from 'node:fs';
import path from 'node:path';

export const LAYOUT = {
  input: 'input',            // the user's script + original voiceover (never modified)
  analysis: 'analysis',      // voiceover / script / alignment analysis
  storyboard: 'storyboard',  // storyboard.json (+ storyboard.md)
  assets: 'assets',          // downloaded + generated media, asset-licence-register.csv
  audio: 'audio',            // vo.wav, music.wav, sfx.wav, mix.wav, words.json, cues.json
  renders: 'renders',        // final renders
  reports: 'reports',        // quality-control-report.md, production report
  versions: 'versions',      // snapshots of index.html + storyboard per revision
};

export const STAGES = ['ingest', 'analyse', 'storyboard', 'assets', 'build', 'preview', 'review', 'approve', 'render', 'qc', 'deliver'];

const stateFile = dir => path.join(dir, '.fvs', 'state.json');

export function readJson(file, fallback = null) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch { return fallback; }
}
export function writeJson(file, obj) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const tmp = file + '.tmp';
  fs.writeFileSync(tmp, JSON.stringify(obj, null, 2) + '\n');
  fs.renameSync(tmp, file);
}

export function readState(dir) {
  return readJson(stateFile(dir), { version: 1, stages: {}, history: [], renders: [], approval: null, revision: 0 });
}
export function writeState(dir, st) { writeJson(stateFile(dir), st); }

export function log(dir, event, data = {}) {
  const st = readState(dir);
  st.history.push({ at: new Date().toISOString(), event, ...data });
  writeState(dir, st);
}

export function markStage(dir, stage, status, data = {}) {
  const st = readState(dir);
  st.stages[stage] = { status, at: new Date().toISOString(), ...data };
  st.history.push({ at: st.stages[stage].at, event: `stage:${stage}:${status}`, ...data });
  writeState(dir, st);
}

export function stageDone(dir, stage) { return readState(dir).stages[stage]?.status === 'done'; }

export function slugify(s) {
  return String(s).toLowerCase().normalize('NFKD').replace(/[^\w\s-]/g, '').trim().replace(/[\s_]+/g, '-').replace(/-+/g, '-').slice(0, 60) || 'film';
}

/** Copy index.html, compositions/ and storyboard into versions/rNNN before a revision changes them. */
export function snapshot(dir, reason) {
  const st = readState(dir);
  const rev = (st.revision || 0) + 1;
  const dst = path.join(dir, LAYOUT.versions, `r${String(rev).padStart(3, '0')}`);
  fs.mkdirSync(dst, { recursive: true });
  for (const rel of ['index.html', 'compositions', 'styles', path.join('storyboard', 'storyboard.json'), path.join('audio', 'cues.json')]) {
    const src = path.join(dir, rel);
    if (fs.existsSync(src)) fs.cpSync(src, path.join(dst, rel), { recursive: true });
  }
  fs.writeFileSync(path.join(dst, 'REASON.txt'), `${new Date().toISOString()}\n${reason}\n`);
  st.revision = rev;
  st.history.push({ at: new Date().toISOString(), event: 'snapshot', revision: rev, reason });
  writeState(dir, st);
  return dst;
}

/** Approval is recorded only from an explicit user statement and is tied to the exact composition. */
export function approve(dir, { by, note, hash }) {
  if (!by) throw new Error('approve needs --by (who approved, e.g. "user in chat")');
  const st = readState(dir);
  st.approval = { at: new Date().toISOString(), by, note: note || null, indexHash: hash };
  st.history.push({ at: st.approval.at, event: 'approved', by, note: note || null, indexHash: hash });
  writeState(dir, st);
  return st.approval;
}
