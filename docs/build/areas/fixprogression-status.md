
## Boss-retry rollback follow-up
Done (FLOW-07, FLOW-08, FLOW-11, FLOW-13, FLOW-06): a run-start rank commit (context RunStart) re-stamps the run-start
checkpoint, so a boss retry or quit keeps the run-2 reallocation. `ModeSelected` drops an unfinished run to its checkpoint
before a new one begins. `EncounterCompleted` counts only Detail `success`. `IsFinalHourRun` checks the FLOW-06 flag.
Tests: `UmbrellaElla.Progression.World.RunStartReallocationSurvivesBossRetry`, `...RestartAfterQuitDropsUncheckpointedXp`,
`...OnlyAWonRunAdvancesScaling`. build exit 0; Progression tests PASS 28/0; module_check 0.
Left: Persist() writes per kill (jam-ok); hard references to BrokenMillRoom/UmbrellaEnemy for kill labels; purchase widget wiring (Flow).
