# Rule ID status (audit re-run on main at 7a4d354, after the Dev Lead review)

Source of truth: `rule-status.csv` (id, area, status, evidence, note, owner). The `owner` column is an addition to the
brief's schema: the brief (docs/build/areas/*.md) that covers the remaining work, `ORPHAN` when none does, empty when built.
Judged from code, tests and the area status files on main; no Unreal build or test was run in this audit. Every cited
test name exists in `Private/Tests`. Main moved from fd1bbdd to 7a4d354 with no `Source/` change, so statuses stand
except the review fixes below.

## Counts (previous audit in brackets)

- **built: 133** (142)
- **partial: 66** (57) - WIND-03, OWL-14, FLOW-25, HAZ-06, HAZ-07, HAZ-08, HAZ-09, HAZ-10, HAZ-11, HAZ-12, HAZ-13, HAZ-14, HAZ-15, HAZ-18, CAM-04, CAM-07, HAZ-25, HAZ-26, HAZ-27, HAZ-28, HAZ-29, HAZ-30, HAZ-31, HAZ-32, HAZ-33, HAZ-34, HAZ-35, HAZ-36, HAZ-38, HAZ-39, FLOW-28, NAR-04, NAR-05, NAR-06, NAR-07, FLOW-48, FLOW-49, FLOW-44, FLOW-45, ART-05, ART-06, ART-07, ANIM-02, ANIM-03, ANIM-04, ANIM-05, ANIM-06, ANIM-07, ANIM-08, ART-08, ART-09, ANIM-09, ART-10, BG-02, BG-03, BG-04, BG-05, BG-06, VFX-02, VFX-03, VFX-04, VFX-05, VFX-07, VFX-08, VFX-10, CORE-06
- **not built: 3** (3) - HAZ-16, ANIM-10, VFX-11
- **blocked: 2** (2) - FLOW-26, FLOW-39

## What changed since the last audit (Dev Lead review, one round)
- HAZ-02..05: dropped the false "Mill wind volumes not spawned" note; `BrokenMillRoom.cpp` spawns both bands. Still built.
- HAZ-06/07 built -> partial: the bands spawn, but the WIND-03 TargetId bug means they cannot move Ella in play.
- HAZ-08..13 built -> partial: only the estimate arithmetic is tested; the GDD rows ask for measured bends, transients and motion.
- VFX-10 built -> partial: target devices and frame-time/memory/overdraw budgets are OPEN and nothing is profiled on
  hardware. Reduced flash is wired (`Settings.World.ReducedFlashReachesVfx`); the old "not wired" note was stale.
- Owner column now points at the briefs on main (levelchunks, enemies2, storyflow, settings2, artfx, artenemy, artui,
  the six snd* lanes, imagegen). 36 of the 37 former ORPHAN IDs have a brief.

## Owner of the remaining work

- levelchunks: WIND-03, HAZ-06, HAZ-07, HAZ-25, HAZ-26, HAZ-27, HAZ-28, HAZ-29, HAZ-30, HAZ-31, HAZ-32, HAZ-33, HAZ-34, HAZ-35, HAZ-36, HAZ-38, HAZ-39, CORE-06
- enemies2: HAZ-14, HAZ-15
- storyflow: NAR-04, NAR-07, FLOW-49; artfx + storyflow: NAR-05 (artfx builds the light shaft/umbra visual, storyflow wires its trigger)
- settings2: FLOW-44, FLOW-45, VFX-10
- artfx: VFX-02, VFX-03, VFX-05, VFX-07, VFX-08, VFX-11
- artenemy: ART-07, ANIM-02, ANIM-04, ANIM-08, ANIM-10, ART-10
- playtest: FLOW-25, HAZ-16, CAM-04, CAM-07, FLOW-28
- artella: ART-05, ANIM-03
- artkeeper: NAR-06, ANIM-06, ANIM-07
- artscene: ART-06, BG-03, BG-04, BG-05, BG-06; artscene + imagegen: BG-02 (imagegen builds the pre-jam input guard)
- artshots: OWL-14, HAZ-18, ANIM-05, VFX-04
- artui: FLOW-48, ART-08, ART-09
- audio + sndhit, sndlaunch, sndstate, sndtele, sndui, sndworld: ANIM-09
- Josh: FLOW-39
- artcal: none directly; its wind calibration fix unblocks artshots wind-zone/wind-lines (HAZ-18, BG-06).

## ORPHAN (no brief on main covers it)

- FLOW-26: GDD row says the design is authored, not implemented; nothing to build until the GDD changes
- HAZ-08..13: estimates checked as arithmetic only; GDD asks to measure actual bends, transients and motion; not measured. New this round. Closest brief: playtest (it already drives the Broken Mill run for
  HAZ-16), but its brief does not name these rows.

## Partly covered (owner named, but part of the rule is in no brief)
- ANIM-03 (artella: 4 static states, not the animation set), ANIM-05 (artshots: wand-shot, not four weapon families),
  NAR-06 (artkeeper owl piece must show the one-hand clock and shaft clue),
  FLOW-28 (playtest measures it; health carry across route checkpoints is in no brief),
  VFX-10 (settings2 covers reduced motion; target-device profiling and budgets are in no brief),
  HAZ-06/07 (levelchunks fixes WIND-03; no test yet drives Ella through the Mill bands with the real current).
- CAM-07: playtest can measure catch flow only once levelchunks spawns currents on the route.
