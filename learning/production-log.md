# Production log

One entry per production: what the user corrected in review, and what that teaches. Claude appends here after
each project (SKILL.md step 9). Reusable preferences are proposed in `style-amendments.md`, never applied to the
style guides without the user's confirmation.

## 2026-11-21 — The Box That Changed the World (pipeline test, simulated review)
- Note (simulated): flat colour behind kinetic words felt empty → put the related photo, dimmed, behind the words.
- Pipeline lessons: look at snapshots of every scene before showing the user (7 visual defects found that lint
  and parity checks could not see); verify a fix before marking the note fixed; never put a derived figure on
  screen (QC now fails it).

## 2026-11-22 — test film approved and delivered
- Approved by the user in chat; HyperFrames render 116 s for 44.4 s on 4 vCPU; final QC 0 failures.
- Delivery limit learned: the Drive connector cannot carry videos (~4 MB/call) — send the MP4 in chat until the
  Drive API OAuth is set up; reference archives must be split into ≤ 2.8 MB standalone parts.
- Research: Agent-Reach (pinned c70ae6d) gives web search/read in the cloud; Wikimedia is blocked there (429).
