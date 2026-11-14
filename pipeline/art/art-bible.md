# Art Bible — Umbrella Ella

## North star: the whole frame (Josh, 13 Nov, D-new-north-star-frame)
The game screen as a whole must look like Ricky's Other Realm study (`bar-other-realm`,
`pipeline/art/reference/discord/20261111-0318_Ricky_other-realm.png`), not only each piece: dark backdrop; thin ash-blue
`#555e60` wind ribbons, never boxes; small figures; floating islands; gold `#E9C46A` and red shots; no placeholder cubes or
bars; no framed or unkeyed art. Every piece is judged in the composed game frame next to the study, never alone.
`tools/build/visual_qa.py` checks it on every merge that touches Source/, Content/, Art/ or pipeline/art. Where this
section and the key-art text below disagree on the frame, this section wins; the key art still sets the drawing finish.
`tools/art_check.py` does not gate whole-frame or scene work (scene, bg, bg-layer, world pieces): its palette and paper
limits come from the key art and fail the study itself. `visual_qa.py` judges those; art_check still gates single pieces
(`tests/test_art_loop_scene.py`: the study passes the scene path, Josh's 15:50 frame fails it).

Source of truth for how the game looks (decision D0, 2026-11-06): the target key art.
Reference file: `pipeline/art/reference/target-keyart.png` (to be added via Git LFS; see docs/references.md R7).
The GDD line "colorful, storybook-inspired" is overridden.

The key art is THE visual target (team, 10 Nov): the game must look like that picture, not only share its palette. It
sets palette, value structure, silhouette language, paper texture, accent rules, wind lines, sparkles, owl design
language and, since 10 Nov, the composition of the style frame (Target frame below). It does not set Ella's pose (in
the game she shoots only with the umbrella lowered, ATTACK_DESCENT, DEC-02) or the gameplay sizes in the asset spec:
those come from colliders and the GDD, and the composition ranges are wide enough for both.

All current art is a replaceable placeholder (GDD SH1.0 ANIM-02, CORE-05): key art, rehearsal sheets, generated sprites, UI ornament
and scenery. Gameplay never reads art: sprites follow fixed gameplay colliders and anchors (muzzle, catch, CLOCK/BODY), never
the reverse. Misaligned art is fixed by visual-only scale, pivot or offset; a collider change needs the design owner's approval.
Missing art shows a neutral visible stand-in and logs the asset ID. A replacement set passes size, alpha and frame checks,
16:9 readability, a collider-alignment preview and a same-seed replay (QA-25..QA-27). Shipping includes only approved assets (QA-28).

Direction stays dark and muted: ink on paper (team, 8 Nov). Every concept sheet is compared at gameplay size (scaled to its
in-game height in a 1080p capture, beside the style frame) before any asset card for it starts.

## GDD SH1.0 (12 Nov): what the new GDD changes here (it wins where this page differs; D-new-sh10-art-conflicts)
- **References are judging targets, never generation inputs.** The key art, Ricky's title image, the Test_Assets sheets
  and every picture in `pipeline/art/references.json` are what the art loop and `art_ref_check.py` judge against (mood,
  palette, finish, the quality bar: match or exceed). No reference, pre-jam picture, screenshot, atlas or crop is ever
  fed to a generator, traced or shipped (GDD SH1.0 ART-03, BG-02, ART-09). New art is made in Blender from the GDD's
  written descriptions after the kickoff, with a provenance row.
- **Keeper:** a crownless fabricated metal owl in side profile: rigid perforated vane wings, exactly two feet, the chest
  clock with one long hand, three distinct hanging mechanisms (front armillary, middle cage, rear gear) on their own chains
  (OWL-08, ART-06). This replaces the key art's organic, crowned owl; the key art still sets palette, values, paper and finish.
- **Ella:** an adult, face hidden by a cloth / mesh mask, two hands on one umbrella with a crown finial and a diamond
  clock-hand terminal; no wand, spells leave the canopy (ART-06). The umbrella stripes stay (the GDD is silent on them).
- **Shots:** red and yellow share one pointed angular geometry (OWL-14); colour is the material (red `#FF3658` / coral
  `#FF7848`, yellow `#FFD84A` / amber `#F5AA28`, pale core `#FFF5DC`). Small Blasts is a gold `#E9C46A` pulse. The old
  "4-point cross" and "round wand bolt" rules below are GDD 1.3 history.
