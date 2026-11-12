ID:            UE-000
Title:         Umbrella open/close changes vertical velocity
MVP item:      2
GDD ref:       Core loop: "open = rise, closed = fall" (docs/gdd/GDD-B1.0.md), GDD RULE
GDD revision:  SH1.0
Features:      MOVE-13
Player outcome: the player opens the umbrella and sees Ella rise, closes it and sees her fall
Owner role:    Gameplay Dev
Reviewer role: Dev Lead
Human:         Rick

Inputs:        Source/UmbrellaElla/Public/Umbrella/UmbrellaComponent.h (from card 0.3)
Context:       new files only
Outputs:       Source/UmbrellaElla/Private/Umbrella/UmbrellaRules.cpp, Source/UmbrellaElla/Private/Tests/UmbrellaRulesTest.cpp
File lane:     Source/UmbrellaElla/{Public,Private}/Umbrella/**, Source/UmbrellaElla/Private/Tests/Umbrella*
Do not touch:  Content/UmbrellaElla/Maps/**, Source/UmbrellaElla/Public/Core/**
Out of scope:  no animation states, no wind currents
Used by:       AEllaCharacter (TD lane, follow-up card UE-013)
Needs:         build, tests
Binary locks:  none

Done when:
  - [ ] tools/ue/build.sh exits 0 and the log is attached
  - [ ] UmbrellaElla.Umbrella.OpenRises passes (Z velocity > 0 within 0.5 s of opening)
  - [ ] UmbrellaElla.Umbrella.ClosedFalls passes at DeltaTime 1/30, 1/60, 1/120
  - [ ] UmbrellaElla.Umbrella.ToggleIgnoredWhileStunned passes (negative case)
Evidence:      PR body: build log tail and check_automation_report.py output

Budget:        90 min agent time + 20 min human review
Stop if:       2 failed attempts with the same error → set blocked, write the diagnosis, stop
Cut tier:      MVP
Unknowns:      none
