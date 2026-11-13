## 1. Per-change verdicts

**1. Idle: mostly done, four fixes.**
- The figure input is gone and the pose comes first. Keep both.
- The draft says the diamond "hangs just below her hands". The shaft is about ⅔ of her height, so with hands under the canopy the terminal sits near her waist. Use: "the shaft runs down past her hands, alongside her body, to the diamond terminal at her waist."
- The draft lacks "no kicking" (ANIM-03). Add "The motion is a slow sway, never a kick."
- The draft puts 4 open umbrellas at 80% canvas height in a 21:9 strip. Each canopy is about 0.5 of the canvas height wide, so the figures nearly fill the strip and the "wide gaps" can't exist. Use 65%.
- I replaced "frame" with "pose". The word invites drawn boxes.

**2. Attack: identity first is done; the length is not.**
- The draft assembles to about 339 words. My corrected version is **295**.
- Cuts, in order:
  - S, 18 words: "thin", "side-view", "no ground, shadow or texture" and the long "no text, boxes, panels or borders" list. "Unbroken" does the work of the box ban.
  - I, 8 words: the eye-glint hex (S already has it) and the dress list, shortened.
  - Attack call, about 12 words: "evenly spaced", the "Copy her…" sentence shortened, the pulse hex.
- Boxes: say "only green between them". Drop the words "frame", "panel", "border".
- Size: add "65% of canvas height". The draft states none.
- Decision, my lean first: drop the figure input from the attack. Round 2 drew her walking in the attack too, which matches the idle failure. The mask also vanished with the input present. To drop it, delete "1 gives her hat, mask and hair; 2, her open umbrella" and mention only the umbrella.

**3. Colour: partly done.**
- The values are right. #FFF3D6 is (255,243,214) and #E9C46A is (233,196,106), both R>G>B.
- "More red than green" is a channel fact the model can't act on. Add a visual anchor: "warm candle-cream, like candlelight, never lemon". It is in the corrected S.
- Round 2's outline #EDE3CF was already warm (R>G>B) and still failed. So the greenish yellow is probably cream anti-aliased into #00FF00 at the edge, not a wrong hue. A prompt can't fully fix that.
- Check a 1–2 px edge erode or despill in the cleanup step.

**4. Finial: good. Keep the sentence.**
- It matches the zoom: a short dark stem on a small collar, ending in one small bead with a tiny point.
- Keep the word "crown" out of every prompt. Round 2 drew a coronet when it appeared.
- I use "finial" alone in the calls.

## 2. Other issues
- Key-art traits added to I:
  - The canopy is nearly as wide as she is tall (~1.2× in the zoom).
  - The scarf is long and streaming.
  - She has a belted waist.
- The pulse sits ahead of the diamond, but ART-06 says spells leave the canopy and ANIM-05 says bright magic is separate VFX. I kept it as drafted. My lean is to drop it from the body strip, which saves about 20 words and removes a gold edge. Your call.
- Small Blasts counterbalance (torso lean, hair flick) is cut for length. Frame 3 reads as "half closed", not "ready", so the loop is imperfect.
- Call 3 now says "Level side view". Call 1 is unchanged except "knob finial" became "finial".

## 3. Corrected text

**S**
```
Style: dark etched storybook engraving for a 2D game sprite: brown-black ink, sepia wash, fine cross-hatching. Near-black silhouette (ink #171614, umber #3A2C25), dark-on-dark interior detail, ragged cloth edges. Thin rim light and a 3 px outline, both warm candle-cream: spark-white #FFF3D6 with touches of gold #E9C46A, always more red than green, never lemon. No glow. Background: one flat pure green #00FF00, edge to edge, unbroken, empty. Nothing on the figure is green. No text.
```

**I**
```
Ella: a slender adult woman, always airborne, in a tall bent pointed witch hat with a wide brim. Long straight dark brown hair falls to mid-back, never short. A dark cloth mask hides her whole face; two small gold eye glints are its only light. A separate long ragged scarf with two tails. Worn layered dark dress with belt, long sleeves, jagged knee-length skirt, stockings, laced boots, gloves; no skin shows. One umbrella, no wand: a shallow dome almost as wide as she is tall, eight broad gores alternating black and taupe, scalloped hem; a long thin dark shaft; a narrow pierced diamond clock-hand terminal at the free end. At the canopy's peak a short dark stem rises from a small collar and ends in one small round bead with a tiny point, barely wider than the shaft. Both gloved hands hold the one shaft.
```

**Call 1 (text only)**
```
A wide 21:9 character turnaround sheet, orthographic, level camera, same distance for every item, every item whole and inside the canvas with green margin above and below. Five separate items in one row, evenly spaced with wide empty green gaps, all the same height, lowest points on one shared invisible line. In the first four Ella floats, slowly sinking, boots hanging with toes pointed down, hair ends, scarf tails and skirt hems drifting up. She holds the closed umbrella upright in front of her chest like a staff, both hands one above the other on the middle of the shaft: the finial points up beside her hat brim, the furled canopy just above her upper hand, the diamond terminal below her lower hand at knee height. Left to right: a front view, both eye glints visible; a three-quarter view turned right; a pure side profile facing right, hair and scarf tails streaming back; a back view, long hair down her back, the shaft visible past one side, finial above her shoulder, diamond below her hip; on the far right the umbrella alone, fully open, seen from the side, shaft vertical and as tall as the figures, finial on top and diamond terminal at the bottom. $S $I
```

**Call 2 (input: open-umbrella crop only)**
```
Ella hangs from her open umbrella in pure side view facing right: arms straight up, both gloved hands stacked on the shaft just under the canopy, her body hanging below like a weight on a string. Her legs dangle loose, boots pointing down, far above any ground; the shaft runs down past her hands, alongside her body, to the diamond terminal at her waist. The open canopy is directly above her head, finial pointing up. One 21:9 strip of 4 poses in a row, level camera, evenly spaced with wide empty green gaps, one figure each, whole umbrella inside, about 65% of the canvas height, same scale, hands and hips at the same height in all four. Pose 1: legs together. Pose 2: boots drift a few degrees apart into a narrow V, skirt and hair sway the other way. Pose 3: the V at its widest, still small and slow. Pose 4: legs together again. The motion is a slow sway, never a kick. The attached image shows only her umbrella, open; copy its design. $S $I
```

**Call 3 (inputs: side-profile crop, open-umbrella crop)**
```
$I Images: 1 gives her hat, mask and hair; 2, her open umbrella. Level side view facing right, she falls slowly, torso upright, boots hanging; the umbrella lies level at her hip, finial behind, diamond pointing right. Three figures in a row, same scale, 65% of canvas height, only green between them. Left: canopy furled. Middle: canopy snapped open behind her; a small gold pulse flies right, clear of her. Right: canopy half closed, air ahead empty. $S
```
Attack assembled count: S 74 + I 145 + call 76 = **295 words**. Hex codes count as words.
