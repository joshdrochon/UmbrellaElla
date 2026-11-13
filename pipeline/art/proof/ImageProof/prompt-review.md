# Ella prompts: round 2 review

## 1. Traits missing or wrong

**Wrong or missing in S and I:**

| Trait | Key art / refs / round 1 | Current text | Fix |
|---|---|---|---|
| Canopy stripes | Key art and `umbrella.png` show about 8 broad alternating black and muted taupe gores radiating from the crown. The scalloped hem has pointed tips. Round 1 drew a smooth canopy with a thin double ring at the hem. | "thin light ivory stripes" | Broad alternating gores, scalloped hem |
| Ribs | Rib tips show at the hem on the pose sheets. | Not mentioned (the art bible lists ribs) | Eight slender ribs with small tips |
| Finial | Small, separate, sits above the canopy. Round 1 drew a plain spike. | "tiny metal crown… wider than the shaft" | Keep it. Add "dark bronze coronet with a collar" and a thin ivory rim highlight. It must be legible at 2K, and "metal stays dark" can hide it. |
| Collar / runner | The GDD Small Blasts row needs a collar to slide. | Not mentioned | Add a sliding collar on the shaft |
| Scarf | Round 1 shows no scarf in any view. The key art and pose sheets show it streaming back like a flag. | "trails from her neck" | A separate piece of cloth with two ragged tails, apart from hair and dress |
| Hair | Round 1 drew a bob in front, three-quarter and back views. | Length stated, but only "falls past shoulders" | Add anatomy anchors: two long locks forward over the shoulders in the front view, streaming back in profile, to mid-back |
| Hands and skin | The pose sheets show pale skin, but they are pose-only. Round 1 attack frames show pale hands. | "hands stay dark" | Dark gloves, no skin visible. This also meets the GDD's concealed natural features. |
| Costume detail | Sash at the waist, high collar, long sleeves, skirt below the knee, laced low-heel boots. | Partly present | Add them. They also cover the GDD "no sexualized exposure" line. |
| Hat | Wide brim, soft crown, band, bent a third of the way up. | "tall bent pointed" | Add brim and band |
| Lighting | Art bible: unlit, one light from the front and slightly above, no baked glow (ANIM-05). | Absent | Add to S |
| Ink and paper | Etched linework, ragged cloth edges, readable at 80–100 px (asset spec). | Etched hatching only | Add "bold shapes readable at about 90 px" and INK `#171614`. Say the paper grain is not on the sprite. |
| Proportions | Slender adult, hat adds about a head. | Only "adult, slim" | Add "about seven and a half heads tall". Give canopy width (about ¾ of her height) and shaft length (about ⅔). |
| Eye glints | One glint is visible in profile. | "two" | State per view |

**Round-1 problems the prompts do not yet cover:**
- **Idle:** the figure sat low in the canvas and the crown nearly touched the top edge.
- **Attack:** she reclined on a diagonal, although the prompt said "upright".
- **Attack:** the shaft sat at chest height, not at the hip.
- **Attack:** a second furled canopy appeared in front of the hands.
- **Attack:** the pulse became a crescent, and it showed in one frame only.

## 2. Art bible and GDD conflicts

- **S and ANIM-05.** S says "no glow", but the pulse and eye glints emit light. Scope the ban to the background and to baked body glow. Make the pulse crisp-edged with no halo, so it cannot spill onto the green key.
- **Idle frame count.** `style.json` anims says idle-float has 4–6 frames, and `sprite_check.py` enforces it. Call 2 asks for 3. ANIM-03's together → V → together fits in 4 frames.
- **Idle frame 3.** "Canopy a little higher" breaks the ANIM-02 stable root and the same-hips rule. Hold hips and hands at one height and only sway the hair and cloth.
- **"Her left" (GDD shared identity row).** Facing right, the viewer sees her right side, so "on her left" is ambiguous in an image prompt. Say "at the left of the image, behind her".
- **ANIM-03 "no kicking".** Call 2 has no explicit no-kick wording. Add "a few degrees, no kick".
- **Small Blasts body.**
  - Call 3 says "one hand sliding" but never names the collar.
  - Add the torso/arm/leg counterbalance and the hair, scarf and skirt follow-through.
  - Frame 3 should read as "recovered", so it loops to frame 1.
