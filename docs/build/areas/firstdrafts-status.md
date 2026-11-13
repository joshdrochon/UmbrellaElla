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
