# Ella proof, round 3 prompts (applied after prompt-review.md; D-new-art-image-model)

Model: gemini-3-pro-image-preview, aspect 21:9, image size 2K, three calls: sheet, idle, attack.
Round 2 -> 3 changes (lead's list, Nov 13):
1. Idle: no figure input. Text plus the open-umbrella crop (from the round 3 sheet) only. The pose comes first.
2. Attack: identity block before the frame list, short frame text, whole prompt under about 300 words. If the strip
   comes back in drawn boxes, cut it by thirds (inset past the box lines) before `frames`.
3. Colour: art_check's bands already hold the canon colours (artcal triage); round 2's rim light came out greenish
   yellow (R = G). The rim light and outline are named by art-bible values: spark-white `#FFF3D6` and gold `#E9C46A`
   (style.json palette), "more red than green". Round 2's `#EDE3CF` outline is not an art-bible value; dropped.
4. Finial: one concrete sentence, as the key art draws it (key art x~255 y~345: a short dark stem on a small collar at
   the canopy peak, ending in a small knob with a tiny point; barely wider than the shaft). GDD ART-06 says "two
   ornaments", the art bible says "crown finial"; the key art's drawing is a knob, not a coronet. The lead chose the
   key art's drawing.
To fit 300 words on the attack call, S and I are rewritten short; the same short S and I go in all three calls.

Review (prompt-review.md, a fresh Sonnet session in an empty /tmp folder, Bash/Edit/Write disallowed) applied: its
corrected S, I and calls are used word for word (attack assembled: 295 words; "crown" dropped from every prompt, the
finial is a bead on a stem; "frame" replaced by "pose"/"figure"; figure size 65%). Its leans NOT taken:
- Drop the side-profile input from the attack call too: not taken. The lead's list drops the figure input on idle only;
  keeping it on attack tests one change (identity first) instead of two.
- Drop the gold pulse from the attack strip: not taken (round 2 kept it per GDD Small Blasts body; separate object).
Its colour note (round 2's #EDE3CF was already warm, so the greenish pixels may be cream anti-aliased into the green
edge) is checked after the calls by where the off-band pixels sit.

## Style block S (same words in every call)

Style: dark etched storybook engraving for a 2D game sprite: brown-black ink, sepia wash, fine cross-hatching. Near-black silhouette (ink #171614, umber #3A2C25), dark-on-dark interior detail, ragged cloth edges. Thin rim light and a 3 px outline, both warm candle-cream: spark-white #FFF3D6 with touches of gold #E9C46A, always more red than green, never lemon. No glow. Background: one flat pure green #00FF00, edge to edge, unbroken, empty. Nothing on the figure is green. No text.

## Identity block I (same words in every call)

Ella: a slender adult woman, always airborne, in a tall bent pointed witch hat with a wide brim. Long straight dark brown hair falls to mid-back, never short. A dark cloth mask hides her whole face; two small gold eye glints are its only light. A separate long ragged scarf with two tails. Worn layered dark dress with belt, long sleeves, jagged knee-length skirt, stockings, laced boots, gloves; no skin shows. One umbrella, no wand: a shallow dome almost as wide as she is tall, eight broad gores alternating black and taupe, scalloped hem; a long thin dark shaft; a narrow pierced diamond clock-hand terminal at the free end. At the canopy's peak a short dark stem rises from a small collar and ends in one small round bead with a tiny point, barely wider than the shaft. Both gloved hands hold the one shaft.

## Call 1: canonical turnaround (text only)

A wide 21:9 character turnaround sheet, orthographic, level camera, same distance for every item, every item whole and inside the canvas with green margin above and below. Five separate items in one row, evenly spaced with wide empty green gaps, all the same height, lowest points on one shared invisible line. In the first four Ella floats, slowly sinking, boots hanging with toes pointed down, hair ends, scarf tails and skirt hems drifting up. She holds the closed umbrella upright in front of her chest like a staff, both hands one above the other on the middle of the shaft: the finial points up beside her hat brim, the furled canopy just above her upper hand, the diamond terminal below her lower hand at knee height. Left to right: a front view, both eye glints visible; a three-quarter view turned right; a pure side profile facing right, hair and scarf tails streaming back; a back view, long hair down her back, the shaft visible past one side, finial above her shoulder, diamond below her hip; on the far right the umbrella alone, fully open, seen from the side, shaft vertical and as tall as the figures, finial on top and diamond terminal at the bottom. $S $I

## Call 2: idle, UP_OPEN overhead rise, 4 poses (input: the open-umbrella crop from call 1 only)

Ella hangs from her open umbrella in pure side view facing right: arms straight up, both gloved hands stacked on the shaft just under the canopy, her body hanging below like a weight on a string. Her legs dangle loose, boots pointing down, far above any ground; the shaft runs down past her hands, alongside her body, to the diamond terminal at her waist. The open canopy is directly above her head, finial pointing up. One 21:9 strip of 4 poses in a row, level camera, evenly spaced with wide empty green gaps, one figure each, whole umbrella inside, about 65% of the canvas height, same scale, hands and hips at the same height in all four. Pose 1: legs together. Pose 2: boots drift a few degrees apart into a narrow V, skirt and hair sway the other way. Pose 3: the V at its widest, still small and slow. Pose 4: legs together again. The motion is a slow sway, never a kick. The attached image shows only her umbrella, open; copy its design. $S $I

## Call 3: Small Blasts, ATTACK_DESCENT, 3 poses (inputs: side-profile and open-umbrella crops from call 1)

$I Images: 1 gives her hat, mask and hair; 2, her open umbrella. Level side view facing right, she falls slowly, torso upright, boots hanging; the umbrella lies level at her hip, finial behind, diamond pointing right. Three figures in a row, same scale, 65% of canvas height, only green between them. Left: canopy furled. Middle: canopy snapped open behind her; a small gold pulse flies right, clear of her. Right: canopy half closed, air ahead empty. $S
