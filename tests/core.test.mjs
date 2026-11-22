// Unit tests for the deterministic core: licences, register CSV, numbers, timing, storyboard rules, preview page.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { classifyLicence, addToRegister, readRegisterRows } from '../lib/assets.mjs';
import { numberValue, checkStoryboard } from '../lib/storyboard.mjs';
import { makeTimeResolver } from '../lib/compose/build.mjs';
import { fnv1a, readRootMeta, buildPreview } from '../lib/videohub/build-preview.mjs';

const tmp = () => fs.mkdtempSync(path.join(os.tmpdir(), 'fvs-test-'));

test('licence policy: commercial + modifiable only', () => {
  for (const ok of ['cc0', 'pdm', 'by-2.0', 'CC BY 4.0', 'pexels', 'pixabay', 'pd-nasa', 'Public domain']) assert.equal(classifyLicence(ok).ok, true, ok);
  for (const bad of ['by-nc-2.0', 'by-nd-4.0', 'by-nc-sa-3.0', 'CC BY-SA 4.0', '', 'all rights reserved', 'needs-review']) assert.equal(classifyLicence(bad).ok, false, bad);
  assert.equal(classifyLicence('by-4.0').attribution, true);
  assert.equal(classifyLicence('cc0').attribution, false);
});

test('licence register round-trips quotes, commas and newlines', () => {
  const d = tmp();
  addToRegister(d, { asset_id: 'a1', filename: 'assets/a1.jpg', attribution_text: '"Ship, at sea" by X is licensed under CC BY 2.0.', notes: 'line1\nline2' });
  addToRegister(d, { asset_id: 'a2', filename: 'assets/a2.jpg', licence: 'CC0' });
  addToRegister(d, { asset_id: 'a1', filename: 'assets/a1b.jpg' });   // replaces a1
  const rows = readRegisterRows(d);
  assert.equal(rows.length, 2);
  assert.equal(rows.find(r => r.asset_id === 'a1').filename, 'assets/a1b.jpg');
  assert.equal(rows.find(r => r.asset_id === 'a2').licence, 'CC0');
});

test('numbers in words and digits', () => {
  assert.equal(numberValue('fifty-eight'), 58);
  assert.equal(numberValue('twenty-four thousand'), 24000);
  assert.equal(numberValue('$5.86'), 5.86);
  assert.equal(numberValue('$70 billion'), 70e9);
  assert.equal(numberValue('two hundred'), 200);
  assert.equal(numberValue('no number here'), null);
});

test('"@word" timing resolves inside the scene and in order', () => {
  const words = [[0, 0.4, 'In'], [0.5, 1.0, '1956,'], [2.0, 2.3, 'a'], [3.0, 3.4, 'ship'], [5.0, 5.3, 'a'], [5.4, 5.8, 'ship']];
  const warns = []; const at = makeTimeResolver(words, w => warns.push(w));
  const sc = { id: 's', start: 4.5, end: 6 };
  assert.equal(at('@ship', sc), 5.4);                 // the occurrence inside the scene, not the earlier one
  assert.equal(at('@a ship', sc), 5.0);               // multi-word phrase
  assert.ok(Math.abs(at('@ship+0.2', sc) - 5.6) < 1e-9);
  assert.equal(at('+0.5', sc), 5.0);
  assert.equal(at(7, sc), 7);
  assert.equal(at('@missing', sc), 4.5); assert.equal(warns.length, 1);
  assert.equal(at('@1956', { id: 'x', start: 0, end: 2 }), 0.5);   // punctuation ignored
});

function fixtureProject() {
  const d = tmp();
  fs.mkdirSync(path.join(d, 'storyboard')); fs.mkdirSync(path.join(d, 'analysis'));
  fs.writeFileSync(path.join(d, 'project.fvs.json'), JSON.stringify({ duration: 6, fps: 30, width: 1920, height: 1080 }));
  fs.writeFileSync(path.join(d, 'analysis', 'alignment.json'), JSON.stringify({ sentences: [{ index: 0, text: 'One.' }, { index: 1, text: 'Two.' }], words: [], mismatches: [], matched_ratio: 1 }));
  return d;
}
const sb = scenes => ({ scenes });

test('storyboard checker: contiguous, full length, every sentence, order', () => {
  const d = fixtureProject();
  const good = [{ id: 'a', start: 0, end: 3, sentences: [0], visual: { type: 'kinetic', text: 'one' } }, { id: 'b', start: 3, end: 6, sentences: [1], visual: { type: 'solid' } }];
  fs.writeFileSync(path.join(d, 'storyboard', 'storyboard.json'), JSON.stringify(sb(good)));
  assert.equal(checkStoryboard(d).ok, true);
  const gap = structuredClone(good); gap[1].start = 3.5;
  fs.writeFileSync(path.join(d, 'storyboard', 'storyboard.json'), JSON.stringify(sb(gap)));
  assert.match(checkStoryboard(d).errors.join(), /gap\/overlap/);
  const short = structuredClone(good); short[1].end = 5;
  fs.writeFileSync(path.join(d, 'storyboard', 'storyboard.json'), JSON.stringify(sb(short)));
  assert.match(checkStoryboard(d).errors.join(), /voiceover is 6s/);
  const missing = structuredClone(good); missing[1].sentences = [0];
  fs.writeFileSync(path.join(d, 'storyboard', 'storyboard.json'), JSON.stringify(sb(missing)));
  assert.match(checkStoryboard(d).errors.join(), /sentences not assigned to any scene: 1/);
  const order = structuredClone(good); order[0].sentences = [1]; order[1].sentences = [0];
  fs.writeFileSync(path.join(d, 'storyboard', 'storyboard.json'), JSON.stringify(sb(order)));
  assert.match(checkStoryboard(d).errors.join(), /script/);
  const noAsset = structuredClone(good); noAsset[0].visual = { type: 'photo' };
  fs.writeFileSync(path.join(d, 'storyboard', 'storyboard.json'), JSON.stringify(sb(noAsset)));
  assert.match(checkStoryboard(d).errors.join(), /needs visual.asset/);
});

