# artcal status (wind art calibration check defect)

## Done (12 Nov)
- `tools/art_judge.py calibrate`: an element with no team image (wind-zone: only the quality bar) is now measured on
  its own references (lowest minus the 0.02 margin, `basis: references`); `--write` records it.
- `pipeline/art/references.json` (calibrate --write): wind-zone detail_min 0.421 -> 0.079 (its only reference,
  bar-other-realm, measures 0.099). No other minimum changed.
- Measured on the reference images themselves (`art_judge.py element <id> <reference>`):
  wind-zone bar-other-realm: before FAIL score=0.2, after PASS score=1.0 (detail 0.099).
  wind-lines keyart-wind-lines: PASS score=1.0 before and after (detail 0.428 >= detail_min 0.408; it was not broken).
- Tests: `tests/test_art_judge_calibrate.py` (9 tests): the stale number fails the reference (broken on purpose), after
  calibrate the reference passes, known-bad renders (make_art_calibration crushed, flat fill) fail, every image
  calibrate measured clears its own element in the real repo, both wind references pass through the CLI.
  `python3 -m unittest tests.test_art_judge_calibrate tests.test_art_calibration tests.test_art_judge
  tests.test_art_judge_record tests.test_art_loop` -> OK.

## Decisions taken by default (build lead / Josh to confirm)
1. score_min for an element with a single image (wind-zone, wind-lines, umbrella, paper) stays at its stored value
   (0.582 / 0.5). The brief said to set it from the references too, but a lone reference scores 1.0 against itself, so
   "lowest minus 0.02" would be 0.98 and again nothing but the reference could pass. Two or more references with no
   team image do get a leave-one-out score_min.
2. The reference fallback applies only when an element has no team image (0), not "fewer than 2". With exactly one
   team image the only other references are the quality bar; using them would drop detail_min on ella-up-open
   (0.448 -> 0.212), ella-attack (0.617 -> 0.212) and umbrella-repair (0.364 -> 0.212), which loosens three bars the
   brief did not name.

## Left, not in this brief
- bar-casters (quality bar, whole sheet, detail 0.232) still scores 0.2 as a candidate on ella-up-open, ella-closed,
  ella-attack, ella-shield, owl-bolt, bolt-hit and umbrella-repair: it is below those elements' team detail floors.
  Not changed (see decision 2).
- The wind-zone element is weak: its reference is a whole opaque scene, so hue-shifted, pixelated and flat-white
  variants of it (make_art_calibration B1, B2, B5) still score about 1.0. Only crushed and grey-silhouette fail.
  A keyed crop of the ribbons as the reference would fix that (new reference, outside this lane).

## Affected tests (12 Nov, commit 7ad7ebd)
`python3 tools/affected_tests.py --run` was stopped twice at its time limit with no result (cause: env, machine load
average over 100 from other workers' Unreal builds). The same modules run directly: 935 tests, 18 failures, none in an
art judge or calibration test. Not re-run on the base commit, so "already failing on main" is read from the messages,
not measured:
- tests.test_smoke_visual (14): ue_run exits 2, `tools/ue/smoke-allow.txt:5: D-new-smoke-concurrency is not a row in
  docs/decisions.md`.
- tests.test_provenance.test_repo: provenance rows for files under pipeline/art/reference/discord-crops/.
- tests.test_final9_fixes (workbench-check on UmbrellaElla.Target.cs), tests.test_audio_check.AudioDumpTool
  (home copy differs from staged), tests.test_assetgen.AudioSteps (25 tracked audio placeholders in the repo).
All outside this lane; for the build lead.
