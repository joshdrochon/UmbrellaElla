# artinventory status

## Done
- `tools/build/art_inventory.py`: lists every shipped visual from the GDD ANIM/ART/BG/VFX/UI rows (STATIC table, rule IDs checked against the manifest) and from the code and art folders (Ella state enum, enemy families x gender, EFlowScreen, backdrop layers, the VFX catalogue sheets, widget classes, every file under Art/ and Content/*/Art). FAILs for a visual no mapping names, a piece not in references.json, a piece with no owner lane, a widget with no piece, an art file with no mapping, and a stale CSV.
- `pipeline/art/references.json`: 58 pieces added (additions only; each carries `owner`): 12 ui-* screens (copied from area/artui so the merge is the same text) + ui-spell-wheel, 5 enemy-* (same ids as area/artenemy), 5 ella, 8 keeper, yellow-shot, stream-beam, 10 bg/world, 26 vfx-* (one per sheet no existing piece judges). Thresholds are inherited from a sibling piece until `art_judge.py calibrate` measures them. `art_judge.py coverage`: PASS.
- `tools/build/quality_gate.py`: `art_inventory` added to BLOCKING (no new FAIL line). Test: `tests/test_art_inventory.py` (15 tests).
- `docs/build/art-inventory.csv`: visual, source, piece, owner, passed (from Saved/Logs/pipeline/art-loop.jsonl of this tree and the sibling worktrees).

## Left / for the lead
- The progress bar script is not in this repo (nothing in tools/ or docs/build computes the 28). It should read `python3 tools/build/art_inventory.py summary` (one line) or the CSV.
- The references.json hash changed, so any art-loop pass on an older hash is stale; re-run the verdict step.
- Merge: area/artui and area/artenemy add the same ui-* / enemy-* keys. Take either side (mine use only references present on main; theirs have richer refs).
- Thresholds on the new pieces are inherited, not measured.

TOTAL=100 PASSED=0 artella=10 artkeeper=9 artscene=15 artui=17 artshots=10 artfx=27 artenemy=12