- **Pulse in the sprite.** ANIM-05 says bright magic is separate VFX, but the Small Blasts body row lists the pulse. The prompt keeps it as a separate object clear of the body, so it can be keyed off.
- **Umbrella stripes.** D-new-umbrella-look says "black with light stripes, as in the key art". The key art's stripes are broad, so "thin" contradicts it.
- **ART-03.** Using in-jam crops as inputs is allowed. The crop must show long hair and the right umbrella, because an image outweighs text. If it shows a bob, regenerate call 1 before calls 2 and 3.

## 3. Gemini practice

- **Style block.** It reads as a keyword and negation list. I rewrote it as prose with positive descriptions, and kept only the short, load-bearing negatives for the keyed background.
- **Camera.** Add "orthographic, level, same distance, whole body in frame, 21:9, margins". The aspect ratio is also set in the API call.
- **Layout.** Add "each frame holds only its own single figure, and the gaps are empty green". This is the positive form of the ghost-head fix.
- **Geometry.** Pin down which end of the umbrella is which, and where the furled canopy sits, with no "her left".
- **Reference wording.** Say what to take (identity, costume, umbrella design). Say what not to take (pose, scale, framing, the closed vertical hold). Say the umbrella is open in this image, because the figure crop shows it closed. Without that, the model has no source for the open-canopy details except text.
- **Order.** Images first in the request, then pose, framing, reference clause, S, I. This is kept. Total length is about 450–550 words, which is fine.

## 4. Do the prompts fix round 1?

| Problem | Verdict |
|---|---|
| Bob hair | **Partly.** The reference crop and stronger anatomy wording should fix it, but an image beats text. Check the call-1 crop first. |
| Plain spike finial | **No.** The text was already there in round 1. It needs the coronet shape, bronze rim and size. |
| Cane hold | **Partly.** "Vertical in front" may still read as a cane. The new wording: hands one above the other on the middle of the shaft, crown beside the hat brim, a held staff, not planted. |
| Back view dropped the umbrella | **Weak.** "Show above and below" is vague. Fixed by placing the shaft visibly past one side. |
| Idle became a walk | **Yes.** The overhead hang, hanging legs and 4 frames fix it. |
| Ghost heads | **Yes.** The single crop plus "empty green gaps" should fix it. |
| Attack posture, hip height, double canopy | **No.** These are fixed in the new text. |

## Decisions for you

- **Idle frame count.** I lean 4, because `sprite_check` enforces 4–6. The alternative is keeping 3.
- **Second reference.** I lean toward attaching the call-1 item 5 crop (open umbrella alone) as a second image, because it is the only source of the canopy design. The alternative is a single figure image. Calls 2 and 3 below assume two images. If you keep one, delete the sentence marked **[2 images]**.
- **Pulse in the attack strip.** I lean keep, drawn as a separate object, because the GDD body row lists it. The alternative is dropping it and handing the whole pulse to VFX (ANIM-05).

---

# Revised text

## S (identical in all three calls)

