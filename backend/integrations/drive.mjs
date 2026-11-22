// Google Drive API v3 client for large files (the Claude Drive connector caps each call at ~4 MB).
// OAuth "installed app" flow with a loopback redirect; the refresh token is stored outside the repository
// (~/.config/faceless-video-studio/google-token.json, mode 600) or read from FVS_GOOGLE_REFRESH_TOKEN on a
// cloud backend (from its secret manager — never from source code).
//
// STATUS: implemented against the documented Drive v3 REST API; NOT yet run against a real account
// (needs the user's OAuth client). See docs/google-drive.md.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import http from 'node:http';
import crypto from 'node:crypto';

// Full Drive scope: drive.file only allows writing into folders this app created, but the YouTube Production
// folders may be created by the user or by Claude's Drive connector, so uploads there need the drive scope.
export const SCOPES = ['https://www.googleapis.com/auth/drive'];
const CFG_DIR = path.join(process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config'), 'faceless-video-studio');
const TOKEN_FILE = path.join(CFG_DIR, 'google-token.json');
export const TREE = ['Input', 'Projects', 'Completed Videos', 'Project Files', 'Production Reports', 'Reference Library'];

export const CLIENT_FILE = path.join(CFG_DIR, 'google-oauth-client.json');

/** OAuth client: from .env (GOOGLE_OAUTH_CLIENT_ID/SECRET), else from the JSON file Google lets you download
 *  (GOOGLE_OAUTH_CLIENT_FILE, default ~/.config/faceless-video-studio/google-oauth-client.json). */
export function client() {
  let id = process.env.GOOGLE_OAUTH_CLIENT_ID, secret = process.env.GOOGLE_OAUTH_CLIENT_SECRET;
  if (!id || !secret) {
    const file = process.env.GOOGLE_OAUTH_CLIENT_FILE || CLIENT_FILE;
    if (fs.existsSync(file)) {
      const j = JSON.parse(fs.readFileSync(file, 'utf8'));
      const c = j.installed || j.web || j;
      if (j.web) throw new Error(`${file} is a "Web application" client; create a "Desktop app" OAuth client instead`);
      id = c.client_id; secret = c.client_secret;
    }
  }
  if (!id || !secret) throw new Error(`no Google OAuth client found: put GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET in the studio's .env, or save the downloaded JSON as ${CLIENT_FILE} (see docs/google-drive.md)`);
  return { id, secret };
}

/** One-time consent on a computer with a browser. Stores the refresh token outside the repo. */
export async function authorize({ open = true } = {}) {
  const { id, secret } = client();
  const state = crypto.randomBytes(16).toString('hex');
  const verifier = crypto.randomBytes(32).toString('base64url');
  const challenge = crypto.createHash('sha256').update(verifier).digest('base64url');
  const { code, redirect } = await new Promise((resolve, reject) => {
    const srv = http.createServer((req, res) => {
      const u = new URL(req.url, 'http://127.0.0.1');
      if (u.searchParams.get('state') !== state) { res.end('state mismatch'); return; }
      res.end('Authorised. You can close this tab.');
      srv.close();
      u.searchParams.get('code') ? resolve({ code: u.searchParams.get('code'), redirect: `http://127.0.0.1:${srv.address().port}` }) : reject(new Error(u.searchParams.get('error') || 'no code'));
    }).listen(0, '127.0.0.1', () => {
      const redirect_uri = `http://127.0.0.1:${srv.address().port}`;
      const url = 'https://accounts.google.com/o/oauth2/v2/auth?' + new URLSearchParams({ client_id: id, redirect_uri, response_type: 'code', scope: SCOPES.join(' '),
        access_type: 'offline', prompt: 'consent', state, code_challenge: challenge, code_challenge_method: 'S256' });
      console.log(`Open this URL to authorise Google Drive access:\n${url}`);
      if (open) import('node:child_process').then(({ spawn }) => spawn(process.platform === 'win32' ? 'cmd' : process.platform === 'darwin' ? 'open' : 'xdg-open', process.platform === 'win32' ? ['/c', 'start', '', url] : [url], { detached: true, stdio: 'ignore' }).unref());
    });
  });
  const r = await fetch('https://oauth2.googleapis.com/token', { method: 'POST', body: new URLSearchParams({ client_id: id, client_secret: secret, code, code_verifier: verifier, grant_type: 'authorization_code', redirect_uri: redirect }) });
  const tok = await r.json();
  if (!tok.refresh_token) throw new Error('no refresh token returned: ' + JSON.stringify(tok));
  fs.mkdirSync(CFG_DIR, { recursive: true });
  fs.writeFileSync(TOKEN_FILE, JSON.stringify({ refresh_token: tok.refresh_token, scope: tok.scope, created: new Date().toISOString() }), { mode: 0o600 });
  return { stored: TOKEN_FILE };
}

let cached = null;
async function accessToken() {
  if (cached && cached.exp > Date.now() + 60000) return cached.token;
  const { id, secret } = client();
  const saved = fs.existsSync(TOKEN_FILE) ? JSON.parse(fs.readFileSync(TOKEN_FILE, 'utf8')) : null;
  const refresh = process.env.FVS_GOOGLE_REFRESH_TOKEN || saved?.refresh_token;
  if (!refresh) throw new Error('not authorised: run `fvs drive-auth` once on a computer with a browser');
  if (!process.env.FVS_GOOGLE_REFRESH_TOKEN && saved && !SCOPES.every(sc => String(saved.scope || '').split(' ').includes(sc)))
    throw new Error('the saved Google login has older, narrower permissions (uploads into your existing folders would fail): run `fvs drive-auth` again');
  const r = await fetch('https://oauth2.googleapis.com/token', { method: 'POST', body: new URLSearchParams({ client_id: id, client_secret: secret, refresh_token: refresh, grant_type: 'refresh_token' }) });
  const t = await r.json();
  if (!t.access_token) throw new Error('token refresh failed: ' + (t.error_description || t.error));
  cached = { token: t.access_token, exp: Date.now() + t.expires_in * 1000 };
  return cached.token;
}

async function api(pathname, opts = {}) {
  const r = await fetch(`https://www.googleapis.com/drive/v3/${pathname}`, { ...opts, headers: { Authorization: `Bearer ${await accessToken()}`, ...(opts.headers || {}) } });
  if (!r.ok) throw new Error(`Drive ${pathname.split('?')[0]}: HTTP ${r.status} ${await r.text()}`);
  return r;
}
const q = s => s.replace(/\\/g, '\\\\').replace(/'/g, "\\'");

export async function findFolder(name, parent = 'root') {
  const r = await (await api(`files?q=${encodeURIComponent(`name = '${q(name)}' and mimeType = 'application/vnd.google-apps.folder' and '${parent}' in parents and trashed = false`)}&fields=files(id,name)`)).json();
  return r.files[0]?.id || null;
}
export async function ensureFolder(name, parent = 'root') {
  const id = await findFolder(name, parent);
  if (id) return id;
  const r = await (await api('files?fields=id', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name, mimeType: 'application/vnd.google-apps.folder', parents: [parent] }) })).json();
  return r.id;
}
/** YouTube Production/{Input,Projects,Completed Videos,Project Files,Production Reports,Reference Library} */
export async function ensureTree(rootName = 'YouTube Production') {
  const root = await ensureFolder(rootName);
  const out = { root };
  for (const n of TREE) out[n] = await ensureFolder(n, root);
  return out;
}

