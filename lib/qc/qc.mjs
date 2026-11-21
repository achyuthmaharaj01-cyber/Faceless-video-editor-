// Quality control. Every check below is actually performed; the report separates passed / failed / warnings /
// manual review, and says what could not be checked and why. Nothing is reported as passed by default.
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { REPO_ROOT, readRootMeta } from '../videohub/build-preview.mjs';
import { python } from '../videohub/notes.mjs';
import { staticServer, launchBrowser } from '../videohub/parity.mjs';
import { LAYOUT, readJson, readState, markStage } from '../project.mjs';
import { checkStoryboard, numberValue } from '../storyboard.mjs';
import { readRegisterRows } from '../assets.mjs';
import { indexHash } from '../render.mjs';

const fmt = t => (t == null ? '—' : `${Math.floor(t / 60)}:${(t % 60).toFixed(2).padStart(5, '0')}`);

/** Text layout in the real composition: off-frame text, overlapping text, broken images — sampled per scene. */
async function layoutChecks(dir, times) {
  const { srv, url } = await staticServer(dir);
  const browser = await launchBrowser();
  const problems = [];
  try {
    const cfg = JSON.parse(fs.readFileSync(path.join(dir, 'preview', 'videohub.html'), 'utf8').match(/__FVS_PREVIEW__=(\{.*?\});/)[1]);
    const page = await browser.newPage({ viewport: { width: cfg.width, height: cfg.height } });
    const errors = []; page.on('pageerror', e => errors.push(e.message));
    const missing = []; page.on('response', r => { if (r.status() >= 400 && !/favicon/.test(r.url())) missing.push(`${r.status()} ${new URL(r.url()).pathname}`); });
    await page.goto(`${url}/preview/videohub.html`);
    await page.waitForFunction(() => window.READY === true || window.__vhError, null, { timeout: 120000 });
    const err = await page.evaluate(() => window.__vhError || null);
    if (err) throw new Error(err);
    for (const t of times) {
      const r = await page.evaluate(({ t, W, H }) => {
        window.renderOut(t);
        const shown = el => { let o = 1; for (let e = el; e && e !== document.body; e = e.parentElement) { const s = getComputedStyle(e); if (s.display === 'none' || s.visibility === 'hidden') return 0; o *= +s.opacity; } return o; };
        // measure the glyphs (a text range), not the element box: a full-width centred block is not off-frame
        const glyphs = e => { const r = document.createRange(); r.selectNodeContents(e); const b = r.getBoundingClientRect(); return b.width ? b : e.getBoundingClientRect(); };
        const texts = [...document.querySelectorAll('.label, .stat, .stat-sub, .kt, .cap-strip, .tyear, .doc h2, .hand, .pricetag, .meter .val')]
          .filter(e => shown(e) > 0.6 && e.textContent.trim()).map(e => ({ id: e.id || e.className, text: e.textContent.trim().slice(0, 40), r: glyphs(e) }))
          .filter(x => x.r.right > 0 && x.r.left < W && x.r.bottom > 0 && x.r.top < H);   // entirely off-screen = not visible
        const out = [];
        for (const x of texts) {
          const { left, top, right, bottom } = x.r;
          if (left < -2 || top < -2 || right > W + 2 || bottom > H + 2) out.push({ kind: 'text cut off by the frame edge', what: x.text, box: [left, top, right, bottom].map(Math.round) });
          else if (left < W * 0.03 || right > W * 0.97 || top < H * 0.03 || bottom > H * 0.97) out.push({ kind: 'text outside the title-safe area', what: x.text, box: [left, top, right, bottom].map(Math.round), soft: true });
        }
        for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++) {
          const a = texts[i].r, b = texts[j].r;
          const w = Math.min(a.right, b.right) - Math.max(a.left, b.left), h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
          if (w > 0 && h > 0 && w * h > 0.15 * Math.min(a.width * a.height, b.width * b.height)) out.push({ kind: 'overlapping text', what: `${texts[i].text} / ${texts[j].text}` });
        }
        for (const img of document.images) if (shown(img) > 0.05 && img.complete && img.naturalWidth === 0) out.push({ kind: 'image failed to load', what: img.getAttribute('src') });
        for (const m of document.querySelectorAll('.missing')) if (shown(m) > 0.05) out.push({ kind: 'missing asset slate on screen', what: m.textContent.trim() });
        return out;
      }, { t, W: cfg.width, H: cfg.height });
      for (const p of r) problems.push({ t, ...p });
    }
    return { problems, pageErrors: errors, missingFiles: [...new Set(missing)].filter(m => !/audio\/mix\.wav/.test(m)) };
  } finally { await browser.close(); srv.close(); }
}

