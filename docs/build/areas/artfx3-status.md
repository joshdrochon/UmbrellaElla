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

## 2026-11-13: crop references (D-new-vfx-calibration, method from area/artfx2 de5d03cd)
Merged origin/area/artfx2. Cut the effect out of the concept sheets (`pipeline/art/proof/artfx3/make_crops.py`; boxes, source and key in `pipeline/art/reference/crops/<element>/crops.json`; originals untouched). Two crops per element, refs point at them (`point_refs.py`), old sheet refs moved to `context`. Recalibrated with `calibrate_mine.py` (art_judge calibrate, leave-one-out, margin 0.02).
score_min / detail_min: needle-channel 0.573/0.485, needle-pierce 0.656/0.356, needle-sliver 0.807/0.373, stream-start 0.704/0.323, stream-sustain 0.73/0.498, part-break 0.684/0.642, part-hit 0.627/0.644, stun 0.764/0.379.
Triage: a first stun calibration (0.18) let a flat gold block pass (score 0.2): check defect (sparse keyed arcs fail the style gate). Fixed with arc crops that keep 14 px of the clock around them. A flat render now fails on every element. Stream-sustain crops that were byte copies of other crops were dropped by load_spec; replaced with distinct ones.
Re-judge of sheet5 (whole 8-frame strip): all fail (0.43-0.53, stun 0.36). Per frame (128 px cells, `art_judge element <id> <frames>`): needle-pierce frame 6 and part-hit frame 0 pass the numeric bar; the rest are 0.04-0.2 below (best: stream-sustain 0.69/0.73, stun 0.69/0.76, needle-channel 0.50/0.57). Note the painted needle sliver is a metal shard; the crop is the gold bolt, so it will not reach 0.81 without a gold-bolt redraw.
No pass record yet: needs new candidates (draft, then final on 3-pro-image) aimed at the crops, the blind panel, and the in-engine context capture.
Environment: 27 Source/ files that were modified at session start show as deleted in this worktree; not touched by this lane.

## 2026-11-13 (later): triage and block
Merged main and origin/area/artslots (ArtSlotTests.cpp conflict: took artslots' version, not my lane).
Triage, stun: ours (prompt). The painted stun is a gold star-and-gear ring; GDD OWL-30 says 1.2 s electrical stun and both crops are blue-white arcs over clock brass. That is why stun scores 0.36 to 0.69 against a 0.76 bar. Fix prepared: `pipeline/art/proof/artfx3/Stun/prompt3.md` (forked ivory/pale-blue arcs plus brass shards) and `cut_strip.py` with `NOGRADE=1` (keeps the painted hue; the default grade pulls everything toward gold). Needle-sliver has the same kind of mismatch (painted metal shard, crop is a gold bolt).
Blocked: paid calls refused (`NO CONTEXT SHOT`, screenfix's -SmokeShotFrames not on main). Written in docs/build/requests/artfx3.md. Shared spend counter: $28.41 of $33.82 used, so about $5.4 is left for every lane.
Next once unblocked: stun arcs draft (flash), cut with NOGRADE=1, per-frame art_judge, then final on 3-pro-image, then context capture and the panel.

## 2026-11-13 (recheck)
Still blocked: origin/main has no SmokeShotFrames in Source/ (area/screenfix not merged). No paid call made. Request in docs/build/requests/artfx3.md stands.

## 2026-11-13 (recheck 2)
Still blocked: origin/main (80aacfd8) has no SmokeShotFrames in Source/. No paid call made. Request in docs/build/requests/artfx3.md stands.

## 2026-11-13 (recheck 3)
Still blocked: origin/main (80aacfd8) has no SmokeShotFrames in Source/. No paid call made. Request in docs/build/requests/artfx3.md stands.

## 2026-11-13 (recheck 4)
Still blocked: origin/main (80aacfd8) has no SmokeShotFrames in Source/; it exists only on origin/area/screenfix. No paid call made. Request in docs/build/requests/artfx3.md stands.

## 2026-11-13 (recheck 5)
Still blocked: origin/main (80aacfd8) has no SmokeShotFrames in Source/; screenfix not merged. No paid call made. Request in docs/build/requests/artfx3.md stands.
