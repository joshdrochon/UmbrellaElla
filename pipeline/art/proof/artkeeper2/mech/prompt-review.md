# Review of prompt.md (fresh session, keeper-mech-front/-middle/-rear)
Checked against GDD SH1.0 OWL-08, OWL-21..25, ANIM-06, "Keeper identity master" row, ART-03/06, art-bible, references keeper-sh10, d-flip-throw, d-toss-kick, d-arc-chain, and keyed_3.png (viewed, described only). study-keeper-character and study-keeper-front-grip: files absent in this worktree (Assets/Art missing, both optional); not viewed.

## Findings
1. WRONG, front: "jointed brass claw-arm with a hinged elbow, claw open". The GDD has the Keeper's own CLOSED claw grip the armillary's outer ring (OWL-21); the head is only the sphere. An arm in the sprite duplicates the body's limb and breaks "no duplicated ring or floating grasp". Removed.
2. WRONG, middle: "visible spring coil" and "curved hinged launching arm". GDD: ribbed cage cylinder (OWL-08). keyed_3 and d-toss-kick/d-arc-chain show a lantern-like cage: cap, ribs, dark gaps, base. The curve is the flight path (OWL-25), not part of the object. Arm removed.
3. WRONG, rear: "second smaller gear meshing" and "striking hammer arm". GDD: rear gear ring only; refs show one spoked cogwheel on a chain (d-flip-throw). Extra gear and hammer removed. Hub and spindle kept (visible in keyed_3).
4. WRONG, all three: "small glass eye at the top". GDD: each chain runs to the head's top eye, i.e. an eyelet ring at the top of the head (the chain attachment), not a glass owl-style eye. keyed_3 shows a small glass eye under each head; the GDD wins, so the prompt asks for a top eyelet ring with the chain going up and nothing under the head. Chain now runs to the frame top edge (cut later), not a stub.
5. Pose first: the draft opens with logistics (one call, one sheet). Now opens with what the objects are and how they hang.
6. Camera: "side view, level camera" was at the very end. Now states orthographic side view, level, centred per third, 16:9, fully inside frame. Gear is face-on (as in the refs), which is stated.
7. Missing visible traits: armillary hoop count and central ball (OWL-08: solid rim, intersecting hoops, central ball); cage proportions (taller than wide, narrowest); gear width (about the armillary); rivets/iron; hanging orientation; distinct silhouettes. Added.
8. Negatives phrased positively: "no feathers, no flesh", "no shadow, no text", "nothing green" rewritten as what is there (rigid metal, floating without cast shadows, all brass/iron/ivory/sepia). "Empty" background kept as positive "filling edge to edge".
9. Palette: added the GDD/references hexes (ink, soot, umber, bronze, taupe) to the style block; kept bronze mid-tone, rim light #FFF3D6 and key #00FF00 (no conflict with brass).
10. Style anchor: "matches the Keeper's body in the supplied image" ties the input image to materials and line (ART-03 allows it: in-jam image, not a reference). Drop that sentence and the input if you want text-only; the prompt still stands on words.
11. Draft header lines (Model, Input image, "One call, one sheet") are metadata, not prompt text; keep them in prompt.md, not in the call.

## Decision for you
Three objects on one sheet vs three calls: one sheet is cheaper and keeps the style the same, but gaps/scale may drift and each object needs cutting. I would keep one sheet for the draft.

## Final prompt
A single concept sheet of three separate hanging mechanism heads belonging to a crownless clockwork owl, the Keeper of Time, drawn as three isolated objects side by side on one flat background, evenly spaced with clear gaps, each hanging straight down from its own short chain, each about 55% of the canvas height including its chain. Straight-on orthographic side view, level camera, no perspective, every object fully inside the frame and centred in its third. 16:9 landscape.

Left, the front mechanism: an armillary sphere. A solid, thick brass outer ring with several thinner brass hoops crossing inside it at different angles, and a small round central ball floating at the crossing point, a clearly open skeletal sphere. At its top, a small round eyelet ring (the top eye) with one short chain running straight up from it to the top edge of the frame.

Middle, the middle mechanism: a ribbed cage cylinder like a small lantern, taller than wide and noticeably narrower than the other two. A rounded cap on top, a stack of horizontal brass ribs separated by dark gaps around a hollow barrel, and a flat base. At its top, a small round eyelet ring (the top eye) with one short chain running straight up to the top edge of the frame.

Right, the rear mechanism: a gear ring. A flat toothed brass cogwheel seen face-on as a round disc, with a ring of evenly spaced teeth, several spokes and a central hub with a short spindle. It is about as wide as the armillary sphere. At its top, a small round eyelet ring (the top eye) with one short chain running straight up to the top edge of the frame.

The three shapes are clearly different silhouettes: open sphere, tall cage, flat toothed wheel. Nothing else is attached to any of them: each is one rigid, fabricated metal object made of aged brass and dull iron with small rivets, and each chain is plain metal links.

Style: a dark etched storybook engraving for a 2D game sprite, in brown-black ink with a sepia wash, fine cross-hatching and visible paper tooth. Quiet palette: ink #171614, soot #292622, umber #463C32, mid-tone bronze #695640, taupe #918173, warm ivory highlights. Bronze stays a mid tone, never near black. A heavy dark outer contour around each object and a thin candle-cream rim light (#FFF3D6) on the lit edges. The look matches the Keeper's body in the supplied image: the same aged brass, engraved line and ink treatment.

Background: one flat, uniform, pure green #00FF00 filling the canvas edge to edge, empty, with the objects floating on it without cast shadows, and no text or labels. Every part of the objects is brass, iron, ivory or sepia; none of it is green.
