# artvideo status (2026-11-13)

Done, committed:
- assetgen video mode (fal Veo 3.1 Fast, 1 USD cap), tools/build/video_to_strip.py with tests.
- Ella idle trial under pipeline/art/proof/artvideo/ella-idle/: ella-idle.mp4 (paid call 1 of 2, 0.60 USD), keyed frames,
  Ella_idle_N8 and N12 strips, .sprite.json sidecars, GIFs over paper and dark, Ella_idle.report.json (jitter after
  registration: max anchor step 0.83 px, max drift from first 0.7 px; height range 19.65%).
- Method documented in docs/build/art-image-model.md ("Animated pieces from video").

Not done:
- Blind panel verdict. `art_loop.py run --card artvideo --piece ella-up-open --ours .../Ella_idle_N8_strip.png`
  (pid 33895, root Saved/artvideo-root) had not finished and wrote no record. Until it does the strip stays a placeholder
  and does not load through the Ella slot. Re-run it if the process is gone.
- 12-frame strip not yet judged.

Paid calls used: 1 of 2.

Not mine, left uncommitted: edits to tools/build/video_to_strip.py (a `keyed` option) and Ella_idle_N24_* files appeared
in this worktree from another session (artella2 runs video_to_strip.py here). The lead should reconcile them.
