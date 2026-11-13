# artcheckfix status
- Fix 1 done: `art_check.measure_sprite/sprite_failures/effect_style`, CLI `--sprite/--effect`; `art_loop.sprite_checks(effect=)`. Tests: tests/test_art_check_sprite.py.
- Fix 2 done: crude copy as calibration pair (`crude_of`), prompt text, `ask_calibrated` redraw (bounded). Before/after: evals/art-judge/calibration-before-after.md (10/12 -> 12/12). Tests: tests/test_art_loop_checkfix.py.
- Fix 3 done: `locate_piece`, `context_crops`, evals/art-judge/context-crops.json; missing piece = context missing.
- Left: crops only for gold/shot/Ella elements; others use their own reference. Pre-existing failing test: test_art_loop Evidence.test_pass_lines (piece list grew).
