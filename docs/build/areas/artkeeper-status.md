# artkeeper status (piece: owl)
Builder: `tools/build/assets/art_keeper_owl.py` (Blender, side-view crownless metal Keeper: plated body, chest clock, rigid ribbed/perforated vane wings, two legs, armillary + lantern + gear on chains). Job: `Art/Source/Keeper/Raw/Owl_Flap/Owl_Flap.job.json`, render: `blender -b --factory-startup -P tools/build/assets/art_keeper_owl.py -- --job <job>`.

| Round | art_ref_check | Blind panel (reference pair, critic c1) | Gap |
|---|---|---|---|
| 1 | PASS 0.704 | reference wins | flat fills, no etched lines, no paper texture, no riveted vanes |
| 2 | FAIL 0.611 (hatch too dark) then fixed | reference wins (1 sampled), quality bar: ours | same |
| 3 | PASS 0.716 (min 0.698), art_check on_palette 0.988, sprite screen_check flat/grey/outline 0 | reference wins 8 of 8 reference pairs, quality bar (bar-casters pair): ours | flat-filled at the sprite's scale: no etched ink / paper texture, riveted perforated vanes not readable |

Critic sanity: the calibration pairs in every folder behaved (SAME pair -> SAME, known-different pair -> correct winner), so the critic is not defective; the gap is the same each round because our toon render stays flat next to the painted references.

Result: owl does NOT pass the blind panel. It stays the tracked `_PH` placeholder; nothing shipped, no provenance row, no Content import. The new Blender builder and renders are committed under the lane as work in progress.
Stuck rule: critic gap unchanged 3 rounds (deterministic score best 0.716): NEEDS HUMAN: Art Director / Josh. Next step that could move it: a painted-texture pass (hand-authored etching/grain image textures or a compositor hatch layer) rather than more geometry.

## Gemini rollout, round 1 (Nov 13)
- Merged main. Prompt for a 4-pose flap grid written and reviewed by a fresh session: Art/Source/Keeper/Paint/R1/{prompt.md,prompt-review.md,final_prompt.txt}. Review applied: 2x2 grid at 16:9 (a 21:9 row makes the owl too small), one hand on the clock, mechanism eyes and left/right anchors, palette hexes, no-patina bronze.
- Input is our Blender render Owl_Flap_00.png; added provenance rows for Owl_Flap_00-05 so assetgen accepts it as an in-jam input.
- BLOCKED: no paid call made. GEMINI_API_KEY is not set in this shell (tools/keys.py status), and worker rules forbid reading ~/.umbrella-ella.env. Spend so far by us: 0.
- To continue: run from a shell that has the key: python3 tools/assetgen.py image --provider gemini --aspect 16:9 --image-size 2K --input Art/Source/Keeper/Raw/Owl_Flap/Owl_Flap_00.png --out pipeline/art/proof/ImageProof/Keeper_R1/keeper_grid.png --prompt "$(cat Art/Source/Keeper/Paint/R1/final_prompt.txt)"; then cut the 2x2 cells, key green, run art_check/art_ref_check, blind panel.
- Open for Josh: GDD says each mechanism's chain runs to the head's top eye; the prompt leaves that route out.

## Gemini rollout, round 1 result (Nov 13)
- Prompt updated per Josh/lead: GDD wins, each mechanism's chain runs from its underside eye to a second eye on top of the head. Call: gemini-3-pro-image-preview 2K 16:9, cost $0.139, shared spend counter 1.781 of 33.82. Output pipeline/art/proof/ImageProof/Keeper_R1/keeper_grid.png (note: default model gemini-2.5-flash refuses --image-size, pass --model gemini-3-pro-image-preview).
- Look: painted etched/bronze, far closer to the references than the Blender render. Not yet judged by the panel (not cut, not keyed).
- Gaps (ours, prompt): wings read as feathered, not rigid vane plates; cage is see-through (chroma green inside would key out); rear gear hidden behind torso; chains do not all reach a top eye; cell 3 wings cover the mechanisms; black grid lines between cells; owl position drifts between cells.
- Next: round 2 prompt fixes these, then cut, key, art_check/art_ref_check, blind panel.