test('preview page: HyperFrames runtime + inline adapter + scene lane; project.json merge keeps user keys', () => {
  const d = tmp();
  const html = `<!doctype html><html><head><meta charset="utf-8"></head><body><div id="root" data-composition-id="main" data-start="0" data-duration="4" data-width="1920" data-height="1080">
<div id="s01" data-composition-id="s01" data-composition-src="compositions/s01.html" data-fvs-scene="01 · intro" data-start="0" data-duration="2"></div>
<div id="s02" data-composition-id="s02" data-composition-src="compositions/s02.html" data-fvs-scene="02 · end &amp; more" data-start="2" data-duration="2"></div></div></body></html>`;
  fs.writeFileSync(path.join(d, 'index.html'), html);
  fs.mkdirSync(path.join(d, '.videohub'));
  fs.writeFileSync(path.join(d, '.videohub', 'project.json'), JSON.stringify({ status: 'approved', title: 'Mine', custom: 1 }));
  const r = buildPreview(d, { fps: 30 });
  const page = fs.readFileSync(path.join(d, 'preview', 'videohub.html'), 'utf8');
  assert.match(page, /<base href="\.\.\/">/);
  assert.match(page, /preview\/hf-runtime\.js/);
  assert.match(page, /window\.renderOut = function/);
  assert.match(page, /data-hyperframes-text-rendering/);
  assert.deepEqual(r.scenes, [{ name: '01 · intro', t0: 0, t1: 2 }, { name: '02 · end & more', t0: 2, t1: 4 }]);
  assert.equal(r.sourceHash, fnv1a(html));
  const pj = JSON.parse(fs.readFileSync(path.join(d, '.videohub', 'project.json'), 'utf8'));
  assert.equal(pj.status, 'approved'); assert.equal(pj.title, 'Mine'); assert.equal(pj.custom, 1);
  assert.equal(pj.live.page, 'preview/videohub.html'); assert.equal(pj.render.script, 'render.mjs');
  assert.ok(fs.existsSync(path.join(d, 'render.mjs')));
  assert.equal(fs.existsSync(path.join(d, 'videohub.html')), false, 'no second root-level composition');
  assert.deepEqual(readRootMeta(html), { id: 'main', width: 1920, height: 1080, duration: 4 });
});

test('fnv1a matches the in-page implementation (UTF-8)', () => {
  const src = fs.readFileSync(new URL('../lib/videohub/vh-adapter.js', import.meta.url), 'utf8');
  const body = src.match(/function fnv1a\(text\) \{([\s\S]*?)\n  \}/)[1];
  const pageFnv = new Function('text', body);
  for (const s of ['', 'abc', 'héllo · 1956 — “quotes”', '<html data-x="1">']) assert.equal(pageFnv(s), fnv1a(s));
});

test('Google OAuth client: from env, or from the downloaded Desktop-app JSON; web clients refused', async () => {
  const d = tmp();
  const keep = { ...process.env };
  try {
    delete process.env.GOOGLE_OAUTH_CLIENT_ID; delete process.env.GOOGLE_OAUTH_CLIENT_SECRET;
    const { client } = await import('../backend/integrations/drive.mjs');
    process.env.GOOGLE_OAUTH_CLIENT_FILE = path.join(d, 'c.json');
    fs.writeFileSync(process.env.GOOGLE_OAUTH_CLIENT_FILE, JSON.stringify({ installed: { client_id: 'id1.apps.googleusercontent.com', client_secret: 's1' } }));
    assert.deepEqual(client(), { id: 'id1.apps.googleusercontent.com', secret: 's1' });
    process.env.GOOGLE_OAUTH_CLIENT_ID = 'id2'; process.env.GOOGLE_OAUTH_CLIENT_SECRET = 's2';
    assert.deepEqual(client(), { id: 'id2', secret: 's2' });          // .env / shell wins
    delete process.env.GOOGLE_OAUTH_CLIENT_ID; delete process.env.GOOGLE_OAUTH_CLIENT_SECRET;
    fs.writeFileSync(process.env.GOOGLE_OAUTH_CLIENT_FILE, JSON.stringify({ web: { client_id: 'w', client_secret: 'w' } }));
    assert.throws(() => client(), /Desktop app/);
    process.env.GOOGLE_OAUTH_CLIENT_FILE = path.join(d, 'missing.json');
    assert.throws(() => client(), /no Google OAuth client found/);
  } finally { for (const k of Object.keys(process.env)) if (!(k in keep)) delete process.env[k]; Object.assign(process.env, keep); }
});
