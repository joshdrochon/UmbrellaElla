# Prompt review, artfx3 VFX strips (Art Director, fresh session, no image call)
Sources: docs/build/art-image-model.md, art-bible.md, GDD-SH1.0 (COM-07/09, ANIM-05/06, VFX rows, Streamed Blast / Needle / Break stun asset rows), references.json elements vfx-needle-*, vfx-stream-*, vfx-part-*, vfx-stun.

## All eight (shared)
- Box risk: removed "flat, face-on emblem", "frames", "grid lines, boxes, panels, frames" (naming them primes them). Stages float on "open, empty green"; the strip is called a "clean sprite strip". "Frame N" became "Stage N".
- Aspect stated in words (wide 4:1 landscape, side view); API still sets aspect_ratio/image_size.
- Negatives rewritten positive: "no green inside any shape" became "shapes use only the palette above"; "never round soft discs" became faceted-blade wording.
- Style block identical across pieces.

## NeedleChannel
- GDD Needle VFX: a slim solid channel hub-to-pointed-terminal, brighter segments travelling inside, never a laser, no rim-tip stars. Old prompt grew a blade in length and ended in a star flare. Now a constant-length contained channel, travelling bright segments, pointed terminal with no star, a tiny sliver leaving at full charge.

## NeedleSliver
- COM-09/ANIM-05: finite sliver, short tail. Pinned the sliver at about a quarter of the stage length with empty green fore and aft so it cannot read as a beam.

## NeedlePierce
- Dropped "punching through a surface" (invites a drawn plane or wall); target is "an unseen target". Kept star flare on contact (impact, not rim-tip). Stage 4 ring replaced by a scatter.

## StreamStart
- GDD: many separate strands converge into one continuous stream, no fog. Old prompt was a plain widening jet. Now strands arc in from the left and merge; "widening" became "lengthening" (beam width is a fixed 14 in COM-07); fog excluded in positive wording.

## StreamSustain
- Added braided strands, seamless loop first-to-last, no fog.

## PartHit / PartBreak
- Palette: brass #E9C46A is Ella's magic gold and the Keeper is metal. Metal is now dark iron #3A3328 and bronze #94611E with thin bronze highlights; amber sparks and cream flashes only. #E9C46A removed from both.
- PartBreak: fragments stated as clean metal pieces (non-graphic wear, ANIM-06); smoke kept as separate angular ink wash.

## Stun
- GDD Break stun: warm gold/ivory body effect, distinct from the local amber slow ring (#E6A638). Removed the amber dashed orbit line (read as the slow ring); stars warm gold and ivory, gears bronze/iron.

## Open for the builder
- Clock/gear teeth are small at a fifth of the width; check at 1K that PartBreak frame 3 fragments stay readable.
