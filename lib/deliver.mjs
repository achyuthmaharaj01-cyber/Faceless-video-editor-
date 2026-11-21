// Package the deliverables of an approved, rendered, quality-checked project.
import fs from 'node:fs';
import path from 'node:path';
import { LAYOUT, readJson, readState, markStage } from './project.mjs';

export async function deliver(projectDir, { to } = {}) {
  const dir = path.resolve(projectDir);
  const st = readState(dir);
  const meta = readJson(path.join(dir, 'project.fvs.json'));
  const render = [...st.renders].reverse().find(r => !r.draft && r.exitCode === 0);
  if (!render) throw new Error('no final render yet (fvs render after approval)');
  if (!st.approval || st.approval.indexHash !== render.indexHash) throw new Error('the last final render is not the approved composition');
  const qc = readJson(path.join(dir, LAYOUT.reports, 'quality-control.json'));
  if (!qc) throw new Error('run fvs qc first');
  const out = path.resolve(to || path.join(dir, 'deliverables'));
  fs.mkdirSync(out, { recursive: true });
  const copy = (src, name) => { const s = path.join(dir, src); if (fs.existsSync(s)) { fs.copyFileSync(s, path.join(out, name || path.basename(src))); return name || path.basename(src); } return null; };
  const files = [
    copy(render.file, `${path.basename(render.file)}`),
    copy(path.join(LAYOUT.reports, 'quality-control-report.md')),
    copy(path.join(LAYOUT.reports, 'attributions.txt')),
    copy(path.join(LAYOUT.assets, 'asset-licence-register.csv')),
    copy(path.join(LAYOUT.storyboard, 'storyboard.md')),
  ].filter(Boolean);
  fs.writeFileSync(path.join(out, 'production-summary.md'), `# ${meta.title}\n\n- Video: ${files[0]}\n- Approved by: ${st.approval.by} (${st.approval.at})\n- Rendered: ${render.at} with HyperFrames (${render.seconds} s)\n- QC: ${qc.fail.length} failed, ${qc.warn.length} warnings, ${qc.manual.length} manual-review items\n- Revisions: ${st.revision}\n`);
  files.push('production-summary.md');
  markStage(dir, 'deliver', 'done', { to: out, files: files.length });
  return { folder: out, files, qcFailed: qc.fail.length, next: 'Upload this folder to Google Drive (YouTube Production/Completed Videos/<title>/) — see docs/google-drive.md' };
}
