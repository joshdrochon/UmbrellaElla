# Requests from flow

## Encounter director state getter (keeper lane)
Main's `UEncounterDirectorSubsystem` (Public/Encounter/EncounterDirectorSubsystem.h) has no state query. Flow's
StartGameReachesFight must assert the director is Active. area/keeper adds `EEncounterState GetState() const`; flow
uses it once 'Merge area/keeper' is on main. Until then the test cannot assert it.
