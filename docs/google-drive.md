# Google Drive

Created in your Drive during setup (via the Claude Google Drive connector):

```
YouTube Production/
  Input/              put the script + voiceover here
  Projects/
  Completed Videos/   final MP4 + QC report + credits per video
  Project Files/
  Production Reports/
  Reference Library/
```

## Two access paths, and their limits (measured)

| Path | What works | Limit |
|---|---|---|
| **Claude Drive connector** (in Claude, incl. the phone app) | search, metadata, folders, reading Google Docs / small files, small uploads | **~4.2 MB per call** (≈ 3.1 MB of file) — a finished video cannot go through it |
| **Drive API with your own OAuth** (`backend/integrations/drive.mjs`, `fvs drive-pull` / `drive-push`) | any size: resumable 8 MiB-chunk uploads and streaming downloads | needs a one-time OAuth setup; implemented, **not yet run** against your account |

A Drive *folder link* never grants API access by itself.

## One-time OAuth setup (≈ 10 minutes, free)

1. console.cloud.google.com → create a project → *APIs & Services* → enable **Google Drive API**.
2. *OAuth consent screen*: External, add yourself as a test user, then **Publish to production** (unverified is
   fine for personal use; in "Testing" Google expires refresh tokens after 7 days).
3. *Credentials* → *Create credentials* → *OAuth client ID* → **Desktop app**, then keep it in **one** of these
   places (never in Git, never pasted into a chat):
   - **`.env` in the studio folder** (next to `package.json`; `fvs` loads it automatically):
     ```
     GOOGLE_OAUTH_CLIENT_ID=1234-abc.apps.googleusercontent.com
     GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-...
     ```
   - or the downloaded JSON file, renamed to
     `C:\Users\<you>\.config\faceless-video-studio\google-oauth-client.json` (macOS/Linux: `~/.config/faceless-video-studio/`).
   `.env` and `client_secret*.json` are listed in `.gitignore`. Delete the copy in Downloads afterwards.
4. On the laptop: `node bin/fvs.mjs drive-auth` → approve in the browser. The refresh token is stored in
   `~/.config/faceless-video-studio/google-token.json` (mode 600), outside the repository.
5. Scope: `drive` (read your inputs and upload into your existing `YouTube Production` folders — the narrower
   `drive.file` cannot write into folders another app created). Revoke any time at myaccount.google.com/permissions.

For a cloud backend, store the refresh token in its secret manager and expose it as `FVS_GOOGLE_REFRESH_TOKEN`.

## Workflow

- Inputs: `fvs drive-pull <dir>` (newest script + voiceover in `Input/`; Google Docs are exported as text), or
  in a Claude session the connector for the script plus the voiceover if it is under ~3 MB.
- Delivery: `fvs deliver <project>` then `fvs drive-push <project>` → `Completed Videos/<title>/`.
- Intermediate files are not uploaded unless you ask.
