# MegaJam 2026 test art

All coordinates are pixels from the top-left of each frame. Columns advance left to right. Row and column indices are zero-based. **SpriteLayout.json** lists the exact frame sizes, pivots, playback rates and attachment points.

| PNG | Layout | Playback |
| --- | --- | --- |
| SKY_StarPaper_Tile | 3200 × 1080 | Repeat along X |
| ENV_GothicSkyline_Tile | 3200 × 720 | Transparent skyline. Repeat along X and align to the bottom of the view |
| CHR_Owl_Flap_Damage | 6 × 5, cells 640 × 512 | Loop across a single row at 10 fps. Row 0 is full health. Rows 1–4 progressively tear the wings and tail. Keep the current column when changing rows |
| CHR_Witch_Cast | 6 × 2, cells 432 × 352 | One shot at 14 fps. Row 0 is the overhead lift pose. Row 1 is the front-guard fall pose with a fuller skirt. Fire on column 3 |
| CHR_Witch_Guard_Transition | 5 × 1, cells 432 × 352 | Play once at 14 fps, forward for lift to guard and backward for guard to lift |
| PROP_Umbrella_Stance_Damage | 5 × 5, cells 368 × 352 | Columns 0–4 match the witch's transition. Hold column 0 for overhead lift and column 4 for front guard. Rows 0–4 run from intact to heavily torn |
| FX_Wand_Star_Travel | 6 × 1, cells 128 × 64 | Loop at 16 fps, facing right |
| FX_Owl_Missile | 160 × 80 | Static missile, facing left |
| FX_Owl_Missile_Travel | 6 × 1, cells 160 × 80 | Loop at 16 fps, facing left |
| FX_Owl_Missile_Hit | 7 × 1, cells 128 × 128 | Play once at 20 fps on impact |
| FX_Wind_Curl | 8 × 1, cells 144 × 112 | Loop at 12 fps |
| FX_Umbrella_Repair | 7 × 1, cells 128 × 128 | Play once at 18 fps at the canopy |

For the umbrella, attach its grip pivot at **(126, 223)** to the witch's frame-specific **grip_px** point in the JSON. Draw the umbrella behind the witch so the hand covers the grip. During the turn, step both sheets on the same column. On a successful front-guard hit, reduce the umbrella's damage row by one, clamped to zero, and play the repair effect. An overhead hit can advance to the next damage row. Use the per-column **wand_tip_px** point to spawn the witch's shot.

Use separate environment layers. A slower horizontal scroll for the sky and a faster scroll for the skyline will give the scene depth. Both textures wrap horizontally.

## Artwork provenance

The flattened `umbrella-ella.png` illustration supplied the design and style reference. The built-in ImageGen tool reconstructed the owl, witch, umbrella, sky and skyline. GIMP 3.2's command-line batch process built the animation frames and damage masks, blended the tiles, rasterized the drawn effects and exported the PNGs.

## ImageGen prompts

### Owl

Using attached image as style and character reference, reconstruct just the complete clockwork owl antagonist as one game-ready 2D cutout on a genuinely transparent canvas. Wide 3:2 or wider. Full owl, completely uncropped, wings open laterally about 15 degrees above horizontal with wing roots clearly recognizable and tail fanned downward, two curled talons. Three-quarter view looking left, bronze and gold clock face chest, charcoal and dark umber layered etched feathers, gold eyes and beak, short sparse clock chains attached to body. Precisely emulate the original dark ink, faded warm paper and engraved medieval clockwork character. Wings and tail are intact, full health, with continuous silhouettes. Leave clear negative spaces between tail and feet, and a generous border all around. Single subject, no parchment, no cast shadow, no glow halo, no sparks, no type.

### Witch

Using attached image as style and character reference, redraw just the complete small witch as a high resolution isolated 2D game sprite on genuine transparency. Exactly one full-body witch, facing screen right in profile, hovering with boots and legs trailing to the left and tapered skirt, pointy hat, long scarf and dark hair curling left, recognizable dark silhouette, subtle etched warm charcoal/sepia highlights like original. Her near arm is held away from her torso and extends forward horizontally to the right, carrying a very thin short wand. The opposite arm is visible above the shoulder and bends up into a small raised gripping fist to hold an invisible handle. Show both hands. Leave margin around hair, boots, wand. Preserve ink-paper cutout look, no flat cartoon/vector, no umbrella, no sparks, no shadow, no text.

### Umbrella

From the attached game illustration, redraw only the witch's fully open umbrella as a single isolated transparent 2D asset. Match original etched black and muted taupe alternating ribs/panels, pointed finial and scalloped batwing-like canopy. Side-on side profile with an exactly vertical dark thin shaft centered underneath, ending in a small curled J grip. Intact canopy full health. Subtle engraved weathered textile texture, crisp silhouette, no cast shadow, witch, light effects, ground, background, text, decorations. Place full item centrally with generous margins.

### Sky

Use the attached game image as a style reference, create ONLY a beige-grey muted night sky texture plate for a sidescrolling game, ultra-wide 3:1 landscape. A softly mottled, lightly grained lithograph paper field, soot gray and warm desaturated mushroom and oatmeal tones, faint wispy fine flowing parallel engraved streamlines mostly near upper edge and lower quarter, a sparse scattering of very small pale cream pinprick stars and a few small etched rings as in the reference. Mid-screen is calm, low contrast, art will be overlaid. No owl, witch, weapons, ground, skyline, mountains, moons, borders, text, horizon or typography. Suitable for repeating horizontally with edge blending; avoid dark vignette or contrasting left/right edges.

### Skyline

Using the attached illustration as the style reference, make a standalone horizontal black city skyline as a single layered ground silhouette for a sidescrolling 2D game. Ultra wide landscape. Genuinely transparent background above the rooftops. Along the entire bottom edge continuous charcoal-black near-silhouette city strip, with varied narrow gothic and Victorian towers, sharp gables, chimneys, with a few subtle amber lit windows. Hand-inked engraved paper aesthetic matching the reference mountains, extremely restrained contrast in silhouette. All buildings rooted to a completely opaque straight black base at bottom edge. Left and right edges should taper to an identical low flat black parapet, about a tenth of image height so this can tile. No perspective vanishing point, no sky, moon, hills, type, shadows. Crisp silhouette with delicate ink texture.

