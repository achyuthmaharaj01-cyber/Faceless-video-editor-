# Reviewing away from the laptop

VideoHub is a local app: it listens on 127.0.0.1:7788 and its queue can run commands. **Do not expose it** — no
port forwarding, public tunnels or proxies. Remote review uses one of these instead.

## 1. Phone, anywhere (no laptop)

In the Claude session that is producing the video:
1. Claude snapshots one frame per scene (`npx hyperframes snapshot <project> --at …`) and sends the contact sheet
   and, on request, a short low-resolution clip of a scene range (`fvs render <project> --draft --start A --end B`,
   a preview, not the final) to the chat.
2. You reply with timestamped notes: `0:32 the map should zoom closer`, `scene 7: different photo`.
3. Claude maps each note to its storyboard scene (narration and timestamps from `audio/words.json`), revises, and
   sends the updated frames.
4. Approval is your explicit message ("approved, render it").

Everything stays inside your authenticated Claude conversation; nothing is published.

## 2. Laptop on, you elsewhere

Turn on Remote Control in the Claude desktop app on the laptop (Settings → Claude Code → Remote Control) and
share the VideoHub films folder. The cloud session can then attach that folder, write the project into it and run
VideoHub's tools there; you review in VideoHub when you are back at the desk (or in a remote-desktop app of your
choice). VideoHub itself still only listens locally.

## 3. At the desk

The full VideoHub workflow (SKILL.md step 6): frame-accurate scrubbing, drawn notes, "Send to Claude", "Check fixes".