export async function qualityControl(projectDir, { video } = {}) {
  const dir = path.resolve(projectDir);
  const meta = readJson(path.join(dir, 'project.fvs.json'));
  const st = readState(dir);
  const sb = readJson(path.join(dir, LAYOUT.storyboard, 'storyboard.json'));
  const al = readJson(path.join(dir, LAYOUT.analysis, 'alignment.json'));
  const pass = [], fail = [], warn = [], manual = [], notChecked = [];
  const P = (m) => pass.push(m), F = (m) => fail.push(m), W = (m) => warn.push(m);
  const fps = meta.fps, frame = 1 / fps;
  const sceneAt = t => sb?.scenes?.find(s => t >= s.start && t < s.end);

  // ---------------------------------------------------------------- final output (ffprobe + signal checks)
  const lastRender = [...st.renders].reverse().find(r => !r.draft && r.exitCode === 0);
  const vid = video ? path.resolve(video) : lastRender ? path.join(dir, lastRender.file) : null;
  let av = null;
  if (!vid || !fs.existsSync(vid)) notChecked.push('Rendered video checks: no final render found (run `fvs render` after approval, or pass --video).');
  else {
    const r = spawnSync(python(), [path.join(REPO_ROOT, 'scripts', 'quality-control', 'av_checks.py'), vid, '--mix', path.join(dir, LAYOUT.audio, 'mix.wav'), '--fps', String(fps)], { encoding: 'utf8', maxBuffer: 1 << 26 });
    if (r.status !== 0) F(`Signal checks could not run: ${r.stderr.slice(-300)}`);
    else av = JSON.parse(r.stdout);
  }
  if (av) {
    const p = av.probe;
    (p.width === meta.width && p.height === meta.height ? P : F)(`Resolution ${p.width}×${p.height} (expected ${meta.width}×${meta.height}).`);
    (Math.abs(p.width / p.height - meta.width / meta.height) < 0.001 ? P : F)(`Aspect ratio ${(p.width / p.height).toFixed(4)}.`);
    (Math.abs(p.fps - fps) < 0.01 ? P : F)(`Frame rate ${p.fps} fps (expected ${fps}).`);
    (p.video_codec === 'h264' ? P : F)(`Video codec ${p.video_codec} (${p.profile}, ${p.pix_fmt}).`);
    (p.audio_codec === 'aac' ? P : F)(`Audio codec ${p.audio_codec}, ${p.audio_channels} ch, ${p.audio_rate} Hz.`);
    const dv = Math.abs(p.video_duration - meta.duration), da = Math.abs(p.audio_duration - meta.duration);
    (dv <= frame + 1e-3 ? P : F)(`Video duration ${p.video_duration.toFixed(3)} s vs voiceover ${meta.duration.toFixed(3)} s (difference ${(dv * 1000).toFixed(0)} ms; allowed one frame, ${(frame * 1000).toFixed(0)} ms).`);
    (da <= 0.05 ? P : F)(`Audio duration ${p.audio_duration.toFixed(3)} s vs voiceover (difference ${(da * 1000).toFixed(0)} ms; AAC priming allowance 50 ms).`);
    if (p.frames) (Math.abs(p.frames - Math.round(meta.duration * fps)) <= 1 ? P : F)(`Frame count ${p.frames} (expected ${Math.round(meta.duration * fps)}).`);
    // black / frozen frames, judged against the storyboard (dark design ≠ rendering error)
    if (!av.black.length) P('No black frames (blackdetect, 0.2 s minimum, luma threshold 8%).');
    for (const b of av.black) {
      const sc = sceneAt(b.start + 0.01);
      const dark = sc && /#0|#1|black|0b08|050505|040805/.test(JSON.stringify(sc.visual?.background || ''));
      (dark ? W : F)(`Black frames ${fmt(b.start)}–${fmt(b.end)} (${b.duration.toFixed(2)} s) in scene ${sc?.id || '?'}${dark ? ' — the scene background is intentionally dark: check it is not empty' : ''}.`);
    }
    if (!av.frozen.length) P('No frozen picture longer than 2 s (freezedetect).');
    for (const z of av.frozen) W(`Picture static ${fmt(z.start)}–${fmt(z.end)} (${z.duration ?? '?'} s) in scene ${sceneAt(z.start + 0.01)?.id || '?'}: intended hold, or a stuck layer?`);
    // audio
    const L = av.loudness;
    if (L.true_peak_dbtp == null) F('True peak could not be measured.');
    else (L.true_peak_dbtp <= -0.9 ? P : L.true_peak_dbtp < 0 ? W : F)(`True peak ${L.true_peak_dbtp} dBTP (ceiling −1 dBTP; above 0 = clipping).`);
    if (L.integrated_lufs != null) (L.integrated_lufs >= -16 && L.integrated_lufs <= -12 ? P : W)(`Integrated loudness ${L.integrated_lufs} LUFS (YouTube reference about −14; quieter is not turned up by YouTube).`);
    const inner = av.silences.filter(s => s.start > 0.5 && s.end < meta.duration - 0.5);
    if (!inner.length) P('No silence longer than 1.5 s inside the film (−50 dB).');
    for (const s of inner) W(`Silence ${fmt(s.start)}–${fmt(s.end)} (${s.duration.toFixed(2)} s).`);
    if (av.sync) {
      (Math.abs(av.sync.offset_ms) <= frame * 1000 && av.sync.correlation > 0.5 ? P : F)(`Audio sync: rendered audio vs approved mix offset ${av.sync.offset_ms} ms, correlation ${av.sync.correlation} (needs ≤ ${(frame * 1000).toFixed(0)} ms and > 0.5).`);
      if (av.sync.tail_rms_db != null) (av.sync.tail_rms_db < -35 ? P : W)(`Audio ending: last 50 ms at ${av.sync.tail_rms_db} dB (${av.sync.tail_rms_db < -35 ? 'fades out' : 'possibly abrupt'}).`);
    }
    // the render is the approved composition
    if (lastRender && !video) (st.approval && st.approval.indexHash === lastRender.indexHash ? P : F)(`Render matches the approved composition (approved ${st.approval?.indexHash || 'never'}, rendered ${lastRender.indexHash}).`);
    // beginning / middle / end frames for a human look
    const thumbs = path.join(dir, LAYOUT.reports, 'qc-frames');
    fs.mkdirSync(thumbs, { recursive: true });
    for (const [n, t] of [['begin', 0.5], ['middle', meta.duration / 2], ['end', Math.max(0, meta.duration - 0.5)]]) {
      spawnSync('ffmpeg', ['-v', 'error', '-y', '-ss', String(t), '-i', vid, '-frames:v', '1', '-vf', 'scale=960:-2', path.join(thumbs, `${n}.jpg`)]);
    }
    manual.push(`Look at reports/qc-frames/begin.jpg, middle.jpg, end.jpg (taken from the rendered file).`);
  }

  // ---------------------------------------------------------------- composition / layout (real browser)
  if (fs.existsSync(path.join(dir, 'preview', 'videohub.html')) && sb) {
    const times = new Set();
    // two moments per scene, away from transition windows (a whip/zoom moves text through the edge on purpose)
    for (const s of sb.scenes) { times.add(+(s.start + 0.6 * (s.end - s.start)).toFixed(3)); times.add(+(s.end - Math.min(0.35, (s.end - s.start) * 0.2)).toFixed(3)); }
    const lay = await layoutChecks(dir, [...times].sort((a, b) => a - b));
    const hard = lay.problems.filter(p => !p.soft);
    if (!hard.length) P(`Layout at ${times.size} sampled moments (two per scene): no text outside the frame, no overlapping text, no broken images, no missing-asset slates.`);
    for (const p of hard) F(`${fmt(p.t)} (${sceneAt(p.t)?.id || '?'}): ${p.kind}: ${p.what}${p.box ? ` at ${p.box.join(',')}` : ''}.`);
    for (const p of lay.problems.filter(p => p.soft)) W(`${fmt(p.t)} (${sceneAt(p.t)?.id || '?'}): ${p.kind}: ${p.what}.`);
    (lay.pageErrors.length ? F : P)(lay.pageErrors.length ? `Script errors in the composition: ${lay.pageErrors.slice(0, 3).join(' | ')}` : 'No script errors while seeking the composition.');
    (lay.missingFiles.length ? F : P)(lay.missingFiles.length ? `Missing files: ${lay.missingFiles.join(', ')}` : 'Every file the composition requested was served (no broken asset paths).');
  } else notChecked.push('Layout checks: no preview page / storyboard.');

  // ---------------------------------------------------------------- content
  const sc = checkStoryboard(dir);
  (sc.ok ? P : F)(sc.ok ? `Storyboard: ${sc.scenes} contiguous scenes cover the whole voiceover; every sentence is on screen in script order.` : `Storyboard errors: ${sc.errors.join('; ')}`);
  for (const w of sc.warnings) W(`Storyboard: ${w}`);
  if (al) {
    const review = al.mismatches.filter(m => !m.benign);
    (al.matched_ratio >= 0.85 ? P : W)(`Narration alignment: ${(al.matched_ratio * 100).toFixed(1)}% of script words matched in the voiceover.`);
    if (review.length) for (const m of review) manual.push(`Narration differs from the script at ${m.start != null ? fmt(m.start) : 'after word ' + m.after_word}: script "${m.script}" / heard "${m.heard}"${m.number_differs ? ' — A NUMBER DIFFERS' : ''}.`);
    else P('Every script/voiceover difference is a formatting or transcription variant (no omitted or changed narration detected).');
  }
  // on-screen numbers must come from the narration of their scene
  if (sb) {
    const numsOnScreen = [];
    for (const s of sb.scenes) {
      const v = s.visual || {};
      if (v.type === 'stat') numsOnScreen.push({ s, value: v.value, shown: `${v.prefix || ''}${v.value}${v.suffix || ''}` });
      for (const L of s.layers || []) for (const txt of [L.text, L.label?.text ?? (typeof L.label === 'string' ? L.label : null), L.price, L.name]) if (txt && /\d/.test(txt)) {
        for (const tok of txt.replace(/(\d),(\d)/g, '$1$2').match(/\$?\d[\d.]*s?/g) || []) numsOnScreen.push({ s, value: numberValue(tok.replace(/s$/, '')), shown: `${tok} (in "${txt}")`, decade: /^\d{3}0s$/.test(tok) });
      }
    }
    const spoken = s => (al?.words || []).filter(w => w.s >= s.start - 0.05 && w.s < s.end).map(w => w.w).join(' ');
    const numbersIn = text => (text.replace(/(\d),(\d)/g, '$1$2').match(/\$?\d[\d.]*s?|\b(?:(?:[a-z]+[\s-]){0,3}(?:thousand|million|billion|hundred)|(?:twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)(?:-[a-z]+)?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen)\b/gi) || [])
      .map(x => numberValue(x)).filter(x => x !== null);
    const scriptNums = numbersIn((al?.sentences || []).map(x => x.text).join(' '));
    const matches = (list, v, decade) => list.some(x => Math.abs(x - v) < 1e-6 || Math.abs(x / 100 - v) < 1e-6 || (decade && x >= v && x < v + 10));
    for (const n of numsOnScreen) {
      const decade = !!n.decade;   // "1950s" is supported by any year of that decade
      const local = n.value == null || matches(numbersIn(spoken(n.s) + ' ' + (n.s.narration || '')), n.value, decade);
      const anywhere = local || matches(scriptNums, n.value, decade);
      (anywhere ? P : F)(`On-screen figure "${n.shown}" in ${n.s.id} ${local ? 'is stated in that scene\'s narration' : anywhere ? 'is stated elsewhere in the script' : 'does NOT appear anywhere in the script (unsupported claim)'}.`);
    }
    manual.push('Fact check: names, dates and figures come from your script; this system checks they match the narration, not that the script is historically correct.');
    manual.push('Watch every scene once: do the visuals show what the narration says (no unrelated or misleading images)?');
  }

  // ---------------------------------------------------------------- licences
  const rows = readRegisterRows(dir);
  const used = new Set();
  for (const f of fs.existsSync(path.join(dir, 'compositions')) ? fs.readdirSync(path.join(dir, 'compositions')) : []) {
    for (const m of fs.readFileSync(path.join(dir, 'compositions', f), 'utf8').matchAll(/src="(assets\/[^"]+)"/g)) used.add(m[1]);
  }
  const reg = new Map(rows.map(r => [r.filename, r]));
  const unregistered = [...used].filter(f => !reg.has(f));
  (unregistered.length ? F : P)(unregistered.length ? `Media used but not in the licence register: ${unregistered.join(', ')}` : `All ${used.size} media files used by the composition are in the licence register.`);
  const incomplete = rows.filter(r => !r.licence || (r.source_platform !== 'original' && !(r.original_url || r.landing_url)) || (r.attribution_required === 'yes' && !r.attribution_text) || r.commercial_use !== 'yes' || r.modification_allowed !== 'yes');
  (incomplete.length ? F : P)(incomplete.length ? `Licence register rows incomplete or not commercial/modifiable: ${incomplete.map(r => r.asset_id).join(', ')}` : `Licence register: ${rows.length} rows complete (licence, source URL, attribution where required, commercial use and modification allowed).`);
  const lowres = rows.filter(r => used.has(r.filename) && r.asset_type === 'image' && +r.width && +r.width < 1600);
  for (const r of lowres) W(`Asset ${r.asset_id} is ${r.width}px wide: upscaled on a ${meta.width}px frame (softer). A higher-resolution licensed source would look better.`);
  const attrib = rows.filter(r => r.attribution_required === 'yes');
  if (attrib.length) manual.push(`Credits needed in the video description (CC BY): ${attrib.length} assets — see reports/attributions.txt.`);
  fs.mkdirSync(path.join(dir, LAYOUT.reports), { recursive: true });
  fs.writeFileSync(path.join(dir, LAYOUT.reports, 'attributions.txt'), attrib.map(r => r.attribution_text).join('\n') + (attrib.length ? '\n' : ''));
  const mixRep = readJson(path.join(dir, LAYOUT.audio, 'mix-report.json'));
  if (mixRep) for (const w of mixRep.warnings || []) W(`Audio: ${w}`);
  if (mixRep && mixRep.cues) P(`Sound design: ${mixRep.cues} SFX cues placed; music source: ${mixRep.musicSource}; narration processing: ${mixRep.voiceProcessing}.`);

  // ---------------------------------------------------------------- report
  const failed = fail.length;
  const md = `# Quality-control report

Project: **${meta.title}** · ${meta.width}×${meta.height} @ ${fps} fps · voiceover ${fmt(meta.duration)}
Checked: ${new Date().toISOString()} · video: ${vid ? path.relative(dir, vid) : 'none'} · composition ${indexHash(dir)}

**Result: ${failed ? `${failed} FAILED` : 'no failed checks'}, ${warn.length} warnings, ${manual.length} manual-review items.**

## Failed (${fail.length})
${fail.map(x => `- ❌ ${x}`).join('\n') || '- none'}

## Warnings (${warn.length})
${warn.map(x => `- ⚠️ ${x}`).join('\n') || '- none'}

## Manual review required (${manual.length})
${manual.map(x => `- 👁 ${x}`).join('\n') || '- none'}

## Passed (${pass.length})
${pass.map(x => `- ✅ ${x}`).join('\n')}

## Not checked
${notChecked.map(x => `- ${x}`).join('\n') || '- nothing skipped'}
`;
  fs.writeFileSync(path.join(dir, LAYOUT.reports, 'quality-control-report.md'), md);
  fs.writeFileSync(path.join(dir, LAYOUT.reports, 'quality-control.json'), JSON.stringify({ pass, fail, warn, manual, notChecked, av }, null, 2));
  markStage(dir, 'qc', failed ? 'failed' : 'done', { failed, warnings: warn.length });
  return { failed, summary: { report: path.join(dir, LAYOUT.reports, 'quality-control-report.md'), failed: fail, warnings: warn.length, manual: manual.length, passed: pass.length, notChecked } };
}
