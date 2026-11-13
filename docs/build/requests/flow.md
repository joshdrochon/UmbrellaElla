# Requests from flow

## Encounter director state getter (keeper lane)
Main's `UEncounterDirectorSubsystem` (Public/Encounter/EncounterDirectorSubsystem.h) has no state query. Flow's
StartGameReachesFight must assert the director is Active. area/keeper adds `EEncounterState GetState() const`; flow
uses it once 'Merge area/keeper' is on main. Until then the test cannot assert it.

## FLOW-34 "Start Director's Cut" label (story lane: pipeline/story/lines.csv) — Nov 13
GDD SH1.0 FLOW-34 and section 3 name the second title button "Start Director's Cut"; the game shows "Director's Cut"
(clause-audit tag ii). story_inventory fails shipped text missing from lines.csv, so flow cannot change the label alone.
Apply together (one commit):
- `pipeline/story/lines.csv` row 89: `ui-title-director-s-cut,label,Director's Cut,,yes,...` -> text `Start Director's Cut`
  (surface `button`, matching ui-title-start-game). Needs the story critic on that one line.
- `Source/UmbrellaElla/Private/Flow/FlowMenuText.cpp`: `DirectorsCutLabel()` returns `TEXT("Start Director's Cut")`.
- `Source/UmbrellaElla/Private/Tests/Flow/FlowRulesTest.cpp` (StartAndPauseDesignRetained): expect `"Start Director's Cut"`.
- clause-proof.csv: `FLOW-34,"second button label is 'Director's Cut', GDD says 'Start Director's Cut'",test:UmbrellaElla.Flow.StartAndPauseDesignRetained`; clause-audit tag -> proven.
Verified on this branch before backing it out: the test passes with the new label and fails with the old one.
