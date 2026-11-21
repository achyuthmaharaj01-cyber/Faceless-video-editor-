// Audio mix: voiceover (untouched) + music bed ducked under it + synthesised SFX on the storyboard cues.
// Writes VideoHub-compatible stems (audio/vo.wav, audio/music.wav, audio/sfx.wav) and audio/mix.wav, which
// the HyperFrames composition plays and VideoHub previews.
//
// Loudness: the mix is measured (EBU R128) and ONE static gain moves it toward the target (YouTube plays back
// at about -14 LUFS). No compressor or limiter is applied to the narration; if the true peak would exceed
// the ceiling, the gain is reduced instead and the shortfall is reported. Set FVS_MASTER_GAIN=off to skip.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { REPO_ROOT } from '../videohub/build-preview.mjs';
import { python } from '../videohub/notes.mjs';
import { LAYOUT, readJson, markStage } from '../project.mjs';
import { readRegister, registerOriginal } from '../assets.mjs';

export const TARGET_LUFS = -14, TP_CEILING = -1.0;

function ff(args, what) {
  const r = spawnSync('ffmpeg', ['-v', 'error', '-y', ...args], { encoding: 'utf8', maxBuffer: 1 << 26 });
  if (r.status !== 0) throw new Error(`${what} failed: ${r.stderr.slice(-600)}`);
}

export function measureLoudness(file) {
  const r = spawnSync('ffmpeg', ['-nostats', '-i', file, '-af', 'ebur128=peak=true', '-f', 'null', '-'], { encoding: 'utf8', maxBuffer: 1 << 26 });
  const s = r.stderr.slice(r.stderr.lastIndexOf('Summary:'));
  const g = k => { const m = s.match(new RegExp(`${k}:\\s+(-?[\\d.]+|-inf)`)); return m && m[1] !== '-inf' ? +m[1] : null; };
  return { integrated: g('I'), lra: g('LRA'), truePeak: g('Peak') };
}

