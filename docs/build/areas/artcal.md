# Check defect: wind art calibration. Branch area/artcal. Read docs/build/worker-rules.md first.
Triage verdict (build lead): check defect. `python3 tools/art_judge.py calibrate` measures wind-zone with team=0 images
(detail_min None) and wind-lines with team=1 (no leave-one-out possible), yet pipeline/art/references.json holds
detail_min 0.421 (wind-zone) and 0.408 (wind-lines), above the detail of their own references (artshots measured 0.099
for wind-zone's only reference). A reference cannot pass its own element, so no wind piece can ever pass.
Fix the calibration, not the bar: (1) measure each wind reference's own detail and score with tools/art_judge.py element
on the reference image itself; (2) for an element with fewer than 2 team images, set score_min/detail_min from its
references (lowest reference minus the same 0.02 margin calibrate uses) in tools/art_judge.py calibrate, so --write
produces it; (3) a test in tests/ that a reference always passes its own element after calibrate, and a known-bad
render (tools/make_art_calibration.py) still fails; (4) run calibrate --write and commit the new numbers.
Lane: tools/art_judge.py, pipeline/art/references.json (calibration fields only), tests/test_art_judge*.py. Done: tests OK,
the reference passes its own element, known-bad fails.
