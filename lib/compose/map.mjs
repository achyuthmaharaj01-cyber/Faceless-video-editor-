// Flat world map as SVG, rendered at build time from Natural Earth data (public domain, via world-atlas)
// with d3-geo. The composition gets plain SVG paths: nothing to load or compute at render time.
import fs from 'node:fs';
import path from 'node:path';
import { geoMercator, geoPath } from 'd3-geo';
import { feature } from 'topojson-client';
import { REPO_ROOT } from '../videohub/build-preview.mjs';

const topo = {};
function countries(res = '50m') {
  topo[res] ??= JSON.parse(fs.readFileSync(path.join(REPO_ROOT, 'node_modules', 'world-atlas', `countries-${res}.json`), 'utf8'));
  return feature(topo[res], topo[res].objects.countries).features.filter(c => c.properties?.name !== 'Antarctica');
}

const projections = new Map();
function projectionFor(w, h) {
  const key = `${w}x${h}`;
  if (!projections.has(key)) {
    // Mercator framed on the inhabited world (lat ~ -56..78), filling the frame
    const p = geoMercator().fitExtent([[0, 0], [w, h]], { type: 'MultiPoint', coordinates: [[-170, 78], [190, -56]] });
    projections.set(key, p);
  }
  return projections.get(key);
}

export function project([lon, lat], w, h) { return projectionFor(w, h)([lon, lat]); }

/**
 * zoom: the largest camera zoom the scene uses. Zoomed-in maps use the 1:10m coastline, clipped to `views`
 * (screen rectangles the camera shows, in map pixels) so the SVG stays small; strokes are thinned by the zoom
 * because CSS-transform scaling also scales SVG strokes.
 */
export function worldMapSvg({ width, height, sea = '#a9dcf3', land = '#86d65a', highlight = [], zoom = 1, views = null }) {
  const base = projectionFor(width, height);
  const res = zoom >= 5 ? '10m' : zoom >= 2 ? '50m' : '110m';
  let p = base;
  if (views && zoom >= 2) {
    const x0 = Math.max(0, Math.min(...views.map(v => v[0])) - 60), y0 = Math.max(0, Math.min(...views.map(v => v[1])) - 60);
    const x1 = Math.min(width, Math.max(...views.map(v => v[2])) + 60), y1 = Math.min(height, Math.max(...views.map(v => v[3])) + 60);
    p = geoMercator().scale(base.scale()).translate(base.translate()).clipExtent([[x0, y0], [x1, y1]]);
  }
  const gp = geoPath(p);
  const hi = new Set((highlight || []).map(s => s.toLowerCase()));
  const sw = (1.4 / Math.max(1, zoom)).toFixed(3);
  const dec = zoom >= 5 ? 2 : 1;
  const paths = countries(res).map(c => {
    const d = gp(c);
    if (!d) return '';
    const isHi = hi.has(String(c.properties?.name).toLowerCase());
    return `<path d="${d.replace(/(\d+\.\d{${dec}})\d+/g, '$1')}" fill="${isHi ? '#f2c94c' : land}" stroke="#5aa83a" stroke-width="${sw}"/>`;
  }).join('');
  return { svg: `<svg viewBox="0 0 ${width} ${height}" style="position:absolute;inset:0;width:100%;height:100%"><rect width="${width}" height="${height}" fill="${sea}"/>${paths}</svg>`, viewW: width, viewH: height };
}
