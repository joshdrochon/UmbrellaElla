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
