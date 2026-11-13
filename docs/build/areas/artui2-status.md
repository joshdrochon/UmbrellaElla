# artui2 status (worker, 12-13 Nov)

Pieces: ui-credits ui-defeated ui-journey-complete ui-spell-wheel ui-story-text ui-tutorial ui-xp-ring. None passed.

## Round 1 (after merging area/artui and main)
- Build on the merged tree fails: `UmbrellaUIStyle.cpp:192` uses `UmbrellaUI::BodyLetterSpacing`, which does not exist
  (the artui worker's uncommitted BodyFont edit leaked in with the merge). Worked around locally with
  `DisplayLetterSpacing`, not committed (artui's file). artui must add the constant or revert the line.
- Captured at 1280x720 (`RUN_RES=1280x720 tools/build/run_game.sh -UIShots=...`): credits, defeated, tutorial, story
  into `pipeline/art/proof/artui2/<piece>/capture_*.png`. `-UIShots` has no shot for journey-complete, spell-wheel or
  xp-ring (they are in-game widgets); they need the in-game smoke shot at the right moment.
- `art_loop.py run --piece ui-defeated`: checks pass (art_ref 0.907, screen_check), calibration 6/8, quality_bar pair ours,
  reference pair reference. Gap: "heading is flat orange with no etched lettering; scene smoother, less textured".
- Same gap as ui-title in 15 rounds. Triage: the screens share one ground and one font with the title, so the cause is
  shared (typeset lettering and smooth ground against a painted key-art reference), not per screen.

## Why stopped
- The fix is shared UI code (`SFlowMenu`, `SFlowTextScreen`, the font, the ground), owned by artui. Editing it from
  here would collide with that lane. A painted heading plate per screen (as the title lockup) is the next try, and only
  pays off if artui's lockup passes first; it has not (r11-r15 reference won).
- Not run: panels on credits, tutorial, story; no spend ($0 this round).
- Next (if artui lands a lockup/lettering/grain fix): re-capture, panel the 4 screens, then add in-game captures for the 3 widgets.

## Round 2 (13 Nov; artui merged, local-only build patch, $0 spent)
- Build blocker: area/artui `UmbrellaUIStyle.cpp:192` `BodyLetterSpacing` missing (request in docs/build/requests/artui2.md). Patched locally, not committed.
- Recaptured credits, defeated, tutorial, story at 1280x720 via `-UIShots`.
- ui-tutorial: PASS (round 2, ours/ours, calibration 6/6, checks pass).
- ui-credits: reference wins (round 2). Gap: plain evenly weighted lettering, no gold/etched finish, bracketed placeholder text visible.
- ui-defeated: reference wins (round 3). Gap: softer, less etched linework and paper grain.
- ui-story-text: round 2 "same" on the reference pair but the tool said continue; round 3 reference wins (caption small, plain, no gold etching, low contrast over ruin).
- ui-story-text round 2 record ("same", no manifest or panel evidence) dropped; rounds 1 and 3 (reference wins) stay. Verifier clean.
- Left: journey-complete, spell-wheel, xp-ring (no capture shot). Credits/defeated/story share the lettering+grain gap with ui-title.
