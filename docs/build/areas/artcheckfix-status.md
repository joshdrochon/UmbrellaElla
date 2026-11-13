# artcheckfix status
- Fix 1 done: `art_check.measure_sprite/sprite_failures/effect_style`, CLI `--sprite/--effect`; `art_loop.sprite_checks(effect=)`. Tests: tests/test_art_check_sprite.py.
- Fix 2 done: crude copy as calibration pair (`crude_of`), prompt text, `ask_calibrated` redraw (bounded). Before/after: evals/art-judge/calibration-before-after.md (10/12 -> 12/12). Tests: tests/test_art_loop_checkfix.py.
- Fix 3 done: `locate_piece`, `context_crops`, evals/art-judge/context-crops.json; missing piece = context missing.
- Left: crops only for gold/shot/Ella elements; others use their own reference. Pre-existing failing test: test_art_loop Evidence.test_pass_lines (piece list grew).
- Review item (enemy "coarse pixel figure"): no code resized, but a 1792x2400 frame went to the critic whole and the viewer shrinks past ~1568 px. `art_loop.fit_packet` now cuts any packet image over `PACKET_MAX` (1568) to the subject's box at full detail (never a resize); `_pair` uses it. Tests: FitPacket in tests/test_art_loop_checkfix.py. test_art_loop and checkfix pass (36 tests). Other four suites not re-run after this change.