- **Start and End screens** show no characters, dark charcoal and muted sepia with faint blue and small gold lights
  (FLOW-34, ART-04). Ricky's title image stays the title-screen target for mood and finish; where it shows a character or
  the brighter alternate palette, the GDD wins.
- **Light:** VFX-07 asks for nearby-surface light; this page's unlit sprites stay, with a separate light-overlay layer per
  effect (D-new-sh10-vfx-lighting).
- **Placeholders:** gameplay may use tracked `_PH` assets; each one is a `coverage` row in
  `pipeline/art/blender/characters.json` naming the card that replaces it. None ships (`pipeline_check.py --release`).
- **The art gate follows it (12 Nov):** `style.json` shot-red is the GDD crimson family, `gold` and `amber-eye` are the
  GDD's `#E9C46A` and `#FFC76A`; in `references.json` the `owl`, `owl-bolt` and `bolt-hit` elements judge the metal
  Keeper and the crimson shot, and the `owl`, `owl-bolt`, `bolt-hit` and Ella elements carry the GDD's words as written
  targets (`keeper-sh10`, `red-shot-sh10`, `ella-sh10`). Details under Look decisions.

## References (enforced in code)
Every reference image is listed in `pipeline/art/references.json` with its role (composition target, character/pose
sheet, owl, effects, palette, scale, pattern) and the cards that must match it; all of them sit in this repo under
`pipeline/art/reference/` (Git LFS): the key art, the Test_Assets sheets and SpriteLayout.json, the rehearsal Ella
sheets, the mockups, the v1.4 gameplay references and Ricky's #art-direction posts (`discord/`, with `index.json`).
They are references only and never ship or get imported (Official Rules §7(h)); jam art is generated during the jam.
Ella runs on the ground in some studies (`study-ella-*`, the rehearsal sheets); in the game she is always
airborne, so use those for pose and look, never for a grounded state.
Ricky's posts show proposed attacks and visuals: anything there that is not in the current GDD (absorbable yellow
shots, a wing gust attack, talon rake, double-beat, owl and clock damage states) is a design proposal for Richard and
is used for its LOOK only. `python3 tools/art_judge.py coverage` (and `tests/test_art_judge.py`) fails a reference no
judge element or no card uses, a reference missing on disk, and an art card with no references.

## Quality bar (top tier, 11 Nov)
Two of Ricky's #art-direction images are the bar for finish, on top of the key-art composition (Josh: anything short
of them is a complete failure): `bar-casters` (Roadwarden / Sundial Casters study: rendering quality, character
detail, projectile construction) and `bar-other-realm` (Other Realm study: scene mood, atmosphere, and how wind flow
reads: flowing ribbons, never a flat box). Every art-loop round also judges our piece blind against one of them, and
a flat primitive or rough placeholder fails outright. Shot VFX follow `references.json` `vfx_spec`: tell, release,
travel, fade; bright core, shell, trail, light spill. Their characters, realm and colours are proposals for Richard:
use them for look and quality, not mechanics. Their colours are in `style.json` as capped accents (Josh, DECIDED
2026-11-10, D-new-palette-accents; see Palette below). The shot red is the GDD SH1.0 crimson again, the same values as
bar-casters (the 11 Nov rust of D-new-owl-shot-look is superseded).

## Look decisions (Josh, DECIDED 2026-11-11)
GDD SH1.0 wins over this section (D-new-sh10-art-conflicts): the Keeper, Ella and Shots lines at the top of this page
replace the owl row, the owl-shots row and the "no mask" part of the face row below, and the art gate files follow them
(12 Nov). The umbrella stripes, the hidden face and the hair and hat stay. The key art (`keyart`, `original-picture`) is
the bar for mood, palette, values and finish, never for the Keeper's form or the shot colour:
- Owl (D-new-owl-look, SUPERSEDED): was the key-art organic owl (tattered feathers, gothic spire crown, amber eyes).
  Now the GDD's crownless metal Keeper. The `owl` element judges `discord-crop-keeper` (the Keeper cut from Ricky's
  toss-and-kick sheet), Ricky's metal-owl sheets (`d-wing-damage`, `d-talon-rake`, `d-gear-break`, `d-flip-throw`,
  `d-toss-kick`, `d-arc-chain`, `d-clock-damage`) and the `study-keeper-*` studies, with the written target
  `keeper-sh10`. `owl-flap` (the organic owl sheet) left it: frame grid only. `gameplay-01/02` stay in the scene for
  composition and scale.
