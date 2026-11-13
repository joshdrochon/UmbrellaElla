# Prompt review: Ella four states (fresh session, text-only review; references viewed, not used as inputs)

Verdict: A needs edits, B needs edits, C needs edits, D needs edits. Nothing is a blocker; every call is fixable by text. Assembled counts of the draft: A 422, B 342, C 376, D 346 (all over ~320). Corrected below: A 357, B 326, C 335, D 327 (S 62 + I ~125 words shared).

## What the references show that the draft misses
- Hair: wavy and loose, wind-torn into tapering strands (draft says "straight").
- Hat: tip folded over and curling back; brim wide. Draft says only "bent".
- Scarf: pale taupe, the lightest large shape on her, two ragged tails. Draft gives no colour. This is also the cheapest fix for dark_share.
- Jacket: fitted, buttoned, high collar, belt; skirt in stacked tiers with sawtooth hems; knit stockings; ankle boots with small heels. Draft has "worn layered dress", too vague.
- Umbrella: slender ribs, scalloped hem; the draft has this. The key art shows light-and-dark stripes; the Rising ref is uniformly dark. Draft's "black" gores push dark_share.
- Key art: Ella is a tiny black silhouette: hat, streaming hair and scarf, ragged skirt, dangling boots, striped dome. Covered.

## Colour (art_check)
- dark_share counts pixels with L* < 18 only (style.json dark_l_max). #3A2C25 is L*19, #5C473E about 32: they are safe, so mid-tone wording is right. Near-black "alternate gores" and "deep folds" are what put R3 at 0.53-0.60. Corrected S keeps near-black to hairline ink and the hat crown, gores in deep umber and mid taupe.
- Note: the sprite check (silhouette kind) wants L* < 35 share >= 0.6. Mid-tone cloth in L* 19-34 meets both. Do not lighten past that; pale taupe stays on scarf and gloves only.
- off_band: allowed hue 20-95, chroma floor 18. #FFF3D6 is chroma 15 (never counted), #E9C46A hue 87 (in band). The lemon outline is hue ~100-109 (e.g. #EDF585 = 109). "More red than green" is a ratio the model ignores. A colour that is in band by itself works better: #FFE6C4 (apricot-cream) sits at hue ~77, chroma ~20, about 18 degrees clear of the band edge. The post-process recolour to #FFF3D6 stays.
- Negatives to turn positive: "No glow" (now "crisp matte edges", dropped for length), "Nothing on the figure is green" (now "Figure colours: umber, taupe, cream, gold"), "no skin" (now "every inch covered"), "no wand" (now "the umbrella is the only object she holds"), "never short", "never a kick", "nothing like walking or sitting".

## Per call
- A UP_OPEN: pose matches Rising-02 (hands stacked overhead, body hangs, shaft to waist diamond). Fix: positives, hair direction, shorter. 
- B ATTACK_DESCENT: pose matches Shooting-03 except the legs. The ref shows a bent running stride in the air; the draft asks legs hanging straight down on purpose (R3 gave seated legs). Kept as a deliberate deviation; lance at "hip" changed to waist height (ref: level with the waist, in front of the torso). Canopy-furled / open-behind / half-closed matches ref frames 1, 2-5, 6.
- C SHIELD_DESCENT: pose matches Absorbing-04 (seated in air, shaft horizontal, canopy open ahead with finial right and rim toward her, diamond behind left hip). Draft said "dome facing right with hollow side toward her", which is ambiguous; now finial right, rim toward her. Width: a figure plus shield is about as wide as it is tall, so three at 65% fill 1.95 of the 2.33 canvas heights; 60% leaves clear gaps.
- D closed free fall: ref FreeFall-03 is a hunched crouch on a vertical furled umbrella, finial down, diamond up, boots on the collar band, one hand on the hat brim, hair and skirt streaming up and back. Draft's "headfirst-leaning" contradicts the ref (head is up, torso hunched forward) and is the wrong word for the model. Also I describes an open dome; D now says "the same umbrella, furled". D has no umbrella image input, which is correct.

## Corrected paragraphs (replace in prompt.md word for word)

