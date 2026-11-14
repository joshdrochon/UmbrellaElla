# Area: visualqa

Started by the build lead (2026-11-13), Josh's priority: the game screen must look like Ricky's Other Realm study
(`bar-other-realm`, pipeline/art/reference/discord/20261111-0318_Ricky_other-realm.png) as a whole frame.

## Owns
- The composed frame: wind drawn in code as thin ash-blue `#555e60` ribbons (art bible line 193; never boxes or panels),
  sprite scale so figures read small as in the study, camera framing that composes the scene (screenfix's Ella-at-top-edge
  item moves here), draw order, and no placeholder boxes, bars or framed/unkeyed art on any gameplay screen.
- Stand-in draw rules: tools/build/art_slots.py, pipeline/art/standins.json, the generated slot catalog, and the presenter
  code that draws stand-ins (ArtSlot / UiArt / SceneArt / Vfx), route/wind stand-in cubes, scene panels and bars.
- The whole-frame check: tools/build/visual_qa.py and its tests.
- Not owned: where the Keeper and Ella spawn on the Director's Cut route (levelchunks, B5/B6); merge main often to pick that up.

## Order of work
1. Josh's 15:50 frame (pipeline/qa/visual/calibration/known-bad-josh-1550.png): framed, stretched, rotated gust stand-ins;
   a large lilac route cube; cream bars at the bottom and right; no Ella. Any stand-in not keyed on transparency or with
   frame borders falls back to the plain placeholder or is not drawn (enforced in art_slots.py with a test); the gusts first.
   Hide stand-in cubes/bars where art exists or tint them into the palette; never draw an artless panel.
2. Wind as ribbons, figure scale, framing, draw order, toward the study. Then iterate with artscene and artella's art.
3. tools/build/visual_qa.py (the gate will call it on every merge touching Source/, Content/, Art/ or pipeline/art):
   captures Start Game play, the Director's Cut route and the Keeper fight in a real window (ue_slot run_game + journeys),
   and an Opus judge (claude -p --model claude-opus-5-5, image input, no tools) compares each side by side with the study
   as a whole frame on a FIXED rubric: dark backdrop; thin ash-blue #555e60 ribbons, never boxes; small figures; floating
   islands; gold #E9C46A and red shots; no placeholder cubes or bars; no framed or unkeyed art. Output per screen: a score
   per rubric item, a "broken to a player" list, and PASS/FAIL. FAIL if any screen scores worse than main's cached
   baseline (logs/visual-baseline/<main sha>.json, refreshed when main moves) or has any "broken to a player" item.
   Exit codes and a one-line summary for gate.sh. Calibration: pipeline/qa/visual/calibration/known-good-other-realm.png
   must PASS and known-bad-josh-1550.png must FAIL; tests for both (judge call recorded/replayable so unit tests do not
   spend), plus parsing tests. Tell the lead the exact command line for the gate step.
4. Every round: a composite per screen (study | before | after) committed under pipeline/qa/visual/, and one dated line
   in pipeline/submission/devlog.md under "## Frames toward the Other Realm study" naming the composite path.

## Deadlines
- A first composed frame (Director's Cut route or Start Game play, after step 1 and first ribbons) committed within 45 min
  of 16:05: pipeline/qa/visual/composed-01.png plus its composite. The lead reports it.

## Rules
Every code fix: break-checked automation test. ue_slot for every Unreal run. Commit only with a clean tree; pre-check
PASS for the exact tip. No image generation spend in this lane (art comes from artscene and artella).
- Keeper fight backdrop seam (levelchunks, 16:14): at the Director's Cut Keeper handoff the route backdrop stops at the route end, so the left ~40% of the screen shows a different backdrop. Make the backdrop continuous across the handoff.
- Camera margin (coordinator, 16:20): keep the gameplay ceiling (z 1036); add a camera margin so Ella's full sprite stays in frame at the ceiling in Start Game and Director's Cut (move's B7 captures show her sprite top cut off). Test: projected sprite top inside the viewport at the ceiling, both modes.
