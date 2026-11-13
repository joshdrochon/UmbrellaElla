# Rule ID status (audit re-run on main at merge of fd1bbdd)

Source of truth: `rule-status.csv` (id, area, status, evidence, note, owner). Judged from code, tests and the area status
files on main; no Unreal build or test was run in this audit. Every cited test name exists in `Private/Tests`.

## Counts (previous audit in brackets)

- **built: 142** (137)
- **partial: 57** (49) - WIND-03, OWL-14, FLOW-25, HAZ-14, HAZ-15, HAZ-18, CAM-04, CAM-07, HAZ-25, HAZ-26, HAZ-27, HAZ-28, HAZ-29, HAZ-30, HAZ-31, HAZ-32, HAZ-33, HAZ-34, HAZ-35, HAZ-36, HAZ-38, HAZ-39, FLOW-28, NAR-04, NAR-05, NAR-06, NAR-07, FLOW-48, FLOW-49, FLOW-44, FLOW-45, ART-05, ART-06, ART-07, ANIM-02, ANIM-03, ANIM-04, ANIM-05, ANIM-06, ANIM-07, ANIM-08, ART-08, ART-09, ANIM-09, ART-10, BG-02, BG-03, BG-04, BG-05, BG-06, VFX-02, VFX-03, VFX-04, VFX-05, VFX-07, VFX-08, CORE-06
- **not built: 3** (7) - HAZ-16, ANIM-10, VFX-11
- **blocked: 2** (11) - FLOW-26, FLOW-39

## What changed since the last audit
- Now built: COM-06 (burst), COM-07 (beam actor), CAM-08 (camera follow called in play), NAR-02, NAR-03, NAR-08 (story on main).
- Regressed: WIND-03 built -> partial. `AWindCurrent` sends the pawn's actor name as TargetId; the Motor accepts only `Ella`,
  so no current moves Ella in play. Fix is written in `docs/build/requests/enemies.md`, not applied. HAZ-14/15 tests work around it.
