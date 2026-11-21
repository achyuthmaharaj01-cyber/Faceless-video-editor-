// Create a production project from a script + voiceover. The originals are copied untouched into input/.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { REPO_ROOT } from './videohub/build-preview.mjs';
import { LAYOUT, slugify, writeJson, markStage, readState, writeState } from './project.mjs';
import { python } from './videohub/notes.mjs';

export const SCRIPT_EXT = ['.txt', '.md', '.markdown', '.docx'];
export const VOICE_EXT = ['.wav', '.mp3', '.m4a', '.aac', '.flac'];
export const FORMATS = { long: { width: 1920, height: 1080, fps: 30 }, short: { width: 1080, height: 1920, fps: 30 } };

export function defaultWorkspace() {
  return process.env.FVS_WORKSPACE || path.join(os.homedir(), 'VideoStudio', 'films');
}

function run(cmd, args, opts = {}) {
  const r = spawnSync(cmd, args, { encoding: 'utf8', maxBuffer: 1 << 28, ...opts });
  if (r.status !== 0) throw new Error(`${path.basename(cmd)} failed: ${(r.stderr || r.stdout || '').slice(-800)}`);
  return r.stdout;
}

export function probeAudio(file) {
  const d = JSON.parse(run('ffprobe', ['-v', 'error', '-print_format', 'json', '-show_format', '-show_streams', file]));
  const a = d.streams.find(s => s.codec_type === 'audio');
  if (!a) throw new Error(`${file} has no audio stream`);
  return { codec: a.codec_name, sampleRate: +a.sample_rate, channels: a.channels, duration: +(+d.format.duration).toFixed(3) };
}

/** Copy the project skeleton: vendored GSAP, fonts, base styles, hyperframes.json. */
export function installTemplate(dir) {
  const tpl = path.join(REPO_ROOT, 'templates', 'hyperframes-project');
  fs.cpSync(tpl, dir, { recursive: true, force: false, errorOnExist: false });
  const vend = path.join(dir, 'vendor');
  fs.mkdirSync(vend, { recursive: true });
  const nm = p => path.join(REPO_ROOT, 'node_modules', p);
  fs.copyFileSync(nm('gsap/dist/gsap.min.js'), path.join(vend, 'gsap.min.js'));
  for (const f of ['three.module.min.js', 'three.core.min.js']) {   // r16x+ module build imports three.core
    if (fs.existsSync(nm(`three/build/${f}`))) fs.copyFileSync(nm(`three/build/${f}`), path.join(vend, f));
  }
  const fonts = path.join(dir, 'fonts');
  fs.mkdirSync(fonts, { recursive: true });
  for (const [pkg, files] of Object.entries({
    inter: ['inter-latin-400-normal.woff2', 'inter-latin-700-normal.woff2', 'inter-latin-800-normal.woff2', 'inter-latin-900-normal.woff2'],
    anton: ['anton-latin-400-normal.woff2'],
    'bebas-neue': ['bebas-neue-latin-400-normal.woff2'],
    'playfair-display': ['playfair-display-latin-700-normal.woff2', 'playfair-display-latin-400-italic.woff2'],
    caveat: ['caveat-latin-700-normal.woff2'],
  })) for (const f of files) { const src = nm(`@fontsource/${pkg}/files/${f}`); if (fs.existsSync(src)) fs.copyFileSync(src, path.join(fonts, f)); }
}

export async function createProject({ name, script, voice, workspace, format = 'long', title }) {
  for (const [f, exts, what] of [[script, SCRIPT_EXT, 'script'], [voice, VOICE_EXT, 'voiceover']]) {
    if (!fs.existsSync(f)) throw new Error(`${what} not found: ${f}`);
    if (!exts.includes(path.extname(f).toLowerCase())) throw new Error(`${what} must be one of ${exts.join(' ')}: ${f}`);
  }
  if (!FORMATS[format]) throw new Error(`format must be long or short`);
  const dir = path.join(path.resolve(workspace || defaultWorkspace()), slugify(name));
  if (fs.existsSync(dir) && fs.readdirSync(dir).length) throw new Error(`project folder already exists and is not empty: ${dir} (pick another name; nothing was overwritten)`);
  for (const sub of Object.values(LAYOUT)) fs.mkdirSync(path.join(dir, sub), { recursive: true });

  const scriptDst = path.join(dir, LAYOUT.input, 'script' + path.extname(script).toLowerCase());
  const voiceDst = path.join(dir, LAYOUT.input, 'voiceover' + path.extname(voice).toLowerCase());
  fs.copyFileSync(script, scriptDst);
  fs.copyFileSync(voice, voiceDst);
  try { fs.chmodSync(voiceDst, 0o444); fs.chmodSync(scriptDst, 0o444); } catch { /* read-only is best effort */ }

  const scriptJson = run(python(), [path.join(REPO_ROOT, 'scripts', 'storyboard', 'script_text.py'), scriptDst]);
  fs.writeFileSync(path.join(dir, LAYOUT.analysis, 'script.json'), scriptJson);
  const sj = JSON.parse(scriptJson);
  if (!sj.stats.words) throw new Error('the script contains no narration text');

  const vo = probeAudio(voiceDst);
  // A PCM copy for mixing and preview. Same samples, no gain, no processing: only container/sample-format
  // (and to 48 kHz stereo when the original differs, which every delivery format needs anyway).
  run('ffmpeg', ['-v', 'error', '-y', '-i', voiceDst, '-ar', '48000', '-ac', '2', '-c:a', 'pcm_s24le', path.join(dir, LAYOUT.audio, 'vo.wav')]);

  installTemplate(dir);
  const fmt = FORMATS[format];
  writeJson(path.join(dir, 'project.fvs.json'), {
    title: title || sj.paragraphs.find(p => p.heading)?.heading || name, name, format, ...fmt,
    duration: vo.duration, created: new Date().toISOString(),
    inputs: { script: path.relative(dir, scriptDst), voice: path.relative(dir, voiceDst), originalScript: path.resolve(script), originalVoice: path.resolve(voice) },
    voice: vo,
  });
  writeJson(path.join(dir, '.videohub', 'project.json'), { title: title || name, status: 'in-progress' });
  const st = readState(dir); writeState(dir, st);
  markStage(dir, 'ingest', 'done', { words: sj.stats.words, sentences: sj.stats.sentences, voiceSeconds: vo.duration });
  return { project: dir, title: title || name, format, ...fmt, voice: vo, script: sj.stats, entities: sj.entities };
}
