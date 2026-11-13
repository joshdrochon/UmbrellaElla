# screenfix status

## Done (commits d87b0e50, bff67883, main merged after)
- Lighting: every placeholder cube, backdrop panel and art slot uses an unlit flat material (`SetFlatUnlit`), plus a fixed-exposure flat post-process on the play camera. No level light needed.
- Draw order: the play camera renders its own view (no auto ortho planes; the frame was centred on world 0,0). Backdrop sits behind gameplay at every camera position.
- Tests: `UmbrellaElla.ScreenFix.*` (gameplay actors in front of every backdrop layer). `tests/test_frame_check.py`.
- Screen check: `tools/frame_check.py` fails on a mostly-black or mostly-flat frame.
- Proof: `pipeline/art/proof/screenfix/mill-after.png` -> `frame_check: PASS black=0.000 flat=0.746`.

## Left
- Nothing. Post-merge: build exit 0, UmbrellaElla.ScreenFix PASS tests=3 failed=0.
