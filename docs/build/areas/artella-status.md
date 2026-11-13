# artella status (Nov 12)

## State: no piece passes the bar. All four stay tracked `_PH` placeholders.
- Rendered with Blender 5.2.1 through `tools/assetgen.py blender --character ella` (anims Open, Attack, Close, Fall;
  IdleFloat not rendered) into `Art/Source/Ella/Raw/Ella_<Anim>_PH/` (4 frames each, 432x352). Provenance rows added (16).
- Pieces: ella-up-open (Open), ella-attack (Attack), ella-closed (Close, Fall), ella-shield: no recipe row exists
  in `characters.json` (the canopy-forward shield pose), so it is not rendered.
- Blind panel NOT run, no `.artloop.json`, nothing shipped under `Art/` or imported to Content. Reason: the stand-in rig is
  primitives (cone hat, box body, cylinder arm) against the painterly Rehearsal/Ella references and the bar-casters tier.
  Open_00 does not even show an open canopy. Running a critic on it would only record a certain fail.
- `screen_check.py` fails on a lone sprite (it measures a 16:9 gameplay frame, not a sprite), so it was not used as a sprite gate.

## Gap to the bar (what a next round must change in `stand_ins.py` build_ella)
Real silhouette: hat brim bend, long hair and scarf, layered ragged skirt, boots, two-hand grip; umbrella canopy with ribs, scalloped
edge, crown finial and diamond terminal; shading and paper-grain finish near the references. Primitives alone are unlikely to reach
"SAME" against the bar; the critic-sanity test (reference passes itself, known-bad fails) was not run.

## Next
1. Add an `ella-shield` row in characters.json (lane allows `tools/build/assets/art_ella*.py`, but characters.json is shared pipeline: request in docs/build/requests/artella.md if the lead wants it).
2. Rebuild build_ella with sculpted detail, re-render, then `art_loop.py blind/panel/verdict` per piece.


## Round log (Nov 12, afternoon)
All four pieces share one rig (`build_ella` in `pipeline/art/blender/stand_ins.py`, lead-directed edit; only that function and two new Ella-only materials changed).
| Round | Change | art_ref_check | Panel (ours vs ref / vs bar-casters) | Critic gap |
|---|---|---|---|---|
| 1 | tiered ragged skirt, hair, torn scarf, bent hat, 16-gore ribbed canopy, boots | 0.2 (min 0.398) | ref wins 3/3, bar wins/same | flat vector fill, no etched line or paper grain, grounded |
| 2 | same + lighter cloth ramp | 0.2 | ref wins 3/3, bar mostly wins | same gap |
| 3 | grain 0.38 on cloth, lighter ramp, 0.2 rad airborne lean | 0.2 | ref wins, bar wins | same gap (flat cartoon, thick uniform outlines, no grain) |
Deterministic: screen_check PASS, art_check sprite colour rules PASS, art_ref_check FAIL (0.2, no movement over 3 rounds).
Critic sanity: reasons are the same every round and match the references and GDD; the calibration folders (known SAME / known winner) were answered correctly in the 6 sessions I read; it picks the reference every time. No defect found, so the bar stands.
Also missing for any pass: the `context` pair needs an in-engine capture after import (not possible until a piece passes).

## State: STUCK (3 flat rounds, same gap, art_ref_check score not moving). All four pieces stay tracked `_PH`.
Nothing shipped under `Art/`, no `.artloop.json`, no Content import. ella-attack, ella-closed, ella-shield not paneled: same rig, same gap, a certain fail.
NEEDS HUMAN: Josh, Blender primitives with toon shading cannot reach painted-sculpt references (Rehearsal Ella, bar-casters). Choices: (a) hand-sculpted / imported model (needs a provenance-clean source), (b) an image-generation path for Ella frames (rule BG-02/ART-03 says references are not generation inputs), (c) accept `_PH` for the jam build.
Lean: (c) now, (b) only if rules allow it.
