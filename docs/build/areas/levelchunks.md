# Director's Cut route as real chunks. Branch area/levelchunks. Read docs/build/worker-rules.md first. Orphan Rule IDs from the audit (docs/build/rule-status.csv on area/audit, fd2bdd6; notes there say what is missing).
IDs: HAZ-25..HAZ-36 (each chunk variant's own geometry, currents, traps and enemies per the GDD's 12-chunk / 24-variant
catalogue; today every variant spawns the same generic cubes), HAZ-38 (safer bypass geometry with a test that reads it),
HAZ-39 (seed fixtures 1001-1003), WIND-03 (regression: AWindCurrent sets TargetId to the pawn; fix and test), CORE-06
(packaging writes asset_manifest= into BUILD_INFO.txt). Traps and enemies through the enemies area's public spawn functions.
Lane: Level/**, Arena/**, Field/**, Hazard/**, Feedback/Build/**, their tests, the asset_manifest lines of tools/ue/package.sh.
