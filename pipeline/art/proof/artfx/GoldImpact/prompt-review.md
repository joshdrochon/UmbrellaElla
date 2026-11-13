# Prompt review: gold impact burst (VFX_GoldImpact, VFX-02..VFX-11)
ROLE: Art Director | fresh session, prompt review only (docs/build/art-image-model.md, "Prompt review before any paid call")
Reviewed: prompt.md as it stands in the worktree (untracked). No image call made; prompt.md not edited.

Checked against: art-bible (Shots line, Palette, Asset spec, impact VFX 20-24 fps, one assumed light R11), GDD SH1.0 VFX-02..11
and the Small Blasts VFX row ("exact impact appearance beyond this bounded gold family is a prototype candidate, not
previously approved art"), `references.json` element `vfx-gold-impact` (refs `wand-star`, `study-ella-small-blasts`,
`study-ella-twin-stars`, `bar-casters`; the first three viewed, described in words only, never inputs).

What the references show (words only)
- wand-star: a thin tan-gold streak with one four-point sparkle at its leading end: long thin vertical and horizontal
  spikes, tiny pale centre, a few faint dots around it.
- study-ella-small-blasts: the pulse is a glowing gold spark spray at the umbrella tip, many hair-thin radiating streaks and
  tiny sparks around a bright centre. No ink outline; it is light, not a drawn solid.
- study-ella-twin-stars: a four-point gold star, long thin axis spikes, tiny diagonal ticks, bright pale centre, a few
  trailing sparks. Palette strip: ink #171614, bronze #695640, shot gold #E9C46A.

## Missing or wrong traits
1. WRONG: frame 1 and 2 describe an "eight-point star" with long points "on the axes and shorter points between". Sound, but
   frame 1 says only "eight very short sharp points", so the axis/diagonal split the refs show is not set from the start.
   Fixed: four long axis points and four short diagonal points stated up front and held in every frame (the
   TwinStarHead review made the same point: rotation changes nothing, 45 degrees swaps long and short).
2. MISSING: the fine spark streaks and tiny sparks of the Small Blasts study. The prompt has only solid blades; the refs'
   character is hair-thin radiating sparks. Added: a few hair-thin streaks in frame 2.
3. RISK: a 3 px ink outline on "thin blades" will swallow them and turn the burst black. The refs' spikes are hair-thin.
   Fixed: outline about 2 px on the large shapes, a hairline edge on streaks and sparks.
4. MISSING: nothing says no target is drawn. "where a shot hits something" invites a wall, owl or enemy. Fixed: only the
   burst is drawn.
5. WRONG: cell proportions. At 21:9 each of four cells is about 0.58:1, taller than wide (the TwinStarHead review called
   them near square; they are not). "Largest frame about half of its cell" is ambiguous. Fixed: sizes as fractions of cell
   width per frame (about 1/5, 2/5, 1/2, 1/2); the cells stated as taller than wide. Builder choice: keep 21:9 Pro 2K (lean),
   or a 4:1 strip on gemini-3.1-flash-image at lower quality.
6. MISSING: frame size budget. Frame 3 is where the burst is widest and Gemini will overrun a narrow cell; the widths above
   cap it, and frame 4 is faintest so the ring can reach the same extent without the cell edge.
7. CAMERA: "seen directly from the front" reads as a character view. Fixed: a flat, face-on emblem, no perspective or depth.
8. NEGATIVES to positives: "does not rotate", "nothing at the centre", "nothing in the effect is green", "glow stays inside"
   are rewritten as what is there ("the points keep the same angles", "the centre is empty green", "made only of gold,
   amber, bronze, cream and ink"). One short "no text" line stays at the end; Gemini follows it.
9. PALETTE: gold #E9C46A, amber #F5AA28, bronze #94611E, core #FFF5DC, ink #171614 are all art-bible / style.json names; keep.
   Added "every hue lies between amber and cream" so no red, teal, pink or blue sparks appear (art-bible accent rule;
   the burst is the player's magic, not danger).
10. LIGHT: one assumed light (front, slightly above) already present; kept. Glow inside the outline kept (VFX-06/07: light
    and spill are a separate engine layer, not baked); the green stays flat and identical in every cell.
11. GDD: VFX-02..11 and the Small Blasts VFX row make the exact impact a prototype candidate, so this look is unapproved art
    until the panel passes it; record that in the provenance row. Impact plays at 20-24 fps (art-bible), so 4 frames is a short
    burst; fine for a first pass, a hit may need 5-6 later. No gameplay timing or hitbox follows from the art.
12. Style block unchanged from the reviewed TwinStarHead block (same wording) except the outline width: keep it as one block.

## Corrected full prompt block
Model: gemini-3-pro-image-preview, 21:9, 2K, text only, no input image. Output: pipeline/art/proof/artfx/GoldImpact/strip.png
The corrected text is `prompt.final.txt` next to this file (use it verbatim).

## Builder notes
- After the call: four cells, burst centred in each, same point, same angles, no rotation, frame 4 faintest, no non-gold hue,
  green untouched, no target drawn. Then key, `sprite_check.py`, `.sprite.json` sidecar and a provenance row.
- Pivot: Center. Cell size and frame count come from the receiving contract; spill and glow are added in engine.
- Outputs of the first call may be inputs for frame consistency of later calls (art-image-model.md); the key art and refs
  never are.
