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

## Round 6 (Nov 12, evening): rerun on main 4ed1d35 (critic-packet fix: transparent renders on one paper ground)
Earlier rounds are invalid evidence; this is the first panel after the fix. Renders: `gp_ella.py` (Grease Pencil drawing),
`Art/Source/Ella/Raw/GP_PH/Ella_{up-open,attack,shield,closed}_GP_PH.png` (600x700). All stay tracked `_PH`.
| Piece | art_ref_check | screen/art_check | Panel (3 sessions per pair) | Critic gap |
|---|---|---|---|---|
| ella-up-open | 0.737 PASS (min 0.398) | PASS | ref wins 2/3, bar wins 2/3 | crude cartoon, blocky shapes, thick uniform outlines, no paper grain or tonal depth, mitten hands |
| ella-attack | 0.2 FAIL (min 0.448) | PASS | ref wins, bar wins | canopy detached from shaft, no two-hand grip, no gold spell, flat angular skirt |
| ella-shield | 0.624 PASS (min 0.586) | PASS | ref wins, bar wins | blocky stacked dress, stiff upright pose, wrong canopy shape, no finish |
| ella-closed | 0.2 FAIL (min 0.749) | PASS | ref wins, bar wins | reads as a grounded figure with a staff, not a closed umbrella; no airborne pose |
No piece passes. `context` pair cannot run until a piece is imported (circular: import only after a pass), so it blocks any pass today; lead should confirm how a first pass can get an in-engine capture.
Critic sanity (run before declaring stuck):
- Reference passes itself: Ella-Rising-02 as "ours" got SAME on all 3 reference-pair sessions and beat the bar image in the bar pair. OK.
- Known-bad fails: our drawings lose to the references in every round; the Roadwarden calibration folders were answered correctly (known winner Y/X, known SAME = SAME) in the sessions read.
- Self-agreement: 3 sessions per pair give the same gap each time; gaps match the references and GDD (airborne, umbrella, etched finish). Calibration scored 3/6 to 7/9, so some calibration sessions are noisy (the panel refused one round on 3/6), but no verdict contradicted the images.
- Side effect: the sanity run logged a "round 4" refused entry for ella-up-open in art-loop.jsonl; ignore it.
No defect found; the bar stands.
Concrete misses I can see in my own images: attack and closed poses are wrong in the drawing (detached canopy, staff instead of folded umbrella, grounded), and the up-open drawing still has flat tiered boxes for the dress. These are fixable drawing errors, but the finish gap (painted sculpt vs scripted strokes) is unlikely to reach SAME in this tool.

## State: STUCK for the same reason as before (finish gap), NEEDS HUMAN unchanged. Nothing shipped, no `.artloop.json`, no Content import.
Choices for Josh: (a) provenance-clean sculpted/painted source, (b) image-generation path if rules allow, (c) keep `_PH` for the jam build.
Lean: (c).

## Round 7 (Nov 13): Gemini rollout, blocked on the key
Done: merged main; four prompts written and reviewed by a fresh Sonnet session (Art/Source/Ella/Paint/prompt.md,
prompt-review.md, assembled prompts.json, `paint.py <piece> <round>` makes one paid call). Review applied word for word
(apricot-cream outline #FFE6C4, mid-tone cloth against dark_share, hair/hat/scarf traits, SHIELD and closed poses fixed).
Ours, fixed with no spend: off_band. `tools/build/assets/art_ella_post.py` recolours the outer 4 px band to #FFF3D6;
R3 idle strip off_band 0.0855 -> 0.0092 (max 0.01). dark_share (0.52) is still above 0.45: this round's prompt targets it.
BLOCKED: GEMINI_API_KEY is not set in this worker's shell (assetgen: "NO KEY"). Worker rules forbid me to read or source
~/.umbrella-ella.env. No paid call was made; spend untouched. Needed: lead exports the key (or keychain item) for this
worker, then run `for n in up-open attack shield closed; do python3 Art/Source/Ella/Paint/paint.py $n R1; done`
(about $0.57), then clean --chroma 00FF00, art_ella_post.py, frames --cells, blind panel.

## Round 8 (Nov 13): R1 Gemini paints judged (merged artinventory; references.json 100 entries kept)
R1 paints (4 frames each, `Art/Source/Ella/Paint/R1/frames_<piece>/`), cut and post-processed; spend so far 4.00 USD of 33.82.
| Piece | art_ref_check | art_check (sprite colour rules) | Panel |
|---|---|---|---|
| ella-up-open | 0.722 PASS (min 0.398) | PASS (dark 0.44, off_band 0.008) | reference pair ours, quality-bar pair ours, calibration 6/6; only `context` missing |
| ella-attack | PASS 0.707 (frame 00) | FAIL accent_area 0.094, off_band 0.040, dark 0.466 | not run |
| ella-shield | FAIL 0.561 (min 0.586) | FAIL off_band 0.013, dark 0.53 | not run |
| ella-closed | FAIL 0.715 (min 0.749) | FAIL accent_area 0.112 | not run |
ella-up-open is the first piece to beat the bar. Blocked from shipping only by the `context` pair: it needs an in-engine capture made
after the piece is imported, and the import is gated on a pass (circular). Lead: say whether to import first as a tracked `_PH`-named
asset so the smoke can capture, or relax the order. Next: R2 paints for attack, shield, closed with prompts adjusted to the failing numbers.
