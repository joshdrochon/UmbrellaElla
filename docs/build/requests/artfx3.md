# artfx3 requests

## 2026-11-13: paid image calls refused until screenfix is on main (blocker, lead only)
`tools/assetgen.py image --piece vfx-stun ...` stops with `NO CONTEXT SHOT: ... origin/main has no -SmokeShotFrames support yet`.
`origin/area/screenfix` has `-SmokeShotFrames` (SmokeHookSubsystem.cpp/.h); `origin/main` does not. Needed: merge area/screenfix to main
(or tell me the guard may be lifted). No paid call was made and the guard was not bypassed. All eight vfx pieces wait on this.
