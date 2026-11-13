# artfx3 requests

## 2026-11-13: paid image calls refused until screenfix is on main (blocker, lead only)
`tools/assetgen.py image --piece vfx-stun ...` stops with `NO CONTEXT SHOT: ... origin/main has no -SmokeShotFrames support yet`.
`origin/area/screenfix` has `-SmokeShotFrames` (SmokeHookSubsystem.cpp/.h); `origin/main` does not. Needed: merge area/screenfix to main
(or tell me the guard may be lifted). No paid call was made and the guard was not bypassed. All eight vfx pieces wait on this.

## 2026-11-13: image spend cap nearly spent (blocker, lead only)
Context-shot guard is cleared. Shared counter is $31.22 of $33.82. Eight vfx pieces are all still below the bar (best whole-strip 0.47 vs 0.57-0.81 needed), and each draft round costs about $0.10 with no pass yet. Needed: a higher IMAGE_SPEND_CAP_USD for this lane, or a decision to leave artfx3 pieces as tracked `_PH` placeholders.