### Style block S
Dark etched storybook engraving for a 2D sprite: brown-black ink, sepia wash, fine cross-hatching. Mid-tone umber and taupe cloth (#3A2C25, #5C473E, #7A6558), pale taupe (#B9A892) on scarf and gloves; near-black only as hairline ink and the hat crown. Thin rim light and 3 px outline in warm apricot-cream (#FFE6C4, touches of gold #E9C46A). Flat pure green #00FF00 background, edge to edge, empty. Figure colours: umber, taupe, cream, gold. Wordless.

### Identity block I
Ella: a slender adult woman, always airborne. Tall pointed witch hat with a wide brim, its tip bent over and curling back. Long wavy dark brown hair streams loose past her waist. A dark cloth mask covers her whole face; two small gold eye glints are its only light. A separate long ragged scarf with two tails. Fitted buttoned dark jacket with belt, long sleeves, layered skirt with sawtooth hems to the knee, knit stockings, laced boots, gloves, every inch covered. The umbrella is the only object she holds: an open shallow dome two-thirds as wide as she is tall, eight gores alternating deep umber and mid taupe, scalloped hem; a long thin dark shaft ending in a narrow pierced diamond; at the peak a short dark stem on a small collar ends in one round bead with a tiny point. Both gloved hands grip the shaft.

### Call A: ella-up-open
Pose first: pure side view facing right, Ella hangs from her open umbrella: arms straight up, gloved hands stacked on the shaft just under the canopy, body hanging below like a weight on a string, legs limp, boots pointing straight down. Canopy directly above her head, finial up; the shaft runs down alongside her body to the diamond at her waist. Hair and scarf stream back left. One 21:9 strip of 4 poses, level camera, wide green gaps, whole umbrella inside, 65% of canvas height, same scale, hands and hips at the same height. Pose 1: boots together. Pose 2: boots drift into a narrow V, skirt and hair sway the other way. Pose 3: the V at its widest, still small. Pose 4: boots together. A slow gentle sway. The attached image shows only her open umbrella; copy its design. $S $I

### Call B: ella-attack
$I Pose first: level side view facing right, Ella falls slowly, torso upright, both legs hanging straight down, limp, boots side by side pointing at the ground. She holds the umbrella level at waist height like a lance, both hands on the shaft, finial behind her, diamond pointing right; hair and scarf stream back. Three figures in a row, 21:9, level camera, same scale, 60% of canvas height, green between them. Left: canopy furled along the shaft. Middle: canopy snapped open behind her, a small separate gold pulse flies right, clear of her. Right: canopy half closed, air ahead empty. The attached image shows only her open umbrella; copy its design. $S

### Call C: ella-shield
$I Pose first: level side view facing right, Ella falls slowly, seated in the air as if on a swing, torso upright, thighs forward, knees bent, shins and boots hanging down. Both gloved hands hold the shaft level in front of her waist; the open canopy is held out ahead at arm's length like a shield, finial pointing right, scalloped rim toward her; the diamond points left behind her hip. Hair and scarf stream back left. Three figures in a row, 21:9, level camera, same scale, 60% of canvas height, green between them. They differ slightly: canopy tilted a few degrees up, level, a few degrees down; hems drifting. The attached image shows only her open umbrella; copy its design. $S

### Call D: ella-closed
$I Pose first: level side view facing right, Ella crouches on her closed umbrella in free fall, torso hunched forward, knees bent high. The same umbrella is furled tight and vertical beneath her: finial pointing down, pierced diamond pointing up between her hands, boots resting on the collar band of the furled canopy. One gloved hand holds her hat brim, the other grips the shaft at her waist. Hair, scarf tails and skirt tiers stream up and back left, as the wind blows from below. Three figures in a row, 21:9, level camera, same scale, 60% of canvas height, green between them. They differ slightly: skirt and hair flutter in different shapes. $S

## Leans (your call, one line each)
- Order: A is pose-first then S, I; B-D are identity-first (R3 evidence: identity first fixed the attack identity). Lean: keep as is, do not unify before a call proves it matters.
- Lean: A at 357 words is over the ~320 target (4 poses). Accept it; cut a pose sentence only if the call returns muddled.
- Lean: the green key is what makes the outline lemon (cream + green spill = hue ~100). If the next call still comes back lemon after the apricot wording, change the key to magenta #FF00FF (spill goes pink, not yellow-green). Do not do it now.
- Lean: if D returns standing or seated instead of crouched, replace "crouches" with "perches".
