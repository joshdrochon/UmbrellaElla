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

## Round 2: draft2 (2026-11-13)
27 pieces (all but bg-start-end), one new flash seed each, `pipeline/art/proof/firstdrafts/<piece>/draft2.png`, jobs from `make_jobs2.py`.
Prompts now carry assetgen's shared style block; the green key was dropped (subject on aged cream paper) because the guard checks the raw draft.
- art_check PASS: ui-journey-complete (1 of 27). Final made: `ui-journey-complete/final2.png` (gemini-3-pro, 2K); the final itself fails art_check (on_palette .949, off_style .016 and more), kept as the best image.
- art_check FAIL, all other 26. Sprite/effect/Keeper pieces (19): accent_area 0.58-0.93 (the cream paper ground reads as gold accent, cap 0.08), and paper_texture low on some (yellow-shot .165). bg-base: accent_wind .309 > .06 (ash-blue sky). menu-screen, ui-level-up, ui-purchase, ui-spell-wheel: see `art_check` (palette/off_style at .89-.97 on_palette, off_style .007-.032).
- Finals made: 1 of 27 (ui-journey-complete). The other 26 stay without a final: guard refuses a failing draft, and the image cap is nearly gone ($33.53 of $33.82).
- Check defect candidate: art_check is built for in-engine screenshots; a paper ground on a sprite sheet scores as gold accent. `--sprite` needs transparency, so a keyed copy would be the fair test. Not done: no spend left to redraw on a key.
- Spend this round: gemini about $1.05 (27 drafts) + $0.139 (1 final). No OpenRouter or fal.