- Owl shots (D-new-owl-shot-look, SUPERSEDED): was the key art's rust-red needle with a crosshair ring. Now the GDD's
  shared red projectile: `style.json` shot-red RED `#ff3658`, CORAL `#ff7848`, RED SHADOW `#8f173c`. The `owl-bolt`
  element judges `discord-crop-red-shot`, `d-red-shots`, `d-clock-double-beat`, `study-keeper-red-shots` and
  `bar-casters` (written target `red-shot-sh10`); `bolt-hit` judges `discord-crop-red-release`, `d-red-shots` and
  `bar-casters`. `keyart-bolt` and `owl-missile-hit` (the rust crosshair burst) left them: kept, judge false.
- Umbrella (D-new-umbrella-look): black with light stripes, as in the key art. `study-umbrella-prop` is the build
  and damage-stage reference only.
- Ella's face (D-new-ella-face, mask part SUPERSEDED): hidden, under the GDD's cloth / mesh mask with separate scarf
  and eye glints. The four Ella elements carry it as the written target `ella-sh10` (also: no wand). `d-ella-eyes`
  draws that mask but is a head-and-shoulders close-up, so it stays out of the elements (judge false, reason updated);
  `study-ella-character` stays for hair, hat, costume and silhouette.
- Ella's look (D-new-ella-look, Claude's call, Josh delegated): designed from `study-ella-character` (dark brown hair,
  hat, hidden face) at the key art's silhouette and scale. The rehearsal Ella sheets (`ella-*`) are pose and
  frame-grid references only, not hair or skin colour. The witch sheets (`witch-cast`, `witch-guard`: another
  character, no umbrella) are frame-grid and layout data only.
- Key-art crops (11 Nov): the owl bolt, the umbrella, the etched wind lines and the rock band are cut out of the key
  art as their own references (`pipeline/art/reference/keyart-crops/`, alpha-keyed, reference only), because a sprite
  cannot be scored against the full frame. `keyart-umbrella` is the `umbrella` look, `keyart-wind-lines` the only
  `wind-lines` reference (`keyart-bolt` is no longer a look: GDD SH1.0); the same reason gives the Discord crops
  (`pipeline/art/reference/discord-crops/`, 12 Nov: the Keeper, the red shot, its release burst); the gameplay zone (`wind-zone`) is judged against
  `bar-other-realm`'s ribbons only, and the two wind elements share no reference. `keyart-skyline` is on hold: the
  key art's band is flat black inside, and as a skyline reference it drops the skyline's detail floor so far that the
  rough Blender skyline passes; the skyline keeps `keyart` and `gothic-skyline` until the team decides.
  `study-environment` is for parallax layering only.
- Out of judging (judge false, no judge element, files kept): `wind-curl` and `umbrella-repair` (teal),
  `owl-missile` and `owl-missile-travel` (blurry), `umbrella-stance` (crude), `d-yellow-crop` (blurry), `d-wing-gust`
  (off-palette blue), and since 12 Nov `owl-flap`, `keyart-bolt`, `owl-missile-hit` (old look) and `d-ella-eyes` (a bust). The same picture is never listed twice: `tools/art_check.py` load_spec drops a listed entry
  whose bytes equal an earlier one, and `team_art.same_as` names the re-encoded copies.

