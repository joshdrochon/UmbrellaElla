# Area: scalecheck

Started by the build lead from this brief (2026-11-13). It is the definition of done.

Lead (auto): your tip 1cd3eb0d failed the pre-check, so it was not queued. Output: PRECHECK FAIL sha=1cd3eb0d64650576b4bcaaa048ce7616d0d067ba FAIL art_inventory: file:Art/Source/StandIns/ella-hurt/ella-hurt_N24_grid.png (Art/Source/StandIns/ella-hurt/ella-hurt_N24_grid.png) has no art-loop piece: add one to pipeline/art/references.json and map it in tools/build/art_inventory.py art_inventory: FAIL (TOTAL=110 PASSED=10 artella=10 artkeeper=10 artscene=16 artui=25 artshots=10 artfx=27 artenemy=12)   art_inventory: new FAIL art_inventory: file:Art/Source/StandIns/ella-hurt/ella-hurt_N24_grid.png (Art/Source/StandIns/ella-hurt/ella-hurt_N24_grid.png) has no art-loop piece: add one to pipeline/art/references.json and map it in tools/build/art_inventory.py . Fix, rerun PRECHECK_FAST=1 bash tools/build/lane_precheck.sh scalecheck --bg until PASS, commit.
