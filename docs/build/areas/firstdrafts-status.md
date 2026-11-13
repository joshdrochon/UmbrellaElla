# firstdrafts status (2026-11-13)

## Pieces with no generated image (28)
Found by matching art-inventory.csv pieces (and the CamelCase group folders of the vfx lanes) against every image under
`../<lane>/pipeline/art/proof/` and the tracked images on main. Placeholders (`_PH`) do not count as generated.
bg-atmosphere, bg-base, bg-start-end, ella-condition, ella-motion, enemy-floodstrider, keeper-clock, keeper-damage,
keeper-departure, keeper-mech-front, keeper-mech-middle, keeper-mech-rear, keeper-talon, keeper-wing, menu-screen,
stream-beam, ui-journey-complete, ui-level-up, ui-purchase, ui-spell-wheel, ui-xp-ring, vfx-clock-open, vfx-departure,
vfx-eye-exposed, vfx-keeper-recovery, vfx-keeper-strike, vfx-restoration, yellow-shot.
(Fewer than the 34 in the brief: the other pieces already have lane drafts.) ella-motion has only the idle video, no named still.

Prompts: `pipeline/art/proof/firstdrafts/make_jobs.py`. One flash draft each into `pipeline/art/proof/firstdrafts/<piece>/draft1.png`.

## Progress

## Result (2026-11-13)
- 28 of 28 pieces now have a flash draft: `pipeline/art/proof/firstdrafts/<piece>/draft1.png` (gemini-2.5-flash-image). Sprite pieces also have `draft1_clean.png` (chroma key #00FF00). No panel, not judged.
- Effect strips (stream-beam, vfx-*) were drawn at 21:9; flash has no 4:1.
- Final model (gemini-3-pro-image-preview, 2K): 1 of 28 made, `bg-start-end/final1.png`. The other 27 are refused by assetgen's DRAFT FIRST guard: `--from-draft` must pass art_check, and these drafts fail it (on_palette, off_band, paper_texture, dark_share). Raw drafts on a green key fail by design; the keyed copies still fail on palette/accents. The guard was not loosened. A pass needs redrawn drafts or the art lanes' loop.
- Spend: gemini only, about $1.09 for 28 drafts + $0.137 for the one final. No OpenRouter or fal calls. Shared counter was $30.0 of $33.82 at start; headroom for all 27 finals (~$3.6) was not there either.
