# Requests from artscene

## 1. Critic packet ground for transparent layers (tools/art_loop.py, not my lane)
Now: `flatten_on_ground` puts a transparent piece on a flat fill, `PACKET_GROUND = (238, 229, 210)`.
Problem: against the key art the critics keep naming the ground, not the piece: "sits on a flat cream fill with no aged-paper grain"
(skyline r12 c1, r13 c3, r14 01-c3, r15 01-c1 and 01-c3). The paper is its own piece; the skyline ships transparent.
Change: composite transparent images (ours and any reference with alpha) over one shared paper-textured ground instead of a flat colour, for
example a tile cut from the paper area of `pipeline/art/reference/target-keyart.png` (x 300-900, y 60-300, mirrored to fill), or flat
`PACKET_GROUND` plus the grain `art_check` measures as paper_texture >= 0.38. Same ground for both sides, so the bar does not move.
Workaround in my lane: none; I keep judging on the flat ground.

## 2. Context pair for scene pieces (arena / flow lanes)
`art_loop verdict` cannot pass skyline, paper or menu-screen without an in-engine capture newer than the piece
(`Saved/Logs/pipeline/*-shot.png` or `Saved/Screenshots/**`). That needs the piece imported as a `_PH`-free texture and drawn by the arena, then a smoke
run. Ask: after a piece wins its reference and quality-bar pairs, the build lead imports it on a scratch branch, runs the smoke, and drops the shot
in my worktree's `Saved/Logs/pipeline/`; I run the context panel on it.
