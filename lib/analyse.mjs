// Voiceover analysis + script alignment (wraps scripts/audio-analysis/voiceover.py).
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { REPO_ROOT } from './videohub/build-preview.mjs';
import { python } from './videohub/notes.mjs';
import { LAYOUT, markStage, readJson } from './project.mjs';

export async function analyse(projectDir, { model = process.env.FVS_WHISPER_MODEL || 'small.en', force = false } = {}) {
  const dir = path.resolve(projectDir);
  const meta = readJson(path.join(dir, 'project.fvs.json'));
  if (!meta) throw new Error(`not a faceless-video-studio project: ${dir}`);
  const args = [path.join(REPO_ROOT, 'scripts', 'audio-analysis', 'voiceover.py'), path.join(dir, meta.inputs.voice),
    path.join(dir, LAYOUT.analysis, 'script.json'), '--out', path.join(dir, LAYOUT.analysis), '--words', path.join(dir, LAYOUT.audio, 'words.json'), '--model', model];
  if (force) args.push('--force');
  markStage(dir, 'analyse', 'running');
  const r = spawnSync(python(), args, { encoding: 'utf8', env: { ...process.env, HF_HUB_DISABLE_XET: '1' }, maxBuffer: 1 << 26 });
  if (r.status !== 0) { markStage(dir, 'analyse', 'failed', { error: (r.stderr || '').slice(-500) }); throw new Error('voiceover analysis failed: ' + (r.stderr || r.stdout).slice(-800)); }
  const summary = JSON.parse(r.stdout.trim().split('\n').pop());
  const al = readJson(path.join(dir, LAYOUT.analysis, 'alignment.json'));
  const review = al.mismatches.filter(m => !m.benign);
  markStage(dir, 'analyse', 'done', { matched: summary.matched_ratio, mismatchesNeedingReview: review.length });
  return { ...summary, mismatchesNeedingReview: review, files: ['analysis/voiceover.json', 'analysis/alignment.json', 'audio/words.json'] };
}
