# artvideo status

Earlier work: assetgen video mode, video_to_strip.py, Ella idle mp4 (1 of 2 paid calls, $0.60), 8 and 12 frame strips
(d95423dd), docs method in art-image-model.md. No second paid call made.

## Ella idle 24-frame strip (Josh: Ella strips are 24 frames)
Shipped for the lead to record Josh's owner approval (pipeline/art/approvals.json not touched).
- Path: `pipeline/art/proof/artvideo/ella-idle/Ella_idle_N24_strip.png`
- sha256: `be885f4d3427762e32cfb4cdf2d6926ae6c46f100c7260a65919e49dccf8e224`
- Size: 11544 x 654, 24 cells of 481 x 654, pivot bottom-centre, fps 6.13 (24 of the 47-frame loop at 12 fps).
- Beside it: `Ella_idle_N24_strip.sprite.json`, `Ella_idle_N24.frames.json`, `Ella_idle_N24_NN.png` (24), `Ella_idle_N24_preview.gif` (paper = scene/paper/paper_r1_c.png, and dark).
- Made from the same 48 keyed frames as N8/N12: `video_to_strip.py --counts 24 --fps 12 --keyed .../keyed` (new `--keyed` option, test added). No re-keying, same crop by construction.

Numbers (Ella_idle.report.json from the run; same registered frames as N12):
- jitter after registration: max anchor step 0.83 px, max drift from first 0.70 px, max height step 4.43 %, height range 19.65 % (reported, not hidden).
- loop: last-to-first 19.77, mean step 43.36, ratio 0.46, loops=true.

Checks run: `sprite_check.py --kind silhouette --grid 481x654 --frames 24 <strip>`: every frame line fill ~0.355, fringe 0, halo 0, border 0 (only tail read; no FAIL line); same on N12. `python3 -m unittest tests.test_video_to_strip`: 4 OK.
Not run:
- art_inventory / art_slots: both FAIL on this branch for reasons outside the strip (T_Ella_Idle_PH has no art-loop piece mapping; ui:clock-face has no slot rule, other lanes' unmerged work).
- In-game slot load (import_art_candidate.py, ella-state:idle): not run. It writes T_Ella_Idle_PH.uasset under Content (other lane), and the single-row strip is 11544 px wide, past 8192. Decision for Josh: lean a 6x4 grid sheet (2886 x 2616) for import; QA/integrator runs the in-engine load.
- Blind panel (art_loop.py) on the 24 strip not run.
- The Ella_idle.report.json in the repo still describes N8/N12; the 24 run's report was not copied over it.

## After merging origin/main (8490c5dd)
- Conflicts in docs/build/art-image-model.md and tools/assetgen.py resolved keeping both sides (video + batch commands, video-from-animation section + shared layers).
- Re-run with main's new jitter check in sprite_check.py: `sprite_check.py --kind silhouette --grid 481x654 --frames 24 Ella_idle_N24_strip.png` = PASS (24 frames, fringe 0, halo 0, border 0; no jitter FAIL). It took 9m40s wall on the loaded machine.
- `python3 -m unittest tests.test_video_to_strip`: OK. Strip sha256 unchanged: be885f4d3427762e32cfb4cdf2d6926ae6c46f100c7260a65919e49dccf8e224.

## Ella idle 24 frames as a 6x4 grid sheet (lead: yes, ship the grid; the strip is past 8192 px)
For the lead to record Josh's owner approval (pipeline/art/approvals.json not touched).
- Path: `pipeline/art/proof/artvideo/ella-idle/Ella_idle_N24_grid.png`
- sha256: `b128aec4bbb9505626d218302568e065173fa3e0b539104fb9cafd8bfc80e4b5`
- 2886 x 2616, 6 cols x 4 rows of 481 x 654, same 24 cells as the strip; sidecar `Ella_idle_N24_grid.sprite.json`
  (silhouette, frames 24, grid 481x654, fps 6.13, loop, pivot bottom-centre). Made with `video_to_strip.py --grid-cols 6` (test added).
- `sprite_check.py --kind silhouette --grid 481x654 --frames 24 <grid>`: PASS, 24 frames, fringe 0, halo 0, border 0, no jitter or pivot FAIL (6m12s wall).
- Merged origin/main (worker-rules only change). Cherry-picked artfx 27f5db0a (T_Ella_Idle_PH -> ella-state:Idle) so art_inventory maps it.
- Slot load (`import_art_candidate.py <grid> ella-state:Idle`): started in the editor; the machine is loaded, see below for the result.
  It writes artella's T_Ella_Idle_PH.uasset, which I do not commit.
