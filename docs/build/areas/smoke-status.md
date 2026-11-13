# smoke status
Done:
- `tools/ue/package.sh`: UAT's Mac archive step copies `Binaries/Mac/UmbrellaElla.app` (no `Contents/UE`). After BuildCookRun the script now replaces the archived app with `Saved/StagedBuilds/Mac/UmbrellaElla.app` (ditto) and fails if it has no `Contents/UE`. `Packaged/Mac/UmbrellaElla.app` runs on its own. package.ps1 not touched (Windows archives from the staged dir).
- `tools/ue/smoke.sh`: the game passes `-stdout -FullStdOutLogOutput`. Without it Log-verbosity lines (all LogUmbrellaElla) never reach stdout, and `-abslog` writes no file on the packaged Mac build, so the stdout log is the game log.
- Smoke hook: now injects keyboard (J = Shoot, expects vz < 0) and gamepad (right trigger + left stick right + A dash; gp_attack_vz < 0, gp_vx > 0) through `APlayerController::InputKey`, logs `input=ok gamepad=ok`. Tests: `UmbrellaElla.Smoke.LowFpsIsMeanOfSlowestShare`, `UmbrellaElla.Smoke.InputCheckFitsBeforeQuit`.
- Evidence: package exit 0 (commit d9ed07d), smoke with fps limits off: SMOKE_OK yes, input=ok, gamepad=ok, bake_preset PASS, 0 crash folders.
Left (see requests/smoke.md):
- `Failed to load` engine audio line fails the smoke (needs allow row or ini change outside my lane).
- fps below 55 under machine load (10 to 25 load average); not re-measured on a quiet machine.
- `-SmokeShot` PNG is never written on the packaged Mac build (screenshot request fires, no file, capture delegate never called); smoke-art is non-blocking until card 0.10b.
- `gp_shield_vz` not injected (shield row still planned). gp_vx is the peak X speed of a stick-right dash, because the SH1.0 move axis never steers.

## Review round (changes)
- Input machine is now `USmokeHookSubsystem::NextInputStep` (plain function). `UmbrellaElla.Smoke.InputCheckFitsBeforeQuit` walks it from Idle to Done, reads `Flow.SmokeShotDelaySeconds`, fails if a transition breaks. Defeat and Story/Credits wait for `InputStep == Done` (or quit + grace). `PadVx` removed, screenshot flag reverted.
- Evidence (commit a420452, Development, Mac, packaged): package exit 0, archive has Contents/UE. Smoke of `Packaged/Mac/UmbrellaElla.app`: SMOKE_OK yes, input=ok, gamepad=ok, bake_preset PASS.
- Still FAIL: 1 `Failed to load` line (engine audio text; needs requests/smoke.md item 1, outside my lane) and fps 15.7 at load average 27 (item 2, needs a quiet machine).