- Story on main but not wired into Flow: NAR-04, NAR-07, FLOW-49 partial (skip press not routed, two ending/credits timelines, Journey Complete buttons unbound).
- Was blocked, now partial/not built: art IDs (Josh's option A ended the wait; art loops are running, no piece has passed yet) and HAZ-16 (automated playtest replaces the human run).
- Still blocked: FLOW-26 (GDD says authored, not implemented), FLOW-39 (credit names for Josh).

## Owner of the remaining work (running workers: artcal artella artkeeper artscene artshots artui audio playtest)

- playtest: FLOW-25, HAZ-16, CAM-04, CAM-07, FLOW-28
- artella: ART-05, ANIM-03
- artkeeper: NAR-06, ANIM-06, ANIM-07
- artscene: ART-06, BG-02, BG-03, BG-04, BG-05, BG-06
- artshots: OWL-14, HAZ-18, ANIM-05, VFX-04
- artui: FLOW-48, ART-08, ART-09
- audio: ANIM-09
- Josh: FLOW-39
- artcal: none directly; its wind calibration fix unblocks artshots wind-zone/wind-lines (HAZ-18, BG-06).

## ORPHAN (no running worker's brief covers it), grouped by the area that should own it

### arena (17): route chunks, wind bug, build record
- WIND-03: regressed from built: AWindCurrent sets TargetId to the pawn actor name, Motor accepts only Ella, so no current moves Ella in play (requests/enemies.md, not applied)
- FLOW-26: GDD row says the design is authored, not implemented; nothing to build until the GDD changes
- HAZ-25: route spawns generic floor/column/trap/enemy cubes per variant; no wind currents and no chunk-specific layout (bridges, shelves, passages)
- HAZ-26: route spawns generic floor/column/trap/enemy cubes per variant; no wind currents and no chunk-specific layout (bridges, shelves, passages)
- HAZ-27: route spawns generic floor/column/trap/enemy cubes per variant; no wind currents and no chunk-specific layout (bridges, shelves, passages)
- HAZ-28: route spawns generic floor/column/trap/enemy cubes per variant; no wind currents and no chunk-specific layout (bridges, shelves, passages)
- HAZ-29: route spawns generic floor/column/trap/enemy cubes per variant; no wind currents and no chunk-specific layout (bridges, shelves, passages)
- HAZ-30: route spawns generic floor/column/trap/enemy cubes per variant; no wind currents and no chunk-specific layout (bridges, shelves, passages)
- HAZ-31: route spawns generic floor/column/trap/enemy cubes per variant; no wind currents and no chunk-specific layout (bridges, shelves, passages)
- HAZ-32: route spawns generic floor/column/trap/enemy cubes per variant; no wind currents and no chunk-specific layout (bridges, shelves, passages)
- HAZ-33: route spawns generic floor/column/trap/enemy cubes per variant; no wind currents and no chunk-specific layout (bridges, shelves, passages)
- HAZ-34: route spawns generic floor/column/trap/enemy cubes per variant; no wind currents and no chunk-specific layout (bridges, shelves, passages)
- HAZ-35: route spawns generic floor/column/trap/enemy cubes per variant; no wind currents and no chunk-specific layout (bridges, shelves, passages)
- HAZ-36: route spawns generic floor/column/trap/enemy cubes per variant; no wind currents and no chunk-specific layout (bridges, shelves, passages)
- HAZ-38: bBypass flag only; no bypass geometry or test that reads a bypass path
- HAZ-39: seed 1001 fallback matches the GDD fixture; 1002/1003 proposals not checked
- CORE-06: Revision and AssetManifest fields read; packaging does not write asset_manifest= to BUILD_INFO (requests/level.md 2)

### enemies (2): Broken Mill with real wind
- HAZ-14: real Ella and Motor now; test broadcasts wind with TargetId=Ella to dodge the WIND-03 TargetId bug, so real wind is unproven
- HAZ-15: free-rise miss case and rescue envelope at minimum lift not tested; same wind TargetId workaround

### settings (2): menu contents, accessibility reads
- FLOW-44: candidate option names only; contents OPEN in GDD
- FLOW-45: reduced flash now wired; text scale and reduced motion not read by HUD or Flow screens (requests/settings.md 6)

### story (4): Flow wiring of the story subsystem
- NAR-04: Flow never calls IsSkipPressForStory/HandleSkipPressed, so the start press is not consumed and skip is not routed (requests/story.md 3)
- NAR-05: caption stand-in; the light shaft and umbra visual is not built
- NAR-07: Flow and Story run two separate ending/credits timelines; ShowDirectorsCutEnding never called (requests/story.md 2, 7)
- FLOW-49: Journey Complete shows after Story's own timed credits, not Flow's; Try Again / Main Menu buttons not bound (requests/story.md 2)

### visuals (12): art/VFX families no art brief names
- ART-07: camera-scale review and target resolutions/aspect not in any art brief
- ANIM-02: stand-ins only; family contract (roots, sockets, transitions, missing-asset fallback) in no brief
- ANIM-04: collision stays fixed; health-condition art states (100..0) in no brief
- ANIM-08: stand-ins; enemy human art in no brief (artshots covers wind fields only)
- ANIM-10: no family has gone through source-export-import-reimport-camera review; art loop covers import, not reimport/game-camera review
- ART-10: stand-ins; no enemy art brief
- VFX-02: effect specs; no Unreal VFX assets; no VFX brief
- VFX-03: sphere stand-ins; four-weapon VFX in no brief (artshots wand-shot only)
- VFX-05: sphere stand-ins; Keeper VFX in no brief
- VFX-07: point-light stand-in, no lit material
- VFX-08: point-light stand-in; lit material policy not resolved
- VFX-11: was blocked; acceptance needs real VFX; nothing to accept yet

## Partly covered (owner named, but part of the rule is in no brief)
- ANIM-03 (artella: 4 static states, not the animation set), ANIM-05 (artshots: wand-shot, not four weapon families),
  CAM-07 (playtest can measure only once the route spawns currents: arena, ORPHAN), FLOW-28 (health carry across route checkpoints: health, ORPHAN),
  NAR-06 (artkeeper owl piece must show the one-hand clock and shaft clue).