/** Newest script + voiceover in Input/ (script: txt/md/docx/Google Doc; voice: wav/mp3/m4a/aac). */
export async function findInputs(inputFolder) {
  const r = await (await api(`files?q=${encodeURIComponent(`'${inputFolder}' in parents and trashed = false`)}&orderBy=modifiedTime desc&fields=files(id,name,mimeType,size,modifiedTime)`)).json();
  const script = r.files.find(f => /\.(txt|md|docx)$/i.test(f.name) || f.mimeType === 'application/vnd.google-apps.document');
  const voice = r.files.find(f => /\.(wav|mp3|m4a|aac)$/i.test(f.name) || /^audio\//.test(f.mimeType));
  return { script, voice, all: r.files };
}

export async function download(file, dst) {
  const isDoc = file.mimeType === 'application/vnd.google-apps.document';
  const r = await api(isDoc ? `files/${file.id}/export?mimeType=text/plain` : `files/${file.id}?alt=media`);
  const out = fs.createWriteStream(dst);
  for await (const chunk of r.body) out.write(chunk);
  await new Promise(res => out.end(res));
  return dst;
}

/** Resumable upload in 8 MiB chunks (works for multi-GB renders; resumes chunk by chunk on failure). */
export async function upload(file, parent, { name = path.basename(file), mimeType = 'application/octet-stream' } = {}) {
  const size = fs.statSync(file).size;
  const init = await fetch('https://www.googleapis.com/upload/drive/v3/files?uploadType=resumable&fields=id,webViewLink', {
    method: 'POST', headers: { Authorization: `Bearer ${await accessToken()}`, 'Content-Type': 'application/json', 'X-Upload-Content-Type': mimeType, 'X-Upload-Content-Length': String(size) },
    body: JSON.stringify({ name, parents: [parent] }) });
  if (!init.ok) throw new Error(`upload init: HTTP ${init.status} ${await init.text()}`);
  const session = init.headers.get('location');
  const CH = 8 * 1024 * 1024;
  const fd = fs.openSync(file, 'r');
  try {
    let offset = 0;
    while (offset < size) {
      const len = Math.min(CH, size - offset), buf = Buffer.alloc(len);
      fs.readSync(fd, buf, 0, len, offset);
      let r;
      for (let attempt = 0; attempt < 5; attempt++) {
        try {
          r = await fetch(session, { method: 'PUT', headers: { 'Content-Length': String(len), 'Content-Range': `bytes ${offset}-${offset + len - 1}/${size}` }, body: buf });
          if (r.status < 500) break;
        } catch { /* network error: retry */ }
        await new Promise(res => setTimeout(res, 2000 * 2 ** attempt));
      }
      if (r?.status === 308) { const rg = r.headers.get('range'); offset = rg ? +rg.split('-')[1] + 1 : offset + len; continue; }
      if (r && (r.status === 200 || r.status === 201)) return r.json();
      throw new Error(`upload failed at byte ${offset}: HTTP ${r?.status}`);
    }
  } finally { fs.closeSync(fd); }
}
