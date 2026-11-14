# Progression proof: B9 Done and Shots fired (Nov 13)

Source tree = the commit that adds this file (built from it; build exit: 0, warnings: 0). engine=5.8.4 config=Development host=mac run=editor -game via tools/build/run_game.sh (640x360 windowed; RUN_RES 1280x720 and 1920x1080 offscreen). -SmokeQuitAfter was not used: its hook starts Start Game from the title by itself, so the purchase screen never opens; the journey hook quits the run at its end.

## B9: purchase screen Done (journey b9_done_click.txt)
```
PROGRESSION_DONE_CLICK ok=1 window=640x360 done_rect=235,297,38x19 inside=1 under=STextBlock on_done=1 before=Purchase after=Title
JOURNEY_END passed=12 failed=0 blocker="none" screen=Title mode=dc retries=0 held=[] encounter=0 phase=wings
```
```
PROGRESSION_DONE_CLICK ok=1 window=1280x720 done_rect=379,554,61x32 inside=1 under=STextBlock on_done=1 before=Purchase after=Title
JOURNEY_END passed=12 failed=0 blocker="none" screen=Title mode=dc retries=0 held=[] encounter=0 phase=wings
```
```
PROGRESSION_DONE_CLICK ok=1 window=1920x1080 done_rect=589,836,94x49 inside=1 under=STextBlock on_done=1 before=Purchase after=Title
JOURNEY_END passed=12 failed=0 blocker="none" screen=Title mode=dc retries=0 held=[] encounter=0 phase=wings
```
Measured: ok=1 needs Done fully inside the window, Slate's hit test at Done's centre landing on Done (on_done=1; the text block is Done's label), and the screen leaving Purchase after a real mouse press and release there. Before the fix agentplay's click landed on SBorder and nothing happened (d00_purchase.png).

## Shots fired (journey shots_fired.txt, 640x360)
```
PROGRESSION_RUN_STATS ok=0 shots_fired=0 shots_fired_at_you=0 attack_emitted=0 screen=Playing
JOURNEY_STEP n=9 line=12 cmd="hold J" result=PASS screen=Playing mode=dc retries=0 held=[J] lives=3/3 active=3.00/3.00 ella=(-720,44) route_cp=0 encounter=0 phase=wings detail="held 8.00s"
PROGRESSION_RUN_STATS ok=1 shots_fired=40 shots_fired_at_you=0 attack_emitted=40 screen=Playing
JOURNEY_END passed=11 failed=0 blocker="none" screen=Playing mode=dc retries=0 held=[] lives=3/3 active=3.00/3.00 ella=(-720,93) route_cp=0 encounter=0 phase=wings
```
Measured: after 8 s of J held, Journey Complete's Shots fired = 40 = the shots Ella's attack component emitted (was 0: story compared the spawn event's Detail with "PlayerBlast", the projectile service sends "EUmbrellaShotKind::PlayerBlast").

## frame_check
- frame_check: PASS image=pipeline/art/proof/progression/b9_after_done_640x360.png black=0.000 flat=0.099 top_colour=(32, 24, 24)
- frame_check: PASS image=pipeline/art/proof/progression/b9_purchase_1280x720.png black=0.002 flat=0.096 top_colour=(64, 56, 48)
- frame_check: PASS image=pipeline/art/proof/progression/b9_purchase_1920x1080.png black=0.002 flat=0.098 top_colour=(64, 56, 48)
- frame_check: PASS image=pipeline/art/proof/progression/b9_purchase_640x360.png black=0.002 flat=0.129 top_colour=(64, 56, 48)
- frame_check: PASS image=pipeline/art/proof/progression/shots_after_hold_640x360.png black=0.068 flat=0.076 top_colour=(192, 176, 208)
