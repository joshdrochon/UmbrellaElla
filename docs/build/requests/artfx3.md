# artfx3 requests

## 2026-11-13: paid image calls refused until screenfix is on main (blocker, lead only)
`tools/assetgen.py image --piece vfx-stun ...` stops with `NO CONTEXT SHOT: ... origin/main has no -SmokeShotFrames support yet`.
`origin/area/screenfix` has `-SmokeShotFrames` (SmokeHookSubsystem.cpp/.h); `origin/main` does not. Needed: merge area/screenfix to main
(or tell me the guard may be lifted). No paid call was made and the guard was not bypassed. All eight vfx pieces wait on this.

## 2026-11-13: image spend cap nearly spent (blocker, lead only)
Context-shot guard is cleared. Shared counter is $31.22 of $33.82. Eight vfx pieces are all still below the bar (best whole-strip 0.47 vs 0.57-0.81 needed), and each draft round costs about $0.10 with no pass yet. Needed: a higher IMAGE_SPEND_CAP_USD for this lane, or a decision to leave artfx3 pieces as tracked `_PH` placeholders.

## 2026-11-13 (later): cap exceeded (blocker, lead only)
Counter $46.59 vs cap $33.82 (../logs/image-cap-usd.txt). Needed: a raised cap for artfx3, or accept the eight vfx pieces as `_PH` placeholders. Also PIL is missing from this python, which blocks cut_strip and per-frame art_judge.
