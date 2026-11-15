# Area: fallrules

Started by the build lead from Josh's 14 Nov brief. It is the definition of done.

- WIND-03: the bottom is lethal (reaching it defeats Ella, same death flow as health).
- D-new-ceiling-lethal: rising past the ceiling top is death, in Start Game, the Director's Cut route and the Keeper arena.
- D-new-move-speeds: one movement path (no double move); Ella's speeds are the felt values Josh kept (rise 240, fall 660,
  free fall 1220, horizontal max 580, hop 80, dash 170, WindMaxSpeed 720, WindScale 2), signed under D-new-creative-director-feel.
- Proof: world tests in the test world, and an offscreen real-game measure within 5% of the speeds before the fix.
