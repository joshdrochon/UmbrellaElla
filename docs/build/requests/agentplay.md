# Requests from agentplay

## soundlabel lane: the dev sound-label list takes every mouse click (workbench builds)
Measured 2026-11-13 (journey run, `tools/build/journeys/lose.txt`): a click on the Start screen's Start Game button hit
`SSoundLabelList`, not the button; the click then moved keyboard focus to `SViewport`, so Enter no longer worked either.
The list is added full-screen at `UmbrellaSoundLabel::ViewportZOrder` and is Visible (hit-testable). Packaged game
(`UMBRELLAELLA_WORKBENCH=0`) is not affected; editor -game and Workbench builds are.

`Source/UmbrellaElla/Private/Feedback/Audio/SoundLabelHud.cpp`, in `SSoundLabelList::Construct`, after `ChildSlot`:
```diff
-			ChildSlot
+			SetVisibility(EVisibility::HitTestInvisible);
+			ChildSlot
```
Workaround until then: the journey hook sets it HitTestInvisible and logs `JOURNEY_WORKAROUND`.
