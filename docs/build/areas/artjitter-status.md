# artjitter status
Done: tools/frame_register.py (anchor, base-span scale, register, jitter, limits with their source); `assetgen frames`
registers by default (`--no-register`, `--anchor-band`, `--span`), anchor into `<stem>.frames.json` and the sheet sidecar;
sprite_check (loop/anim sheets) and art_loop.sprite_checks (folded into the art_check result) FAIL above 3 px / 2%.
Tests: tests/test_frame_register.py (shaken fails, registered passes, reference loops pass), test_sprite_check passes.
Not run: tests/test_art_loop.py Evidence.test_pass_lines_need_this_commit_and_these_references fails on piece list from the
repo's pass records (not touched by this lane). Left: lanes with their own cut scripts (none found in tools/) need none.
