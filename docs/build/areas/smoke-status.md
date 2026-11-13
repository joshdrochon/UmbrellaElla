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
