// Environment check: every tool the studio needs, with the exact fix for what is missing.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { REPO_ROOT, RUNTIME_SRC } from './videohub/build-preview.mjs';
import { python } from './videohub/notes.mjs';
import { launchBrowser } from './videohub/parity.mjs';

const win = process.platform === 'win32';
function ver(cmd, args = ['-version']) {
  const r = spawnSync(cmd, args, { encoding: 'utf8', shell: win });
  return r.status === 0 ? (r.stdout || r.stderr).split('\n')[0].trim() : null;
}

export async function doctor() {
  const rows = [];
  const add = (name, ok, detail, fix) => rows.push({ name, ok, detail, fix });
  const [maj, min] = process.versions.node.split('.').map(Number);
  add('Node.js ≥ 22', maj >= 22, process.version, win ? 'winget install -e --id OpenJS.NodeJS.LTS' : 'install Node 22 LTS');
  const ff = ver('ffmpeg'), fp = ver('ffprobe');
  add('FFmpeg', !!ff, ff || 'not found', win ? 'winget install -e --id Gyan.FFmpeg' : 'sudo apt install ffmpeg');
  add('FFprobe', !!fp, fp || 'not found', 'installed with FFmpeg');
  const py = ver(python(), ['--version']);
  add('Python 3.10+', !!py, py || `"${python()}" not found (set FVS_PYTHON)`, win ? 'winget install -e --id Python.Python.3.12' : 'install python3');
  if (py) {
    const r = spawnSync(python(), ['-c', 'import numpy, cv2, PIL, faster_whisper, docx; print("ok")'], { encoding: 'utf8' });
    add('Python packages', r.status === 0, r.status === 0 ? 'numpy, opencv, Pillow, faster-whisper, python-docx' : (r.stderr || '').trim().split('\n').pop(), `${python()} -m pip install -r requirements.txt`);
  }
  const hf = fs.existsSync(path.join(REPO_ROOT, 'node_modules', 'hyperframes', 'package.json')) && JSON.parse(fs.readFileSync(path.join(REPO_ROOT, 'node_modules', 'hyperframes', 'package.json'), 'utf8')).version;
  add('HyperFrames (pinned)', !!hf && fs.existsSync(RUNTIME_SRC), hf ? `hyperframes ${hf}` : 'not installed', 'npm install (in the studio folder)');
  try { const b = await launchBrowser(); add('Chromium for previews/QC', true, (await b.version()), ''); await b.close(); }
  catch (e) { add('Chromium for previews/QC', false, e.message.split('\n')[0], 'npx hyperframes browser ensure  (or set FVS_CHROME to Chrome/Edge)'); }
  // VideoHub
  const vhDirs = [process.env.VIDEOHUB_DIR, path.join(os.homedir(), 'VideoHub'), path.join(os.homedir(), 'Documents', 'VideoHub')].filter(Boolean);
  const vh = vhDirs.find(d => fs.existsSync(path.join(d, 'server', 'cli.js')));
  add('VideoHub', !!vh, vh || 'not found (set VIDEOHUB_DIR to its folder)', 'see docs/videohub-integration.md (install from github.com/TensaikunYT/Videohub)');
  const claudeCfg = path.join(os.homedir(), '.claude.json');
  const mcp = fs.existsSync(claudeCfg) && /"videohub"/.test(fs.readFileSync(claudeCfg, 'utf8'));
  add('VideoHub MCP registered for Claude Code', mcp, mcp ? 'videohub entry found in ~/.claude.json' : 'not registered (the CLI fallback still works)', 'run VideoHub setup with --agents claude, then restart Claude Code');
  add('Pexels / Pixabay API keys (optional)', !!(process.env.PEXELS_API_KEY || process.env.PIXABAY_API_KEY), [process.env.PEXELS_API_KEY && 'Pexels', process.env.PIXABAY_API_KEY && 'Pixabay'].filter(Boolean).join(', ') || 'none: only Openverse, Wikimedia and NASA are searched', 'free keys: pexels.com/api, pixabay.com/api/docs → .env');
  const ok = rows.filter(r => !/optional|MCP/.test(r.name)).every(r => r.ok);
  const text = rows.map(r => `${r.ok ? '✓' : '✗'} ${r.name.padEnd(40)} ${r.detail}${r.ok || !r.fix ? '' : `\n    fix: ${r.fix}`}`).join('\n');
  return { ok, rows, text };
}
