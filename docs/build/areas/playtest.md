# Automated playtest measurements. Branch area/playtest. Read docs/build/worker-rules.md first.
Josh: no human playtests. Measure CAM-04, CAM-07, FLOW-25, FLOW-28 (docs/build/rule-status.csv: QA-36 camera and
readability measurements) and HAZ-16 (the Broken Mill human acceptance run) with automated play: drive Ella through the
smoke hook / a scripted run in the packaged or editor game, log the measured values in the run log, and check them
against the GDD rows with a script and tests. Wait for "Merge area/smoke" in git log main (check every few minutes,
max 60 min), then merge main. Record each measurement and its evidence in your status file (playtest-status.md next to this brief).
Lane: Source/UmbrellaElla/{Public,Private}/Smoke/** (after smoke merges), Private/Tests/Smoke/**, tools/build/playtest*.py.
