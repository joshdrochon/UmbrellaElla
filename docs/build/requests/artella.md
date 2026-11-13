# artella requests (to the build lead)

## 1. The `context` pair makes a first pass impossible inside this lane (tools/art_loop.py, not my lane)
- What: `art_loop.py panel` lists `context` as missing for every Ella piece ("no in-engine capture made after the
  piece: import it and run the smoke"). The area brief says a piece is imported only after it passes. So no Ella piece
  can pass today, whatever the reference and quality-bar panels answer.
- Second problem: the context pair puts the whole game screenshot against the key art. That verdict depends on the
  scene, the Keeper and the shots (other lanes), not on the Ella sprite.
- Decision needed (Josh or lead; this is a bar question, so I am not choosing):
  - (a) the lead imports a candidate that has passed `reference` + `quality_bar` + the deterministic checks as a
    tracked `_PH`, runs the smoke, and the context panel runs on that capture; or
  - (b) context is judged once for the `scene` piece only, not per element piece.
- My lean: (a). It keeps the bar as written and only fixes the order of steps.
- Until answered: I run the `reference` and `quality_bar` panels and the deterministic checks, and keep every piece `_PH`.

## 2. No Ella `_PH` slot exists in the game, so the lane cannot make its own context capture (Nov 13)
- Checked after merging main (ad9d6d1d "Context capture"): `Content/UmbrellaElla/Art/` has only `VFX/`. Nothing in `Source/`
  loads an Ella texture or flipbook: `UEllaAnimPresenterComponent::BuildVisual` uses `IdleFlipbook` (never set by any caller,
  `SetStateFlipbook` has no caller) and otherwise builds a cube stand-in. A run_game.sh capture would show the cube.
- Need (Gameplay/Feedback lane, not mine): `BuildVisual` loads `/Game/UmbrellaElla/Art/Ella/FB_Ella_<State>_PH` (Open, Attack,
  Shield, Closed) via LoadObject when present, falls back to the cube when not. Then I import the candidate as `_PH` flipbooks
  with a committed editor script and make the capture.
- Until then ella-up-open (reference + quality-bar pairs ours) cannot get a `context` pair.

## 3. Context capture fires before shaders are ready on a loaded machine (Nov 13 late)
- Need (smoke/screenfix lane): make `-SmokeShot` frame-based or wait until shaders are done, or accept `-SmokeShotDelay=<s>` on the command line. Today it is a fixed 5 s (`SmokeHookSubsystem.cpp:132`) and the only capture made showed "Preparing Shaders" on black.
- Until then no Ella piece can get a `context` pair. Waiting on it: import up-open as T_Ella_Idle_PH (already done), capture, finish panel; paint shield R3 and closed R3.
- Round 21: workaround exists (`-ini:Game:[/Script/UmbrellaElla.UmbrellaTuning]:Flow=(SmokeShotDelaySeconds=N)`), but N=120 hits Defeat (Ella dies) and N=35 waits on slots. A frame-based shot (after first gameplay frame + shaders ready) is still the fix.