```
Style: a dark painterly etched storybook illustration for a 2D side-view game sprite, drawn like an old engraving in brown-black ink with a thin sepia wash and fine etched cross-hatching in the shadows. The figure is a near-black silhouette that reads by shape alone: charcoal, soot and umber darks, the darkest tone ink #171614, with interior detail dark on dark. Subdued bronze and warm ivory appear only as thin rim light on edges and small highlights on metal. Cloth edges are ragged, torn into jagged points. Shapes are bold and simple enough to read when the figure is shown only about 90 pixels tall. The light is soft, even and unlit-looking, from the front and slightly above; the figure casts no shadow and no part of the body glows, apart from the gold elements named below. A clean warm ivory #EDE3CF outline, about 3 px at 2K, follows the outer edge of the whole figure and of every separate piece. The background is one perfectly flat, uniform pure green #00FF00 filling the canvas edge to edge, identical everywhere and completely empty: no ground, no shadow, no gradient, no grain or paper texture, no glow or light spill. Every part of the figure is charcoal, umber, bronze, ivory or gold; nothing in it or reflected on it is green. The image is wordless: no text, labels, numbers, grid lines, frames or watermark.
```

## I (identical in all three calls)

```
Ella is an adult woman of slender build, about seven and a half heads tall, always airborne and never touching the ground. On her head is a wide-brimmed, tall pointed witch hat of soft dark cloth with a band, bent a third of the way up so its tip folds over backwards. Her hair is dark brown, a shade lighter than her clothes, long and straight: it falls from under the brim past her shoulders to the middle of her back with loose strands lifting in the air, and from the front two long locks hang forward over her shoulders to her chest. It is never short and never a bob. Her whole face, from brim to chin, is hidden under a dark cloth or mesh mask; two small separate gold #E9C46A glints, one per eye (only the near eye in profile), are the only light on her. A long ragged scarf, a separate piece of cloth clearly apart from the hair and the dress, wraps her neck and trails two ragged tails behind her. She wears a fully covering, layered, worn dark dress: long sleeves, high collar, a wide sash at the waist, and a skirt of several ragged jagged-edged layers ending below the knee, over opaque dark stockings and laced ankle boots with low heels, and dark gloves, so no skin shows. She carries one slender umbrella and no wand. Opened, its canopy is a shallow dome about three quarters as wide as she is tall, with a scalloped hem and eight gores of alternating broad black and muted warm taupe bands radiating from the top, over eight slender dark metal ribs whose small pointed tips show at the hem. At the very top of the canopy sits a small pointed crown finial: a tiny dark bronze coronet of three to five upward points on a small collar, clearly wider than the shaft, with a thin ivory highlight on its points. A long thin straight dark shaft runs down from it, with a small sliding collar on it. At the free end of the shaft hangs a separate narrow pierced diamond (lozenge) clock-hand terminal of dark bronze. From crown to terminal the umbrella is about two thirds of her height; closed, the canopy furls into a slim bundle. Both of her gloved hands grip the one shaft. Her body, hands, cloth and metal stay dark.
```

## Call 1: canonical turnaround (text only)

```
A wide 21:9 character turnaround sheet, drawn orthographically with a level camera straight on, at the same distance for every item, each whole figure fully inside the frame with generous green margin above and below. Five separate items stand in one row, evenly spaced with wide empty green gaps between them, all the same height and scale, their lowest points aligned on one shared invisible line. In the first four items Ella hovers in the air, slowly sinking, her boots hanging with the toes pointed down well clear of any surface, and her hair ends, scarf tails and skirt hems drifting gently upward. She carries her closed umbrella upright in front of her chest, both gloved hands one above the other on the middle of the shaft, like a staff held out in front of her and planted on nothing: the crown finial points up beside her hat brim, the slim furled canopy rests just above her upper hand, and the diamond terminal hangs below her lower hand at about knee height. The items, left to right: first, a front view, her two long locks of hair hanging over her shoulders and both eye glints visible; second, a three-quarter view turned toward the right; third, a pure side profile facing right, her long hair and the two scarf tails streaming back behind her; fourth, a back view, her long dark hair covering her back down to the middle of it, the shaft of the closed umbrella still held in both hands and visible past one side of her body, its crown finial above her shoulder and its diamond terminal below her hip; fifth, on the far right, the same umbrella alone, fully open, seen from the side with the shaft vertical and as tall as the figures, the broad black and taupe gores, the scalloped hem, the rib tips and the crown finial at the top all clearly legible, and the diamond terminal at the bottom. $S $I
```