## Target frame (measured from the key art, 10 Nov)
`tools/art_judge.py scene` scores a screenshot against this; the ranges live in `references.json` `scene`.
| Element | In the key art | Target range (share of the frame) |
|---|---|---|
| Owl | wings spread, right half, centre x 0.68, 83% of the height, 64% of the width | centre x 0.55-0.90, height 0.45-0.95, width 0.25-0.90 |
| Chest clock | glowing gold inside the owl | gold share ≥ 0.0008, ≥ 60% of it inside the owl's box |
| Ella | small on the left under the striped umbrella, centre x 0.16, body about 11% of the height | centre x 0.04-0.35, height 0.04-0.30 |
| Scale | owl about 7x Ella's height | owl:Ella height ≥ 3 |
| Skyline | black jagged band along the bottom, median 10% of the height, full width | median 0.03-0.25, across ≥ 90% of the width |
| Owl shots | the key art draws rust-red needles flying left; the game's are the GDD SH1.0 crimson shots | red share ≥ 0.0008 (the scene's `rust` class also catches the crimson shots: 0.0194 on `gameplay-02`) |
| Look | paper texture, etched wind lines, gold star wand shots, sparkle dots | art_check PASS; layout and edge similarity to the key art ≥ 0.65 |
The key art and its earlier cut pass at 1.0; a flat teal box with a small owl and no skyline fails. The ranges are
provisional until card 0.10 scores the first in-engine rebuild.

## What the reference shows
Wide side-on frame on aged, stained sepia/taupe paper. Small black-silhouette Ella on the left,
floating under an open striped black umbrella, firing a line of small gold-white glowing shots.
A huge tattered dark owl on the right: ragged spread wings, glowing amber eyes, a gold clock face
with gears in its chest, gothic spires and a gear crown, chains with crosshair pendants. Five rust-red
needle-shaped enemy projectiles, each with a crosshair ring, fly left. Thin etched wavy wind lines cross the frame. Jagged pure-black
rock silhouette along the bottom. Faint white sparkle dots.

