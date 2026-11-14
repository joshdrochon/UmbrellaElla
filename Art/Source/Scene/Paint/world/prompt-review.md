# Prompt review: world scene prompts (r1/r4/r5)

Study read: near-black warm charcoal void; clock rims are faint bronze arcs (humps) with tick marks and long wax-like drips; low haze ridges; many tiny amber flecks; islands have a flat crust top with a thin gold rim light and an underside that streams down in long swept drips with a spray of dark specks; skeletal ring-wheel windmill with web-like sails; barn roof drapes into web membranes; faint ash-blue wind ribbons (not for static art). Finish in the study is smooth-painted; the style block asks for etched ink, so wording must not pull toward "painted".

## Problems in all five
- A. "as a ... painted storybook illustration" fights the style block ("etched storybook engraving"). Replace with "as a dark storybook illustration".
- B. "aged paper grain under all colour" can lift the void to beige. Add to every opaque prompt (start-end, bg-base): "The paper itself is near-black charcoal; its grain shows only as faint lighter fibre, so the sky stays almost black."
- C. Aspect is never stated. Add it (see each section).
- D. Underside wording says "ragged hanging roots". The study shows long wax-like drips. Use "hanging in long, swept, wax-like drips and tendrils, with a spray of dark specks beneath".
- E. Hex codes may be printed as text by Gemini. Keep them, but add once: "Colours are given only as guidance; never print them."
- F. Negatives ("no border, frame, lettering") are the only way those are said. Lead with the positive ("edge-to-edge artwork, text-free"); keep the short negative after.

## Green-key pieces (world-solids, skyline, bg-land): shared risk
- Style block says "visible paper grain under all colour; no flat fills". The prompts say "one even flat shade". The model will grain the green, so the key leaves noise. Add: "The green background is flat digital green with no paper grain, no hatching, no texture; the grain and hatching apply to the earth only."
- "No green appears inside the earth" is a negative. Positive: "The earth uses only warm browns, umbers and near-black; its lit edges are warm gold-brown, never green-tinted."
- "no gradient, glow or shadow" -> "one unchanging green, with no light falling on it."
- Soft or hazy edges against green leave halos. Haze is added in engine, not painted.

---

## start-end_r1.txt
Verdict: change
- Aspect: first sentence, add "16:9 landscape" -> "A wide 16:9, wordless, character-free landscape ...".
- ART-04 / FLOW-34 want charcoal and sepia with faint blue and small gold lights. Blue is missing. Add after the haze sentence: "A very faint ash-blue cast lies in the haze in a few places, and the amber flecks read as small gold lights."
- Clock rims: study shows arches with drips, not full circles. Replace "huge thin bronze-grey circular rims, only partly visible" with "huge thin bronze-grey clock rims, seen only as great partial arcs".
- Windmill: replace "a tall skeletal windmill whose thin spindly sails curl like dry branches" with "a skeletal windmill, a thin ring wheel with a few curved web-like spokes, its sails curling like dry branches".
- Barn: add "its broken roof sagging and trailing in thin webbed shreds".
- Fleck count "never more than a few dozen" is too low for the study (about 80-100). Use "scattered thinly, a hundred or so tiny flecks".
- Boss arena: this image sits behind actors. The island with the barn is lower right; add "kept below the middle of the frame, with the centre and upper half left quiet and empty" so it does not read as a platform (BG-05 quiet zones). The last sentence already says empty upper half and centre; make it explicit that the island stays low.
- Lighting sentence is fine. Add A, B, D, E.

## world-solids_r1.txt
Verdict: change
- Aspect/use: not stated. Add: "a very wide, short strip, about 8:1, because it will be stretched along thin ledges and columns."
- "thickest in the middle and thinner at both ends" breaks stretching and tiling. Replace with "The body has the same thickness from end to end, so the strip can be stretched or repeated."
- "its underside breaks up ... that fade out before the bottom edge": fading into green makes a soft key. Replace "fade out" with "end in hard-edged dark specks and tendrils, none fading or blurred".
- Ends "cut cleanly by the canvas edges": add "the crust, layers and rim light continue to both edges at the same height".
- Green block: apply the shared fixes above (no grain on green, no green spill, positive phrasing).
- Add D, E.

## skyline_r4.txt
Verdict: change
- Aspect: "very wide" is not a ratio. Add "in the widest format available, about 4:1 or wider".
- Contradiction: "soft and hazy as seen through smoke" vs "edges meet it cleanly". Replace the last clause with "Distance is shown only by their dark, low-contrast umber-grey colour; every edge is crisp against the green."
- Undersides: apply D. The study islands are wax-drippy; "tapers ... like a melting clod" is close, but add "long wax-like drips".
- Windmill: "a ring wheel with thin curved spokes". The barn roof: "sagging".
- Repeat: "falls quiet and empty at both ends" - say positively: "Both the far left and far right ends hold only green, at least a tenth of the width each, so the strip repeats without a break."
- Shared green fixes apply. Count "seven to nine" is fine.

## bg-land_r5.txt
Verdict: change
- Aspect: add "16:9 landscape" or the intended panel ratio; none is given.
- Haze conflict as in skyline: replace "Their colour is muted and slightly hazy, so they read as further back" with "Their colours are muted and a step darker than the play area, with crisp edges; the engine adds haze."
- Arch: "a crumbling stone arch" has no colour or shape. Use "an open arch of dark bronze-grey stone, a hollow gap through it, its crown crumbling and warped like a bent clock hand" (BG-04 open arch, BG-05 warped clock-hand architecture).
- "three floating eroded islands ... different heights with wide gaps" is good for slicing; add "no island overlaps another" so each can be cut out as its own sprite (BG-04).
- Add D, E and the shared green fixes. The thin dark outline sentence is good; keep it.

## bg-base_r1.txt
Verdict: change
- Aspect: add "a 2:1 panel" in the first sentence (it is the stated format and is missing).
- Tiling: "left and right edges match in tone" is not enough; clock rims and ridges cut at the edge will jump. Replace with "No clock rim, ridge or fleck touches the left or right edge; the void and haze run on unchanged across both edges, so the picture can sit beside a copy of itself."
- GDD BG-03 lists Sky Base A/B and Clock-Ridge Pair A/B as separate outputs, not one flattened painting. This prompt bakes them together. Decision for the owner: (1) keep it as a combined placeholder and say so, or (2) split into a sky-only prompt (void, haze, flecks) and a separate clock-ridge prompt. My lean: split on the merits, since BG-03 asks for it.
- Negative "holds no land, buildings or figures": positive "an empty sky of void, haze, clock rims and flecks only".
- "faint hour tick marks" and drips are present. Add the ash-blue cast as in start-end if this stays a combined panel.
- Add A, B, D (clock-rim drips only), E.
