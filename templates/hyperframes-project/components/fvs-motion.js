/* faceless-video-studio motion interpreter (runs in the HyperFrames composition).
 * index.html carries the film's motion as data (window.FVS_SPEC, written by `fvs build`); this turns it into
 * one paused GSAP timeline at absolute seconds and registers it LAST, as HyperFrames requires.
 * Every value is a function of timeline time only: no clock, no unseeded randomness, no layout reads in
 * onUpdate, so any frame renders the same in any order (HyperFrames determinism contract). */
(function () {
  'use strict';
  function fmtNumber(v, f) {
    f = f || {};
    var d = f.decimals || 0, x = Math.abs(v), unit = '';
    if (f.compact) {
      var units = [[1e12, 'T'], [1e9, 'B'], [1e6, 'M'], [1e3, 'K']];
      for (var i = 0; i < units.length; i++) if (x >= units[i][0]) { x = x / units[i][0]; unit = units[i][1]; break; }
    }
    var s = x.toFixed(d);
    if (f.grouping !== false) { var p = s.split('.'); p[0] = p[0].replace(/\B(?=(\d{3})+(?!\d))/g, ','); s = p.join('.'); }
    return (v < 0 ? '-' : '') + (f.prefix || '') + s + unit + (f.suffix || '');
  }
  window.FVS_FORMAT = fmtNumber;

  window.FVS_RUN = function (spec) {
    var tl = gsap.timeline({ paused: true });
    var q = function (sel) { return document.querySelectorAll(sel); };
    (spec.motion || []).forEach(function (m) {
      var targets = q(m.s);
      if (!targets.length) { console.warn('[fvs] no element for ' + m.s); return; }
      if (m.k === 'ft') {
        var to = Object.assign({ duration: m.d, ease: m.e || 'none', immediateRender: m.i !== false }, m.to);
        tl.fromTo(targets, m.from, to, m.t);
      } else if (m.k === 'set') {
        tl.set(targets, m.to, m.t);
      } else if (m.k === 'count') {
        var node = targets[0], o = { v: m.from };
        node.textContent = fmtNumber(m.from, m.f);
        tl.fromTo(o, { v: m.from }, { v: m.to, duration: m.d, ease: m.e || 'power2.out',
          onUpdate: function () { node.textContent = fmtNumber(o.v, m.f); } }, m.t);
      } else if (m.k === 'attr') {
        tl.fromTo(targets, { attr: m.from }, { attr: m.to, duration: m.d, ease: m.e || 'none' }, m.t);
      }
    });
    window.__timelines[spec.id || 'main'] = tl;   // registered last
    return tl;
  };
})();