## Pillars
1. **Aged paper ground.** Stained, mottled sepia field. Never flat, never white.
2. **Near-black silhouettes.** Ella, the owl and its projectiles read by shape. Interior detail is dark-on-dark only.
3. **Brand accents first, capped extras second.** Gold/amber = the player's magic and the owl's eyes and clock. Red = danger (the GDD SH1.0 crimson shots, a capped accent; the key art's rust stays a palette colour). The quality-bar colours (ash-blue wind flow, shot reds and yellows) appear only in their role and under their cap (Palette). No other saturated hue: no teal, green, purple, pink, no saturated blue.
4. **Etched atmosphere.** Wind lines and sparkles are decoration. They must never look like gameplay.
5. **Ella small, owl huge.** The scale contrast is the drama, but never at the cost of reading Ella and her umbrella state.

## Gameplay readability rules (these beat style)
- Umbrella open vs closed is readable in silhouette alone. Open silhouette width ≥ 1.8× closed.
- The wand bolt (Ella's automatic shot) is small, round and gold-white. Owl projectiles are danger: at least 2× its size (look: the GDD SH1.0 Shots line at the top of this page; the rust-red needle is history). Never the same hue family.
- Gameplay zones (the WIND-01 upward wind zone, P0; hazard telegraphs; later gust zones) read as a zone with edges,
  but in the etched style: etched upward wind strokes or particles over a subtle paper tint, inside an engraved
  border. Never a flat solid fill, a plain primitive or a placeholder glyph. A zone must be told apart from the
  decorative wind lines at a glance (rule 4 stays: decoration never looks like gameplay): the zone has a border and
  upward strokes, the decoration has neither. Checked by `screen_check.py` (no flat region) and by the art loop
  against the zone's references (`wind-zone` in `references.json`; card 0.10c).
- No debug or placeholder visuals in the default build: hitbox and collision draws, flat primitive stand-ins and debug
  text only behind the dev flag `ue.Debug`, off by default (`pipeline/unreal-rules.md` Display). `screen_check.py`
  fails a large flat single-colour rectangle, a grey placeholder box or a debug outline on a default-build
  screenshot, and the smoke runs it by itself.
- Projectiles draw above Ella. Danger is never hidden.
- Draw order: paper < wind lines < owl < Ella < wand bolts < owl projectiles < VFX < HUD.
- UI text: minimum on-screen text height 18 px at 1280x720 and above (the same number as `SMOKE_MIN_TEXT_PX` and the test `UmbrellaElla.Presentation.UIScalesWithResolution`).

## Eval captures
The Integrator places fixed cameras `CAM_Eval_Arena` (the whole arena) and `CAM_Eval_Stress` (the desperation cluster), plus `CAM_Eval_StyleFrame` and `CAM_Eval_Swatch`. Art review captures come from these, at 1920×1080, with `HighResShot 1920x1080`.

## Automatic art checks and the art loop (no human approves a look)
Where they run: in every smoke (`tools/ue/smoke.sh` / `smoke.ps1`, so the daily and kickoff's build path) on the
smoke's own default-build screenshot, and on generated art in kickoff's art loop. GitHub CI cannot run Unreal, so CI
runs `tools/check_pr.py`, which rejects a PR whose pasted evidence lacks the PASS lines.
1. Deterministic, final: `art_check.py` (palette, paper texture), `screen_check.py` (flat fills, grey boxes, debug
   outlines, 16:9), `art_ref_check.py --card <id>` (the card's own references; its line carries `refs=<hash>` of
   `references.json` and the commit), and `hitbox_check.py` for gameplay sprites.
2. The art loop (`tools/art_loop.py`): every art card is split into its smallest judgeable pieces (each element its
   references cover, plus the full frame). A builder session makes or revises a piece in Blender
   (`pipeline/art/blender/`); separate critic sessions with fresh context see only X.png and Y.png pairs (labels
   stripped, random order) and a fixed prompt, and answer WINNER: X|Y|SAME and the single biggest GAP, never a score.
   Each round a panel of 3 sessions judges ours against every reference of the element, the quality bar, a sheet in
   motion and the piece in an in-engine capture; each session hides the pair among calibration pairs and counts only
   if it gets them all right. The gap goes back to the builder. The piece is done when every counted session picks
   ours or SAME on every pair and every deterministic check passes; shipped art carries that record
   (`check_pr.py` rule artship, `submission_check.py art`). The numeric judge's minimums are calibrated from the team
   art (`tools/art_judge.py calibrate`, leave-one-out) over the fixed set under `pipeline/art/reference/` only, so
   they are the same in every repo; the Assets/ studies are look and context references that never move them. No round cap; three
   rounds in a row with no improvement on both raise NEEDS HUMAN with the first and latest image and the gaps. Every
   round is logged (`Saved/Logs/pipeline/art-loop.jsonl` and the journal).
3. A card closes only with an `art_loop: PASS` line for each piece and an `art_ref_check: PASS` line on its commit
   and the current `references.json` (`check_pr.py` rules artref and artloop; kickoff will not send it to review
   without them).

## Palette
Machine-readable palette and thresholds: `pipeline/art/style.json`, checked by `tools/art_check.py`.
INK `#171614` joins the darks (silhouette role). Capped accents (`style.json` `accents`; Josh, DECIDED 2026-11-10,
D-new-palette-accents), each allowed only in its role, inside its CIELAB hue and chroma band, and under its share of
the frame; all of them together stay at or under 10% of the pixels, so the brand palette dominates:

| Role | Colours | Hue band (CIELAB, deg) | Chroma | Max share |
|---|---|---|---|---|
| wind (WIND-01 flow ribbons) | ash blue `#555e60` (measured on the Other Realm ribbons; its label `#7P9698` is not a hex) | 190-260 | 2-12 | 6% |
| shot-red (red shots: GDD SH1.0 shared red projectile; band measured on Ricky's red-shot sheets, 12 Nov) | RED `#ff3658`, CORAL `#ff7848`, RED SHADOW `#8f173c` | 5-50 | 30-85 | 4% |
| shot-yellow (yellow shots, shot cores) | YELLOW `#ffd84a`, AMBER `#f5aa28`, YELLOW SHADOW `#94611e`, CORE `#fff5dc` | 55-100 | 8+ | 4% |

Brand hue gate: gold/amber ~55-95 and rust ~20-50 (`hue_gate`). An accent pixel outside its band, a teal or saturated
blue, and a flat fill of any colour still fail (`off_style`, `off_band`, the caps, `paper_texture`, `screen_check.py`).
**The hex values are estimated by eye and are provisional.** First task for the Art Director:
add the reference file, run `python3 tools/art_check.py --extract pipeline/art/reference/target-keyart.png`,
replace the palette with measured values, and set `palette_status` to `measured`.

## Asset spec (prototype targets; change only on measured evidence)
| Asset | On screen at 1080p | Pivot |
|---|---|---|
| Ella + open umbrella | 80–100 px tall | Bottom center |
| Ella, closed umbrella | same body height; umbrella width ≤ 0.55× open | Bottom center |
| Wand bolt | 10–14 px core, ≤ 8 px glow | Center |
| Owl red shot (GDD SH1.0 shared red projectile: pointed angular head, short tail) | 28–36 px | Center (rotate with transform, not frames) |
| Owl returning arc (P2) | same core as the bolt, red trail | Center |
| WIND-01 wind zone (P0): etched upward strokes, engraved border, paper tint | the zone rectangle in `pipeline/level/encounter.json` | Bottom left |
| Owl (MVP, the one boss) | 55–70% of screen height, split into parts (body, wings, chest clock) | Per-part pivots |
| Paper and background layers | full screen | Bottom left |

Pivots: machine copy in `style.json` `unreal_import.sprite.required_pivot` (one pivot per asset across all anims, checked by `--import-report`). Width: `sprite_check.py --width-ratio`.

Authoring scale is open (D13): 2× with mipmaps (lean) or 1×.

Flipbook frame rates (machine copy: `style.json` `anims`, checked by `tools/sprite_check.py`): idle-float 8 fps (4–6 frames) · fall 12 fps (2–4) · open/close transition 24 fps
(3–4 frames; the new state's first frame shows on the same frame as the input) · attack 15 fps (3–4) ·
hit/death 12 fps · owl wing 10 fps · impact VFX 20–24 fps. Characters never above 15 fps.

## Import settings
Checked by `tools/sprite_check.py --config`, `--import-report` and `--names`. Rules and [VERIFY] list: `pipeline/art/import-rules.md`.
- Frame names: `SPR_<Asset>_<Anim>_<NN>` (2 digits, from 00), extracted with Extract Sprites in Grid mode, Naming Template `SPR_<Asset>_<Anim>_{0}` [VERIFY]. Agree names before extracting; flipbook order follows them.
- Sheet cell, margin and spacing are in the asset brief and the `.sprite.json` sidecar. Extraction uses the same numbers.
- `bResizeSpriteDataToMatchTextures` on, sprite atlas groups off (project settings, card 0.3) [VERIFY].
- Texture filter **bilinear/trilinear**, not Nearest. This is painted art at non-integer scales; Nearest gives jagged, shimmering edges.
  Do not use the Paper2D "2D Pixels (unfiltered)" group or "Apply Paper2D Texture Settings".
- sRGB on. Compression UserInterface2D (RGBA) for sprites. Never Stream on for sprites.
- If D13 picks mipmaps, sprite sheets must be power-of-two sized (pad them); Unreal gives non-power-of-two textures no mips.
- Unlit sprite materials only (masked for hard silhouettes, translucent only for glow; `--import-report` fails a silhouette or tile on translucent).
- No normal maps and no lit sprite materials (`--import-report` checks the material path). Paint all dark-on-dark interior detail
  under one assumed light: from the front, slightly from above (proposed; decision row D-new-art-light requested). Judge rubric row R11.
- Post-process locked: manual exposure (no eye adaptation; Metering Mode Manual, compensation 0) [VERIFY on 5.8.4], no vignette, grain, chromatic aberration
  or motion blur, anti-aliasing off or FXAA (TAA/TSR smears small sprites), tone curve neutral.
  Check: `make_art_calibration.py --swatch` sprite under `CAM_Eval_Swatch`; `art_check.py --swatch <capture>` PASS (every swatch ΔE76 ≤ 3).
  If it fails, fix tonemapping before judging any art.

## Provenance (hard gate)
Every asset gets a row in `pipeline/art/provenance.csv` before it merges:
asset path, author (human), origin (`hand-made` | `AI-generated` | `AI-assisted` | `third-party`),
tool + model + version, prompt, seed, input images, date, licence, attribution.
- Prompts never name living artists or copyrighted IP.
- Third-party: CC0 or CC-BY (credit in CREDITS.md) or a licence that allows our use. No licence URL, no merge.
- **Blocker before Day 1:** someone checks the jam's rules on AI art and disclosure (D14).
