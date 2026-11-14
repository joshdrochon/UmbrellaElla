# Prompt review: island solids (world-solids_r2, world-solids-block_r1)

Study islands: flat crumbly crust with small clumps and scattered gold glints; a short lit front lip (warm bronze band just under the top edge, slight overhang); thin gold rim on the top edge; dark underside that tapers (small island: rough inverted point) or hangs in long swept wax-like sheets (big island); dark specks, a few amber, spraying down-left from the lowest edges. Light falls from above and slightly front-right, so the top and lip glow and the underside sinks to umber-black. Both prompts get the green-key rules, positive phrasing and colours-guidance line right. No text risk beyond hex codes, which the guidance line covers.

## world-solids_r2.txt
Verdict: change
- Aspect: "about 6:1" is not a ratio the tool can send; it will snap to 4:1 or 8:1. Replace with "A very wide, short 8:1 strip" and run `--aspect 8:1` (3.1 flash only, per assetgen.py). 8:1 sits inside the 7-15:1 range, so stretch stays under 2x.
- Light: "from the upper right behind the slab, so the body is in deep umber shadow" makes a back-lit silhouette; the study is top-lit. Replace with "Lighting is low and warm, falling from above and slightly in front on the right, so the top crust and its front lip glow warm bronze and the underside sinks into deep umber shadow."
- Missing traits. After "with fine grit" add: ", small crumbling clumps along its top edge and a scattering of tiny warm gold glints; just below the top edge a short, slightly overhanging front lip catches the light as a warm bronze band".
- Underside: use the agreed D wording. Replace "in long, swept, flowing sheets and folds, like wind-blown sand or worn cloth" with "in long, swept, wax-like drips and flowing sheets, like melting wax or worn cloth".
- Specks: after "dark specks and grains" add "with a few warm amber ones among them, each speck large enough to read clearly".
- Repeat seam: add after "none reach the bottom edge": "At the far left and far right edges the underside is only the solid body; every stream starts and ends inside the strip, so copies sit side by side without a seam."
- Top margin: replace "near the top of the canvas" with "with a thin band of green above it, so the rim light is never cut".

## world-solids-block_r1.txt
Verdict: change
- Aspect: 3:2 vs blocks 0.7:1 to 2.7:1. 4:3 sits nearer the middle (geometric mean about 1.4) and keeps both stretches near 2x. Replace "A 3:2 landscape image" with "A 4:3 image".
- Collider fit: "centred and filling most of the canvas width" and "about a fifth of the way down" leave unknown green margins round the standing surface. Replace with "its top crust reaching within a few percent of the left and right edges" and "with only a thin band of green above it".
- Tall columns (0.7:1): "narrows like an upside-down mountain" leaves the lower collider with no earth beside it. Your call: keep the study's tapering underside, or keep walls straight. Lean: replace with "The steep side walls run straight down through the upper two-thirds of the canvas; only the lowest third narrows into the underside," since the player climbs those walls.
- Light: same replacement as the strip, "behind the island" -> "from above and slightly in front on the right".
- Missing traits: same crust-glint, clumps and front-lip addition as the strip; same D wording for the underside; same amber-speck addition.
- Walls: add "the walls show faint horizontal strata with warm highlights on their upper ledges" so the stretched sides read as eroded earth, not a smear.
