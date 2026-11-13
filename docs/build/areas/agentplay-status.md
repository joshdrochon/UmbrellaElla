# agentplay status (HAZ-16 agent play-tester, D-new-haz16-agent-playtest)

## Built
- `Source/UmbrellaElla/Private/Smoke/AgentPlayHookSubsystem.cpp` (+ `Public/Smoke/AgentPlayHookSubsystem.h`, `AgentPlayRules.*`): workbench builds
  only, exists only with `-AgentPlay=<dir>`. Writes the window to `<dir>/frames/fNNNNNN.jpg` about every 150 ms while the game runs
  and when a turn ends; reads `<dir>/turn_NNNN.txt` key scripts and presses them through `APlayerController::InputKey`; pauses between
  turns (a slow player costs no game time); `stop.txt` ends the attempt. `result.json` holds what the game measured itself: damage,
  useful hits (guard HP lost / FriendlyDamage), shots, warning events, off-line (reset) seconds, idle seconds, teleport check. No move,
  aim, heal or wait-skip command exists; keys are the default controls only (`AgentPlayRules::ResolveKeyName`).
- `tools/build/agent_play.py`: a fresh `claude -p` Sonnet session per attempt (`--tools ""`, stream-json image input, empty cwd, no
  settings) sees only frames and `tools/build/agent_play_controls.txt`. Before any play it states expected solid / harmful / background
  and its descent/reset plan; each turn it says what it sees and whether it saw a warning; at the end it gives its words, understood,
  warning noticed, too slight, and a boring yes/no. Writes `haz16.log`: `PLAYTEST_HAZ16_ATTEMPT` per attempt, `PLAYTEST_HAZ16` per
  (res, health, profile). Debug draw off; `--health healthy|low|both`; `--profile comparison` (20 HP) refused unless `--after` points
  at natural attempts the player understood and rejected as boring (GDD HAZ-16: one changed variable, 10 HP first).
- `tools/build/playtest_check.py` HAZ-16: only `source=agent` lines count; needs 1280x720 and (1728x1117 or 1920x1080), healthy and
  low at each, no boring / not cleared / teleport / autoaim / invulnerability, and the expect/plan/words items present. The old check
  wanted 1920x1080 on this Mac, which clamps it; D-new-haz16-agent-playtest moves that size to the Windows check.

## Tests
- `UmbrellaElla.Smoke.AgentPlay.*` (5 rule tests: key whitelist, turn schedule, refusals, release-before-press, file/frame names): PASS.
- `tests/test_agent_play.py` (fake game thread speaking the file protocol, fake player): attempt flow, refused scripts, stop, log lines,
  checker verdicts, comparison gate, key-table parity with the C++ table. `tests/test_playtest_check.py` updated.

## Findings on the game as rendered (this Mac, editor -game, offscreen)
- With no light the Slate window read-back shows only the HUD clock and a dim light shaft; the lit placeholder cubes (Ella, guard) render
  black. The hook adds one directional light (workbench only, `-AgentPlayNoLight` turns it off; `lit_by_hook=1` in result.json).
  With it the screen shows a large grey tiled surface over the room; Ella and the guard are not readable at their positions.
  This is the game's current look, not the hook: a player cannot discover the room from it. See the attempt records for the player's words.
- The Mill room is spawned under the play camera at the player start (`AGENTPLAY_SETUP` log line) with its normal 10 HP guard; the
  scripted run's far-off scratch room is outside the arena camera.

## Not run / left
- 1920x1080: Windows check only (`python3 tools/build/agent_play.py --rule HAZ-16 --res 1920x1080`).
- Full matrix (1280x720 and 1728x1117, healthy and low, 3 attempts each) not run: the screen is unreadable (above), so every run
  would be a recorded reject. Run it once the room is readable. 20 HP comparison: only after a natural reject by the player.
