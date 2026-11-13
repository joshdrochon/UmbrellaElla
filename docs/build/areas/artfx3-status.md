# artfx3 status

No piece has reached the bar. `python3 tools/build/art_pass_verify.py` reports 0 verified passes. Every piece is still a tracked placeholder.

Per piece (all eight share the same state): two flash drafts (`draft1`, `draft2`), cut with `cut_strip.py` into `sheet1`, `sheet2`, `sheet3`, `sheet5` (`sheet4` for StreamStart only). Current candidate: `sheet5` (8-frame v2 draft, palette grade + ink edge).

| Piece | Folder | Round | Best sheet |
|---|---|---|---|
| vfx-needle-channel | NeedleChannel | 2 | sheet5 |
| vfx-needle-pierce | NeedlePierce | 2 | sheet5 |
| vfx-needle-sliver | NeedleSliver | 2 | sheet5 |
| vfx-stream-start | StreamStart | 2 | sheet5 |
| vfx-stream-sustain | StreamSustain | 2 | sheet5 |
| vfx-part-break | PartBreak | 2 | sheet5 |
| vfx-part-hit | PartHit | 2 | sheet5 |
| vfx-stun | Stun | 2 | sheet5 |

Open gaps (critic records in `pipeline/art/critic/vfx-*.json`):
- `art_ref_check` fails on the sheets (checked on vfx-stun); art_check and screen_check pass.
- No in-engine context capture yet (waits on the screenfix smoke shot).
- PartBreak frame 3 fragments still need a check at 1K.
- Provenance rows for derived files record the SATCAP ladder, not the exact cap per sheet.

Left: more rounds on the draft model, final candidates on 3-pro-image, context capture, then the blind critic panel.
