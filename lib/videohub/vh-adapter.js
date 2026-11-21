/*
 * HyperFrames → VideoHub live-preview adapter (runs inside the generated preview page).
 *
 * VideoHub's contract (docs/PROJECT-CONTRACT.md §2): the page defines window.renderOut(t), draws second t
 * synchronously, is a pure function of t, and sets window.READY once everything is loaded.
 *
 * HyperFrames' contract: its runtime (hyperframe.runtime.iife.js, injected ahead of this file) exposes
 * window.__player once the composition is built. __player.renderSeek(t) is the same entry point the
 * HyperFrames producer drives during an export render: it pauses the clock, seeks every GSAP timeline and
 * frame adapter to t synchronously, applies clip visibility windows, syncs media and paints VFX.
 *
 * So renderOut(t) = __player.renderSeek(t). The preview shows the real composition (index.html), not a
 * re-implementation. Two documented differences from the final render:
 *   - <video> frames decode asynchronously in a browser, so a seeked video can show its new frame a few ms
 *     after renderOut returns (the export engine pre-extracts frames instead). DOM, text, images, SVG,
 *     canvas and GSAP motion are exact.
 *   - VideoHub plays the film's sound itself (audio/mix.wav), so all page media are muted here.
 */
(function () {
  'use strict';
  var cfg = window.__FVS_PREVIEW__ || {};
  var fps = +cfg.fps || 30;
  var duration = +cfg.duration || 0;
  var media = [];

  window.VH_CONFIG = { width: +cfg.width || 1920, height: +cfg.height || 1080, fps: fps, duration: duration || undefined };

  function fail(msg) {
    window.__vhError = msg;
    try { console.error('[fvs-adapter] ' + msg); } catch (e) { /* ignore */ }
  }

  // FNV-1a over UTF-8 bytes; the generator computes the same hash in Node.
  function fnv1a(text) {
    var bytes = new TextEncoder().encode(text), h = 0x811c9dc5;
    for (var i = 0; i < bytes.length; i++) { h ^= bytes[i]; h = Math.imul(h, 0x01000193) >>> 0; }
    return ('00000000' + h.toString(16)).slice(-8);
  }

  // The generated page is a copy of index.html. If index.html changed since, say so instead of
  // previewing an outdated film.
  function checkFresh() {
    if (!cfg.sourceHash || !cfg.sourceFile) return true;
    try {
      var x = new XMLHttpRequest();
      x.open('GET', cfg.sourceFile + '?fvs=' + Date.now(), false);
      x.send();
      if (x.status >= 200 && x.status < 300 && fnv1a(x.responseText) !== cfg.sourceHash) {
        fail('Preview is out of date: ' + cfg.sourceFile + ' changed after the preview page was generated. ' +
             'Run `node bin/fvs.mjs preview <project>` (the agent does this after every edit).');
        return false;
      }
    } catch (e) { /* offline file:// open: skip the check */ }
    return true;
  }

  function muteAll() {
    media = Array.prototype.slice.call(document.querySelectorAll('audio, video'));
    media.forEach(function (m) { m.muted = true; m.volume = 0; });
  }

  function scenes() {
    if (cfg.scenes && cfg.scenes.length) return cfg.scenes;
    var out = [];
    document.querySelectorAll('[data-fvs-scene]').forEach(function (el) {
      var t0 = parseFloat(el.getAttribute('data-start')), d = parseFloat(el.getAttribute('data-duration'));
      if (isFinite(t0) && isFinite(d)) out.push({ name: el.getAttribute('data-fvs-scene') || el.id, t0: t0, t1: t0 + d });
    });
    return out.sort(function (a, b) { return a.t0 - b.t0; });
  }

  window.renderOut = function (t) {
    var p = window.__player;
    if (!p || typeof p.renderSeek !== 'function') throw new Error('HyperFrames runtime is not initialised (no __player.renderSeek)');
    var end = duration > 0 ? duration - 0.5 / fps : Infinity;
    var at = Math.max(0, Math.min(+t || 0, end));
    p.renderSeek(at);
    for (var i = 0; i < media.length; i++) if (!media[i].muted) media[i].muted = true;
  };

  function assetsSettled(deadline) {
    var imgs = Array.prototype.slice.call(document.images);
    var pending = imgs.filter(function (im) { return !im.complete; });
    var vids = Array.prototype.slice.call(document.querySelectorAll('video')).filter(function (v) { return v.readyState < 2; });
    if (!pending.length && !vids.length) return true;
    if (performance.now() > deadline) {
      console.warn('[fvs-adapter] still loading after 30 s: ' + pending.length + ' image(s), ' + vids.length + ' video(s)');
      return true;   // VideoHub still opens; the QC stage reports missing media separately
    }
    return false;
  }

  function start() {
    if (!checkFresh()) return;
    var t0 = performance.now(), deadline = t0 + 30000;
    var fontsReady = false;
    (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(function () { fontsReady = true; });
    (function poll() {
      if (window.__vhError) return;
      var p = window.__player;
      var runtimeReady = window.__playerReady === true && window.__renderReady === true && p && typeof p.renderSeek === 'function';
      if (runtimeReady && fontsReady && assetsSettled(deadline)) {
        if (!duration && typeof p.getDuration === 'function') { duration = p.getDuration(); window.VH_CONFIG.duration = duration; }
        muteAll();
        window.VH_SCENES = scenes();
        try { window.renderOut(0); } catch (e) { fail(e.message); return; }
        window.READY = true;
        return;
      }
      if (performance.now() - t0 > 90000) { fail('HyperFrames runtime did not become ready within 90 s (playerReady=' + window.__playerReady + ', renderReady=' + window.__renderReady + ')'); return; }
      setTimeout(poll, 50);
    })();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
