# Keeper paint R1: prompt review (fresh reviewer, before any paid call)

Checked: prompt.md against docs/build/art-image-model.md (review section), GDD OWL-08, ART-06, ANIM-06, "Keeper identity master", art-bible.md, style.json. Reference crop viewed only to describe in words.

VERDICT: changes needed before the call. One blocker (layout), the rest are fixes.

## What the reference crop shows (words only)
Left-facing bronze owl, wide wings swept up and back, layered long overlapping plates with rivets and an angular elbow spar. Head: heavy brow, hooked beak, round bright eye. Large chest clock with Roman numerals and hands, ringed by gears. Two bird legs with talons. Three chained pieces: a cage lantern far left, an armillary under the clock, a small gear ring at the rear. The wing plates read as feathers; that is the main drift risk.

## Blocker
1. **Layout contradiction.** A 21:9 canvas split into 4 cells gives each cell about 0.58 wide : 1 tall. This owl (body, chains, wings) is wider than tall, about 1.4 : 1, and 70% of canvas height makes it about 9 units wide in a 5.25 cell. Four owls cannot fit; Gemini will crop, overlap or shrink them. Fix: a 2x2 grid in 16:9 (cell 1.78 : 1, owl fits at about 80% of cell height). If a single row is required, the owl must be about 35% of canvas height (about 300 px at 2K), which is too small to paint well. Decision for Josh; the final prompt below uses 2x2, the row variant is at the end.

## Missing traits (GDD / reference)
2. Each mechanism has its OWN small dull eye on its underside and its OWN independent chain; chains do not start at wings, neck or feet (Keeper identity master). Prompt says "own chains" only.
3. "Mysterious, not monstrous" tone is absent.
4. Clock: "one stable physical long hand and a pivot"; the reference has two hands, so say one hand, no short hand.
5. Wing plates read as feathers to the model. Describe them as straight-edged tapered metal vane plates with slots and rivets, in overlapping rows. "No feathers" is a negative and Gemini often ignores it.
6. Two wings in pure side view: say near wing and far wing both show, the far one slightly offset and darker.
7. Attachment of wings: shoulder roots and spars to the torso (GDD "connected shoulder roots/spars").
8. Mechanism positions use "front/middle/rear" with no left/right anchor. Owl faces left, so front = left (beak side), rear = right (tail side). Say it.
9. Palette hexes missing for the body: use style.json owl-umber #3A2C25, owl-feather #5C473E, silhouette #1D1713, ink #171614, and a bronze highlight. Gold #E9C46A and cream #FFF3D6 are correct. The amber eye #FFC76A is for the exposed-eye state only; keep eye dull here (OK as written).
10. Smoke (ART-06) is a separate layer in the GDD row; state "air around the owl is clear, no smoke" so it does not appear.

## Contradictions and risks
11. Poses 2 and 4 are both "level and spread", so they will look identical in side view and a level wing is foreshortened. Give each a direction: pose 2 (downstroke) wing tips a little above level, pose 4 (upstroke) tips trailing a little below level, wings bent at the elbow.
12. "Heavy dark outer contour" vs the keying method (2-3 px light outline). Keep both: dark ink contour, then a thin cream rim just inside it. Already half there; name the order.
13. "Paper tooth" on the owl is fine; the background must stay flat (method doc: grain off the key). Prompt does say flat green; keep it, and say the paper tooth is on the owl only.
14. "Nothing on the owl is green" is a negative. Add a positive: bronze is warm brown, no verdigris or patina. Bronze is the usual cause of green leak.
15. "No text, no shadow on the ground" are negatives; rewrite as positives (clear background, owl floats).
16. "Pose first" rule: prompt opens with the subject, then poses, which is acceptable, but the identity of the attached image and what to copy should be stated first so the model reads it as image 1.
17. Scale lock "same size and place" is good; also fix the baseline: body centre on the same horizontal line in every cell.

## Corrected final prompt (word for word)
```
Use the attached image only as the design reference for the owl's body, clock, legs, tail and the three hanging mechanisms; copy its shapes and materials, not its wing pose. Paint a new picture of the Keeper of Time, a large crownless mechanical owl, mysterious rather than monstrous, hovering and flapping slowly.

The picture is a 2x2 grid of four equal cells, read left to right, top row then bottom row, each cell holding one whole owl. Every owl is in pure side view facing left, level camera, the same scale, filling about 80% of its cell height, with its body centre on the same spot in every cell and wide empty space around it. Body, head, clock, legs, tail and the three hanging mechanisms keep the same size and place in all four; only the wings move. Both wings show: the near wing in front, the far wing just behind and slightly darker.
Cell 1: both wings raised high above the back, tips pointing up.
Cell 2: wings on the downstroke, spread back, tips a little above level.
Cell 3: wings swept low below the body, tips pointing down.
Cell 4: wings on the upstroke, tips trailing a little below level, bent at the elbow.

The owl: a compact round torso centred on an aged clock face with Roman numerals, glass and exactly one long hand on a pivot. A small angular owl head with a heavy brow, a short hooked beak and one dull, muted glass eye. Two very broad wings built from straight-edged, tapered, perforated and ridged metal vane plates in overlapping rows, fixed with rivets, joined to the torso by bevelled shoulder spars and hinges. Two short mechanical legs ending in exactly two clawed feet, hanging in the air with no ground. A plated tail. Below the body hang exactly three separate mechanisms, each on its own independent thin chain, each with one small dull eye on its underside: at the front, on the beak side at the left, a small armillary sphere with a solid rim and crossing hoops; in the middle, a ribbed cage cylinder; at the rear, on the tail side at the right, a toothed gear ring. All three are different shapes and none touches the wings, neck or feet.

Style: a dark etched storybook engraving for a 2D game sprite. Brown-black ink line #171614 with a heavy dark outer contour, sepia wash, fine cross-hatching and visible paper tooth on the owl only. Metal in quiet dark iron, steel and dull bronze, a warm brown bronze with no patina, in the tones #3A2C25, #5C473E and #1D1713, with warm ivory highlights and dark-on-dark interior detail. Just inside the contour runs a thin rim light in warm candle-cream #FFF3D6 (leaning red-orange, never lemon or lime). Only the clock face glows, a soft gold #E9C46A. Every colour on the owl is a warm brown, gold or cream.

Background: one flat, perfectly even, pure green #00FF00 filling the whole picture edge to edge, clear of any marks, texture, gradient, smoke, text or shadow, with the owls floating freely on it.
```
Settings: model gemini-3-pro-image-preview, aspect_ratio 16:9, image_size 2K, attached image = Owl_Flap_00.png only.

## Variant if the single row is kept (21:9)
Replace the layout paragraph with: "The picture is one row of four equal cells, left to right, each holding one whole owl, side view facing left, the same scale, each owl about 35% of the canvas height and 80% of its cell width, centred in its cell on one shared horizontal line, with empty space between cells." Expect a small owl; round 2 would need a crop or a bigger canvas.

## Open question for Josh (not decided here)
GDD says each mechanism has its own underside eye and a chain "to the head's top eye". The prompt keeps chains independent and eyes on the mechanisms, and leaves the head-top route to the attached render. If the render does not show it, someone must say where the chains end.
