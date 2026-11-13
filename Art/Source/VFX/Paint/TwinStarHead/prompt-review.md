# Prompt review: Twin Stars head strip (VFX-03)
ROLE: Art Director | fresh session, prompt review only (docs/build/art-image-model.md, "Prompt review before any paid call")
Reviewed: prompt.md as committed (de99763e). No image call made; prompt.md not edited.

Checked against: art-bible (Shots line, Palette, Gameplay readability, Asset spec, light layer rule D-new-sh10-vfx-lighting),
GDD SH1.0 COM-08 (Twin Stars), COM-06 (Small Blasts), OWL-14 (shared geometry), VFX-03, VFX-06, VFX-07, the Twin Stars VFX
row of the art list (compact golden #E9C46A four/eight-point star heads, short finite tails), `references.json` element
`wand-shot` (refs `wand-star`, `bar-casters`; both viewed, described in words only, never inputs).

What the references show (words only)
- wand-star: a very thin, horizontal, tapered gold-tan streak that fades to a point on the left, with one small
  four-point sparkle (long vertical and horizontal spikes, tiny pale centre) at its right-hand leading end; a few faint dots
  around it. Travels right.
- bar-casters shared projectile: side view, sharply pointed angular head at the leading end (serrated, spear-like), a
  bright pale core inside a layered coloured shell, a darker shadow edge, then a short geometric tail of broken dashes and
  small squares. Core, shell, trail is the construction; tell, release, travel, fade is the sequence.

## Missing or wrong traits

Shape of the Twin Stars head
1. WRONG: the head is drawn "seen flat from the front" as a lone star. Every shot in this game travels right in side view
   and has a head plus a short tail. The prompt has no tail at all, though the art list says "short finite tails". Needed:
   the star sits at the leading (right) end of a short tapered tail that points left.
2. WRONG: "turned a quarter of the way round". A star with four long and four short points looks identical after a 90 degree
   turn, so frames 2 and 4 would not change; a 45 degree turn swaps long and short points and breaks the silhouette. Animate
   by pulse (core brightness, points length, tail length), not rotation.
3. WRONG/CONTRADICTION: "the same size and line weight in every frame" versus frames 2 and 4 "a little larger". Pick one:
   the star body stays the same size; only the core glow and the point and tail lengths breathe, within the cell.
4. MISSING: the shared geometry (OWL-14, art-bible Shots line): pointed and angular, not round. The star's long points
   should read as the same sharp, serrated, angular family as the shots; the rightward long point is the longest.
5. MISSING: the construction from `vfx_spec`: bright core, shell, trail. Prompt gives core and body but no shell layer and
   no dark shadow edge. Needed: pale core #FFF5DC, gold shell #E9C46A, amber #F5AA28 shading, yellow shadow #94611E edge.
6. MISSING: scale. Compact: head about 28 to 36 px at 1080p in game (asset spec, shared shot size). Cells should show the
   head filling about 45 percent of the cell height with the tail behind it, not a huge ornate star.
7. MISSING: one head per strip is right (COM-08 has two heads from upper and lower rims), but the prompt must say it is a
   single head and that the pair is made in the game, so the image does not draw two stars or a connecting trail.
8. WRONG: "tiny separate gold sparkle dots ... each a small pointed diamond with its own ink outline" will cost chroma-key
   cleanup and read as debris. Keep at most three, small, close to the tail; they are optional decoration, never gameplay.
9. WRONG: "engraved dark-gold hatching on one side of each facet" and "cut gem" push toward a jewel, not a shot. Hatching
   should be light and used only as shell shading on the lower half; the ink outline stays.

Colour
10. WRONG naming: "warm ivory #EDE3CF" is not an art-bible or `style.json` colour. The bible's named pale value is CORE
    #FFF5DC. Use the named palette only: INK #171614 outline, gold #E9C46A, amber #F5AA28, yellow shadow #94611E, core #FFF5DC.
11. MISSING: no other hue. Palette rule: gold/amber family only for the player's magic; no red, teal, green, pink, blue
    or purple in the head, tail or sparkles. Prompt only says "nothing is green".
12. RISK: a pale ivory rim just outside the ink outline can be keyed away along with a green fringe. Keep one clean ink
    outline and no rim; edge separation comes from the flat green.

Light spill and rim colours
13. The prompt is right to forbid glow and spill on the background (VFX-06: light is a separate layer, D-new-sh10-vfx-lighting;
    VFX-07 spill is added in engine, never baked). Keep this, but say it in the positive: the head glows only inside its own
    outline; the core is the brightest point. No halo, bloom, lens flare or soft light outside the ink line.
14. MISSING: the lighting on the shape. Art-bible R11, one assumed light, from the front and slightly above. State it so
    shading is consistent: lit from the front, shade on the lower edge.
15. MISSING: the spill colour for the later overlay layer is gold #E9C46A with core #FFF5DC; no rim colour is painted in
    this image. Note it so the engine layer, not the painting, carries the warm spill on nearby cloth and metal.

Style and format
16. The style block is good (dark painterly etched, paper grain inside shapes, ink outline). Keep it. Add the "one assumed
    light" line and the positive wording of constraints (the review rule: "feet off the ground", not "no walking").
17. "No gradient, no texture, no grain, no vignette" written as a list of nos: restate positively ("one flat, even, uniform
    pure green field"). Keep "No text" once as a short final line, as Gemini follows it.
18. Frames: say left to right, same baseline, tail pointing left, head pointing right. 4 frames in 21:9 (about 5.25:1 each
    cell near square) fits; say "four equal cells".
19. The prompt is mostly keyword-like in the second paragraph; the pose (head right, tail left) must come first, as narration.

## Corrected full prompt block

Model: gemini-3-pro-image-preview, 21:9, 2K, text only, no input image. Output: Art/Source/VFX/Paint/TwinStarHead/strip.png

```
A horizontal strip of four equal cells, left to right, showing four animation frames of one small magic projectile for a
2D side-view game: a compact gold star head flying to the right, trailing a short tapered tail to the left. All four
frames sit on the same horizontal centre line, each centred in its own cell, evenly spaced with wide empty gaps of flat
green between them, so no frame touches another or the edge of the picture. The star head is the same size in all four
frames. The picture is seen directly from the side, at the distance of a game sprite, with the projectile occupying about
a third of its cell.

The head is a sharp, angular eight-point star in the shape of a faceted compass star. Four long points lie on the
horizontal and vertical axes, and four shorter points lie between them. The long point on the right, the direction of
travel, is the longest and sharpest, and the left point flows straight into the tail. Every point is a thin, pointed
blade with straight edges, like a cut spear tip. The tail is short: a tapered gold streak that narrows to a point on the
left, ending in a few broken dashes and two or three tiny pointed diamond sparks. It reaches back about as far as one and
a half star widths and never reaches the neighbouring cell.

The head is built in three layers. At its centre is a small bright core of pale cream #FFF5DC. Around the core is a
shell of warm gold #E9C46A. The lower half of the shell is shaded with a few fine etched hatching lines in amber #F5AA28,
and the lower edge is darkened with deep bronze #94611E. The tail uses the same gold and amber, getting paler and thinner
toward its tip. The only colours in the whole effect are these gold, amber, bronze and cream tones plus the near-black
ink outline, so the star reads as one warm gold family.

Lighting comes from one source, in front of the star and slightly above, so the upper edges are brighter and the lower
edges are shaded. The glow stays inside the star: the core is the brightest point, and the light fades to the ink outline
inside the shape. Outside the outline the picture is only the flat green.

Frame 1: the star at rest, core small, points at their normal length, tail at normal length. Frame 2: the core brighter and
larger, the points a little longer, the tail a little longer. Frame 3: back to frame 1, the core small, the points a
little shorter, the tail a little shorter. Frame 4: the core brighter again, the points and tail at normal length. The
star does not rotate: only the core, point length and tail length change from frame to frame.

Style: a dark painterly etched storybook illustration, ink and wash with fine etched cross-hatching and a faint paper
grain inside the shapes only. Each shape has a clean near-black ink outline #171614 about 3 px wide at this size. The
background is one perfectly flat, even, uniform pure green #00FF00 filling the canvas edge to edge, with the shapes cut
cleanly against it and the green identical in every cell. Nothing in the effect is green. The image contains only the
four projectiles on green: no text, labels, numbers, grid lines, frames or watermark.
```

## Builder notes
- After the call: check the strip for 4 cells, same size, no rotation, no non-gold hue, green untouched, then run the card's
  checks. A PNG needs its `.sprite.json` sidecar and a provenance row before it is used.
- Pivot: Center (shared shot rule). Rotation is by transform, not frames.
- Twin Stars needs two heads from the two canopy anchors 44 units apart (COM-08); the second is the same asset, placed in
  engine. Do not paint two.