export async function mixProject(projectDir) {
  const dir = path.resolve(projectDir);
  const meta = readJson(path.join(dir, 'project.fvs.json'));
  const sb = readJson(path.join(dir, LAYOUT.storyboard, 'storyboard.json'), {});
  const A = p => path.join(dir, LAYOUT.audio, p);
  const D = meta.duration;
  const warnings = [];
  const music = sb.music || {};

  // 1) SFX stem from cues
  const cues = readJson(A('cues.json'), { cues: [] });
  const synth = path.join(REPO_ROOT, 'scripts', 'sound-design', 'synth.py');
  let r = spawnSync(python(), [synth, 'sfx', '--cues', A('cues.json'), '--duration', String(D), '--out', A('sfx.wav')], { encoding: 'utf8' });
  if (r.status !== 0) throw new Error('sfx synthesis failed: ' + r.stderr.slice(-400));

  // 2) music bed: a registered licensed track, else the procedural bed (original)
  let musicSource;
  const reg = readRegister(dir);
  if (music.track && music.track !== 'procedural' && music.track !== 'none') {
    const a = reg.get(music.track) || (fs.existsSync(path.join(dir, music.track)) ? { file: music.track } : null);
    if (!a) throw new Error(`music track "${music.track}" is neither a registered asset id nor a file in the project`);
    if (!reg.get(music.track) && ![...reg.values()].some(x => x.file === music.track)) warnings.push(`music ${music.track} is not in the licence register`);
    const offset = music.offset || 0;
    ff(['-stream_loop', '-1', '-ss', String(offset), '-i', path.join(dir, a.file), '-t', String(D), '-af', `afade=t=in:d=1.5,afade=t=out:st=${Math.max(0, D - 2.5)}:d=2.5`, '-ar', '48000', '-ac', '2', A('bed_raw.wav')], 'music decode');
    musicSource = a.file;
  } else if (music.track === 'none') {
    ff(['-f', 'lavfi', '-i', `anullsrc=r=48000:cl=stereo`, '-t', String(D), A('bed_raw.wav')], 'silent bed');
    musicSource = 'none';
  } else {
    r = spawnSync(python(), [synth, 'music', '--duration', String(D), '--mood', music.mood || 'curious', '--out', A('bed_raw.wav'), ...(music.bpm ? ['--bpm', String(music.bpm)] : [])], { encoding: 'utf8' });
    if (r.status !== 0) throw new Error('music synthesis failed: ' + r.stderr.slice(-400));
    registerOriginal(dir, { id: 'music-procedural', file: 'audio/bed_raw.wav', kind: 'audio', usage: 'background music bed', how: `synthesised by scripts/sound-design/synth.py (mood ${music.mood || 'curious'})` });
    musicSource = `procedural (${music.mood || 'curious'})`;
    warnings.push('music is the procedural placeholder bed: replace it with a licensed track for publishing quality (storyboard.music.track)');
  }
  registerOriginal(dir, { id: 'sfx-synth', file: 'audio/sfx.wav', kind: 'audio', usage: 'sound effects stem', how: 'synthesised by scripts/sound-design/synth.py' });

  // 3) duck the music under the voice (sidechain keyed by the narration)
  const gain = music.gain_db ?? -20, duck = Math.abs(music.duck_db ?? 12);
  const ratio = Math.max(2, Math.min(20, 10 ** (duck / 20) * 1.5));
  ff(['-i', A('vo.wav'), '-i', A('bed_raw.wav'), '-filter_complex',
    `[1:a]volume=${gain}dB,aformat=sample_rates=48000:channel_layouts=stereo[m];[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[k][unused];[unused]anullsink;` +
    `[m][k]sidechaincompress=threshold=0.015:ratio=${ratio.toFixed(2)}:attack=20:release=420:makeup=1[d]`,
    '-map', '[d]', '-t', String(D), '-c:a', 'pcm_s24le', A('music.wav')], 'music ducking');

  // 4) sum the stems, measure, one static gain
  ff(['-i', A('vo.wav'), '-i', A('music.wav'), '-i', A('sfx.wav'), '-filter_complex',
    '[0:a][1:a][2:a]amix=inputs=3:normalize=0:duration=first[a]', '-map', '[a]', '-t', String(D), '-c:a', 'pcm_s24le', A('premix.wav')], 'mix');
  // Peak limiting touches the narration's peaks, so it runs only when the user approved it
  // (storyboard.audio.limiter = true, recorded with who approved it).
  const limiter = sb.audio?.limiter === true;
  if (limiter) {
    ff(['-i', A('premix.wav'), '-af', 'alimiter=limit=0.708:attack=5:release=60:level=disabled', '-c:a', 'pcm_s24le', A('premix_lim.wav')], 'approved limiter');
    fs.renameSync(A('premix_lim.wav'), A('premix.wav'));
  }
  const pre = measureLoudness(A('premix.wav'));
  let g = 0;
  if (process.env.FVS_MASTER_GAIN !== 'off' && pre.integrated !== null) {
    g = TARGET_LUFS - pre.integrated;
    if (pre.truePeak !== null && pre.truePeak + g > TP_CEILING && !limiter) {
      const capped = TP_CEILING - pre.truePeak;
      warnings.push(`loudness target ${TARGET_LUFS} LUFS needs +${g.toFixed(1)} dB but the true peak allows only ${capped.toFixed(1)} dB: mix lands at ${(pre.integrated + capped).toFixed(1)} LUFS (no limiter is applied to the narration; approve limiting if you want it louder)`);
      g = capped;
    }
  }
  // with an approved limiter the gain is applied before a final true-peak-safe limit at the ceiling
  const chain = limiter ? `volume=${g.toFixed(2)}dB,alimiter=limit=${(10 ** (TP_CEILING / 20) * 0.94).toFixed(3)}:attack=3:release=50:level=disabled` : `volume=${g.toFixed(2)}dB`;
  ff(['-i', A('premix.wav'), '-af', chain, '-c:a', 'pcm_s24le', '-ar', '48000', A('mix.wav')], 'master gain');
  fs.rmSync(A('premix.wav'), { force: true });
  const post = measureLoudness(A('mix.wav'));
  const res = { musicSource, cues: cues.cues.length, preMix: pre, masterGainDb: +g.toFixed(2), final: post, voiceProcessing: limiter ? `peak limiter (approved: ${sb.audio?.limiterApprovedBy || 'not recorded'}) + static gain` : 'none (static master gain only)', warnings };
  fs.writeFileSync(A('mix-report.json'), JSON.stringify(res, null, 2));
  markStage(dir, 'mix', 'done', { lufs: post.integrated, tp: post.truePeak });
  return res;
}