## Call 2: idle, UP_OPEN overhead rise (reference: figure crop, plus umbrella crop)

```
Ella hangs in a slow hover beneath her open umbrella, seen in pure side view facing right. Both of her arms are stretched straight up above her head and both gloved hands grip the one shaft just below the canopy, so her whole body hangs from the umbrella like a weight from a string. The open canopy sits directly above her head with its crown finial pointing straight up at the top; the shaft passes between her hands and ends just below them in the diamond terminal. Her legs hang straight down, relaxed and limp, the boots dangling with the toes pointed down, high above any surface. Layout: one horizontal strip on a 21:9 canvas holding 4 frames of this hover, in one row, evenly spaced with wide empty flat green gaps, each frame containing only its own single figure with her whole umbrella inside the frame, the crown finial well clear of the top edge and the boots well clear of the bottom edge, the figure filling about 80% of the canvas height. The camera is level and at the same distance in every frame; scale, line weight, and the heights of the hips and hands are identical in every frame. Frame 1: legs together, hanging straight. Frame 2: the boots swing a few degrees apart into a narrow V, one slightly forward and one slightly back, the skirt and hair swaying gently the other way. Frame 3: the V at its widest, still small and slow, with no kick. Frame 4: the legs swing back together, almost as in frame 1. [2 images] The two attached images are reference only for her identity: the first shows Ella in side profile, the second shows her umbrella open. Copy her face covering, hat, hair length and colour, scarf, dress, boots and the umbrella design. Do not copy the first image's pose, scale, framing or closed upright umbrella hold; here the umbrella is open overhead and the layout is the one described above. $S $I
```

## Call 3: Small Blasts, ATTACK_DESCENT (same references)

```
Ella is slowly falling, her torso upright and vertical with the hips directly below the shoulders, facing right, seen in pure side view. She holds her umbrella horizontally and low at her hip, level with her belt, both gloved hands on the one shaft, elbows bent and tucked against her sides, forearms horizontal. The crown finial is the rear tip of the umbrella at the far left of the image, behind her; the shaft points straight forward to the right, and the diamond clock-hand terminal is the free front tip at the far right. Her legs hang down with the knees slightly bent and the boots dangling, toes down, high above any surface; her hair, scarf tails and skirt hems drift gently upward. Layout: one horizontal strip on a 21:9 canvas holding 3 frames, in one row, each frame centred in its own third of the canvas with a margin of flat green at each side, each frame containing only its own single figure with the whole umbrella inside the frame, the gaps between frames empty. The camera is level and at the same distance in every frame; scale and line weight are identical in every frame, and her hips stay at the same spot in all three. Frame 1, ready: the canopy is furled into a slim bundle on the rear third of the shaft, behind her. Frame 2, fire: the canopy has snapped open behind her, flaring like a bowl with its crown point on the shaft at the far left and its scalloped rim facing right, ending a hand's width behind her back; her torso leans back a little, her front arm pushes the shaft forward, her legs swing slightly forward in counterbalance, and the hair, scarf tails and skirt flick backward; one small separate gold #E9C46A magic pulse, a crisp-edged round bead with a short tapered tail trailing behind it and no halo, travels to the right just ahead of the diamond terminal and well clear of her body. Frame 3, recover: the canopy is half closed and folding back toward the shaft, her rear hand slides the collar along the shaft while the front hand holds the shaft still, her torso and legs settling back toward frame 1, and the air ahead of the diamond terminal is empty green. The gold pulse is the only bright thing in the strip. [2 images] The two attached images are reference only for her identity: the first shows Ella in side profile, the second shows her umbrella open. Copy her face covering, hat, hair length and colour, scarf, dress, boots and the umbrella design. Do not copy the first image's pose, scale, framing or closed upright umbrella hold; the pose and the layout are the ones described above. $S $I
```
