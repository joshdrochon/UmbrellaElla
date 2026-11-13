## levelchunks status
Done (branch area/levelchunks, build exit 0, Level/Field/Arena tests PASS, module_check and manifest_check 0 problems):
- HAZ-25..HAZ-36, HAZ-38, HAZ-39: `ChunkLayouts`, `ChunkCatalogueData`, `LevelPlan`; tests `UmbrellaElla.Level.ChunkLayoutsMatchCatalogue` and the other ChunkLayoutTests.
- WIND-03: `UmbrellaElla.Field.World.CurrentTargetsEllaAndMovesHer`.
- CORE-06: `tests/test_levelchunks_core06.py` (package.sh writes asset_manifest=).
Fix after 3935a34: a `-Wshadow` break between `LevelCatalogue.cpp` and `ChunkLayouts.cpp` (`M` alias) is renamed; the build now passes.
Review fixes: retry keeps `max(1, GetCheckpointReached())`; seeds 1001-1003 now run the generator (the fixture short-circuit and
`HasFixtureRoute` are gone; the GDD routes stay illustrative and only seed the fallback layout); `UmbrellaElla.Level.SeedFixtures1001To1003`
now checks each seed's generated route (valid, not fallback, deterministic, authored layouts and bypass valid, retry differs).
PlaytestRun `MeasureFlow28` already counts threats after `StepFollow(KeeperHandoffX(), 1)` (merged from main); no Playtest/smoke run by me.
`EnemySizeFraction` renamed `CheckpointStandFraction`.
Left: nothing in this lane. The `Hazard` folder has no tests of its own.
