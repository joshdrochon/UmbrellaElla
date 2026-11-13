## levelchunks status
Done (branch area/levelchunks, build exit 0, Level/Field/Arena tests PASS, module_check and manifest_check 0 problems):
- HAZ-25..HAZ-36, HAZ-38, HAZ-39: `ChunkLayouts`, `ChunkCatalogueData`, `LevelPlan`; tests `UmbrellaElla.Level.ChunkLayoutsMatchCatalogue` and the other ChunkLayoutTests.
- WIND-03: `UmbrellaElla.Field.World.CurrentTargetsEllaAndMovesHer`.
- CORE-06: `tests/test_levelchunks_core06.py` (package.sh writes asset_manifest=).
Fix after 3935a34: a `-Wshadow` break between `LevelCatalogue.cpp` and `ChunkLayouts.cpp` (`M` alias) is renamed; the build now passes.
Left: nothing in this lane. Two Core/Playtest changes wait for the build lead in `docs/build/requests/levelchunks.md`.
`Hazard` has no tests under its own prefix (no tests to run for it).
Not mine, left uncommitted: `tools/ue/smoke.sh`, `tools/ue_run.py` (outside lane).
