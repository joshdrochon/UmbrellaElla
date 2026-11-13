# Director's Cut level, playable (audit partials). Branch area/level. Read docs/build/worker-rules.md first.
docs/build/rule-status.csv (area/audit, merging): HAZ-24..41 chunks are data only, "no placeable level actors or
geometry"; CAM-04/07/08, FLOW-25/28 are rule functions only; CORE-06 revision/asset-manifest fields not wired.
Build: (1) a level director that spawns the nine-chunk Director's Cut route from the chunk catalogue data (FLOW-24,
HAZ-24, HAZ-37) as placeholder geometry actors from engine primitives, seeded placement (FLOW-46 colours belong to
enemies), refuges and checkpoints (FLOW-27, FLOW-28) and the Keeper handoff at the end; (2) the scrolling camera
follows it (CAM-04..08); (3) traps/enemies are placed through the enemies area's public spawn functions (read
Enemy/, Trap/, BrokenMill/ public headers; do not edit them; request missing ones in docs/build/requests/level.md);
(4) CORE-06: BuildIdentity revision and asset-manifest fields from BUILD_INFO/UMBRELLAELLA_BUILD_COMMIT. World tests:
the route spawns 9 chunks in order with a fixed seed, Ella can be placed at each checkpoint, camera follows.
Lane: Level/**, Arena/**, Hazard/**, Feedback/Build/**, Content/UmbrellaElla/Maps/**, Tests/Level/**, Tests/Arena/**.
Done: worker-rules DoD.
