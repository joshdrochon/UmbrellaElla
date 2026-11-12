> Generated from `pipeline/art/art-bible.md`, `pipeline/art/style.json`, `pipeline/art/references.json`, `pipeline/art/reference/discord/index.json`, `pipeline/art/reference/Test_Assets/SpriteLayout.json`, `pipeline/art/reference/Test_Assets/Asset Notes.md`, `pipeline/art/blender/characters.json`, `pipeline/art/blender/plan.py`, `pipeline/art/blender/stand_ins.py`, `pipeline/art/blender/render_sprite.py`, `pipeline/art/import-rules.md`, `pipeline/art/provenance.csv`, `pipeline/checklists/animation-review.md`, `pipeline/templates/asset-brief.md`, `evals/art-judge/README.md`, `evals/art-judge/blind_pairwise.md`, `evals/art-judge/agreement.csv`, `evals/art-judge/critic-calibration.json`, `tools/art_judge_prompt.md`, `tools/art_check.py`, `tools/screen_check.py`, `tools/art_judge.py`, `tools/art_ref_check.py`, `tools/art_loop.py`, `tools/sprite_check.py`, `tools/make_art_calibration.py`, `tools/png.py` at `fbcd307` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Art Pipeline

A readable copy for people. Agents load these rules from the repo paths listed below.

## About this pipeline

- **Purpose:** One look that matches the key art, measured in-engine, with every asset traced to a licence.
- **Owner:** Art Director (direction, review) and Asset Specialist (sprites, flipbooks, provenance).
- **Inputs:** Every reference picture in `pipeline/art/references.json` (the curated set under `pipeline/art/reference/`, the key art first, plus the team art under `Assets/` and `Mockups/` it joins each run), the art bible, asset briefs on cards.
- **Outputs:** Sprites, flipbooks and backgrounds rendered in Blender (pipeline/art/blender/), art review verdicts, provenance rows, art-loop pass records, the art-judge calibration set.
- **Gates:** The automated art gate on every visible change (`art_check.py --gate`: references, numbers, calibrated blind judge; no human art sign-off). Automatic on every smoke: `art_check.py`, `screen_check.py` and `art_judge.py scene` on the smoke screenshot; `art_ref_check.py` against each card's references; the art loop (builder and blind critic until the references' bar: ours or SAME against a reference, the quality bar and, for a sheet, in motion); `check_pr.py` rules art, artref, artloop and artship in CI; `submission_check.py art` on the package; `sprite_check.py` in CI.

## Built from

- Art direction: `pipeline/art/art-bible.md`, `pipeline/art/style.json`, `pipeline/art/references.json`, `pipeline/art/reference/discord/index.json`, `pipeline/art/reference/Test_Assets/SpriteLayout.json`, `pipeline/art/reference/Test_Assets/Asset Notes.md`
- Blender art generator: `pipeline/art/blender/characters.json`, `pipeline/art/blender/plan.py`, `pipeline/art/blender/stand_ins.py`, `pipeline/art/blender/render_sprite.py`
- Import and provenance: `pipeline/art/import-rules.md`, `pipeline/art/provenance.csv`
- Checklists and templates: `pipeline/checklists/animation-review.md`, `pipeline/templates/asset-brief.md`
- Art judge: `evals/art-judge/README.md`, `evals/art-judge/blind_pairwise.md`, `evals/art-judge/agreement.csv`, `evals/art-judge/critic-calibration.json`, `tools/art_judge_prompt.md`
- Commands and checks: `tools/art_check.py`, `tools/screen_check.py`, `tools/art_judge.py`, `tools/art_ref_check.py`, `tools/art_loop.py`, `tools/sprite_check.py`, `tools/make_art_calibration.py`, `tools/png.py`

## Art direction

### `pipeline/art/art-bible.md`

#### Art Bible — Umbrella Ella

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

##### GDD SH1.0 (12 Nov): what the new GDD changes here (it wins where this page differs; D-new-sh10-art-conflicts)
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

##### References (enforced in code)
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

##### Quality bar (top tier, 11 Nov)
Two of Ricky's #art-direction images are the bar for finish, on top of the key-art composition (Josh: anything short
of them is a complete failure): `bar-casters` (Roadwarden / Sundial Casters study: rendering quality, character
detail, projectile construction) and `bar-other-realm` (Other Realm study: scene mood, atmosphere, and how wind flow
reads: flowing ribbons, never a flat box). Every art-loop round also judges our piece blind against one of them, and
a flat primitive or rough placeholder fails outright. Shot VFX follow `references.json` `vfx_spec`: tell, release,
travel, fade; bright core, shell, trail, light spill. Their characters, realm and colours are proposals for Richard:
use them for look and quality, not mechanics. Their colours are in `style.json` as capped accents (Josh, DECIDED
2026-11-10, D-new-palette-accents; see Palette below), except the shot red: bar-casters sets how a shot is built
(core, shell, trail, spill), never its colour (D-new-owl-shot-look below).

##### Look decisions (Josh, DECIDED 2026-11-11)
GDD SH1.0 wins over this section (D-new-sh10-art-conflicts): the Keeper, Ella and Shots lines at the top of this page
replace the owl row, the owl-shots row and the "no mask" part of the face row below. The umbrella stripes, the hidden face
and the hair and hat stay. Until the Art Director re-points them, `style.json` shot-red and the `references.json` owl
refs still follow the old rows. The key art (`keyart`, `original-picture`) is the bar for mood, palette, values and finish:
- Owl (D-new-owl-look): the key-art organic owl: tattered feathers, gothic spire crown, a glowing gold gear clock with
  no numerals, amber eyes. The riveted metal-owl images (the `study-keeper-*` studies, Ricky's owl sheets `d-*`, the
  v1.4 `gameplay-01/02` concepts) are motion and mechanism references for attacks only, never the owl's look: they
  left the `owl` element (role `motion`, judge false); `gameplay-01/02` stay in the scene for composition and scale.
- Owl shots (D-new-owl-shot-look): a rust-red needle with a crosshair ring, as in the key art and `owl-missile`
  (`#743422` family; `style.json` shot-red re-measured from the key art's bolts). The pink `#ff3658` chevrons are not
  the look; `bar-casters` is kept for build quality only.
- Umbrella (D-new-umbrella-look): black with light stripes, as in the key art. `study-umbrella-prop` is the build
  and damage-stage reference only.
- Ella's face (D-new-ella-face): hidden, as in `study-ella-character`. No mask, no glowing eyes: `d-ella-eyes` (and
  its copy in Assets/Conceptual Art/) left Ella's look references.
- Ella's look (D-new-ella-look, Claude's call, Josh delegated): designed from `study-ella-character` (dark brown hair,
  hat, hidden face) at the key art's silhouette and scale. The rehearsal Ella sheets (`ella-*`) are pose and
  frame-grid references only, not hair or skin colour. The witch sheets (`witch-cast`, `witch-guard`: another
  character, no umbrella) are frame-grid and layout data only.
- Key-art crops (11 Nov): the owl bolt, the umbrella, the etched wind lines and the rock band are cut out of the key
  art as their own references (`pipeline/art/reference/keyart-crops/`, alpha-keyed, reference only), because a sprite
  cannot be scored against the full frame. `keyart-bolt` is the `owl-bolt` look, `keyart-umbrella` the `umbrella`
  look, `keyart-wind-lines` the only `wind-lines` reference; the gameplay zone (`wind-zone`) is judged against
  `bar-other-realm`'s ribbons only, and the two wind elements share no reference. `keyart-skyline` is on hold: the
  key art's band is flat black inside, and as a skyline reference it drops the skyline's detail floor so far that the
  rough Blender skyline passes; the skyline keeps `keyart` and `gothic-skyline` until the team decides.
  `study-environment` is for parallax layering only.
- Out of judging (judge false, no judge element, files kept): `wind-curl` and `umbrella-repair` (teal),
  `owl-missile` and `owl-missile-travel` (blurry), `umbrella-stance` (crude), `d-yellow-crop` (blurry), `d-wing-gust`
  (off-palette blue). The same picture is never listed twice: `tools/art_check.py` load_spec drops a listed entry
  whose bytes equal an earlier one, and `team_art.same_as` names the re-encoded copies.

##### Target frame (measured from the key art, 10 Nov)
`tools/art_judge.py scene` scores a screenshot against this; the ranges live in `references.json` `scene`.
| Element | In the key art | Target range (share of the frame) |
|---|---|---|
| Owl | wings spread, right half, centre x 0.68, 83% of the height, 64% of the width | centre x 0.55-0.90, height 0.45-0.95, width 0.25-0.90 |
| Chest clock | glowing gold inside the owl | gold share ≥ 0.0008, ≥ 60% of it inside the owl's box |
| Ella | small on the left under the striped umbrella, centre x 0.16, body about 11% of the height | centre x 0.04-0.35, height 0.04-0.30 |
| Scale | owl about 7x Ella's height | owl:Ella height ≥ 3 |
| Skyline | black jagged band along the bottom, median 10% of the height, full width | median 0.03-0.25, across ≥ 90% of the width |
| Owl bolts | rust-red needles with a crosshair ring flying left | rust share ≥ 0.0008 |
| Look | paper texture, etched wind lines, gold star wand shots, sparkle dots | art_check PASS; layout and edge similarity to the key art ≥ 0.65 |
The key art and its earlier cut pass at 1.0; a flat teal box with a small owl and no skyline fails. The ranges are
provisional until card 0.10 scores the first in-engine rebuild.

##### What the reference shows
Wide side-on frame on aged, stained sepia/taupe paper. Small black-silhouette Ella on the left,
floating under an open striped black umbrella, firing a line of small gold-white glowing shots.
A huge tattered dark owl on the right: ragged spread wings, glowing amber eyes, a gold clock face
with gears in its chest, gothic spires and a gear crown, chains with crosshair pendants. Five rust-red
needle-shaped enemy projectiles, each with a crosshair ring, fly left. Thin etched wavy wind lines cross the frame. Jagged pure-black
rock silhouette along the bottom. Faint white sparkle dots.

##### Pillars
1. **Aged paper ground.** Stained, mottled sepia field. Never flat, never white.
2. **Near-black silhouettes.** Ella, the owl and its projectiles read by shape. Interior detail is dark-on-dark only.
3. **Brand accents first, capped extras second.** Gold/amber = the player's magic and the owl's eyes and clock. Rust red = danger. The quality-bar colours (ash-blue wind flow, shot reds and yellows) appear only in their role and under their cap (Palette). No other saturated hue: no teal, green, purple, pink, no saturated blue.
4. **Etched atmosphere.** Wind lines and sparkles are decoration. They must never look like gameplay.
5. **Ella small, owl huge.** The scale contrast is the drama, but never at the cost of reading Ella and her umbrella state.

##### Gameplay readability rules (these beat style)
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

##### Eval captures
The Integrator places fixed cameras `CAM_Eval_Arena` (the whole arena) and `CAM_Eval_Stress` (the desperation cluster), plus `CAM_Eval_StyleFrame` and `CAM_Eval_Swatch`. Art review captures come from these, at 1920×1080, with `HighResShot 1920x1080`.

##### Automatic art checks and the art loop (no human approves a look)
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

##### Palette
Machine-readable palette and thresholds: `pipeline/art/style.json`, checked by `tools/art_check.py`.
INK `#171614` joins the darks (silhouette role). Capped accents (`style.json` `accents`; Josh, DECIDED 2026-11-10,
D-new-palette-accents), each allowed only in its role, inside its CIELAB hue and chroma band, and under its share of
the frame; all of them together stay at or under 10% of the pixels, so the brand palette dominates:

| Role | Colours | Hue band (CIELAB, deg) | Chroma | Max share |
|---|---|---|---|---|
| wind (WIND-01 flow ribbons) | ash blue `#555e60` (measured on the Other Realm ribbons; its label `#7P9698` is not a hex) | 190-260 | 2-12 | 6% |
| shot-red (owl shots; re-measured from the key art's bolts, D-new-owl-shot-look) | RUST `#723929`, RUST SHADOW `#5b2519`, RUST HIGH `#79331f` | 25-55 | 20-50 | 4% |
| shot-yellow (yellow shots, shot cores) | YELLOW `#ffd84a`, AMBER `#f5aa28`, YELLOW SHADOW `#94611e`, CORE `#fff5dc` | 55-100 | 8+ | 4% |

Brand hue gate: gold/amber ~55-95 and rust ~20-50 (`hue_gate`). An accent pixel outside its band, a teal or saturated
blue, and a flat fill of any colour still fail (`off_style`, `off_band`, the caps, `paper_texture`, `screen_check.py`).
**The hex values are estimated by eye and are provisional.** First task for the Art Director:
add the reference file, run `python3 tools/art_check.py --extract pipeline/art/reference/target-keyart.png`,
replace the palette with measured values, and set `palette_status` to `measured`.

##### Asset spec (prototype targets; change only on measured evidence)
| Asset | On screen at 1080p | Pivot |
|---|---|---|
| Ella + open umbrella | 80–100 px tall | Bottom center |
| Ella, closed umbrella | same body height; umbrella width ≤ 0.55× open | Bottom center |
| Wand bolt | 10–14 px core, ≤ 8 px glow | Center |
| Owl clockwork bolt (rust needle with a crosshair ring) | 28–36 px | Center (rotate with transform, not frames) |
| Owl returning arc (P2) | same core as the bolt, red trail | Center |
| WIND-01 wind zone (P0): etched upward strokes, engraved border, paper tint | the zone rectangle in `pipeline/level/encounter.json` | Bottom left |
| Owl (MVP, the one boss) | 55–70% of screen height, split into parts (body, wings, chest clock) | Per-part pivots |
| Paper and background layers | full screen | Bottom left |

Pivots: machine copy in `style.json` `unreal_import.sprite.required_pivot` (one pivot per asset across all anims, checked by `--import-report`). Width: `sprite_check.py --width-ratio`.

Authoring scale is open (D13): 2× with mipmaps (lean) or 1×.

Flipbook frame rates (machine copy: `style.json` `anims`, checked by `tools/sprite_check.py`): idle-float 8 fps (4–6 frames) · fall 12 fps (2–4) · open/close transition 24 fps
(3–4 frames; the new state's first frame shows on the same frame as the input) · attack 15 fps (3–4) ·
hit/death 12 fps · owl wing 10 fps · impact VFX 20–24 fps. Characters never above 15 fps.

##### Import settings
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

##### Provenance (hard gate)
Every asset gets a row in `pipeline/art/provenance.csv` before it merges:
asset path, author (human), origin (`hand-made` | `AI-generated` | `AI-assisted` | `third-party`),
tool + model + version, prompt, seed, input images, date, licence, attribution.
- Prompts never name living artists or copyrighted IP.
- Third-party: CC0 or CC-BY (credit in CREDITS.md) or a licence that allows our use. No licence URL, no merge.
- **Blocker before Day 1:** someone checks the jam's rules on AI art and disclosure (D14).

### `pipeline/art/style.json`

```json
{
  "palette_status": "measured",
  "palette_note": "Card 0.7, measured with: python3 tools/art_check.py --measure-palette pipeline/art/reference/target-keyart.png (each named colour re-centred on the reference pixels nearest it, within delta_e_tolerance). gold, amber-eye and spark-white cover under 0.05% of the key art, so they keep their by-eye values (see each entry's source). No art sign-off: card 0.7's gate patch (the TD human applies it) carries the values; art acceptance is the automated art gate (tools/art_check.py --gate). art_check fails while palette_status is not measured and the reference file exists.",
  "delta_e_tolerance": 14,
  "dark_l_max": 18,
  "off_style_saturation_min": 0.55,
  "texture_delta_l": 2.0,
  "texture_note": "paper_texture: share of side-by-side sampled pixel pairs (both above dark_l_max) whose L* differs by >= texture_delta_l. paper_texture_min was provisional (0.1), set from synthetic frames (red-team round 2, finding 14: a flat gray graybox passed every other gate). Day-0 card 0.7 re-sets it from the measured reference key art; the reference must pass with margin. Measured on the reference (card 0.7): paper_texture 0.7696. paper_texture_min = 0.38, half the key art (Josh, 11 Nov). Measured 11 Nov: key art 0.7696, its earlier cut 0.7181 (pass); the GDD v1.4 concept frames gameplay-01 0.2596 and gameplay-02 0.3077 sit below it (draft concepts, not the target).",
  "max_samples": 60000,
  "palette": [
    {
      "name": "paper-light",
      "role": "background",
      "hex": "#aa8f7f",
      "source": "measured: mean of the 0.0257 share of reference pixels nearest this entry (was #a89a8c, shift dE 6.51)"
    },
    {
      "name": "paper-mid",
      "role": "background",
      "hex": "#93786b",
      "source": "measured: mean of the 0.3275 share of reference pixels nearest this entry (was #8c7d70, shift dE 5.35)"
    },
    {
      "name": "paper-stain",
      "role": "background",
      "hex": "#7b6157",
      "source": "measured: mean of the 0.229 share of reference pixels nearest this entry (was #6f6157, shift dE 5.58)"
    },
    {
      "name": "etch-line",
      "role": "background",
      "hex": "#c4a999",
      "source": "measured: mean of the 0.0011 share of reference pixels nearest this entry (was #b8ab9e, shift dE 5.99)"
    },
    {
      "name": "owl-umber",
      "role": "midground",
      "hex": "#3a2c25",
      "source": "measured: mean of the 0.1415 share of reference pixels nearest this entry (was #3d2f26, shift dE 1.84)"
    },
    {
      "name": "owl-feather",
      "role": "midground",
      "hex": "#5c473e",
      "source": "measured: mean of the 0.1154 share of reference pixels nearest this entry (was #58463a, shift dE 2.38)"
    },
    {
      "name": "silhouette",
      "role": "silhouette",
      "hex": "#1d1713",
      "source": "measured: mean of the 0.1424 share of reference pixels nearest this entry (was #16110f, shift dE 3.46)"
    },
    {
      "name": "spark-white",
      "role": "accent",
      "hex": "#fff3d6",
      "source": "by eye: under 0.05% of reference pixels (0.0001), so not measurable from the key art; Rick confirms"
    },
    {
      "name": "gold",
      "role": "accent",
      "hex": "#e9b04a",
      "source": "by eye: under 0.05% of reference pixels (0.0), so not measurable from the key art; Rick confirms"
    },
    {
      "name": "amber-eye",
      "role": "accent",
      "hex": "#c8862a",
      "source": "by eye: under 0.05% of reference pixels (0.0001), so not measurable from the key art; Rick confirms"
    },
    {
      "name": "rust-red",
      "role": "accent",
      "hex": "#743422",
      "source": "measured: mean of the 0.0024 share of reference pixels nearest this entry (was #8f3a2b, shift dE 10.58)"
    },
    {
      "name": "ink",
      "role": "silhouette",
      "hex": "#171614",
      "source": "Josh, 2026-11-10 (D-new-palette-accents): INK from the quality-bar sheet (references.json vfx_spec, bar-casters) joins the darks"
    }
  ],
  "accents": {
    "_about": "Capped accents (Josh, DECIDED 2026-11-10, D-new-palette-accents; shot-red re-measured from the key art's rust bolts, Josh, DECIDED 2026-11-11, D-new-owl-shot-look): the quality-bar colours from Ricky's latest images, allowed only in their role and only up to a share of the frame, so the brand palette above still dominates. A pixel that is not near a palette colour counts as an accent of a role when it is within that role's delta_e_max of one of its colours AND its CIELAB hue and chroma fall in the role's band; it then counts as on-palette and never as off_style or off_band. Anything else (teal, saturated blue, a flat fill) is judged by the rules above as before. art_check fails a frame whose accents together pass total_share_max, or one role past its share_max.",
    "total_share_max": 0.1,
    "roles": {
      "wind": {
        "what": "the WIND-01 flow ribbons (bar-other-realm: ash-blue flowing ribbons, never a flat box)",
        "share_max": 0.06,
        "delta_e_max": 12,
        "chroma": [
          2,
          12
        ],
        "hue_bands_deg": [
          [
            190,
            260
          ]
        ],
        "colours": [
          {
            "name": "wind-ash-blue",
            "hex": "#555e60",
            "source": "measured on pipeline/art/reference/discord/20261111-0318_Ricky_other-realm.png: mean of the brightest 10% of the ribbon pixels (5477 pixels with CIELAB hue 180-300, chroma >= 2.5, L* >= 30 in x 150-1672, y 100-620; L* 39.1, C* 4.0, hue 221). The label in the image reads '#7P9698', which is not a hex; the ribbons as rendered are this colour (body mean #495052, delta E 5.8)"
          }
        ]
      },
      "shot-red": {
        "what": "the owl's shots: the key art's rust-red needle with a crosshair ring, its core, shell, trail and spill (Josh, DECIDED 2026-11-11, D-new-owl-shot-look; vfx_spec: tell, release, travel, fade). The pink chevrons of bar-casters and Ricky's red-shot sheets are not the look",
        "share_max": 0.04,
        "delta_e_max": 12,
        "chroma": [
          20,
          50
        ],
        "hue_bands_deg": [
          [
            25,
            55
          ]
        ],
        "colours": [
          {
            "name": "RUST",
            "hex": "#723929",
            "source": "measured on pipeline/art/reference/target-keyart.png, the five bolts (8065 pixels with CIELAB chroma >= 20 and hue <= 55 in x 408-928, y 222-650; chroma 20-44, hue 29-55): mean (L* 30.9, C* 31.8, hue 42)"
          },
          {
            "name": "RUST SHADOW",
            "hex": "#5b2519",
            "source": "measured on pipeline/art/reference/target-keyart.png, the five bolts (8065 pixels with CIELAB chroma >= 20 and hue <= 55 in x 408-928, y 222-650; chroma 20-44, hue 29-55): mean of the darkest 10% (L* 22.3)"
          },
          {
            "name": "RUST HIGH",
            "hex": "#79331f",
            "source": "measured on pipeline/art/reference/target-keyart.png, the five bolts (8065 pixels with CIELAB chroma >= 20 and hue <= 55 in x 408-928, y 222-650; chroma 20-44, hue 29-55): mean of the most saturated 10% (C* 39.9)"
          }
        ],
        "note": "All three are within delta_e_tolerance of the palette's rust-red (#743422), so the key-art shot pixels count as the brand rust (accent_area cap); this role catches rust variants just outside the palette, capped at share_max. Pink #ff3658 now fails off_style (D-new-owl-shot-look)"
      },
      "shot-yellow": {
        "what": "yellow shots (absorbable shots in Ricky's proposal) and every shot core",
        "share_max": 0.04,
        "delta_e_max": 12,
        "chroma": [
          8,
          120
        ],
        "hue_bands_deg": [
          [
            55,
            100
          ]
        ],
        "colours": [
          {
            "name": "YELLOW",
            "hex": "#ffd84a",
            "source": "bar-casters (Roadwarden / Sundial Casters sheet), references.json vfx_spec"
          },
          {
            "name": "AMBER",
            "hex": "#f5aa28",
            "source": "bar-casters (Roadwarden / Sundial Casters sheet), references.json vfx_spec"
          },
          {
            "name": "YELLOW SHADOW",
            "hex": "#94611e",
            "source": "bar-casters (Roadwarden / Sundial Casters sheet), references.json vfx_spec"
          },
          {
            "name": "CORE",
            "hex": "#fff5dc",
            "source": "bar-casters (Roadwarden / Sundial Casters sheet), references.json vfx_spec"
          }
        ]
      }
    }
  },
  "thresholds": {
    "on_palette_min": 0.8,
    "off_style_max": 0.02,
    "accent_area_max": 0.08,
    "dark_share_min": 0.04,
    "dark_share_max": 0.45,
    "off_band_max": 0.01,
    "paper_texture_min": 0.38
  },
  "screen_check": {
    "note": "tools/screen_check.py: no flat fills, grey placeholder boxes or debug outlines in the default build, and a 16:9 gameplay view. Areas are shares of the gameplay view.",
    "flat_tol": 2,
    "flat_area_min": 0.01,
    "grey_area_min": 0.0025,
    "grey_chroma_max": 8,
    "grey_value_min": 24,
    "grey_value_max": 232,
    "rect_fill_min": 0.9,
    "outline_area_min": 0.01,
    "outline_fill_max": 0.35,
    "outline_edge_share": 0.9,
    "bar_value_max": 12,
    "aspect": "16:9",
    "aspect_tol": 0.01
  },
  "hue_gate": {
    "chroma_min": 18,
    "allowed_hue_bands_deg": [
      [
        20,
        95
      ]
    ],
    "note": "CIELAB hue angle. Gold/amber ~55-95, rust ~20-50 (art/design review C2 M2). Re-centre on measured reference means +/-15 deg once the palette is measured."
  },
  "sprite": {
    "status": "provisional",
    "note": "Thresholds for tools/sprite_check.py, set from synthetic fixtures, not yet measured on real sprites. Measure on the first approved sprites before tightening or loosening.",
    "alpha_clear_max": 8,
    "alpha_solid_min": 247,
    "require_pow2": false,
    "pow2_note": "Open until D13. If D13 picks mipmaps, set true: Unreal gives non-power-of-two textures no mips (art-bible Import settings).",
    "halo_l_min": 60,
    "dark_l_max": 35,
    "kinds": {
      "silhouette": {
        "note": "Ella, enemies, rock, spikes: near-black shapes cut out of a transparent sheet",
        "border_visible_max": 0.0,
        "fill_min": 0.25,
        "fill_max": 0.92,
        "fringe_max": 0.25,
        "halo_max": 0.1,
        "dark_share_min": 0.6
      },
      "fx": {
        "note": "shots, glows, sparkles: soft alpha is expected",
        "border_visible_max": 0.0,
        "fill_min": 0.05,
        "fill_max": 1.0,
        "fringe_max": 1.0,
        "halo_max": 1.0,
        "dark_share_min": 0.0
      },
      "tile": {
        "note": "ground or paper tiles that fill their frame on purpose",
        "border_visible_max": 1.0,
        "fill_min": 0.0,
        "fill_max": 1.0,
        "fringe_max": 0.25,
        "halo_max": 1.0,
        "dark_share_min": 0.0,
        "seam_delta_e_max": 6.0,
        "seam_note": "Mean CIELAB delta E76 between the left and right edge columns (and top and bottom with sidecar \"tile_axes\": \"xy\"). Provisional, set from synthetic tiles."
      }
    },
    "pivot_drift_max_px": 2,
    "pivot_feet_rows": 8,
    "pivot_drift_note": "Feet point = bottom-center of the lowest pivot_feet_rows opaque rows of each frame (not the whole opaque box, so an umbrella that opens to one side does not move it); max minus min across frames. A sidecar may set \"feet_rows\" for one sheet. Checked on every silhouette sheet whose sidecar has \"anim\" or \"loop\": true, loops and one-shots alike (Open, Close, Attack, Hit, Death). A sidecar may raise the limit for one sheet with \"pivot_drift_max_px\" plus a non-empty \"pivot_drift_reason\". Limit proposed in D-new-port-13; pivot_feet_rows 8 proposed in D-new-art-drift.",
    "sidecar_exempt_dirs": [
      "Raw",
      "Reference"
    ],
    "sidecar_note": "sprite_check --scan fails a PNG with no .sprite.json sidecar unless one of its folders is named in sidecar_exempt_dirs (case-insensitive). Proposed default; see decisions_for_josh.",
    "umbrella_width_ratio_min": 1.8,
    "umbrella_width_note": "sprite_check --width-ratio OPEN CLOSED: narrowest open frame's opaque box width / widest closed frame's width must be >= this (art bible: open >= 1.8x closed, closed <= 0.55x open)."
  },
  "anims": {
    "note": "Machine copy of the art-bible flipbook table. Key = the <Anim> part of FB_<Asset>_<Anim>. fps is a number or [min, max]; frames is [min, max] or null (not set by the art bible). sprite_check checks a sidecar's \"anim\" against it; the editor dump check (--import-report) checks FramesPerSecond and keyframe count.",
    "IdleFloat": {
      "fps": 8,
      "frames": [
        4,
        6
      ]
    },
    "Fall": {
      "fps": 12,
      "frames": [
        2,
        4
      ]
    },
    "Open": {
      "fps": 24,
      "frames": [
        3,
        4
      ]
    },
    "Close": {
      "fps": 24,
      "frames": [
        3,
        4
      ]
    },
    "Attack": {
      "fps": 15,
      "frames": [
        3,
        4
      ]
    },
    "Hit": {
      "fps": 12,
      "frames": null
    },
    "Death": {
      "fps": 12,
      "frames": null
    },
    "Flap": {
      "fps": 10,
      "frames": null
    },
    "Impact": {
      "fps": [
        20,
        24
      ],
      "frames": null
    }
  },
  "naming": {
    "note": "Asset names under Content/UmbrellaElla/Art/**, checked by sprite_check --names. Frames: SPR_<Asset>_<Anim>_<NN>, 2 digits from 00 (Extract Sprites, Grid mode, Naming Template SPR_<Asset>_<Anim>_{0}) [VERIFY the template token on 5.8.4]. Proposed; see decisions_for_josh.",
    "asset_regex": "^(T|SPR|FB)_[A-Z][A-Za-z0-9]*_[A-Z][A-Za-z0-9]*(_\\d{2})?(_PH)?$",
    "banned_regex": "(?i)_(v\\d+|final|new)(?=_|$)",
    "extensions": [
      ".uasset"
    ]
  },
  "swatch": {
    "note": "Engine colour round-trip check (art_check --swatch). make_art_calibration.py --swatch writes the source sprite: one cell per palette entry, in style.json order, cols per row. CAM_Eval_Swatch frames it; rect is where it lands in the 1920x1080 capture (null = the whole capture). [VERIFY rect once the camera exists.]",
    "cols": 6,
    "cell_px": 64,
    "rect": null,
    "inset": 0.25,
    "delta_e_max": 3.0
  },
  "unreal_import": {
    "status": "proposed",
    "note": "Rules for the editor-side asset dump checked by sprite_check --import-report, the Config keys checked by sprite_check --config, and the .uproject plugins checked by --uproject. Property and key names are from memory of Paper2D, not read from 5.8.4. [VERIFY each name in card 0.4a.] status goes to 'verified' only when every name is pasted from 5.8.4; tests/test_sprite_check.py fails once card 0.4a is done and this is still 'proposed'. Detail: pipeline/art/import-rules.md.",
    "texture": {
      "filter_banned": [
        "TF_Nearest"
      ],
      "srgb": true,
      "compression": "TC_EditorIcon",
      "never_stream": true,
      "lod_group_banned": [
        "TEXTUREGROUP_Pixels2D"
      ],
      "lod_group": null,
      "lod_group_note": "null until D-new-art-texgroup (proposed TEXTUREGROUP_UI) [VERIFY the group's mip and filter settings on 5.8.4 against D13]. null: any group except lod_group_banned passes, and --gate fails. Set: every texture and Config DefaultSpriteTextureGroup must equal it, so World (mips, LOD bias) no longer passes.",
      "mips": null,
      "mips_note": "null until D13. D13 = 2x with mips: MipGenSettings must not be TMGS_NoMipmaps and the texture must be power-of-two. D13 = 1x: TMGS_NoMipmaps. sprite_check --import-report --gate fails while this is null, and tests/test_sprite_check.py fails once L_StyleFrame.umap exists (card 0.10) and this is still null. Cutoff and default requested in docs/decisions.md (proposed: before 0.10, default none)."
    },
    "sprite": {
      "materials_by_kind": {
        "silhouette": [
          "/Paper2D/MaskedUnlitSpriteMaterial.MaskedUnlitSpriteMaterial"
        ],
        "tile": [
          "/Paper2D/MaskedUnlitSpriteMaterial.MaskedUnlitSpriteMaterial"
        ],
        "fx": [
          "/Paper2D/MaskedUnlitSpriteMaterial.MaskedUnlitSpriteMaterial",
          "/Paper2D/TranslucentUnlitSpriteMaterial.TranslucentUnlitSpriteMaterial"
        ]
      },
      "kind_prefixes": {
        "SPR_FX": "fx",
        "SPR_Paper": "tile",
        "SPR_Rock": "tile"
      },
      "kind_note": "Kind of a sprite: the dump's \"kind\" field if present (copied from the source sheet's sidecar), else the first matching kind_prefixes entry, else silhouette. Only fx may use Translucent (art bible: translucent only for glow). Prefixes SPR_FX*, SPR_Paper*, SPR_Rock* are proposed names (decisions_for_josh).",
      "collision": "None",
      "atlas_group": null,
      "pivot_modes": [
        "Bottom_Center",
        "Center_Center",
        "Bottom_Left",
        "Custom"
      ],
      "required_pivot": {
        "SPR_Ella_": "Bottom_Center",
        "SPR_Spikes_": "Bottom_Center",
        "SPR_Shot_": "Center_Center",
        "SPR_Cross_": "Center_Center",
        "SPR_Flyer_": "Center_Center",
        "SPR_Rock_": "Bottom_Left"
      },
      "pivot_note": "required_pivot: one pivot mode per asset prefix, from the art-bible asset table. Every sprite of one SPR_<Asset>_ shares one pivot across all its anims, so the umbrella Open/Close switch cannot jump. Prefixes other than SPR_Ella_ and SPR_Spikes_ are proposed asset names (decisions_for_josh).",
      "full_rect_geometry": "SourceBoundingBox",
      "full_rect_max_px": 256,
      "required_sockets": {
        "SPR_Ella_": [
          "Muzzle"
        ]
      },
      "sockets_note": "Socket name Muzzle is a proposal (decisions_for_josh). Dump sockets are {\"name\", \"location\": [x, y]} (the socket's LocalTransform X and Z, in the sprite's pixel space [VERIFY on 5.8.4]). One socket may move at most socket_drift_max_px across the frames of one SPR_<Asset>_<Anim> set (proposed 2, D-new-art-drift).",
      "socket_drift_max_px": 2
    },
    "pixels_per_unit": null,
    "pixels_per_unit_note": "null until card 0.10 confirms it (D-new-port-10). null: every sprite in the dump must share one pixels_per_unit. Set: every sprite and Config DefaultPixelsPerUnrealUnit must equal it.",
    "flipbook": {
      "frames_total_max": 60,
      "note": "frames_total_max: jam-brief content cap, flipbook frames 60 in total, counted as unique sprites across all FB_ keyframes. Keyframe sprites must be SPR_<Asset>_<Anim>_NN of the flipbook's own anim, in ascending NN, with no sprite twice in a row (use frame_run for a hold). An anims row with \"order\": \"any\" allows other orders, e.g. ping-pong (none set; decisions_for_josh)."
    },
    "uproject": {
      "required_plugins": [
        "Paper2D"
      ],
      "banned_plugins": [
        "PaperZD"
      ],
      "note": "sprite_check --uproject UmbrellaElla.uproject: Plugins must list each required plugin with Enabled true, and no banned one (unreal-rules.md). [VERIFY plugin names on 5.8.4]"
    },
    "config": {
      "DefaultEditor.ini": {
        "[/Script/Paper2DEditor.PaperImporterSettings]": {
          "DefaultSpriteTextureGroup": {
            "present": true,
            "not": [
              "TEXTUREGROUP_Pixels2D"
            ],
            "equals_style": "texture.lod_group"
          },
          "bOverrideTextureCompression": {
            "equals": "True"
          },
          "DefaultSpriteTextureCompression": {
            "equals": "TC_EditorIcon"
          },
          "UnlitDefaultMaskedMaterialName": {
            "equals": "/Paper2D/MaskedUnlitSpriteMaterial.MaskedUnlitSpriteMaterial"
          },
          "UnlitDefaultTranslucentMaterialName": {
            "equals": "/Paper2D/TranslucentUnlitSpriteMaterial.TranslucentUnlitSpriteMaterial"
          },
          "bPickBestMaterialWhenCreatingSprites": {
            "present": true,
            "note": "Open (decision row D-new-art-pickbest requested, proposed False: force the masked default; materials_by_kind already covers translucent fx). Once decided, replace present with equals."
          },
          "DefaultPixelsPerUnrealUnit": {
            "present": true,
            "equals_style": "pixels_per_unit"
          }
        }
      },
      "DefaultEngine.ini": {
        "[/Script/Paper2D.PaperRuntimeSettings]": {
          "bResizeSpriteDataToMatchTextures": {
            "equals": "True"
          },
          "bEnableSpriteAtlasGroups": {
            "equals": "False"
          }
        }
      }
    }
  }
}
```

### `pipeline/art/references.json`

```json
{
 "version": 2,
 "_about": "The team's art references: the one list every art tool and the Art Director agent compares against (tools/art_check.py --references and --gate, tools/art_judge.py, tools/art_ref_check.py, tools/art_loop.py, tools/art_judge_prompt.md, tools/assetgen.py practice stand-ins, tools/submission_check.py assets). Reference only, never shipped: GDD 1.3 7C and its Provenance line ('Do not copy into the jam entry'); Official Rules 7(h) (game content is made during the Contest Period); a shipped byte copy of any file here fails submission_check.py assets. Schema (one list, `references`): id; path (repo-relative: under pipeline/art/reference/, or the team's own art folder for a team-art entry; null for kind described); kind (image | data | described); role (list, every value a key of `roles`); what; cards (Day-0 cards and MVP items judged against it: a Day-0 card listed on an image runs tools/art_ref_check.py, art_judge.py coverage); consulted_by (other cards and checks that read it without an art_ref_check verdict; art_check --references lists them with cards); judge (true = the blind X/Y judge sees it as style context); required (art_check --references and --gate fail while it is missing; false on an image = optional: a checkout without the file leaves the entry out of the list and out of every judge element, so the team-art entries work in repos that have only some of the files); judge_exempt (why no judge element uses it); tier (top = quality bar); cell (frame size of a sheet); description (kind described: the written target); note; origin. Kind data with role layout = the frame grids, pivots and fps (the source for sprite sidecars). elements and scene = what tools/art_judge.py scores; quality_bar = the top tier; gdd_embedded = images the current GDD embeds join the list automatically; team_art = every image under Assets/ and Mockups/ joins the list automatically (folders named obsolete skipped, already-listed paths and byte copies skipped), look only, never shipped. Practice repos only (.pipeline-practice): `tools/assetgen.py image --provider reference` (and any image step with no key) places the best-matching picture here by role as a stand-in, provenance `source=reference (practice)`; on the team repo assetgen refuses it and submission_check.py assets fails such a row.",
 "note": "Every reference image the art is judged against: the curated set in this repo under pipeline/art/reference/ (Git LFS; `origin` says where each came from), plus the team's own art folders (Assets/, Mockups/: the described studies below and, through team_art, any image the team adds). References only, never shipped or imported (Official Rules §7(h): no game content before Nov 12; jam art is generated during the jam). tools/art_judge.py and tools/art_ref_check.py read this file: `scene` scores build screenshots, `elements` score generated art; each art card's own references are the ones listing it in `cards`. The evidence line carries refs=<first 12 hex of this file's sha256>, so a PASS made against an older or smaller set is refused (tools/check_pr.py rule artref). GDD SH1.0 (12 Nov): these pictures are judging targets for the art loop and art_ref_check.py, never generation inputs (ART-03, BG-02); card numbers follow the SH1.0 MVP list and the art cards 0.37-0.41.",
 "roles": {
  "composition target": "the whole-frame look a capture is judged against (layout, value structure, mood)",
  "character poses": "Ella and umbrella poses and states (UP_OPEN, ATTACK_DESCENT, SHIELD_DESCENT, free fall)",
  "owl": "the clockwork owl: body, chest clock, wing damage rows, its attack patterns",
  "effects": "projectiles, impacts, wind, repair bursts",
  "palette": "style.json palette and paper texture were measured from it",
  "scale": "gameplay size and proportions at 1080p, background layer sizes",
  "quality bar": "the top tier for rendering quality and finish: every art-loop round is also judged blind against one (quality_bar)",
  "pattern": "attack-pattern diagrams: shapes and timing, not art style",
  "layout": "frame grids, pivots and fps: the source for sprite sidecars (.sprite.json)",
  "menu style bar": "a written target for menu screens and transitions (no image)",
  "team art": "a picture the team added to its art folders (Assets/, Mockups/; team_art): look only, gameplay comes from the GDD",
  "menu screen": "the title or another menu screen a menu card builds to (layout, title lockup, menu placement, mood)",
  "motion": "how an attack or a mechanism moves (poses, timing, parts): never the look (D-new-owl-look)"
 },
 "references": [
  {
   "id": "keyart",
   "path": "pipeline/art/reference/target-keyart.png",
   "kind": "image",
   "role": [
    "composition target",
    "palette"
   ],
   "what": "The composition target (team, 10 Nov): the game must look like this frame. Owl large on the right with wings spread and the chest clock glowing gold; Ella small on the left under a striped umbrella; black jagged skyline along the bottom; etched wavy wind lines; rust-red cross bolts; gold star wand shots; textured paper; sparkle dots. Also the palette source (style.json)",
   "cards": [
    "0.10",
    "MVP 15",
    "0.21b",
    "0.37",
    "0.38",
    "0.39",
    "0.40",
    "0.41"
   ],
   "consulted_by": [
    "0.7",
    "0.10a",
    "0.22",
    "every art PR (art_check.py --gate)"
   ],
   "judge": true,
   "required": true,
   "note": "The style target. style.json palette and paper_texture_min were measured from it (card 0.7). The X/Y judge's comparator (pair <capture>:target-keyart).",
   "origin": "this repo"
  },
  {
   "id": "keyart-bolt",
   "path": "pipeline/art/reference/keyart-crops/owl-bolt.png",
   "kind": "image",
   "role": [
    "effects"
   ],
   "what": "The owl's shot as the key art draws it: a rust-red needle with a crosshair ring, faces left (D-new-owl-shot-look). Key-art box x576-752 y407-446; opaque where CIELAB chroma >= 18, hue 20-65, L* < 55, grown 1 px",
   "cards": [
    "0.10b",
    "MVP 7"
   ],
   "judge": true,
   "required": true,
   "origin": "crop of the team key art (pipeline/art/reference/target-keyart.png, 11 Nov), keyed to an alpha mask; reference only"
  },
  {
   "id": "keyart-umbrella",
   "path": "pipeline/art/reference/keyart-crops/umbrella.png",
   "kind": "image",
   "role": [
    "character poses"
   ],
   "what": "The umbrella as the key art draws it: open, black with light stripes, shaft down (D-new-umbrella-look). Key-art box x176-324 y347-440; opaque where L* < 32 (largest piece), canopy rows filled across so the light stripes stay",
   "cards": [
    "MVP 4",
    "MVP 12"
   ],
   "judge": true,
   "required": true,
   "origin": "crop of the team key art (pipeline/art/reference/target-keyart.png, 11 Nov), keyed to an alpha mask; reference only"
  },
  {
   "id": "keyart-wind-lines",
   "path": "pipeline/art/reference/keyart-crops/wind-lines.png",
   "kind": "image",
   "role": [
    "effects"
   ],
   "what": "The key art's decorative etched wind lines: thin wavy parallel strokes (decoration, never gameplay). Key-art box x150-557 y68-196; opaque where L* < 36 in long thin strokes (paper grain dropped)",
   "cards": [
    "0.10c",
    "MVP 11"
   ],
   "judge": true,
   "required": true,
   "origin": "crop of the team key art (pipeline/art/reference/target-keyart.png, 11 Nov), keyed to an alpha mask; reference only"
  },
  {
   "id": "keyart-skyline",
   "path": "pipeline/art/reference/keyart-crops/skyline.png",
   "kind": "image",
   "role": [
    "scale"
   ],
   "what": "The key art's black jagged rock band along the bottom. Key-art box x0-1188 y732-940 (left of the owl); opaque where L* < 22 (largest piece: the rocks, not the wind lines)",
   "cards": [
    "0.10c",
    "MVP 12"
   ],
   "judge": false,
   "required": true,
   "origin": "crop of the team key art (pipeline/art/reference/target-keyart.png, 11 Nov), keyed to an alpha mask; reference only",
   "judge_exempt": "on hold (11 Nov): the key art's rock band is flat black inside (interior detail 0.089). As a skyline ref it moves skyline to score_min 0.68 / detail_min 0.069 (from 0.527 / 0.143) and the rough Blender skyline (tests/fixtures/art/crude/skyline_crude.png, detail 0.11) then PASSES at 0.748. Until the team picks how the skyline is judged, skyline keeps keyart and gothic-skyline"
  },
  {
   "id": "original-picture",
   "path": "pipeline/art/reference/Mockups/originalPicture.png",
   "kind": "image",
   "role": [
    "composition target"
   ],
   "what": "Earlier cut of the key art, same composition; style and character source of the rehearsal sprites",
   "cards": [
    "0.10",
    "0.21b"
   ],
   "consulted_by": [
    "0.22"
   ],
   "judge": true,
   "required": true,
   "note": "Earlier cut of the key art, same composition; the style and character source for the rehearsal sprites.",
   "origin": "Mockups/originalPicture.png (GameJam2026 main)"
  },
  {
   "id": "gameplay-01",
   "path": "pipeline/art/reference/v1.4/gameplay-01.png",
   "kind": "image",
   "role": [
    "composition target",
    "scale"
   ],
   "what": "Gameplay mood: Ella rises on the left while the clockwork owl hangs a mechanism above a lakeside town. Composition and scale only: its riveted metal owl is not the owl's look (D-new-owl-look)",
   "cards": [
    "0.10",
    "MVP 15"
   ],
   "consulted_by": [
    "0.22"
   ],
   "judge": true,
   "required": true,
   "note": "GDD v1.4 draft concept 1: Ella rises on the left while the owl hangs a mechanism above a lakeside town (scale, palette, silhouette). A copy is in this repo (v1.4/); gdd_embedded also picks up the GDD's own copy when that GDD is current.",
   "origin": "scratch/gdd/v1.4/art-references/gameplay-01.png (v1.4 draft (local, not in a repo))"
  },
  {
   "id": "gameplay-02",
   "path": "pipeline/art/reference/v1.4/gameplay-02.png",
   "kind": "image",
   "role": [
    "composition target",
    "owl",
    "scale"
   ],
   "what": "Gameplay scale: the owl with its chest clock fires a red volley toward Ella. Composition and scale only: its riveted metal owl is not the owl's look (D-new-owl-look)",
   "cards": [
    "0.10",
    "MVP 5"
   ],
   "consulted_by": [
    "0.22"
   ],
   "judge": true,
   "required": true,
   "note": "GDD v1.4 draft concept 2: the owl with its chest clock fires a red volley toward Ella (clock, direction of fire). A copy is in this repo (v1.4/); gdd_embedded also picks up the GDD's own copy when that GDD is current.",
   "origin": "scratch/gdd/v1.4/art-references/gameplay-02.png (v1.4 draft (local, not in a repo))"
  },
  {
   "id": "missile-patterns",
   "path": "pipeline/art/reference/Mockups/missile-pattern-reference.png",
   "kind": "image",
   "role": [
    "owl",
    "pattern"
   ],
   "what": "Ten owl missile-pattern diagrams (straight, aimed, fans, lanes, gap wall, arcs, wave, spiral). Not art style",
   "cards": [
    "MVP 5"
   ],
   "consulted_by": [
    "0.8b"
   ],
   "judge": false,
   "required": true,
   "judge_exempt": "pattern diagrams, not art: pipeline/level/encounter.md patterns are checked by tools/encounter_check.py, not by a look",
   "note": "Ten owl missile-pattern diagrams (straight, aimed, fans, lanes, gap wall, arcs, wave, spiral). Pattern shapes, not art style.",
   "origin": "Mockups/missile-pattern-reference.png (GameJam2026 main)"
  },
  {
   "id": "ella-rising",
   "path": "pipeline/art/reference/Rehearsal/Ella/Ella-Rising-02.png",
   "kind": "image",
   "role": [
    "character poses",
    "scale"
   ],
   "what": "Rising, umbrella open overhead, 6 poses in 3 x 2: UP_OPEN. Pose and frame-grid reference only, not hair or skin colour (D-new-ella-look)",
   "cards": [
    "0.10b",
    "MVP 15",
    "0.38"
   ],
   "consulted_by": [
    "0.28",
    "MVP 2",
    "MVP 3"
   ],
   "judge": true,
   "required": true,
   "cell": [
    512,
    512
   ],
   "note": "Rising: umbrella open overhead, 6 poses in 3 x 2. Matches UP_OPEN.",
   "origin": "Rehearsal/Art/Sprites/Ella/Rising/Ella-Rising-02.png (GameJam2026 main)"
  },
  {
   "id": "ella-shooting",
   "path": "pipeline/art/reference/Rehearsal/Ella/Ella-Shooting-03.png",
   "kind": "image",
   "role": [
    "character poses",
    "scale"
   ],
   "what": "Shooting, umbrella level like a lance, 6 poses in 3 x 2: ATTACK_DESCENT. Pose and frame-grid reference only, not hair or skin colour (D-new-ella-look)",
   "cards": [
    "0.10b",
    "MVP 15",
    "0.38"
   ],
   "consulted_by": [
    "0.28",
    "MVP 9"
   ],
   "judge": true,
   "required": true,
   "cell": [
    512,
    512
   ],
   "note": "Shooting: umbrella held level like a lance, 6 poses in 3 x 2. Matches ATTACK_DESCENT.",
   "origin": "Rehearsal/Art/Sprites/Ella/Shooting/Ella-Shooting-03.png (GameJam2026 main)"
  },
  {
   "id": "ella-absorbing",
   "path": "pipeline/art/reference/Rehearsal/Ella/Ella-Absorbing-04.png",
   "kind": "image",
   "role": [
    "character poses",
    "scale"
   ],
   "what": "Absorbing, canopy turned forward as a shield, 6 poses in 3 x 2: SHIELD_DESCENT. Pose and frame-grid reference only, not hair or skin colour (D-new-ella-look)",
   "cards": [
    "MVP 15",
    "0.38"
   ],
   "consulted_by": [
    "0.10b",
    "0.28",
    "MVP 10"
   ],
   "judge": true,
   "required": true,
   "cell": [
    512,
    512
   ],
   "note": "Absorbing: canopy turned forward as a shield, 6 poses in 3 x 2. Matches SHIELD_DESCENT.",
   "origin": "Rehearsal/Art/Sprites/Ella/Absorbing/Ella-Absorbing-04.png (GameJam2026 main)"
  },
  {
   "id": "ella-freefall",
   "path": "pipeline/art/reference/Rehearsal/Ella/Ella-FreeFall-03.png",
   "kind": "image",
   "role": [
    "character poses",
    "scale"
   ],
   "what": "Free fall, umbrella closed under her, 6 poses in 3 x 2: the closed silhouette. Pose and frame-grid reference only, not hair or skin colour (D-new-ella-look)",
   "cards": [
    "0.10b",
    "MVP 15",
    "0.38"
   ],
   "consulted_by": [
    "0.28",
    "MVP 2"
   ],
   "judge": true,
   "required": true,
   "cell": [
    512,
    512
   ],
   "note": "Free fall: umbrella closed under her, 6 poses in 3 x 2.",
   "origin": "Rehearsal/Art/Sprites/Ella/FreeFall/Ella-FreeFall-03.png (GameJam2026 main)"
  },
  {
   "id": "witch-cast",
   "path": "pipeline/art/reference/Test_Assets/CHR_Witch_Cast.png",
   "kind": "image",
   "role": [
    "character poses"
   ],
   "what": "Witch cast, 6 x 2 cells of 432 x 352, 14 fps, one shot; row 0 lift, row 1 guard fall; fires on column 3",
   "cards": [
    "MVP 3",
    "MVP 15"
   ],
   "consulted_by": [
    "0.10b",
    "0.28"
   ],
   "judge": false,
   "required": true,
   "cell": [
    432,
    352
   ],
   "note": "Witch cast: 6 x 2 cells of 432 x 352, 14 fps, one shot; row 0 lift, row 1 guard fall; fires on column 3.",
   "origin": "Test_Assets/CHR_Witch_Cast.png (GameJam2026 main)",
   "judge_exempt": "a different character with no umbrella; kept as frame-grid and layout data only"
  },
  {
   "id": "witch-guard",
   "path": "pipeline/art/reference/Test_Assets/CHR_Witch_Guard_Transition.png",
   "kind": "image",
   "role": [
    "character poses"
   ],
   "what": "Lift-to-guard turn, 5 x 1 cells of 432 x 352, 14 fps",
   "cards": [
    "MVP 4",
    "MVP 15"
   ],
   "consulted_by": [
    "0.10b"
   ],
   "judge": false,
   "required": true,
   "cell": [
    432,
    352
   ],
   "note": "Lift-to-guard turn: 5 x 1 cells of 432 x 352, 14 fps; backward for guard to lift.",
   "origin": "Test_Assets/CHR_Witch_Guard_Transition.png (GameJam2026 main)",
   "judge_exempt": "a different character with no umbrella; kept as frame-grid and layout data only"
  },
  {
   "id": "umbrella-stance",
   "path": "pipeline/art/reference/Test_Assets/PROP_Umbrella_Stance_Damage.png",
   "kind": "image",
   "role": [
    "character poses"
   ],
   "what": "Umbrella, 5 x 5 cells of 368 x 352; columns overhead to front guard, rows intact to torn; grip pivot (126, 223)",
   "cards": [
    "MVP 4",
    "MVP 15"
   ],
   "consulted_by": [
    "0.10b",
    "0.28",
    "MVP 10"
   ],
   "judge": false,
   "required": true,
   "cell": [
    368,
    352
   ],
   "note": "Umbrella: 5 x 5 cells of 368 x 352; columns overhead to front guard, rows intact to torn; grip pivot (126, 223).",
   "origin": "Test_Assets/PROP_Umbrella_Stance_Damage.png (GameJam2026 main)",
   "judge_exempt": "crude; the umbrella's look is keyart-umbrella (D-new-umbrella-look); kept for its frame grid and damage rows only"
  },
  {
   "id": "owl-flap",
   "path": "pipeline/art/reference/Test_Assets/CHR_Owl_Flap_Damage.png",
   "kind": "image",
   "role": [
    "owl",
    "scale"
   ],
   "what": "Owl flap loop, 6 x 5 cells of 640 x 512, 10 fps, faces left; row 0 full, rows 1-4 torn. The owl's look (D-new-owl-look): the key-art organic owl",
   "cards": [
    "0.10b",
    "MVP 5",
    "MVP 15"
   ],
   "consulted_by": [
    "0.28"
   ],
   "judge": true,
   "required": true,
   "cell": [
    640,
    512
   ],
   "note": "Owl flap loop: 6 x 5 cells of 640 x 512, 10 fps, faces left; row 0 full health, rows 1-4 tear wings and tail.",
   "origin": "Test_Assets/CHR_Owl_Flap_Damage.png (GameJam2026 main)"
  },
  {
   "id": "owl-missile",
   "path": "pipeline/art/reference/Test_Assets/FX_Owl_Missile.png",
   "kind": "image",
   "role": [
    "effects",
    "scale"
   ],
   "what": "Static owl missile, one 160 x 80 frame, faces left",
   "cards": [
    "0.10b",
    "MVP 5"
   ],
   "consulted_by": [
    "0.28"
   ],
   "judge": false,
   "required": true,
   "note": "Static owl missile, one 160 x 80 frame, faces left.",
   "origin": "Test_Assets/FX_Owl_Missile.png (GameJam2026 main)",
   "judge_exempt": "blurry; the shot's look is keyart-bolt (D-new-owl-shot-look); kept for its frame size only"
  },
  {
   "id": "owl-missile-travel",
   "path": "pipeline/art/reference/Test_Assets/FX_Owl_Missile_Travel.png",
   "kind": "image",
   "role": [
    "effects"
   ],
   "what": "Owl missile in flight, 6 x 1 cells of 160 x 80, 16 fps loop",
   "cards": [
    "MVP 5"
   ],
   "judge": false,
   "required": true,
   "cell": [
    160,
    80
   ],
   "note": "Owl missile in flight: 6 x 1 cells of 160 x 80, 16 fps loop, faces left.",
   "origin": "Test_Assets/FX_Owl_Missile_Travel.png (GameJam2026 main)",
   "judge_exempt": "blurry; the shot's look is keyart-bolt (D-new-owl-shot-look); kept for its frame grid only"
  },
  {
   "id": "owl-missile-hit",
   "path": "pipeline/art/reference/Test_Assets/FX_Owl_Missile_Hit.png",
   "kind": "image",
   "role": [
    "effects"
   ],
   "what": "Missile impact, 7 x 1 cells of 128 x 128, 20 fps, once",
   "cards": [
    "MVP 5"
   ],
   "consulted_by": [
    "MVP 10"
   ],
   "judge": true,
   "required": true,
   "cell": [
    128,
    128
   ],
   "note": "Missile impact: 7 x 1 cells of 128 x 128, 20 fps, plays once.",
   "origin": "Test_Assets/FX_Owl_Missile_Hit.png (GameJam2026 main)"
  },
  {
   "id": "wand-star",
   "path": "pipeline/art/reference/Test_Assets/FX_Wand_Star_Travel.png",
   "kind": "image",
   "role": [
    "effects",
    "scale"
   ],
   "what": "Wand shot, 6 x 1 cells of 128 x 64, 16 fps loop, faces right (gold star)",
   "cards": [
    "0.10c",
    "MVP 3"
   ],
   "judge": true,
   "required": true,
   "cell": [
    128,
    64
   ],
   "note": "Wand shot: 6 x 1 cells of 128 x 64, 16 fps loop, faces right.",
   "origin": "Test_Assets/FX_Wand_Star_Travel.png (GameJam2026 main)"
  },
  {
   "id": "umbrella-repair",
   "path": "pipeline/art/reference/Test_Assets/FX_Umbrella_Repair.png",
   "kind": "image",
   "role": [
    "effects"
   ],
   "what": "Repair burst at the canopy, 7 x 1 cells of 128 x 128, 18 fps, once (shield heal)",
   "cards": [
    "MVP 4"
   ],
   "consulted_by": [
    "0.14b"
   ],
   "judge": false,
   "required": true,
   "cell": [
    128,
    128
   ],
   "note": "Repair burst at the canopy: 7 x 1 cells of 128 x 128, 18 fps, plays once.",
   "origin": "Test_Assets/FX_Umbrella_Repair.png (GameJam2026 main)",
   "judge_exempt": "teal, a banned hue (art bible pillar 3); kept for its frame grid only"
  },
  {
   "id": "wind-curl",
   "path": "pipeline/art/reference/Test_Assets/FX_Wind_Curl.png",
   "kind": "image",
   "role": [
    "effects"
   ],
   "what": "Wind curl, 8 x 1 cells of 144 x 112, 12 fps loop: the etched wind stroke for decorative lines and the WIND-01 zone",
   "cards": [
    "0.10c",
    "MVP 2"
   ],
   "consulted_by": [
    "0.14b"
   ],
   "judge": false,
   "required": true,
   "cell": [
    144,
    112
   ],
   "note": "Wind curl: 8 x 1 cells of 144 x 112, 12 fps loop.",
   "origin": "Test_Assets/FX_Wind_Curl.png (GameJam2026 main)",
   "judge_exempt": "teal, a banned hue (art bible pillar 3); the wind lines' look is keyart-wind-lines; kept for its frame grid only"
  },
  {
   "id": "gothic-skyline",
   "path": "pipeline/art/reference/Test_Assets/ENV_GothicSkyline_Tile.png",
   "kind": "image",
   "role": [
    "scale"
   ],
   "what": "Transparent near skyline tile 3200 x 720, bottom-aligned, scrolls faster",
   "cards": [
    "0.10c",
    "MVP 15"
   ],
   "judge": true,
   "required": true,
   "cell": [
    800,
    720
   ],
   "note": "Transparent near skyline, 3200 x 720; repeats along X, aligned to the bottom of the view, scrolls faster.",
   "origin": "Test_Assets/ENV_GothicSkyline_Tile.png (GameJam2026 main)"
  },
  {
   "id": "star-paper",
   "path": "pipeline/art/reference/Test_Assets/SKY_StarPaper_Tile.png",
   "kind": "image",
   "role": [
    "scale",
    "palette"
   ],
   "what": "Far sky and paper tile 3200 x 1080, scrolls slower; the paper texture",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "judge": true,
   "required": true,
   "cell": [
    1080,
    1080
   ],
   "note": "Far sky layer, 3200 x 1080; repeats along X, scrolls slower than the skyline.",
   "origin": "Test_Assets/SKY_StarPaper_Tile.png (GameJam2026 main)"
  },
  {
   "id": "sprite-layout",
   "path": "pipeline/art/reference/Test_Assets/SpriteLayout.json",
   "kind": "data",
   "role": [
    "layout"
   ],
   "what": "Frame size, grid, pivot, fps, row labels and facing of each Test_Assets sheet: the sidecar numbers to copy (tools/sprite_check.py)",
   "cards": [
    "0.10b",
    "0.10c"
   ],
   "consulted_by": [
    "0.28",
    "every sprite sheet (.sprite.json sidecar)"
   ],
   "judge": false,
   "required": true,
   "judge_exempt": "data, not an image: its grids and pivots go into the .sprite.json sidecars that sprite_check.py checks",
   "note": "Frame sizes, grid, pivots, fps, grip_px and wand_tip_px per sheet. GDD 1.3 7A: illustrative; the final asset manifest is the authority.",
   "origin": "Test_Assets/SpriteLayout.json (GameJam2026 main)"
  },
  {
   "id": "asset-notes",
   "path": "pipeline/art/reference/Test_Assets/Asset Notes.md",
   "kind": "data",
   "role": [
    "layout"
   ],
   "what": "Sheet layouts, playback, the umbrella grip and wand-tip rules, and the provenance of the rehearsal art",
   "cards": [
    "0.10b"
   ],
   "judge": false,
   "required": true,
   "judge_exempt": "notes, not an image: the sheet layouts beside SpriteLayout.json",
   "note": "Sheet layouts, playback and provenance of the rehearsal art (generated and reference-derived).",
   "origin": "Test_Assets/Asset Notes.md (GameJam2026 main)"
  },
  {
   "id": "d-red-shots",
   "path": "pipeline/art/reference/discord/20261110-0258_Ricky_1.png",
   "kind": "image",
   "role": [
    "effects",
    "motion"
   ],
   "what": "Look only: Keeper of Time: red (damaging) shots concept sheet",
   "cards": [
    "0.10b",
    "MVP 5"
   ],
   "judge": false,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov",
   "judge_exempt": "the riveted metal owl (Josh, DECIDED 2026-11-11, D-new-owl-look): kept for how the attacks and mechanisms move, never for the owl's look; its pink chevron shots are not the shot look either (D-new-owl-shot-look: the key art's rust-red needle with a crosshair ring)"
  },
  {
   "id": "d-yellow-shots",
   "path": "pipeline/art/reference/discord/20261110-0328_Ricky_1.png",
   "kind": "image",
   "role": [
    "effects"
   ],
   "what": "Look only: Yellow (absorbable) shots sheet with Ella's umbrella capture and lit movement modes. Absorbable yellow shots are not in GDD 1.3 (the shield catches owl bolts): a design proposal for Richard",
   "cards": [
    "MVP 4"
   ],
   "judge": true,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov"
  },
  {
   "id": "d-yellow-crop",
   "path": "pipeline/art/reference/discord/20261110-0331_Ricky_1.png",
   "kind": "image",
   "role": [
    "effects",
    "motion"
   ],
   "what": "Look only: Crop of the yellow-shot sequence: tell, release, travel, fade; umbrella pull-in and capture ('even brighter on the umbrella when she absorbs?')",
   "cards": [
    "MVP 4"
   ],
   "judge": false,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov",
   "judge_exempt": "blurry crop; kept for the tell, release, travel, fade order"
  },
  {
   "id": "d-wing-gust",
   "path": "pipeline/art/reference/discord/20261110-0348_Ricky_1.png",
   "kind": "image",
   "role": [
    "effects",
    "motion"
   ],
   "what": "Look only: Wing gust attack, Ella pushed back, damaging vs rideable wind. OWL-02 (owl gust) is OFF in GDD 1.3; only WIND-01 (safe current) ships: use it for how wind reads, never as a new attack",
   "cards": [
    "0.10c",
    "MVP 2"
   ],
   "judge": false,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov",
   "judge_exempt": "off-palette blue (art bible pillar 3); kept for how the gust moves"
  },
  {
   "id": "d-talon-rake",
   "path": "pipeline/art/reference/discord/20261110-0512_Ricky_1.png",
   "kind": "image",
   "role": [
    "owl",
    "motion"
   ],
   "what": "Look only: Talon rake with a sliding mechanical leg extension: an attack not in GDD 1.3 (proposal); look of the owl only",
   "cards": [
    "MVP 5"
   ],
   "judge": false,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov",
   "judge_exempt": "the riveted metal owl (Josh, DECIDED 2026-11-11, D-new-owl-look): kept for how the attacks and mechanisms move, never for the owl's look"
  },
  {
   "id": "d-clock-double-beat",
   "path": "pipeline/art/reference/discord/20261110-0800_Ricky_1.png",
   "kind": "image",
   "role": [
    "effects",
    "motion"
   ],
   "what": "Look only: Clock double-beat attack: clock-hand cycle, repeated red shot paths (proposal); look of the bolts and clock only",
   "cards": [
    "MVP 5"
   ],
   "judge": false,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov",
   "judge_exempt": "the riveted metal owl (Josh, DECIDED 2026-11-11, D-new-owl-look): kept for how the attacks and mechanisms move, never for the owl's look; its pink chevron shots are not the shot look either (D-new-owl-shot-look: the key art's rust-red needle with a crosshair ring)"
  },
  {
   "id": "d-gear-break",
   "path": "pipeline/art/reference/discord/20261110-1047_Ricky_1.png",
   "kind": "image",
   "role": [
    "owl",
    "motion"
   ],
   "what": "Look only: Owl state study 01: rear gear mechanism hit and break. The owl has no HP in GDD 1.3 (§7A): damage states are a proposal; look only",
   "cards": [
    "MVP 5",
    "MVP 15"
   ],
   "judge": false,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov",
   "judge_exempt": "the riveted metal owl (Josh, DECIDED 2026-11-11, D-new-owl-look): kept for how the attacks and mechanisms move, never for the owl's look"
  },
  {
   "id": "d-wing-damage",
   "path": "pipeline/art/reference/discord/20261110-1047_Ricky_2.png",
   "kind": "image",
   "role": [
    "owl",
    "motion"
   ],
   "what": "Look only: Owl state study 02: wing damage and disable (proposal; look only)",
   "cards": [
    "MVP 15"
   ],
   "judge": false,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov",
   "judge_exempt": "the riveted metal owl (Josh, DECIDED 2026-11-11, D-new-owl-look): kept for how the attacks and mechanisms move, never for the owl's look"
  },
  {
   "id": "d-flip-throw",
   "path": "pipeline/art/reference/discord/20261110-1048_Ricky_1.png",
   "kind": "image",
   "role": [
    "owl",
    "motion"
   ],
   "what": "Look only: Rear mechanism over-back flip throw, gear on chain (proposal; look only)",
   "cards": [
    "MVP 5"
   ],
   "judge": false,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov",
   "judge_exempt": "the riveted metal owl (Josh, DECIDED 2026-11-11, D-new-owl-look): kept for how the attacks and mechanisms move, never for the owl's look"
  },
  {
   "id": "d-toss-kick",
   "path": "pipeline/art/reference/discord/20261110-1048_Ricky_2.png",
   "kind": "image",
   "role": [
    "owl",
    "motion"
   ],
   "what": "Look only: Middle mechanism toss and kick, lantern cage (proposal; look only)",
   "cards": [
    "MVP 5"
   ],
   "judge": false,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov",
   "judge_exempt": "the riveted metal owl (Josh, DECIDED 2026-11-11, D-new-owl-look): kept for how the attacks and mechanisms move, never for the owl's look"
  },
  {
   "id": "d-arc-chain",
   "path": "pipeline/art/reference/discord/20261110-1048_Ricky_3.png",
   "kind": "image",
   "role": [
    "owl",
    "motion"
   ],
   "what": "Look only: Middle mechanism arc chain cast; the returning arc is an Experiment in GDD SH1.0 OWL-07 (proposal; look only)",
   "cards": [
    "MVP 5"
   ],
   "judge": false,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov",
   "judge_exempt": "the riveted metal owl (Josh, DECIDED 2026-11-11, D-new-owl-look): kept for how the attacks and mechanisms move, never for the owl's look"
  },
  {
   "id": "d-ella-eyes",
   "path": "pipeline/art/reference/discord/20261110-1049_Ricky_1.png",
   "kind": "image",
   "role": [
    "character poses",
    "motion"
   ],
   "what": "Look only: Ella eye study: cloth mask, yellow glowing eyes with motion traces, hat on and off ('I didn't understand her dark face so I gave her a mask and yellow glowing eyes')",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "judge": false,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov",
   "judge_exempt": "Josh, DECIDED 2026-11-11, D-new-ella-face: Ella's face stays hidden, no mask and no glowing eyes; kept for the eye-trace motion only"
  },
  {
   "id": "d-clock-damage",
   "path": "pipeline/art/reference/discord/20261110-1220_Ricky_1.png",
   "kind": "image",
   "role": [
    "owl",
    "motion"
   ],
   "what": "Look only: Clock damage and failure: glass cracks, hand stops, keeper alive. GDD 1.3 keeps the clock-hit cue only (attack interruption OFF): look only",
   "cards": [
    "MVP 5"
   ],
   "judge": false,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 10 Nov",
   "judge_exempt": "the riveted metal owl (Josh, DECIDED 2026-11-11, D-new-owl-look): kept for how the attacks and mechanisms move, never for the owl's look"
  },
  {
   "id": "bar-casters",
   "path": "pipeline/art/reference/discord/20261111-0319_Ricky_roadwarden-sundial-casters.png",
   "kind": "image",
   "role": [
    "quality bar"
   ],
   "tier": "top",
   "what": "THE top bar for rendering quality, character detail and projectile/VFX construction (Josh, 11 Nov: anything short of this is a complete failure). 'Roadwarden / Sundial Casters, key poses and shared shots, study 01': painted turnaround Ready/Aim/Fire/Recover; red and yellow projectiles built as bright core, shell and trail; tell, release, travel, fade sequences; light spill. The characters are a design proposal for Richard: LOOK and quality only, no mechanics",
   "cards": [
    "0.10",
    "0.10b",
    "0.10c",
    "MVP 5",
    "MVP 3",
    "MVP 4",
    "MVP 15"
   ],
   "judge": true,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 2026-11-11T03:19Z (JPEG, stored as PNG for the judge)"
  },
  {
   "id": "bar-other-realm",
   "path": "pipeline/art/reference/discord/20261111-0318_Ricky_other-realm.png",
   "kind": "image",
   "role": [
    "quality bar"
   ],
   "tier": "top",
   "what": "The bar for scene mood, atmosphere and wind-flow rendering: 'Other Realm, hybrid study, proposed 01': dark scene, ash-blue wind-flow ribbons, floating eroded islands, gold shots, red bolts. This is how the WIND-01 zone should read (flowing ribbons, never a flat box). The realm is a design proposal for Richard: LOOK and quality only, no mechanics",
   "cards": [
    "0.10",
    "0.10c",
    "MVP 2",
    "MVP 15"
   ],
   "judge": true,
   "required": true,
   "origin": "Discord #art-direction, Ricky, 2026-11-11T03:18Z"
  },
  {
   "id": "menu-style-bar",
   "path": null,
   "kind": "described",
   "role": [
    "menu style bar"
   ],
   "what": "Written target for every menu screen and transition (title, pause, settings, Survived and fail): the feel of the paper cut-out, shadow-puppet animated end-credits sequence of the 2004 film 'Lemony Snicket's A Series of Unfortunate Events', in our brand and never deviating from our art. No frame of that film is stored or copied (copyright; Official Rules §7(h) and §15(d) ask for original work)",
   "description": [
    "layered paper cut-out silhouettes in near-black ink",
    "parallax depth planes: three or more paper layers that slide at different speeds",
    "hand-made, stop-motion-like motion: stepped timing, slight jitter, never smooth tweened easing",
    "ink-and-paper textures on every surface: the game's aged, stained sepia paper and etched lines",
    "gothic storybook typography",
    "the game's limited palette only (style.json: paper, ink, gold/amber, rust red)",
    "a painted vignette darkening the paper edges (part of the menu art, not the post-process vignette, which stays off)"
   ],
   "cards": [
    "0.21b"
   ],
   "judge": false,
   "required": false,
   "origin": "Josh, 11 Nov (written; no image)"
  },
  {
   "id": "title-screen",
   "path": "pipeline/art/reference/discord/20261112-0443_Ricky_title-screen.png",
   "kind": "image",
   "role": [
    "menu screen",
    "composition target"
   ],
   "what": "The title-screen target (Josh, 11 Nov): card 0.21b's title screen builds to this frame. Layout, title lockup, menu placement and mood: a painted, misty sepia scene of floating islands with a cottage and a windmill; a clock face top-left; the title lettered 'UMBRELLA GIRL' in an ornate serif with a clock-hand flourish; a menu with START GAME and DIRECTOR'S CUT. The title text and the painted look are open questions for the team (docs/decisions.md D-new-title-screen): look and layout only, never the wording. Reference only, never shipped",
   "cards": [
    "0.21b"
   ],
   "consulted_by": [
    "0.20",
    "0.21",
    "Art Director",
    "UI and UX"
   ],
   "judge": true,
   "required": true,
   "note": "Posted before the jam start (2026-11-12T04:43Z = 11 Nov 8:43 PM PT): reference only, never shipped (Official Rules §7(h)).",
   "origin": "Discord DM from Ricky to Josh (not #art-direction), 2026-11-12T04:43Z"
  },
  {
   "id": "study-ella-character",
   "path": "Assets/Art/Ella-Character-Study-01.png",
   "kind": "image",
   "role": [
    "team art",
    "character poses",
    "palette"
   ],
   "what": "Ella hero sheet: front, 3/4, side and back turnaround with the umbrella stowed on her back, hidden face, silhouette and etched-texture versions, materials and the INK-to-PAPER palette. Ella's look (D-new-ella-look): dark brown hair, hat, hidden face, at the key art's silhouette and scale",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "consulted_by": [
    "0.28"
   ],
   "judge": true,
   "required": false,
   "note": "Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  },
  {
   "id": "study-ella-freefall",
   "path": "Assets/Art/Ella-FreeFall-Pose-Study-01.png",
   "kind": "image",
   "role": [
    "team art",
    "character poses"
   ],
   "what": "Ella fast free fall: riding the closed umbrella point-down like a pogo, one hand on the hat, speed lines and the falling silhouette. Ella runs on the ground in some studies; in the game she is always airborne",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "consulted_by": [
    "0.28",
    "MVP 2"
   ],
   "judge": true,
   "required": false,
   "note": "Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  },
  {
   "id": "study-ella-needle-1",
   "path": "Assets/Art/Ella-Needle-Spell-Study-01.png",
   "kind": "image",
   "role": [
    "team art",
    "character poses",
    "effects"
   ],
   "what": "Ella needle spell: canopy open behind her, shaft held level like a lance firing separate gold pulse shots forward (build, release, next pulse) and the small-scale silhouette",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "consulted_by": [
    "MVP 9"
   ],
   "judge": true,
   "required": false,
   "note": "Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  },
  {
   "id": "study-ella-needle-2",
   "path": "Assets/Art/Ella-Needle-Spell-Study-02.png",
   "kind": "image",
   "role": [
    "team art",
    "character poses",
    "effects"
   ],
   "what": "Ella needle spell, second pass of study 01 (same pose, gold pulse shots along the level shaft)",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "consulted_by": [
    "MVP 9"
   ],
   "judge": true,
   "required": false,
   "note": "The same bytes as Assets/Conceptual Art/Ella-Needle-Spell-Study-02.png (concept-ella-needle-2); each repo has one of the two paths. Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  },
  {
   "id": "study-ella-rising-1",
   "path": "Assets/Art/Ella-Rising-Pose-Study-01.png",
   "kind": "image",
   "role": [
    "team art",
    "character poses",
    "scale"
   ],
   "what": "Ella rising: umbrella open overhead, firm two-hand grip, weight hanging below, gold lift sparks at the canopy rim, and the suspended silhouette. Ella runs on the ground in some studies; in the game she is always airborne",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "consulted_by": [
    "0.28",
    "MVP 2",
    "MVP 3"
   ],
   "judge": true,
   "required": false,
   "note": "Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  },
  {
   "id": "study-ella-rising-2",
   "path": "Assets/Art/Ella-Rising-Pose-Study-02.png",
   "kind": "image",
   "role": [
    "team art",
    "character poses",
    "scale"
   ],
   "what": "Ella rising, second pass of study 01 (handle with the clock-hand terminal below the grip). Ella runs on the ground in some studies; in the game she is always airborne",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "consulted_by": [
    "0.28",
    "MVP 2",
    "MVP 3"
   ],
   "judge": true,
   "required": false,
   "note": "Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  },
  {
   "id": "study-ella-small-blasts",
   "path": "Assets/Art/Ella-SmallBlasts-Cycle-Study-01.png",
   "kind": "image",
   "role": [
    "team art",
    "character poses",
    "effects"
   ],
   "what": "Ella small blasts: four-step cycle with the umbrella held level (ready folded, open with one gold magic pulse, close, ready again)",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "consulted_by": [
    "MVP 9"
   ],
   "judge": true,
   "required": false,
   "note": "The same bytes as Assets/Conceptual Art/Ella-SmallBlasts-Cycle-Study-01.png (concept-ella-small-blasts); each repo has one of the two paths. Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  },
  {
   "id": "study-ella-stored-thunder",
   "path": "Assets/Art/Ella-StoredThunder-Study-02.png",
   "kind": "image",
   "role": [
    "team art",
    "character poses",
    "effects"
   ],
   "what": "Ella stored thunder: the whole open umbrella charged with gold lightning, one heavy forward discharge and its pulse, release and aftershock rhythm",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "consulted_by": [
    "MVP 9"
   ],
   "judge": true,
   "required": false,
   "note": "The same bytes as Assets/Conceptual Art/Ella-StoredThunder-Study-02.png (concept-ella-stored-thunder); each repo has one of the two paths. Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  },
  {
   "id": "study-ella-streamed-blast",
   "path": "Assets/Art/Ella-StreamedBlast-Shoulder-Study-03.png",
   "kind": "image",
   "role": [
    "team art",
    "character poses",
    "effects"
   ],
   "what": "Ella streamed blast: umbrella open on her shoulder, a continuous gold stream sourced inside the canopy, with the canopy close-up and the small-scale silhouette",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "consulted_by": [
    "MVP 9"
   ],
   "judge": true,
   "required": false,
   "note": "The same bytes as Assets/Conceptual Art/Ella-StreamedBlast-Shoulder-Study-03.png (concept-ella-streamed-blast); each repo has one of the two paths. Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  },
  {
   "id": "study-ella-twin-stars",
   "path": "Assets/Art/Ella-TwinStars-Study-01.png",
   "kind": "image",
   "role": [
    "team art",
    "character poses",
    "effects"
   ],
   "what": "Ella twin stars: open canopy held forward, two gold star shots leaving the upper and lower canopy tips on two forward lanes",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "consulted_by": [
    "MVP 9"
   ],
   "judge": true,
   "required": false,
   "note": "The same bytes as Assets/Conceptual Art/Ella-TwinStars-Study-01.png (concept-ella-twin-stars); each repo has one of the two paths. Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  },
  {
   "id": "study-environment",
   "path": "Assets/Art/Environment-Study-01.png",
   "kind": "image",
   "role": [
    "team art",
    "scale",
    "composition target"
   ],
   "what": "Layered world: a medieval town on a shore under a darkening sky with an upper flight limit, travel to the right, parallax layers (sky, distant land, town and shore, black near ground), materials and palette. For parallax layering only: the skyline's look is the key art's black rock band",
   "cards": [
    "0.10c",
    "MVP 15"
   ],
   "consulted_by": [
    "0.10"
   ],
   "judge": true,
   "required": false,
   "note": "Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  },
  {
   "id": "study-foundation",
   "path": "Assets/Art/Foundation-Study-01.png",
   "kind": "image",
   "role": [
    "team art",
    "palette"
   ],
   "what": "Visual foundation: materials (blackened iron, aged bronze, dark steel, umbrella cloth, paper and ink, abstract ground), the world palette with gold and red for magic shots only, and soft, side-lit and in-motion lighting on the owl's wing and clock",
   "cards": [
    "0.10b",
    "MVP 15"
   ],
   "consulted_by": [
    "0.10"
   ],
   "judge": true,
   "required": false,
   "note": "Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  },
  {
   "id": "study-keeper-front-grip",
   "path": "Assets/Art/Keeper-Front-Grip-Study-04.png",
   "kind": "image",
   "role": [
    "team art",
    "owl",
    "motion"
   ],
   "what": "Keeper of Time front mechanism: a talon grips a ring on a chain, loads it under the body and releases it (grip, load, release); a mechanical handling study",
   "cards": [
    "MVP 5"
   ],
   "judge": false,
   "required": false,
   "note": "Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)",
   "judge_exempt": "the riveted metal owl (Josh, DECIDED 2026-11-11, D-new-owl-look): kept for how the attacks and mechanisms move, never for the owl's look"
  },
  {
   "id": "study-keeper-red-shots",
   "path": "Assets/Art/Keeper-Red-Shots-Study-02.png",
   "kind": "image",
   "role": [
    "team art",
    "effects",
    "owl",
    "motion"
   ],
   "what": "Keeper red shots: the firing tell at the chest, a volley of red bolts at Ella, each shot's tell, release, travel and fade, bright core, red shell and short trail, and the temporary light spill",
   "cards": [
    "0.10b",
    "MVP 5"
   ],
   "judge": false,
   "required": false,
   "note": "Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)",
   "judge_exempt": "the riveted metal owl (Josh, DECIDED 2026-11-11, D-new-owl-look): kept for how the attacks and mechanisms move, never for the owl's look; its pink chevron shots are not the shot look either (D-new-owl-shot-look: the key art's rust-red needle with a crosshair ring)"
  },
  {
   "id": "study-keeper-character",
   "path": "Assets/Art/KeeperofTime-Character-Study-02.png",
   "kind": "image",
   "role": [
    "team art",
    "owl",
    "palette",
    "motion"
   ],
   "what": "The Clockkeeper: the mechanical owl with wings spread, chest clock and three hanging mechanisms; 3/4, side and back views, silhouette, close-ups and materials",
   "cards": [
    "0.10b",
    "MVP 5",
    "MVP 15"
   ],
   "consulted_by": [
    "0.28"
   ],
   "judge": false,
   "required": false,
   "note": "Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)",
   "judge_exempt": "the riveted metal owl (Josh, DECIDED 2026-11-11, D-new-owl-look): kept for how the attacks and mechanisms move, never for the owl's look"
  },
  {
   "id": "study-umbrella-prop",
   "path": "Assets/Art/Umbrella-Prop-Study-03.png",
   "kind": "image",
   "role": [
    "team art",
    "character poses"
   ],
   "what": "Ella's umbrella: open and closed, crown finial and clock-hand terminal, and the health stages 100/75/50/25 % as the cloth drains and tears. Build and damage-stage reference only: the umbrella's look is the key art's, black with light stripes (D-new-umbrella-look)",
   "cards": [
    "MVP 4",
    "MVP 15"
   ],
   "consulted_by": [
    "0.10b",
    "MVP 10"
   ],
   "judge": true,
   "required": false,
   "note": "Look only: any gameplay in it that is not in the current GDD is a proposal, never a new mechanic. Optional: a repo without this file leaves the entry out.",
   "origin": "Assets/Art/ in the practice repo (Ricky, 10 Nov)"
  }
 ],
 "elements": {
  "ella-up-open": {
   "what": "Ella with the umbrella open overhead (UP_OPEN), the anchor 'Ella open'",
   "refs": [
    "ella-rising",
    "study-ella-character",
    "study-ella-rising-1",
    "study-ella-rising-2",
    "bar-casters"
   ],
   "score_min": 0.398,
   "detail_min": 0.448,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {
     "ella-rising": 0.418
    },
    "detail": {
     "ella-rising": 0.468
    }
   }
  },
  "ella-closed": {
   "what": "Ella with the umbrella closed (the anchor 'Ella closed', falling states)",
   "refs": [
    "ella-freefall",
    "ella-shooting",
    "study-ella-character",
    "study-ella-freefall",
    "bar-casters"
   ],
   "score_min": 0.749,
   "detail_min": 0.617,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {
     "ella-freefall": 0.769,
     "ella-shooting": 0.769
    },
    "detail": {
     "ella-freefall": 0.682,
     "ella-shooting": 0.637
    }
   }
  },
  "ella-attack": {
   "what": "ATTACK_DESCENT: umbrella level like a lance, wand firing",
   "refs": [
    "ella-shooting",
    "study-ella-character",
    "study-ella-needle-1",
    "study-ella-needle-2",
    "study-ella-small-blasts",
    "study-ella-stored-thunder",
    "study-ella-streamed-blast",
    "study-ella-twin-stars",
    "bar-casters"
   ],
   "score_min": 0.448,
   "detail_min": 0.617,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {
     "ella-shooting": 0.468
    },
    "detail": {
     "ella-shooting": 0.637
    }
   }
  },
  "ella-shield": {
   "what": "SHIELD_DESCENT: canopy turned forward",
   "refs": [
    "ella-absorbing",
    "study-ella-character",
    "d-yellow-shots",
    "bar-casters"
   ],
   "score_min": 0.586,
   "detail_min": 0.364,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {
     "ella-absorbing": 0.606,
     "d-yellow-shots": 0.753
    },
    "detail": {
     "ella-absorbing": 0.684,
     "d-yellow-shots": 0.384
    }
   }
  },
  "umbrella": {
   "what": "the umbrella prop and its wear stages: the key art's black umbrella with light stripes (keyart-umbrella, D-new-umbrella-look); study-umbrella-prop for build and damage stages only",
   "refs": [
    "keyart-umbrella",
    "study-umbrella-prop"
   ],
   "score_min": 0.5,
   "detail_min": 0.438,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {},
    "detail": {
     "keyart-umbrella": 0.458
    },
    "note": "one team image and nothing to compare it with: score_min not measurable"
   }
  },
  "owl": {
   "what": "the owl (body, wings, chest clock): the key-art organic owl, tattered feathers, gothic spire crown, glowing gold gear clock with no numerals, amber eyes (D-new-owl-look)",
   "refs": [
    "owl-flap"
   ],
   "score_min": 0.525,
   "detail_min": 0.635,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {},
    "detail": {
     "owl-flap": 0.655
    },
    "note": "one team image and nothing to compare it with: score_min not measurable"
   }
  },
  "owl-bolt": {
   "what": "the owl's shot: the key art's rust-red needle with a crosshair ring (keyart-bolt, D-new-owl-shot-look); bar-casters for the build quality only (core, shell, trail, spill), not its colour",
   "refs": [
    "keyart-bolt",
    "bar-casters"
   ],
   "score_min": 0.473,
   "detail_min": 0.391,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {
     "keyart-bolt": 0.493
    },
    "detail": {
     "keyart-bolt": 0.411
    }
   }
  },
  "bolt-hit": {
   "what": "the bolt impact",
   "refs": [
    "owl-missile-hit",
    "bar-casters"
   ],
   "score_min": 0.53,
   "detail_min": 0.25,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {
     "owl-missile-hit": 0.55
    },
    "detail": {
     "owl-missile-hit": 0.27
    }
   }
  },
  "wand-shot": {
   "what": "Ella's gold star wand shot",
   "refs": [
    "wand-star",
    "bar-casters"
   ],
   "score_min": 0.334,
   "detail_min": 0.077,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {
     "wand-star": 0.354
    },
    "detail": {
     "wand-star": 0.097
    }
   }
  },
  "umbrella-repair": {
   "what": "the shield-heal burst at the canopy",
   "refs": [
    "d-yellow-shots",
    "bar-casters"
   ],
   "score_min": 0.733,
   "detail_min": 0.364,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {
     "d-yellow-shots": 0.753
    },
    "detail": {
     "d-yellow-shots": 0.384
    }
   }
  },
  "wind-lines": {
   "what": "decorative etched wind lines (never gameplay-looking): the key art's etched lines (keyart-wind-lines) only",
   "refs": [
    "keyart-wind-lines"
   ],
   "score_min": 0.582,
   "detail_min": 0.408,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {},
    "detail": {
     "keyart-wind-lines": 0.428
    },
    "note": "one team image and nothing to compare it with: score_min not measurable"
   }
  },
  "wind-zone": {
   "what": "the WIND-01 upward wind zone: etched upward strokes, engraved border, paper tint; never a flat fill (screen_check); judged against bar-other-realm's flowing ribbons only (no refs shared with wind-lines)",
   "refs": [
    "bar-other-realm"
   ],
   "score_min": 0.582,
   "detail_min": 0.421,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {},
    "detail": {},
    "note": "one team image and nothing to compare it with: score_min not measurable"
   }
  },
  "skyline": {
   "what": "the black jagged skyline layer: the key art's black rock band (keyart; keyart-skyline is cut but on hold, see its judge_exempt); study-environment for parallax layering only",
   "refs": [
    "gothic-skyline",
    "keyart",
    "study-environment"
   ],
   "score_min": 0.527,
   "detail_min": 0.143,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {
     "gothic-skyline": 0.547,
     "keyart": 0.547
    },
    "detail": {
     "gothic-skyline": 0.163,
     "keyart": 0.555
    }
   }
  },
  "paper": {
   "what": "the paper and far-sky layer",
   "refs": [
    "star-paper",
    "study-foundation"
   ],
   "score_min": 0.5,
   "detail_min": 0.085,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {},
    "detail": {
     "star-paper": 0.105
    },
    "note": "one team image and nothing to compare it with: score_min not measurable"
   }
  },
  "menu-screen": {
   "what": "a menu screen or transition frame (title, pause, settings, Survived, fail) in the menu style",
   "refs": [
    "keyart",
    "original-picture",
    "title-screen",
    "menu-style-bar"
   ],
   "score_min": 0.805,
   "described": "menu-style-bar",
   "detail_min": 0.249,
   "calibration": {
    "method": "leave-one-out on the team images under pipeline/art/reference/ (quality bar and Assets/ studies excluded)",
    "margin": 0.02,
    "measured": "2026-11-11",
    "loo": {
     "keyart": 0.993,
     "original-picture": 0.993,
     "title-screen": 0.825
    },
    "detail": {
     "keyart": 0.555,
     "original-picture": 0.52,
     "title-screen": 0.269
    }
   }
  }
 },
 "scene": {
  "what": "a build screenshot against the key-art composition. Ranges measured from keyart, original-picture and gameplay-02 (10 Nov) and wide enough for the art-bible gameplay sizes (Ella 80-100 px, owl 55-70% of the height at 1080p)",
  "refs": [
   "keyart",
   "original-picture",
   "gameplay-01",
   "gameplay-02"
  ],
  "classes": {
   "dark_l_max": 30,
   "ella_l_max": 34,
   "accent_chroma_min": 25,
   "gold_hue": [
    55,
    95
   ],
   "gold_l_min": 50,
   "rust_hue": [
    15,
    55
   ]
  },
  "ella_x_min": 0.05,
  "ella_x_max": 0.35,
  "skyline_median": [
   0.03,
   0.25
  ],
  "skyline_cover_min": 0.9,
  "owl": {
   "cx": [
    0.55,
    0.9
   ],
   "h": [
    0.45,
    0.95
   ],
   "w": [
    0.25,
    0.9
   ]
  },
  "ella": {
   "cx": [
    0.04,
    0.35
   ],
   "h": [
    0.04,
    0.3
   ]
  },
  "owl_to_ella_h_min": 3.0,
  "gold_share_min": 0.0008,
  "clock_in_owl_min": 0.6,
  "rust_share_min": 0.0008,
  "similarity_min": 0.732,
  "status": "provisional: calibrate on the first in-engine rebuild (card 0.10, the key-art style frame)",
  "calibration": {
   "method": "leave-one-out on the scene references",
   "margin": 0.02,
   "measured": "2026-11-11",
   "loo": {
    "keyart": 0.986,
    "original-picture": 0.986,
    "gameplay-01": 0.752,
    "gameplay-02": 0.81
   }
  }
 },
 "discord_note": "pipeline/art/reference/discord/ (index.json beside them: author, time, message, description; one byte-identical repost skipped) holds Ricky's #art-direction posts of 10 Nov. They show Ricky's proposed attacks and visuals. Use them for LOOK only: any gameplay in them that is not in the current GDD (absorbable yellow shots, wing gust attack, talon rake, double-beat, owl and clock damage states, throws and chain casts) is a design proposal for Richard, never a new mechanic. References only, never shipped (Official Rules §7(h)).",
 "not_art_cards": {
  "0.10a": "the colour-calibration swatch: art_check.py --swatch measures it, it is not game art",
  "0.4d": "the TD's art dump script and import settings: no art is made",
  "0.20": "the UI string table and text styles: text data, no art",
  "0.35": "the Story role's screen copy: the SourceString cells of the UI string table, text, no art"
 },
 "quality_bar": {
  "refs": [
   "bar-casters",
   "bar-other-realm"
  ],
  "rule": "Top tier, on top of the key-art composition target. Every art-loop round also puts our piece blind against a quality-bar image (bar-casters for characters and shot VFX, bar-other-realm for the scene and wind); a round passes only when the critic picks neither the piece reference nor the quality bar over ours. A frame or piece that reads as flat primitives or a rough placeholder is an automatic FAIL (screen_check.py flat/grey/outline, the element judge's flat-fill and off-palette caps).",
  "by_piece": {
   "wind-zone": "bar-other-realm",
   "wind-lines": "bar-other-realm",
   "scene": "bar-other-realm",
   "skyline": "bar-other-realm",
   "paper": "bar-other-realm",
   "menu-screen": "bar-other-realm"
  },
  "default": "bar-casters",
  "palette_note": "The quality-bar colours (ash-blue flow, the yellows) and the key art's shot rust (D-new-owl-shot-look; the bar's hot red #FF3658 and coral are not our look) are in style.json as capped accents (Josh, DECIDED 2026-11-10, D-new-palette-accents): art_check.py accepts them only in their role, hue band and share cap."
 },
 "vfx_spec": {
  "source": "bar-casters",
  "sequence": [
   "tell",
   "release",
   "travel",
   "fade"
  ],
  "construction": "bright core, shell, trail, light spill on nearby surfaces",
  "palette": {
   "INK": "#171614",
   "RUST": "#723929",
   "RUST SHADOW": "#5b2519",
   "RUST HIGH": "#79331f",
   "YELLOW": "#FFD84A",
   "AMBER": "#F5AA28",
   "YELLOW SHADOW": "#94611E",
   "CORE": "#FFF5DC"
  },
  "rule": "The spec for every shot VFX (owl bolts, wand shots, impacts): each one has the four stages and the core/shell/trail build, taken from bar-casters for build quality only. The owl's shot colour is the key art's rust-red needle with a crosshair ring (Josh, DECIDED 2026-11-11, D-new-owl-shot-look: RUST, RUST SHADOW, RUST HIGH measured from the key art); the pink chevrons (#FF3658) are not the look. style.json carries them as the shot-red and shot-yellow capped accents, INK with the darks (see quality_bar.palette_note)."
 },
 "gdd_embedded": {
  "_about": "Images the current GDD embeds (markdown ![..](path) or <img src=..>, relative to the GDD file) join the list each run: the GDD a run picked with kickoff --gdd ($JAM_GDD, tools/gdd_select.py, which prints the images it brings) is read, else the one docs/gdd/CURRENT names. An entry above with the same path keeps its role and cards. Not required: a GDD without images adds none.",
  "from": "docs/gdd/CURRENT",
  "role": [
   "composition target",
   "scale"
  ],
  "cards": [
   "0.10",
   "0.22"
  ],
  "judge": true,
  "required": false
 },
 "team_art": {
  "_about": "Every image (png, jpg, jpeg, webp, any case) under the team's art folders joins the list each run (tools/art_check.py load_spec, the loader every art tool shares), unless it is already listed: the same path, or the same bytes as a listed file or as a team image joined before it (an LFS pointer compares by its object id). A folder whose name says obsolete (for example Assets/'... Test Assets - obsolete') is skipped. A joined image gets these defaults: kind image, role team art, judge true (style context for the blind judge, look only like the #art-direction posts: gameplay comes from the GDD), no judge element and no card until the Art Director gives it its own entry above, and it is never shipped (submission_check.py assets). An image that cannot be read (not the picture its extension says, empty or truncated) fails art_check.py --references and --gate, art_judge.py coverage and kickoff --check; both print a `team art:` line with how many images joined.",
  "folders": [
   "Assets",
   "Mockups"
  ],
  "skip_words": [
   "obsolete"
  ],
  "role": [
   "team art"
  ],
  "cards": [],
  "consulted_by": [
   "0.10",
   "0.10b",
   "0.10c"
  ],
  "judge": true,
  "required": false,
  "same_as": {
   "Assets/Art/Keeper-Talon-Rake-Study-07.png": "d-talon-rake",
   "Assets/Art/Keeper-Wing-Gust-Study-02.png": "d-wing-gust",
   "Assets/Art/Keeper-Yellow-Shots-Study-03.png": "d-yellow-shots",
   "Assets/Conceptual Art/Ella-Mask-Eye-Trail-Study-02.png": "d-ella-eyes"
  }
 }
}
```

### `pipeline/art/reference/discord/index.json`

```json
{
  "channel": "Epic Game Jam 2026 / #art-direction",
  "channel_url": "https://discord.com/channels/1567126067448385620/1569544714024386730",
  "collected_at": "2026-11-10",
  "messages_scanned": 31,
  "timezone_note": "posted_at and filename stamps are UTC (Discord showed Pacific, UTC-8)",
  "images": [
    {
      "file": "20261110-0258_Ricky_1.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T02:58:50.185Z",
      "message_text": "",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569546851235930182/image.png",
      "width": 1536,
      "height": 1024,
      "message_id": "1569546851571736617",
      "description": "Keeper of Time: red (damaging) shots concept sheet 01"
    },
    {
      "file": "20261110-0328_Ricky_1.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T03:28:56.293Z",
      "message_text": "",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569554426669179041/image.png",
      "width": 1448,
      "height": 1086,
      "message_id": "1569554426937475082",
      "description": "Keeper of Time: yellow (absorbable) shots sheet 02, incl. Ella umbrella capture and lit movement modes"
    },
    {
      "file": "20261110-0331_Ricky_1.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T03:31:04.994Z",
      "message_text": "so even more brighter on the umbrella when she absorbs?\n\nthere are two different pictures of the absorbing.",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569554966450802828/image.png",
      "width": 661,
      "height": 268,
      "message_id": "1569554966748725268",
      "description": "Crop of yellow-shot sequence: tell/release/travel/fade, umbrella pull-in and capture"
    },
    {
      "file": "20261110-0348_Ricky_1.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T03:48:12.716Z",
      "message_text": "",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569559277083955240/image.png",
      "width": 1448,
      "height": 1086,
      "message_id": "1569559277327097887",
      "description": "Keeper of Time: wing gust attack, Ella pushed-back responses, damaging vs rideable wind"
    },
    {
      "file": "20261110-0512_Ricky_1.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T05:12:13.739Z",
      "message_text": "",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569580420616429648/image.png",
      "width": 1448,
      "height": 1086,
      "message_id": "1569580420910022727",
      "description": "Keeper of Time: talon rake, sliding mechanical leg extension"
    },
    {
      "file": "20261110-0800_Ricky_1.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T08:00:00.788Z",
      "message_text": "",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569622644825923725/image.png",
      "width": 1448,
      "height": 1086,
      "message_id": "1569622645173915750",
      "description": "Keeper of Time: clock double-beat attack (clock-hand cycle, repeated red shot paths)"
    },
    {
      "file": "20261110-1047_Ricky_1.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T10:47:47.122Z",
      "message_text": "",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569664865952337991/image.png",
      "width": 1536,
      "height": 1024,
      "message_id": "1569664866439143434",
      "description": "Keeper of Time state study 01: rear gear mechanism hit and break"
    },
    {
      "file": "20261110-1047_Ricky_2.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T10:47:55.566Z",
      "message_text": "",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569664901427892294/image.png",
      "width": 1536,
      "height": 1024,
      "message_id": "1569664901855580291",
      "description": "Keeper of Time state study 02: wing damage and disable"
    },
    {
      "file": "20261110-1048_Ricky_1.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T10:48:14.083Z",
      "message_text": "attacks:",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569664979206930492/image.png",
      "width": 1536,
      "height": 1024,
      "message_id": "1569664979521511424",
      "description": "Keeper of Time: rear mechanism over-back flip throw (gear on chain)"
    },
    {
      "file": "20261110-1048_Ricky_2.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T10:48:19.762Z",
      "message_text": "",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569665002972123176/image.png",
      "width": 1536,
      "height": 1024,
      "message_id": "1569665003340955739",
      "description": "Keeper of Time: middle mechanism toss and kick (lantern cage)"
    },
    {
      "file": "20261110-1048_Ricky_3.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T10:48:29.534Z",
      "message_text": "",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569665044197802024/image.png",
      "width": 1536,
      "height": 1024,
      "message_id": "1569665044327960588",
      "description": "Keeper of Time: middle mechanism arc chain cast"
    },
    {
      "file": "20261110-1048_Ricky_4.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T10:48:38.938Z",
      "message_text": "clock attack:",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569665083582447636/image.png",
      "width": 1448,
      "height": 1086,
      "message_id": "1569665083771199582",
      "description": "Keeper of Time: clock double-beat attack (byte-identical repost of 20261110-0800_Ricky_1.png)",
      "duplicate_of": "20261110-0800_Ricky_1.png"
    },
    {
      "file": "20261110-1049_Ricky_1.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T10:49:44.026Z",
      "message_text": "I didn't understand her dark face so I gave her a mask and yellow glowing eyes her eyes will have traces to them:",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569665356455219320/image.png",
      "width": 1536,
      "height": 1024,
      "message_id": "1569665356769923122",
      "description": "Ella eye trace study: cloth mask, yellow glowing eyes, hat on/off, motion traces"
    },
    {
      "file": "20261110-1220_Ricky_1.png",
      "author": "Ricky",
      "posted_at": "2026-11-10T12:20:43.364Z",
      "message_text": "",
      "source_url_without_signature": "https://cdn.discordapp.com/attachments/1569544714024386730/1569688254578692156/image.png",
      "width": 1536,
      "height": 1024,
      "message_id": "1569688254893260860",
      "description": "Keeper of Time state study 01: clock damage and failure (glass cracks, hand stops, keeper alive)"
    },
    {
      "file": "20261112-0443_Ricky_title-screen.png",
      "author": "Ricky",
      "posted_at": "2026-11-12T04:43:00Z",
      "message_text": "",
      "source_url_without_signature": null,
      "width": 1672,
      "height": 941,
      "message_id": null,
      "description": "Title screen: painted misty sepia floating islands with cottage and windmill, clock face top-left, 'UMBRELLA GIRL' title with clock-hand flourish, menu START GAME / DIRECTOR'S CUT",
      "source": "Discord DM from Ricky to Josh, not #art-direction (the channel above): added by hand, no message id or CDN link recorded"
    }
  ],
  "links": []
}
```

### `pipeline/art/reference/Test_Assets/SpriteLayout.json`

```json
{
  "CHR_Owl_Flap_Damage.png": {
    "frame_size": [
      640,
      512
    ],
    "columns": 6,
    "rows": 5,
    "pivot_px": [
      296,
      280
    ],
    "fps": 10,
    "row_labels": [
      "full",
      "damage_1",
      "damage_2",
      "damage_3",
      "damage_4"
    ],
    "column_order": "flap loop, left to right",
    "loop": true,
    "faces": "left"
  },
  "CHR_Witch_Cast.png": {
    "frame_size": [
      432,
      352
    ],
    "columns": 6,
    "rows": 2,
    "pivot_px": [
      229,
      188
    ],
    "fps": 14,
    "row_labels": [
      "lift",
      "guard_fall"
    ],
    "loop": false,
    "faces": "right",
    "fire_on_column": 3,
    "wand_tip_px": [
      [
        385.1,
        147.7
      ],
      [
        368.9,
        107.2
      ],
      [
        380.0,
        129.6
      ],
      [
        387.3,
        164.2
      ],
      [
        387.1,
        180.9
      ],
      [
        385.1,
        147.7
      ]
    ],
    "grip_px": [
      [
        201.2,
        73.8
      ],
      [
        262.2,
        151.9
      ]
    ]
  },
  "CHR_Witch_Guard_Transition.png": {
    "frame_size": [
      432,
      352
    ],
    "columns": 5,
    "rows": 1,
    "pivot_px": [
      229,
      188
    ],
    "fps": 14,
    "loop": false,
    "column_order": "lift to guard; reverse for guard to lift",
    "grip_px": [
      [
        201.2,
        73.8
      ],
      [
        217.4,
        74.2
      ],
      [
        246.3,
        88.0
      ],
      [
        264.3,
        118.0
      ],
      [
        262.2,
        151.9
      ]
    ]
  },
  "PROP_Umbrella_Stance_Damage.png": {
    "frame_size": [
      368,
      352
    ],
    "columns": 5,
    "rows": 5,
    "pivot_px": [
      126,
      223
    ],
    "fps": 14,
    "loop": false,
    "row_labels": [
      "full",
      "damage_1",
      "damage_2",
      "damage_3",
      "damage_4"
    ],
    "column_order": "overhead, turn 1, turn 2, turn 3, front guard",
    "guard_heal": "on a successful guard hit use the previous damage row and play FX_Umbrella_Repair"
  },
  "FX_Wand_Star_Travel.png": {
    "frame_size": [
      128,
      64
    ],
    "columns": 6,
    "rows": 1,
    "pivot_px": [
      99,
      32
    ],
    "fps": 16,
    "loop": true,
    "faces": "right"
  },
  "FX_Owl_Missile.png": {
    "frame_size": [
      160,
      80
    ],
    "columns": 1,
    "rows": 1,
    "pivot_px": [
      46,
      40
    ],
    "fps": 0,
    "loop": false,
    "faces": "left"
  },
  "FX_Owl_Missile_Travel.png": {
    "frame_size": [
      160,
      80
    ],
    "columns": 6,
    "rows": 1,
    "pivot_px": [
      46,
      40
    ],
    "fps": 16,
    "loop": true,
    "faces": "left"
  },
  "FX_Owl_Missile_Hit.png": {
    "frame_size": [
      128,
      128
    ],
    "columns": 7,
    "rows": 1,
    "pivot_px": [
      64,
      64
    ],
    "fps": 20,
    "loop": false
  },
  "FX_Wind_Curl.png": {
    "frame_size": [
      144,
      112
    ],
    "columns": 8,
    "rows": 1,
    "pivot_px": [
      77,
      59
    ],
    "fps": 12,
    "loop": true,
    "faces": "right"
  },
  "FX_Umbrella_Repair.png": {
    "frame_size": [
      128,
      128
    ],
    "columns": 7,
    "rows": 1,
    "pivot_px": [
      64,
      64
    ],
    "fps": 18,
    "loop": false
  }
}
```

### `pipeline/art/reference/Test_Assets/Asset Notes.md`

#### MegaJam 2026 test art

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

##### Artwork provenance

The flattened `umbrella-ella.png` illustration supplied the design and style reference. The built-in ImageGen tool reconstructed the owl, witch, umbrella, sky and skyline. GIMP 3.2's command-line batch process built the animation frames and damage masks, blended the tiles, rasterized the drawn effects and exported the PNGs.

##### ImageGen prompts

###### Owl

Using attached image as style and character reference, reconstruct just the complete clockwork owl antagonist as one game-ready 2D cutout on a genuinely transparent canvas. Wide 3:2 or wider. Full owl, completely uncropped, wings open laterally about 15 degrees above horizontal with wing roots clearly recognizable and tail fanned downward, two curled talons. Three-quarter view looking left, bronze and gold clock face chest, charcoal and dark umber layered etched feathers, gold eyes and beak, short sparse clock chains attached to body. Precisely emulate the original dark ink, faded warm paper and engraved medieval clockwork character. Wings and tail are intact, full health, with continuous silhouettes. Leave clear negative spaces between tail and feet, and a generous border all around. Single subject, no parchment, no cast shadow, no glow halo, no sparks, no type.

###### Witch

Using attached image as style and character reference, redraw just the complete small witch as a high resolution isolated 2D game sprite on genuine transparency. Exactly one full-body witch, facing screen right in profile, hovering with boots and legs trailing to the left and tapered skirt, pointy hat, long scarf and dark hair curling left, recognizable dark silhouette, subtle etched warm charcoal/sepia highlights like original. Her near arm is held away from her torso and extends forward horizontally to the right, carrying a very thin short wand. The opposite arm is visible above the shoulder and bends up into a small raised gripping fist to hold an invisible handle. Show both hands. Leave margin around hair, boots, wand. Preserve ink-paper cutout look, no flat cartoon/vector, no umbrella, no sparks, no shadow, no text.

###### Umbrella

From the attached game illustration, redraw only the witch's fully open umbrella as a single isolated transparent 2D asset. Match original etched black and muted taupe alternating ribs/panels, pointed finial and scalloped batwing-like canopy. Side-on side profile with an exactly vertical dark thin shaft centered underneath, ending in a small curled J grip. Intact canopy full health. Subtle engraved weathered textile texture, crisp silhouette, no cast shadow, witch, light effects, ground, background, text, decorations. Place full item centrally with generous margins.

###### Sky

Use the attached game image as a style reference, create ONLY a beige-grey muted night sky texture plate for a sidescrolling game, ultra-wide 3:1 landscape. A softly mottled, lightly grained lithograph paper field, soot gray and warm desaturated mushroom and oatmeal tones, faint wispy fine flowing parallel engraved streamlines mostly near upper edge and lower quarter, a sparse scattering of very small pale cream pinprick stars and a few small etched rings as in the reference. Mid-screen is calm, low contrast, art will be overlaid. No owl, witch, weapons, ground, skyline, mountains, moons, borders, text, horizon or typography. Suitable for repeating horizontally with edge blending; avoid dark vignette or contrasting left/right edges.

###### Skyline

Using the attached illustration as the style reference, make a standalone horizontal black city skyline as a single layered ground silhouette for a sidescrolling 2D game. Ultra wide landscape. Genuinely transparent background above the rooftops. Along the entire bottom edge continuous charcoal-black near-silhouette city strip, with varied narrow gothic and Victorian towers, sharp gables, chimneys, with a few subtle amber lit windows. Hand-inked engraved paper aesthetic matching the reference mountains, extremely restrained contrast in silhouette. All buildings rooted to a completely opaque straight black base at bottom edge. Left and right edges should taper to an identical low flat black parapet, about a tenth of image height so this can tile. No perspective vanishing point, no sky, moon, hills, type, shadows. Crisp silhouette with delicate ink texture.


## Blender art generator

### `pipeline/art/blender/characters.json`

```json
{
  "_about": "Blender stand-in recipes: one entry per character or prop, one row per animation. tools/assetgen.py blender --character <id> --anim <Anim> turns a row into a render job (pipeline/art/blender/plan.py): frame size, pivot and facing come from the references.json `layout` entry named in `layout` (pipeline/art/reference/Test_Assets/SpriteLayout.json), fps and the allowed frame count from pipeline/art/style.json `anims` (the art-bible flipbook table), colours from style.json `palette` and `accents`. `piece` is the art-loop judge element (references.json elements) a row is judged as. A row's `keys` are poses at times 0..1 (bone angles in degrees in the picture plane, `canopy` 0 closed .. 1 open, `lift` in pixels); the planner spreads them over the row's frames (a loop wraps to its first key). The Blender scene is built by pipeline/art/blender/stand_ins.py and rendered by render_sprite.py (`blender -b -P render_sprite.py -- --job <job.json>`). An art-loop revision changes this file, stand_ins.py or `look` (model detail, materials, lines, light), never the checks.",
  "look": {
    "_about": "Ink-and-paper NPR for every recipe: toon shading in `shades` (darks from style.json, light from the front, slightly above: art bible R11), Freestyle ink lines of line_px in the ink colour, paper grain in the material and, when the compositor supports it, a grain pass there too. Transparent film, orthographic camera, Standard view transform (no filmic tone change to the palette).",
    "shades": [
      "ink",
      "silhouette",
      "owl-umber"
    ],
    "ink": "ink",
    "line_px": 1.6,
    "grain": 0.06,
    "grain_scale": 180.0,
    "seed": 11,
    "light_deg": [
      62,
      0,
      18
    ],
    "samples": 16
  },
  "characters": {
    "ella": {
      "what": "Ella (GDD SH1.0 ART-06): an adult in a bent pointed hat, face hidden by a cloth / mesh mask, long dark hair and scarf, one slender striped umbrella with a crown finial and a diamond clock-hand terminal; no wand. Stand-in rig: body, skirt, umbrella arm, canopy, free arm (the old wand arm; the wand mesh is gone). Two-hand grip, legs, scarf and mask need the card 0.38 rig",
      "asset": "Ella",
      "builder": "ella",
      "layout": "CHR_Witch_Cast.png",
      "px_per_unit": 70.0,
      "element": "character",
      "anims": {
        "IdleFloat": {
          "piece": "ella-up-open",
          "frames": 6,
          "loop": true,
          "keys": [
            {
              "t": 0.0,
              "canopy": 1.0,
              "lift": 0,
              "rot": {
                "umbrella_arm": 0,
                "wand_arm": 10,
                "skirt": 0
              }
            },
            {
              "t": 0.5,
              "canopy": 1.0,
              "lift": 4,
              "rot": {
                "umbrella_arm": 4,
                "wand_arm": 16,
                "skirt": 6
              }
            }
          ]
        },
        "Fall": {
          "piece": "ella-closed",
          "frames": 4,
          "loop": true,
          "keys": [
            {
              "t": 0.0,
              "canopy": 0.0,
              "lift": 0,
              "rot": {
                "umbrella_arm": -150,
                "wand_arm": -30,
                "skirt": -12
              }
            },
            {
              "t": 0.5,
              "canopy": 0.0,
              "lift": -2,
              "rot": {
                "umbrella_arm": -140,
                "wand_arm": -40,
                "skirt": -20
              }
            }
          ]
        },
        "Open": {
          "piece": "ella-up-open",
          "frames": 4,
          "loop": false,
          "keys": [
            {
              "t": 0.0,
              "canopy": 0.0,
              "lift": 0,
              "rot": {
                "umbrella_arm": -90,
                "wand_arm": 0,
                "skirt": -6
              }
            },
            {
              "t": 1.0,
              "canopy": 1.0,
              "lift": 2,
              "rot": {
                "umbrella_arm": 0,
                "wand_arm": 10,
                "skirt": 0
              }
            }
          ]
        },
        "Close": {
          "piece": "ella-closed",
          "frames": 4,
          "loop": false,
          "keys": [
            {
              "t": 0.0,
              "canopy": 1.0,
              "lift": 2,
              "rot": {
                "umbrella_arm": 0,
                "wand_arm": 10,
                "skirt": 0
              }
            },
            {
              "t": 1.0,
              "canopy": 0.0,
              "lift": 0,
              "rot": {
                "umbrella_arm": -90,
                "wand_arm": 0,
                "skirt": -6
              }
            }
          ]
        },
        "Attack": {
          "piece": "ella-attack",
          "frames": 4,
          "loop": false,
          "keys": [
            {
              "t": 0.0,
              "canopy": 0.0,
              "lift": 0,
              "rot": {
                "umbrella_arm": -90,
                "wand_arm": 80,
                "skirt": -8
              }
            },
            {
              "t": 0.4,
              "canopy": 0.0,
              "lift": 0,
              "rot": {
                "umbrella_arm": -92,
                "wand_arm": 95,
                "skirt": -10
              },
              "flash": 1.0
            },
            {
              "t": 1.0,
              "canopy": 0.0,
              "lift": 0,
              "rot": {
                "umbrella_arm": -90,
                "wand_arm": 82,
                "skirt": -8
              }
            }
          ]
        }
      }
    },
    "owl": {
      "what": "the Keeper of Time (GDD SH1.0 OWL-08, ART-06): a crownless fabricated metal owl. Stand-in rig: front view body, head, tail and two wings (no crown since GDD SH1.0). The side profile, two feet, rigid vane wings, chest clock hand and the three hanging mechanisms need the card 0.37 rig",
      "asset": "Owl",
      "builder": "owl",
      "layout": "CHR_Owl_Flap_Damage.png",
      "px_per_unit": 62.0,
      "element": "owl",
      "piece": "owl",
      "anims": {
        "Flap": {
          "frames": 6,
          "loop": true,
          "keys": [
            {
              "t": 0.0,
              "lift": 0,
              "rot": {
                "wing_near": 38,
                "wing_far": 30,
                "head": 0,
                "tail": 0
              }
            },
            {
              "t": 0.5,
              "lift": -6,
              "rot": {
                "wing_near": -34,
                "wing_far": -26,
                "head": -4,
                "tail": 6
              }
            }
          ]
        }
      }
    },
    "bolt": {
      "what": "the shared red / yellow shot (GDD SH1.0 OWL-14: one pointed angular geometry, colour by material; rotated in engine, not by frames). Stand-in: the four-point cross until card 0.41",
      "asset": "Bolt",
      "builder": "bolt",
      "layout": "FX_Owl_Missile.png",
      "px_per_unit": 30.0,
      "element": "effects",
      "piece": "owl-bolt",
      "anims": {
        "Still": {
          "frames": 1,
          "loop": false,
          "keys": [
            {
              "t": 0.0,
              "rot": {}
            }
          ]
        }
      }
    },
    "skyline": {
      "what": "the black jagged skyline layer (spires, gears, rock) along the bottom of the frame",
      "asset": "Skyline",
      "builder": "skyline",
      "frame_size": [
        1920,
        360
      ],
      "pivot_px": [
        0,
        360
      ],
      "faces": "right",
      "px_per_unit": 24.0,
      "element": "background",
      "piece": "skyline",
      "anims": {
        "Still": {
          "frames": 1,
          "loop": false,
          "keys": [
            {
              "t": 0.0,
              "rot": {}
            }
          ]
        }
      }
    }
  },
  "coverage_about": "GDD SH1.0 required animation and state coverage (ANIM-02..ANIM-08, ART-08, BG-03, BG-04, VFX-03..VFX-05) against what these recipes can render today. status `recipe`: a row above renders it now with the stand-in rig (gameplay placeholder quality, judged by the art loop). status `_PH`: the stand-in rigs cannot make it; gameplay uses the tracked placeholder named in `placeholder` (a still or a silhouette flipbook ending _PH) until the `replaced_by` card lands. `tool`: blender = a Blender recipe once the rig exists; unreal = an Unreal material / Niagara effect, not a Blender render. `pipeline_check.py --release` fails any _PH asset left in Content/ at G4; placeholders never ship. tests/test_art_coverage.py checks this list.",
  "coverage": [
    {
      "gdd": "ANIM-03",
      "family": "ella",
      "action": "overhead rise (legs together, V-split, together)",
      "status": "recipe",
      "tool": "blender",
      "recipe": "ella.IdleFloat",
      "why": "canopy open and lift bob render now; the leg V-split needs leg bones (card 0.38)"
    },
    {
      "gdd": "ANIM-03",
      "family": "ella",
      "action": "RegularFall for Small / Twin / Needle",
      "status": "recipe",
      "tool": "blender",
      "recipe": "ella.Fall"
    },
    {
      "gdd": "ANIM-03",
      "family": "ella",
      "action": "mode transitions (open, close)",
      "status": "recipe",
      "tool": "blender",
      "recipe": "ella.Open"
    },
    {
      "gdd": "ANIM-03",
      "family": "ella",
      "action": "mode transitions (close)",
      "status": "recipe",
      "tool": "blender",
      "recipe": "ella.Close"
    },
    {
      "gdd": "ANIM-05",
      "family": "ella",
      "action": "Small Blasts body: folded-ready, snap open, pulse, close, cock",
      "status": "recipe",
      "tool": "blender",
      "recipe": "ella.Attack",
      "why": "a low-hip pose today; the collar slide needs the second arm (card 0.38)"
    },
    {
      "gdd": "ANIM-05",
      "family": "ella",
      "action": "shoulder-braced Streamed Blast",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Ella_StreamBrace_PH",
      "replaced_by": "0.38",
      "why": "needs legs, a second arm on the shaft, scarf and mask in the Ella rig and an art-bible anims row"
    },
    {
      "gdd": "ANIM-03",
      "family": "ella",
      "action": "absorbing fall",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Ella_AbsorbFall_PH",
      "replaced_by": "0.38",
      "why": "needs legs, a second arm on the shaft, scarf and mask in the Ella rig and an art-bible anims row"
    },
    {
      "gdd": "ANIM-03",
      "family": "ella",
      "action": "compact closed-umbrella free fall",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Ella_FreeFall_PH",
      "replaced_by": "0.38",
      "why": "needs legs, a second arm on the shaft, scarf and mask in the Ella rig and an art-bible anims row"
    },
    {
      "gdd": "ANIM-03",
      "family": "ella",
      "action": "overhead hop",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Ella_Hop_PH",
      "replaced_by": "0.38",
      "why": "needs legs, a second arm on the shaft, scarf and mask in the Ella rig and an art-bible anims row"
    },
    {
      "gdd": "ANIM-03",
      "family": "ella",
      "action": "forward and back falling cartwheels, free-fall dash",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Ella_Dash_PH",
      "replaced_by": "0.38",
      "why": "needs legs, a second arm on the shaft, scarf and mask in the Ella rig and an art-bible anims row"
    },
    {
      "gdd": "ANIM-03",
      "family": "ella",
      "action": "hit and recovery",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Ella_Hit_PH",
      "replaced_by": "0.38",
      "why": "needs legs, a second arm on the shaft, scarf and mask in the Ella rig and an art-bible anims row"
    },
    {
      "gdd": "ANIM-03",
      "family": "ella",
      "action": "repair",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Ella_Repair_PH",
      "replaced_by": "0.38",
      "why": "needs legs, a second arm on the shaft, scarf and mask in the Ella rig and an art-bible anims row"
    },
    {
      "gdd": "ANIM-03",
      "family": "ella",
      "action": "living critical state",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Ella_Critical_PH",
      "replaced_by": "0.38",
      "why": "needs legs, a second arm on the shaft, scarf and mask in the Ella rig and an art-bible anims row"
    },
    {
      "gdd": "ANIM-03",
      "family": "ella",
      "action": "bounded zero-health dissolve",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Ella_Dissolve_PH",
      "replaced_by": "0.38",
      "why": "needs legs, a second arm on the shaft, scarf and mask in the Ella rig and an art-bible anims row"
    },
    {
      "gdd": "ANIM-05",
      "family": "ella",
      "action": "Twin Stars low-hip paired release",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Ella_TwinStars_PH",
      "replaced_by": "0.38",
      "why": "needs legs, a second arm on the shaft, scarf and mask in the Ella rig and an art-bible anims row"
    },
    {
      "gdd": "ANIM-05",
      "family": "ella",
      "action": "Needle low-hip steady pulse",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Ella_Needle_PH",
      "replaced_by": "0.38",
      "why": "needs legs, a second arm on the shaft, scarf and mask in the Ella rig and an art-bible anims row"
    },
    {
      "gdd": "ANIM-04",
      "family": "ella",
      "action": "whole-character condition states (boots fade by 75, hat by 50, living mask and scarf)",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "T_Ella_Condition_PH",
      "replaced_by": "0.38"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "identity hover / wingbeat",
      "status": "recipe",
      "tool": "blender",
      "recipe": "owl.Flap",
      "why": "front-view stand-in; the side profile with vane wings is card 0.37"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "wing wear and disabled-gust state",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_WingsDamaged_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "clock cover open / close",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_ClockCover_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "clock glass, cracks and the long hand (double beat XII to III)",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_ClockHand_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "wing gather, flap, front and recovery (gust)",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_Gust_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "EMPTY-claw talon warning, rake, recovery",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_Talon_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "CLOSED-claw front armillary grasp and release",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_FrontCast_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "middle cage curved cast",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_MiddleCast_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "rear gear first stroke, safe pause, second stroke",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_RearCast_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "harmless returns and settle",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_CastReturn_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "surviving-mechanism sets 7 to 6 to 4 to 0",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_Mechanisms_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "break stun and recovery",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_Stun_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "exposed eye, eye hit",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_Eye_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "blackout body hide and restore",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_Blackout_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "phase and retry initialization",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_PhaseReset_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-06",
      "family": "keeper",
      "action": "living departure into darkness",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_Keeper_Departure_PH",
      "replaced_by": "0.37",
      "why": "the stand-in owl has no feet, chains, mechanisms, clock hand or side profile"
    },
    {
      "gdd": "ANIM-08",
      "family": "enemy",
      "action": "WardenSundial F: idle, locomotion, turn, tell, aim, fire (red and yellow), recoil, recovery, hit, wear, defeat",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_WardenSundialF_Actions_PH",
      "replaced_by": "0.39",
      "why": "no enemy builder in stand_ins.py yet"
    },
    {
      "gdd": "ANIM-08",
      "family": "enemy",
      "action": "WardenSundial M: idle, locomotion, turn, tell, aim, fire (red and yellow), recoil, recovery, hit, wear, defeat",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_WardenSundialM_Actions_PH",
      "replaced_by": "0.39",
      "why": "no enemy builder in stand_ins.py yet"
    },
    {
      "gdd": "ANIM-08",
      "family": "enemy",
      "action": "WardenArmillary F: idle, locomotion, turn, tell, aim, fire (red and yellow), recoil, recovery, hit, wear, defeat",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_WardenArmillaryF_Actions_PH",
      "replaced_by": "0.39",
      "why": "no enemy builder in stand_ins.py yet"
    },
    {
      "gdd": "ANIM-08",
      "family": "enemy",
      "action": "WardenArmillary M: idle, locomotion, turn, tell, aim, fire (red and yellow), recoil, recovery, hit, wear, defeat",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_WardenArmillaryM_Actions_PH",
      "replaced_by": "0.39",
      "why": "no enemy builder in stand_ins.py yet"
    },
    {
      "gdd": "ANIM-08",
      "family": "enemy",
      "action": "WardenEscapement F: idle, locomotion, turn, tell, aim, fire (red and yellow), recoil, recovery, hit, wear, defeat",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_WardenEscapementF_Actions_PH",
      "replaced_by": "0.39",
      "why": "no enemy builder in stand_ins.py yet"
    },
    {
      "gdd": "ANIM-08",
      "family": "enemy",
      "action": "WardenEscapement M: idle, locomotion, turn, tell, aim, fire (red and yellow), recoil, recovery, hit, wear, defeat",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_WardenEscapementM_Actions_PH",
      "replaced_by": "0.39",
      "why": "no enemy builder in stand_ins.py yet"
    },
    {
      "gdd": "ANIM-08",
      "family": "enemy",
      "action": "Floodstrider F: idle, locomotion, turn, tell, aim, fire (red and yellow), recoil, recovery, hit, wear, defeat, stilt stepping and height changes",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_FloodstriderF_Actions_PH",
      "replaced_by": "0.39",
      "why": "no enemy builder in stand_ins.py yet"
    },
    {
      "gdd": "ANIM-08",
      "family": "enemy",
      "action": "Floodstrider M: idle, locomotion, turn, tell, aim, fire (red and yellow), recoil, recovery, hit, wear, defeat, stilt stepping and height changes",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_FloodstriderM_Actions_PH",
      "replaced_by": "0.39",
      "why": "no enemy builder in stand_ins.py yet"
    },
    {
      "gdd": "ANIM-08",
      "family": "enemy",
      "action": "Courier F: idle, locomotion, turn, tell, aim, fire (red and yellow), recoil, recovery, hit, wear, defeat, hover and flight",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_CourierF_Actions_PH",
      "replaced_by": "0.39",
      "why": "no enemy builder in stand_ins.py yet"
    },
    {
      "gdd": "ANIM-08",
      "family": "enemy",
      "action": "Courier M: idle, locomotion, turn, tell, aim, fire (red and yellow), recoil, recovery, hit, wear, defeat, hover and flight",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "FB_CourierM_Actions_PH",
      "replaced_by": "0.39",
      "why": "no enemy builder in stand_ins.py yet"
    },
    {
      "gdd": "ANIM-08",
      "family": "world",
      "action": "broad current / catch / return fields, refuge, yellow bay, mill sweep, shutter, bellows front",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "T_Env_Fields_PH",
      "replaced_by": "0.41"
    },
    {
      "gdd": "BG-03",
      "family": "background",
      "action": "atmosphere set (cloud, mist, water, wind, clock face and hands, sky, clock ridges)",
      "status": "_PH",
      "tool": "blender",
      "placeholder": "T_Env_Atmosphere_PH",
      "replaced_by": "0.41"
    },
    {
      "gdd": "BG-04",
      "family": "background",
      "action": "architecture (barn, factory, school, chapel; upright and inverted) and land",
      "status": "recipe",
      "tool": "blender",
      "recipe": "skyline.Still",
      "why": "the skyline stand-in covers the far layer; the authored buildings are card 0.41"
    },
    {
      "gdd": "ART-08",
      "family": "ui",
      "action": "clock HUD: face, health hand, life hand, lit arc; XP ring",
      "asset_ids": ["UI-XP-01"],
      "status": "_PH",
      "tool": "blender",
      "placeholder": "T_HUD_Clock_PH",
      "replaced_by": "0.40"
    },
    {
      "gdd": "ART-08",
      "family": "ui",
      "action": "menu environments, animated Pause backdrop, Journey Complete art",
      "asset_ids": ["UI-WIN-01"],
      "status": "_PH",
      "tool": "blender",
      "placeholder": "T_Menu_Backdrop_PH",
      "replaced_by": "0.40"
    },
    {
      "gdd": "VFX-03",
      "family": "vfx",
      "action": "four spell families: release, travel or sustain, impact, end, cancel",
      "status": "_PH",
      "tool": "unreal",
      "placeholder": "NS_Spell_Families_PH",
      "replaced_by": "0.41"
    },
    {
      "gdd": "VFX-04",
      "family": "vfx",
      "action": "red and yellow launch, travel, impact, yellow pull-in and capture, heal confirmation",
      "status": "recipe",
      "tool": "blender",
      "recipe": "bolt.Still",
      "why": "the shot head renders now; trails and capture are Unreal effects (card 0.41)"
    },
    {
      "gdd": "VFX-05",
      "family": "vfx",
      "action": "Keeper effects: warnings, gust front, clock beat, stun, slow ring, eye, blackout, departure",
      "status": "_PH",
      "tool": "unreal",
      "placeholder": "NS_Keeper_Effects_PH",
      "replaced_by": "0.41"
    }
  ]
}
```

### `pipeline/art/blender/plan.py`

Usage text from the file:

```text
Render jobs for the Blender stand-ins (stdlib only; tools/assetgen.py blender and the tests import it).

A job is everything render_sprite.py needs, so the Blender side reads no repo file itself:
  character, anim, builder, frame size, pivot (pixel the rig's origin lands on), facing, px_per_unit, fps, loop,
  one pose per frame, the colours (style.json palette + accents by name), the look, the output names.
Sources (pipeline/art/blender/characters.json `_about`): the recipe row, the references.json `layout` entry it names
(SpriteLayout.json: frame_size, pivot_px, faces, fps), the style.json `anims` row (fps and allowed frame count).
A recipe that disagrees with them (a frame count the art bible does not allow, an unknown layout sheet) is refused.

  python3 pipeline/art/blender/plan.py --character owl --anim Flap --out-dir Art/Source/Owl/Raw/Flap   print the job
```

Tests: `tests/test_art_coverage.py`, `tests/test_art_ship.py`

### `pipeline/art/blender/stand_ins.py`

Usage text from the file:

```text
Blender stand-ins for the game's sprites: build, rig, shade (runs inside Blender; render_sprite.py imports it).

Every builder makes its parts in world units at rest, facing +X, with the rig's origin at the world origin (the
pixel the layout's pivot_px names), binds each part rigidly to one bone (vertex group + Armature modifier, parented
to the armature so a mirror flips it all) and returns the armature. Pose angles are degrees in the picture plane,
positive = counter-clockwise as the camera sees it (+Z toward -X).
Look (pipeline/art/blender/characters.json `look`): toon ramps in near-black palette shades with paper grain in the
material, emission-only accents (gold clock and star, amber eyes, rust-red bolt), Freestyle ink lines, one sun from
the front slightly above (art bible R11), transparent film, Standard view transform.
Add a character: write build_<name>(mats, rnd) here, add its recipe to characters.json. Revise the look for the art
loop here or in the recipe; never in the checks.
```

Tests: `tests/test_art_coverage.py`

### `pipeline/art/blender/render_sprite.py`

Usage text from the file:

```text
Render one job's frames headless (run by Blender, never by python3):

  blender -b --factory-startup -P pipeline/art/blender/render_sprite.py -- --job <job.json>

The job (pipeline/art/blender/plan.py, written by tools/assetgen.py blender) names the builder, frame size, pivot,
facing, poses and look. Builds the stand-in (stand_ins.py), keys every pose on its frame, renders each frame to its
PNG (orthographic, transparent, ink-and-paper NPR), saves the .blend next to the frames (the provenance input), and
prints one line tools/assetgen.py reads:
  BLENDER_RENDER version=<x.y.z> frames=<n> blend=<path> freestyle=on|off compositor=on|off
Exit 1 on any error (Blender's own exit code stays 0 after a Python error, so the script exits itself).
```

Tests: `tests/fixtures/gdd13/pipeline/art/blender/stand_ins.py`, `tests/test_art_ship.py`, `tests/test_assetgen.py`

## Import and provenance

### `pipeline/art/import-rules.md`

#### Unreal import rules for art (on demand: Asset Specialist, Art Director, Technical Director)

Load this for any card that imports or changes a texture, sprite or flipbook, and at each gate.
The rules are data in `pipeline/art/style.json` (`unreal_import`, `anims`, `naming`) and are checked by
`tools/sprite_check.py`. Status: **proposed**. No engine was installed when they were written, so every
Unreal property, enum and ini key name below is [VERIFY] until card 0.4a reads it from 5.8.4.

##### 1. Project defaults (Config), set once in card 0.3
`python3 tools/sprite_check.py --config Config` must print PASS. It reads:

| File | Section | Key | Rule |
|---|---|---|---|
| DefaultEditor.ini | `[/Script/Paper2DEditor.PaperImporterSettings]` | `DefaultSpriteTextureGroup` | set, not `TEXTUREGROUP_Pixels2D`; equals `unreal_import.texture.lod_group` once D-new-art-texgroup sets it (proposed `TEXTUREGROUP_UI`) |
| | | `bOverrideTextureCompression` | `True` |
| | | `DefaultSpriteTextureCompression` | `TC_EditorIcon` (UserInterface2D) |
| | | `UnlitDefaultMaskedMaterialName` | `/Paper2D/MaskedUnlitSpriteMaterial.MaskedUnlitSpriteMaterial` |
| | | `UnlitDefaultTranslucentMaterialName` | `/Paper2D/TranslucentUnlitSpriteMaterial.TranslucentUnlitSpriteMaterial` |
| | | `bPickBestMaterialWhenCreatingSprites` | set. True or False is open (decision row requested: D-new-art-pickbest, proposed False). The check moves to `equals` once decided |
| | | `DefaultPixelsPerUnrealUnit` | set; equals `unreal_import.pixels_per_unit` once card 0.10 fills it (D-new-port-10) |
| DefaultEngine.ini | `[/Script/Paper2D.PaperRuntimeSettings]` | `bResizeSpriteDataToMatchTextures` | `True` (a D13 2×→1× switch keeps pivots and collision) |
| | | `bEnableSpriteAtlasGroups` | `False` (experimental) |

All key names [VERIFY on 5.8.4]. A missing `Config/` prints SKIP until card 0.3 merges; after that CI runs it with `--require-dir`
(CI step requested from the TD; until it lands, card 0.3's PR pastes `--config Config --require-dir` PASS).
`python3 tools/sprite_check.py --uproject UmbrellaElla.uproject` must print PASS: Plugins lists `{"Name": "Paper2D", "Enabled": true}` and no `PaperZD`.

##### 2. Per-asset rules (editor dump)
`python3 tools/sprite_check.py --import-report Saved/ArtDump.json` prints one error per broken rule per asset.
The dump is made inside the editor by `tools/ue/art_dump.py` over `/Game/UmbrellaElla/Art`. The script does not exist yet.
Card 0.4d (owner Technical Director agent, gate patch applied by the TD human; after 0.4a and 0.10b, before 0.10) writes it [VERIFY the 5.8.4
`-run=pythonscript` / commandlet name]. Its output is an envelope; a hand dump is the bare `assets` list:

```
{"tool": "tools/ue/art_dump.py", "root": "/Game/UmbrellaElla/Art", "assets": [ ...one object per asset... ]}
{"class": "Texture2D",  "name", "filter", "srgb", "compression", "never_stream", "lod_group", "mip_gen", "width", "height",
 "sheet": {"grid": [w, h], "margin", "spacing"} (copied from the source PNG's .sprite.json sidecar)}
{"class": "PaperSprite","name", "kind" (optional, from the sheet sidecar), "material", "collision", "atlas_group", "pivot_mode",
 "pivot", "render_geometry", "width", "height", "sockets": [{"name", "location": [x, y]}], "pixels_per_unit",
 "texture" (source texture name), "source_uv": [x, y], "source_size": [w, h]}
{"class": "PaperFlipbook","name", "fps", "keyframes": [{"sprite": "SPR_<Asset>_<Anim>_NN", "frame_run": 1}, ...]}
```
Source properties [VERIFY]: `Filter`, `SRGB`, `CompressionSettings`, `NeverStream`, `LODGroup`, `MipGenSettings`;
`DefaultMaterial`, `SpriteCollisionDomain`, `AtlasGroup`, `PivotMode`, `CustomPivotPoint`, render geometry mode, `Sockets` (each `SocketName` and `LocalTransform` X, Z),
`PixelsPerUnrealUnit`, `SourceTexture`, `SourceUV`, `SourceDimension`; `FramesPerSecond`, `KeyFrames` (each `Sprite` and `FrameRun`).
The sidecar is found from the texture's source file path (`AssetImportData`) [VERIFY].
The format contract is `tests/fixtures/art_dump/anchors.json` (the 5 anchors). It must print errors=0; the same file with one
texture set to `TF_Nearest` must print errors=1 (`tests/test_sprite_check.py`). The dump script's own test should reuse it.
An empty dump or an unknown class is an error, so a dump that found nothing never passes.

| Rule | Error when |
|---|---|
| filter | Filter is `TF_Nearest` |
| srgb | sRGB off |
| compression | not `TC_EditorIcon` (UserInterface2D) |
| stream | NeverStream off |
| texture_group | `TEXTUREGROUP_Pixels2D` (unfiltered group); once `unreal_import.texture.lod_group` is set, any other group (World has mips and LOD bias) |
| mips | per D13 (`unreal_import.texture.mips`: null until decided; `mips` needs mips and power-of-two, `none` needs no mips) |
| material | by kind: silhouette and tile need the unlit masked material; only fx may use unlit translucent. Kind = dump `kind`, else `kind_prefixes` (`SPR_FX*` fx, `SPR_Paper*`/`SPR_Rock*` tile), else silhouette |
| collision | sprite collision not None |
| atlas | any atlas group set |
| pivot | mode differs from `required_pivot` for the asset prefix (Ella, Spikes Bottom_Center; Shot, Cross, Flyer Center_Center; Rock Bottom_Left), or not in the allowed list; or sprites of one `SPR_<Asset>_` differ in pivot across any of its anims |
| ppu | sprites differ in `pixels_per_unit`, or differ from `unreal_import.pixels_per_unit` once set |
| geometry | sprite over 256 px using Full Rect (`SourceBoundingBox`) render geometry (overdraw) |
| socket | `SPR_Ella_*` without a `Muzzle` socket (name proposed); a socket with no `location`; one socket moving more than `socket_drift_max_px` (2) in x or y across the frames of one `SPR_<Asset>_<Anim>` set |
| fps / frames | `FB_<Asset>_<Anim>` FramesPerSecond outside the `anims` row; unique keyframe sprites outside its frame range; a keyframe that is not `SPR_<Asset>_<Anim>_NN`; `_NN` not ascending (unless the row says `"order": "any"`); the same sprite twice in a row (use `frame_run`); more than 60 unique sprites over all flipbooks (jam cap) |
| grid | a `SPR_<Asset>_<Anim>_NN` frame whose `source_uv` or `source_size` is not cell NN of its texture's `sheet` grid (cells counted left to right, then top to bottom, after margin and spacing), or whose texture has no `sheet` [VERIFY that Grid-mode Extract Sprites keeps the full cell and numbers every cell, empty ones too] |
| dump | empty dump, or a class other than the three above |
| gate (only with `--gate`) | not the `art_dump.py` envelope with root `/Game/UmbrellaElla/Art`; `unreal_import.status` not `verified`; `unreal_import.texture.mips` null (D13 open); `unreal_import.texture.lod_group` null (D-new-art-texgroup open); a frame whose texture is missing from the dump |

Done when (each gate): `python3 tools/sprite_check.py --import-report Saved/ArtDump.json --gate` on the script's dump of all of
`Content/UmbrellaElla/Art` prints PASS errors=0, pasted in the gate record. So a gate cannot pass before 0.4a (names), 0.4d
(script) and D13 (mips). D13 cutoff and its default are requested in `docs/decisions.md` (proposed: before card 0.10, default `none`).

###### Card 0.4d done-when (the card row is in `pipeline/day0-cards.md`)
Owner Technical Director agent; kickoff applies its gate patch (`tools/git_gate.py apply --auto`). Lane: `tools/ue/art_dump.py`, `pipeline/art/style.json`, `pipeline/art/import-rules.md`. After 0.4a and 0.10b, before 0.10.
- `tools/ue/art_dump.py` runs headless on `/Game/UmbrellaElla/Art` and writes the envelope above to `Saved/ArtDump.json`.
- On the 5 anchors, `--import-report` prints errors=0, the same as `tests/fixtures/art_dump/anchors.json`.
- With one anchor texture set to `TF_Nearest` in the editor, it prints errors=1 (`filter`). Both outputs pasted.
- With one `SPR_Ella_Open_NN` Muzzle socket moved 4 px, it prints errors=1 (`socket`): the dump writes each socket's `location`.
- Its own test loads `tests/fixtures/art_dump/anchors.json` as the format contract.
- Every property, enum, ini key and texture group name in this file and in `style.json` is read from 5.8.4 and pasted
  on the card. `grep -c VERIFY pipeline/art/import-rules.md` prints 0, and `style.json unreal_import.status` is `verified`.
- Naming Template: Extract Sprites, Grid mode, on one anchor sheet, with `SPR_<Asset>_<Anim>_{0}`. The card pastes the
  names it made. If they are not 2-digit (`_0` instead of `_00`), the card adds the rename step (section 3 fallback),
  runs it on that sheet, and pastes `--names` PASS.
- The texture group the dump reports for the anchors is pasted, so D-new-art-texgroup can set `lod_group`.
The rule logic is tested in `tests/test_sprite_check.py` with a fixture that breaks each rule once.

###### Until `art_dump.py` exists: hand dump (Technical Director)
The rules do not change. The TD writes the dump by hand instead of the script, then runs the same command.
1. In the editor, open each new or changed `T_`, `SPR_`, `FB_` asset in the card. Copy each field in the schema above from its
   Details panel into `Saved/ArtDump.json` (not committed). Flipbooks: list every keyframe's sprite and frame run, in order.
2. Run `python3 tools/sprite_check.py --import-report Saved/ArtDump.json`.
3. Paste in the PR: the PASS line with errors=0, the asset count in the dump, and the line `hand dump by <TD name>`.
Done when: errors=0 is pasted, and the dump's asset count equals the number of `.uasset` files the PR adds or changes under
`Content/UmbrellaElla/Art` (`git diff --name-only origin/main | grep -c 'Content/UmbrellaElla/Art/.*\.uasset'`).
A hand dump never covers a gate. Gates need the script's dump of the whole folder; `--gate` fails a bare list.

##### 3. Names
`python3 tools/sprite_check.py --names Content/UmbrellaElla/Art` checks every `.uasset` name:
`^(T|SPR|FB)_<Asset>_<State or Anim>(_NN)?(_PH)?$`, no `_v2`, `_final`, `_new`.
Frames: `SPR_<Asset>_<Anim>_<NN>`, 2 digits from 00. Extract with Extract Sprites, Grid mode, Naming Template
`SPR_<Asset>_<Anim>_{0}` [VERIFY the token and zero-padding on 5.8.4], using the sheet's cell, margin and spacing from its sidecar.
Fallback if 5.8.4 cannot pad (card 0.4d finds out): after extracting, rename each `_N` frame to `_0N` in the editor
(Python `unreal.EditorAssetLibrary.rename_asset`, run from the Output Log [VERIFY]), never with file tools.
`--names` flags an unpadded frame and points here. Done when: `--names` prints PASS on the sheet's folder.

##### 4. Umbrella width
`python3 tools/sprite_check.py --width-ratio <open sheet.png> <closed sheet.png>` must print PASS: the narrowest open frame's
opaque box is at least `sprite.umbrella_width_ratio_min` (1.8) times the widest closed frame's. Grid comes from each sheet's sidecar.

##### 5. Engine colour (swatch)
`python3 tools/make_art_calibration.py --swatch <path>` writes the palette swatch. Placed under `CAM_Eval_Swatch`, its
capture must pass `python3 tools/art_check.py --swatch <capture>` (every cell ΔE76 ≤ 3). Set `style.json swatch.rect`
to where the swatch lands in the capture. Re-run on any trigger in `art-director.md` step 10.

##### 6. Optional 3D source by Blender script (Art Director choice; off by default)
Only when the Art Director picks a 3D source for a prop or background, on the card. Otherwise this path does not exist.
- The model is a Python script that Blender runs headless (`blender -b -P <script>.py`). Never hand-edit the mesh:
  fix the one script line and re-run it.
- Simple shapes only (primitives, extrusions, bevels). No realistic meshes.
- The script renders a sprite. The sprite goes through the normal gates: `sprite_check.py` on the sheet and
  `art_check.py` on the in-engine capture. The colour bible (`pipeline/art/art-bible.md`, `style.json`) applies to
  every output, as it does for drawn sprites.
- `pipeline/art/provenance.csv` records the script as the source: `tool` = Blender, `origin` = the script path.
- A downloaded model needs a CC licence in its provenance row, and a script decimates it to low-poly before render.
Source: R12 in `docs/references.md`.

### `pipeline/art/provenance.csv`

```csv
asset_path,author,origin,tool,model_version,prompt,seed,input_images,date,licence,attribution
pipeline/art/reference/target-keyart.png,unknown (shared in chat by Josh; Josh to confirm),unknown (Josh to confirm),unknown,unknown,unknown,unknown,unknown,2026-11-06,unknown (Josh to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-0258_Ricky_1.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-0328_Ricky_1.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-0331_Ricky_1.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-0348_Ricky_1.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-0512_Ricky_1.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-0800_Ricky_1.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-1047_Ricky_1.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-1047_Ricky_2.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-1048_Ricky_1.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-1048_Ricky_2.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-1048_Ricky_3.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-1049_Ricky_1.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261110-1220_Ricky_1.png,Ricky (team),"Discord #art-direction, Ricky, 10 Nov",unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261111-0318_Ricky_other-realm.png,Ricky (team),"Discord #art-direction, Ricky, 2026-11-11T03:18Z",unknown,unknown,unknown,unknown,unknown,2026-11-11,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261111-0319_Ricky_roadwarden-sundial-casters.png,Ricky (team),"Discord #art-direction, Ricky, 2026-11-11T03:19Z (JPEG, stored as PNG for the judge)",unknown,unknown,unknown,unknown,unknown,2026-11-11,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/20261112-0443_Ricky_title-screen.png,Ricky (team),"Discord DM from Ricky to Josh (not #art-direction), 2026-11-12T04:43Z (11 Nov 8:43 PM PT, before the jam start)",unknown,unknown,unknown,unknown,unknown,2026-11-12,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/discord/index.json,Ricky (team),Discord #art-direction export (index of Ricky's posts),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/keyart-crops/owl-bolt.png,same as the key art (Josh to confirm),"crop of the team key art pipeline/art/reference/target-keyart.png, keyed to an alpha mask (11 Nov); reference only",none,none,none,none,pipeline/art/reference/target-keyart.png,2026-11-11,same as the key art; reference only and never shipped,none
pipeline/art/reference/keyart-crops/umbrella.png,same as the key art (Josh to confirm),"crop of the team key art pipeline/art/reference/target-keyart.png, keyed to an alpha mask (11 Nov); reference only",none,none,none,none,pipeline/art/reference/target-keyart.png,2026-11-11,same as the key art; reference only and never shipped,none
pipeline/art/reference/keyart-crops/wind-lines.png,same as the key art (Josh to confirm),"crop of the team key art pipeline/art/reference/target-keyart.png, keyed to an alpha mask (11 Nov); reference only",none,none,none,none,pipeline/art/reference/target-keyart.png,2026-11-11,same as the key art; reference only and never shipped,none
pipeline/art/reference/keyart-crops/skyline.png,same as the key art (Josh to confirm),"crop of the team key art pipeline/art/reference/target-keyart.png, keyed to an alpha mask (11 Nov); reference only",none,none,none,none,pipeline/art/reference/target-keyart.png,2026-11-11,same as the key art; reference only and never shipped,none
pipeline/art/reference/Rehearsal/Ella/Ella-Absorbing-04.png,team (GameJam2026 main),Rehearsal/Art/Sprites/Ella/Absorbing/Ella-Absorbing-04.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Rehearsal/Ella/Ella-FreeFall-03.png,team (GameJam2026 main),Rehearsal/Art/Sprites/Ella/FreeFall/Ella-FreeFall-03.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Rehearsal/Ella/Ella-Rising-02.png,team (GameJam2026 main),Rehearsal/Art/Sprites/Ella/Rising/Ella-Rising-02.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Rehearsal/Ella/Ella-Shooting-03.png,team (GameJam2026 main),Rehearsal/Art/Sprites/Ella/Shooting/Ella-Shooting-03.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Mockups/missile-pattern-reference.png,team (GameJam2026 main),Mockups/missile-pattern-reference.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Mockups/originalPicture.png,team (GameJam2026 main),Mockups/originalPicture.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/CHR_Owl_Flap_Damage.png,team (GameJam2026 main),Test_Assets/CHR_Owl_Flap_Damage.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/CHR_Witch_Cast.png,team (GameJam2026 main),Test_Assets/CHR_Witch_Cast.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/CHR_Witch_Guard_Transition.png,team (GameJam2026 main),Test_Assets/CHR_Witch_Guard_Transition.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/ENV_GothicSkyline_Tile.png,team (GameJam2026 main),Test_Assets/ENV_GothicSkyline_Tile.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/FX_Owl_Missile.png,team (GameJam2026 main),Test_Assets/FX_Owl_Missile.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/FX_Owl_Missile_Hit.png,team (GameJam2026 main),Test_Assets/FX_Owl_Missile_Hit.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/FX_Owl_Missile_Travel.png,team (GameJam2026 main),Test_Assets/FX_Owl_Missile_Travel.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/FX_Umbrella_Repair.png,team (GameJam2026 main),Test_Assets/FX_Umbrella_Repair.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/FX_Wand_Star_Travel.png,team (GameJam2026 main),Test_Assets/FX_Wand_Star_Travel.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/FX_Wind_Curl.png,team (GameJam2026 main),Test_Assets/FX_Wind_Curl.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/PROP_Umbrella_Stance_Damage.png,team (GameJam2026 main),Test_Assets/PROP_Umbrella_Stance_Damage.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/SKY_StarPaper_Tile.png,team (GameJam2026 main),Test_Assets/SKY_StarPaper_Tile.png (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/SpriteLayout.json,team (GameJam2026 main),Test_Assets/SpriteLayout.json (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/Test_Assets/Asset Notes.md,team (GameJam2026 main),Test_Assets/Asset Notes.md (GameJam2026 main),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/v1.4/gameplay-01.png,team (GDD v1.4 draft),scratch/gdd/v1.4/art-references (local draft),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
pipeline/art/reference/v1.4/gameplay-02.png,team (GDD v1.4 draft),scratch/gdd/v1.4/art-references (local draft),unknown,unknown,unknown,unknown,unknown,2026-11-10,unknown (team to confirm); reference only and never shipped,none
```

## Checklists and templates

### `pipeline/checklists/animation-review.md`

#### Animation, tiling and audio review (Art Director and Asset Specialist, on demand)

Load this for any card that adds a flipbook, a tiling asset, or a sound.

##### Flipbooks
- [ ] Judged in motion: a clip from a packaged or Standalone build at the gameplay camera, showing
      move → open → close → attack → hurt. Stills alone never approve a flipbook or umbrella-state art.
- [ ] Every frame keeps the same design: umbrella stripe count and handle, Ella's proportions, outline weight.
      No boiling outline. The umbrella never vanishes between frames.
- [ ] The bottom-center pivot does not drift. The opaque bounding box's bottom-center moves ≤ 2 px across the frames of every
      silhouette sheet with an `"anim"`, one-shots (Open, Close, Attack, Hit, Death) included (proposed, D-new-port-13).
      Measured by `sprite_check.py`. A sidecar may raise it with `"pivot_drift_max_px"` only with a `"pivot_drift_reason"`. Paste the PASS line.
- [ ] One pivot per asset across all its anims (idle and Open must not jump): `--import-report` fails a mixed set.
- [ ] Keyframes play in ascending `_NN` with holds as `frame_run`, never a repeated sprite (`--import-report`).
- [ ] Frame count and fps fit the `anims` row in `style.json`: the sidecar's `"anim"` for the sheet, `--import-report` for the `FB_` asset.
- [ ] A `_PH` silhouette version of this flipbook was played in L_Graybox and its frame count confirmed before final frames.
- [ ] Each flipbook maps to one C++ state (named in the asset brief). It says loop or one-shot, and what interrupts it.
- [ ] Gameplay never waits on a flipbook. No damage window, state change or invulnerability starts on a flipbook's end or a frame event.

##### Tiling assets (paper background, landscape layers)
- [ ] Reviewed with at least 3 copies side by side in the engine. No visible seam. No obvious repeat pattern at 1080p.
- [ ] `sprite_check.py` with `"kind": "tile"` prints PASS: mean edge ΔE76 ≤ `seam_delta_e_max` (add `"tile_axes": "xy"` for paper that tiles both ways).

##### Sounds
- [ ] `python3 tools/audio_check.py --scan Audio/Source` PASS pasted; rules in `pipeline/roles/audio.md`.
- [ ] Every sound that signals a state (owl windups, player hurt, umbrella tear) has a matching visual. The game is playable muted.
- [ ] Provenance row filled, like art.

### `pipeline/templates/asset-brief.md`

#### Asset brief (add to every Asset Specialist card) and asset handoff (end of every asset PR)

A fresh session must be able to make the asset from the card alone. Every reference is a repo path.
"The image we discussed" is not a reference. A brief with an empty field is not ready.

##### Brief (in the card's Inputs)
```
Purpose:          <what the player must read from it, e.g. "umbrella is open, Ella will rise">
Anchors:          <repo paths of approved frames or the key art; traits to keep from each>
States / frames:  <exact list, e.g. idle-float 4, fall 3, open 3, close 3>
                  <for each flipbook: C++ state it shows, trigger, loop or one-shot, what interrupts it>
Size and pivot:   <the art-bible asset-spec row>
Sheet grid:       cell <W>x<H>, margin <px>, spacing <px> (goes into the .sprite.json sidecar)
Sockets:          <name, position in the sprite, same on every frame (`--import-report` fails a move over 2 px within one anim); e.g. Muzzle at the umbrella tip; or "none">
Motion pass:      _PH silhouette flipbook in L_Graybox, clip <link>, frame count confirmed by the Game Designer
Draw layer:       <the art-bible draw-order slot>
Tool:             <tool + plan, e.g. "image model X, free tier">; paid credits or sign-ups only by a named human with a `Spend OK:` link (agent-ops.md)
Banned:           cutting from the key art, prompts naming living artists or others' IP, pixel-art look, white or flat background
Paths:            Art/Source/<Asset>/** and Content/UmbrellaElla/Art/<Asset>/**
Gates:            art-director.md gates + pipeline/checklists/animation-review.md if animated
Generation budget: <max generations per state, e.g. 6>
Stop if:          budget used, or 3 review rounds in a row with the same gap and no better score (D-new-no-round-cap)
Receiving card:   <Integrator card ID that places it>
```
VFX briefs also state purpose, duration and draw layer. No full-screen flash.

##### Handoff (last section of the asset PR)
```
Assets:      <T_/SPR_/FB_ paths>
State map:   <FB_ asset → C++ state>
Pivot:       <per sprite>
Sockets:     <name and position per sprite, or none>
Checks:      sprite_check --scan, --names, --import-report output (errors=0)
Collision:   sprite collision None (gameplay collision is on the actor)
Generations used: <n of budget>
Known limits: <or "none">
Next:        <Integrator card ID>
```

## Art judge

### `evals/art-judge/README.md`

#### Art judge eval

The art loop's critic (`tools/art_loop.py`) uses this blind X/Y protocol per piece: ours against one of the piece's references from `pipeline/art/references.json`, labels stripped, order random, a fresh session that sees nothing of the builder. `tools/art_judge.py` and `tools/art_ref_check.py` are its deterministic half.

Two judges, in order. The numeric one runs first and cannot be overridden.

1. **Numeric:** `tools/art_check.py` on each in-engine capture (palette, hue bands, accent area, silhouettes).
2. **LLM judge:** the Art Director role in a fresh session, using the gate list in
   `pipeline/roles/art-director.md` and the blind X/Y protocol: the capture as X against the key art as Y, with the
   team's own art (`pipeline/art/references.json`, `python3 tools/art_check.py --references`) as style context.
   Pass/fail per gate with a location in the image. No 1–10 scores (numeric scores drift between runs and hide
   which gate failed).

No human signs off art (Josh, 2026-11-10). `python3 tools/art_check.py --gate <capture>` runs the whole gate: the
team's references are present, the numeric check passes, the judge is calibrated (below) and the capture's X/Y row
has every rubric row true. The Art Director agent re-places or regenerates until it prints `ART_GATE: PASS`.

##### Calibration (run before judging; void the review if it fails)
Build the set once the reference is in the repo:
```
python3 tools/make_art_calibration.py pipeline/art/reference/target-keyart.png evals/art-judge/calibration/
```
| Image | Expected numeric | Expected LLM judge |
|---|---|---|
| reference (G1, the key art) | PASS | approve: the known-good anchor until G2 exists (the judge is blind to where an image came from) |
| first in-engine style frame that passed `art_check.py --gate` (G2, add to `anchors/`) | PASS | approve |
| B1_colorful | FAIL | request_changes |
| B2_pixelated | may pass (shape problem) | request_changes (pixel-art auto-fail) |
| B4_grey_silh | FAIL | request_changes |
| B5_flat_white | FAIL | request_changes |
| B6_gold_flood | FAIL (`accent_area`) | request_changes |
| B7_crushed | FAIL (`dark_share`) | request_changes |

Each review session: shuffle the candidate with 1 known-good in-engine anchor and 2 known-bad images, unlabelled.
The review counts only if the judge approves the anchor and rejects both known-bad. Until G2 exists the anchor is
the key art reference; the known-bad images are made from it (`make_art_calibration.py`).

Bars (see docs/audit.md section 5):
- 100% of known-bad images rejected, 100% of known-good approved, across the full set (7/7-style agreement).
- Pin the judge as (model, prompt version). Re-run the full calibration set when either changes.
- Stability: run one borderline capture 3 times. If the verdict flips, the gate FAILs and the Art Director agent splits the
  gate wording (a prompt change: a gate patch, new rubric version, re-run the calibration).
- Revisions are judged blind as X/Y in both orders; both orders must agree. Full protocol, rubric rows and the pairwise calibration set: [`blind_pairwise.md`](blind_pairwise.md).

##### Judge pin
Judge pin: model `claude-opus-5-5`, prompt `art-judge-xy/3`, rubric `rubric/2`.
The model id is proposed (decision requested). Every `agreement.csv` row's `model` must equal it, and the prompt
and rubric versions must equal the header of `tools/art_judge_prompt.md` (`tests/test_art_judge_record.py`).
A new pin voids the calibration: re-run the full set.

##### Run record (required before an art verdict counts)
One schema for `evals/art-judge/agreement.csv`, the same as `blind_pairwise.md` "Agreement with the human":
`date,pair_id,seed,model,prompt_version,rubric_version,judge_closer,judge_rows_x,judge_rows_y,order_stable,expected_closer,note`.
A calibration pair (`blind_pairwise.md` table) is one row: `expected_closer` is the table's expected winner, `note` is `calibration`.
A row agrees when `judge_closer` equals `expected_closer` and `order_stable` is `yes`.
Until the file holds one full run for the pinned judge with every row agreeing, `art_check.py --gate` FAILs and no art
verdict counts. This file is a gate path: the run is recorded as a gate patch kickoff applies once per pin (`tools/git_gate.py apply --auto`).
A candidate's own X/Y row (`pair_id` `<capture stem>:target-keyart`, X = the capture, `judge_rows_x` = `all` when every
rubric row is true, else the false rows; `expected_closer` `-`, `note` `gate`) goes in the judge log
`Saved/art-judge/judge-log.csv`, which `art_check.py --gate --judge` reads.
`tests/test_art_judge_record.py` fails if `anchors/` has files but no such run is recorded, if a row disagrees,
or if this file and `blind_pairwise.md` list different columns.

`tests/test_art_check.py` runs the numeric half of this table automatically once
`pipeline/art/reference/target-keyart.png` exists.

### `evals/art-judge/blind_pairwise.md`

#### Blind pairwise art judge (X/Y)

The LLM half of the art gate. The numeric half (`tools/art_check.py`, `tools/sprite_check.py`) runs
first and its FAIL is final. This protocol only decides what numbers cannot: shape language,
readability, lighting consistency, artifacts. Nothing here has been run against a model yet; it is the protocol to run.
The judge model is pinned in `evals/art-judge/README.md` ("Judge pin").

Prompt: `tools/art_judge_prompt.md` (prompt `art-judge-xy/3`, rubric `rubric/2`).
Art gate run: X = the in-engine capture, Y = the key art (`pipeline/art/reference/target-keyart.png`); the team's
pictures in `pipeline/art/references.json` with `judge: true` go in as style context, never as candidates.

##### What the judge answers
- Eleven boolean rubric rows (R1–R11), each pinned to a line in `pipeline/art/art-bible.md` or a key in
  `pipeline/art/style.json`, per image, each with a location. A `true` without a location is `false`.
- One comparison: which of X and Y is closer to the standard, or `tie`.
- No numeric scores. A judge that returns a number instead of a boolean is a failed run.

##### Order and blinding
1. The runner names the two images `X` and `Y` only. File names, dates, PR numbers, "old/new",
   "anchor" and "known-bad" never reach the judge.
2. Order is random per run, from a seed written in the run record. Each pair is judged twice, in
   both orders (A as X, then B as X). Both orders must give the same winner and the same per-image
   booleans. A flip on any row is a disagreement: that row is reported as "unstable", the verdict
   on that pair does not count, and a human decides.
3. One session per pair. The judge never sees its own earlier verdicts.

##### Calibration set (run before a judging session; void the session if it fails)
| Pair | Expected `closer` | Expected rubric rows |
|---|---|---|
| anchor vs B1_colorful | anchor | B1: R3 false |
| anchor vs B2_pixelated | anchor | B2: R9 false |
| anchor vs B4_grey_silh | anchor | B4: R2 false |
| anchor vs B5_flat_white | anchor | B5: R1 false |
| anchor vs B6_gold_flood | anchor | B6: R4 false |
| anchor vs B7_crushed | anchor | B7: R2 false |
| anchor vs anchor (same image) | tie | identical booleans in both positions |

Known-bad images come from `python3 tools/make_art_calibration.py <anchor or reference> <out dir>`.
The anchor is the key art reference until G2 exists, then G2: the first in-engine style frame that passed
`art_check.py --gate`, saved in `evals/art-judge/anchors/`. No human picks either one.

Bar: 7/7 pairs correct in both orders (14/14 runs), and the expected false row hit in each.

##### Ground truth
The calibration set is the ground truth: the team's own key art and the known-bad images made from it, so no human
verdict is needed (Josh, 2026-11-10: art direction is not a human checkpoint).
- Each calibration pair is logged with the judge's verdict in `evals/art-judge/agreement.csv` with columns
  `date,pair_id,seed,model,prompt_version,rubric_version,judge_closer,judge_rows_x,judge_rows_y,order_stable,expected_closer,note`.
- Report agreement as `matches / pairs` on `closer`, counting unstable pairs as misses. Bar: 7/7.
- A calibration miss voids the judge: `art_check.py --gate` FAILs until a new pin passes the full set.

##### Pinning
A calibration result is valid only for one exact (model id, `prompt_version`, `rubric_version`),
written at the top of each run record. Changing any of the three, or editing `art-bible.md` or the
style.json thresholds the rubric cites, voids the calibration: re-run the full set.

##### Stability
Run one borderline pair 3 times with different seeds. If the winner or any row flips, the rubric row
that flipped is too vague: the Art Director agent splits or rewords it in a gate patch (kickoff applies it, `tools/git_gate.py apply --auto`),
which bumps `rubric_version`.

### `evals/art-judge/agreement.csv`

```csv
date,pair_id,seed,model,prompt_version,rubric_version,judge_closer,judge_rows_x,judge_rows_y,order_stable,expected_closer,note
```

### `evals/art-judge/critic-calibration.json`

```json
{
 "_about": "The blind calibration set every art-loop critic session is checked on (tools/art_loop.py blind/judge). Each session folder holds the pair being judged among two calibration pairs it cannot tell apart: a crude render below against a team image of the same element (the team image must win) and a crude render against a one-pixel-shifted copy of itself (SAME). A session that misses either does not count; three counted sessions per pair, unanimous, are a panel. Answers are logged in the evals/art-judge/agreement.csv columns to Saved/Logs/pipeline/critic-calibration.csv. The crude renders are the first Blender stand-ins (11 Nov), which every element they target fails on the numeric judge (tests/test_art_calibration.py).",
 "crude": [
  {"file": "tests/fixtures/art/crude/ella_idle_crude.png", "elements": ["ella-up-open", "ella-shield", "umbrella"]},
  {"file": "tests/fixtures/art/crude/ella_attack_crude.png", "elements": ["ella-attack", "ella-closed"]},
  {"file": "tests/fixtures/art/crude/owl_flap_crude.png", "elements": ["owl"]},
  {"file": "tests/fixtures/art/crude/bolt_crude.png", "elements": ["owl-bolt", "bolt-hit", "wand-shot", "umbrella-repair"]},
  {"file": "tests/fixtures/art/crude/skyline_crude.png", "elements": ["skyline", "paper", "wind-lines", "wind-zone", "menu-screen", "scene"]}
 ]
}
```

### `tools/art_judge_prompt.md`

#### Art judge prompt (blind X/Y)

Prompt version: `art-judge-xy/3`. Rubric version: `rubric/2` (below). Any edit to this file bumps
the version it touches, and the calibration in `evals/art-judge/blind_pairwise.md` must be re-run
before the judge's verdicts count again.

The runner fills the `{...}` slots. It never tells the judge which image is old, new, the anchor or a
known-bad image. Images are named only `X` and `Y`. For the art gate X is the in-engine capture and Y the key art;
`{style_references}` is every picture in `pipeline/art/references.json` with `judge: true`
(`python3 tools/art_check.py --references --json`, which adds the current GDD's embedded images).

---

You are judging two images of the same game scene, image X and image Y, against a fixed art standard.
The team's own art is attached as style context only (never one of X or Y): {style_references}. You do not know which one is newer, which one a person made, or which one is expected
to win. Do not guess. Judge only what is visible.

The standard is the art bible below and the numbers from `pipeline/art/style.json`:

{art_bible}

Palette and limits (from style.json): {style_json_palette_and_thresholds}

Numeric gate already run on both images (`tools/art_check.py --json`). A FAIL here is final and
you cannot override it; you still answer every question:
X: {art_check_json_x}
Y: {art_check_json_y}

For EACH image, answer every question with `true` or `false` and a location in the image
("bottom-left rock band", "Ella, centre-left"). A `true` with no location counts as `false`.
No scores, no ratings, no 1–10 numbers.

| id | question (true = meets the standard) | source |
|---|---|---|
| R1 | Background is aged, mottled paper; not flat, not white | art bible pillar 1, auto-fail "white or flat background" |
| R2 | Ella, enemies, ground and hazards read as near-black silhouettes; interior detail is dark-on-dark | pillar 2; style.json `dark_l_max`, `dark_share_*` |
| R3 | The only saturated hues are gold/amber and rust red | pillar 3; style.json `hue_gate`, `off_style_max` |
| R4 | Gold/amber and rust are small accents, not large areas | style.json `accent_area_max` |
| R5 | Umbrella open vs closed is readable from the silhouette alone | readability rule 1 (open width ≥ 1.8× closed) |
| R6 | Player shots (gold-white) and danger (rust) are in different hue families | readability rule 2 |
| R7 | Spikes differ from walkable rock by shape and a rust edge | readability rule 4 |
| R8 | Wind lines and sparkles are faint decoration and cannot be mistaken for gameplay objects | pillar 4 |
| R9 | Painted edges are smooth: no pixel-art stair-stepping or Nearest-filter shimmer | import settings; auto-fail "pixel-art look" |
| R10 | No watermark, signature, garbled text, extra limbs, melted gears or other AI artifacts | auto-fail list |
| R11 | Every asset is lit the same way: interior highlights and dark-on-dark detail all suggest one light from the front, slightly above; no normal-map or lit-material shading | art bible Import settings (no normal maps, one assumed light) |

Then answer one comparison question: `closer`: which image is closer to the standard, `X`, `Y` or
`tie`, decided only by the rubric rows where the two images differ. If no row differs, answer `tie`.

Reply with only this JSON object:
```
{"X": {"R1": [true, "where"], ..., "R11": [true, "where"]},
 "Y": {"R1": [true, "where"], ..., "R11": [true, "where"]},
 "closer": "X" | "Y" | "tie",
 "deciding_rows": ["R3", ...]}
```

## Commands and checks

### `tools/art_check.py`

Usage text from the file:

```text
Deterministic art-direction check for IN-ENGINE screenshots (not source PNGs).

It measures a screenshot against the numbers in pipeline/art/style.json:
  on_palette    share of pixels close to an approved palette color (ΔE76 in CIELAB)
  off_style     share of strongly saturated pixels that match no approved color
  accent_area   share of pixels that are accent colors (gold / rust)
  dark_share    share of near-black silhouette pixels (L* below a cutoff)
  off_band      share of colorful pixels (chroma C* above a floor) whose hue is outside
                the allowed gold and rust bands. This catches "colorful storybook" drift.
  accents       style.json "accents" (D-new-palette-accents): the quality-bar colours (wind ash blue, the shot reds
                and yellows), each with a role, a hue and chroma band and a max share of the frame. A pixel off the
                palette that matches an accent in its band is on-palette and never off_style or off_band; the
                accents' shares (accent_<role>, accent_extra) fail past their caps.
  paper_texture share of side-by-side sampled pixel pairs (both lighter than the silhouette cutoff) whose
                L* differs by at least texture_delta_l. Painted paper varies pixel to pixel; a flat
                graybox, a flat fill or a near-uniform frame scores near 0 and fails paper_texture_min.

It is the cheap, objective half of the art gate. The LLM judge (evals/art-judge, blind X/Y against the key
art) covers what numbers cannot: shape language, mood, readability. No human approves art: `gate` below is the
whole art-direction check, and the Art Director agent regenerates or re-places until it passes.

Usage:
  python3 tools/art_check.py Saved/Screenshots/shot.png
  python3 tools/art_check.py --json shot.png
  python3 tools/art_check.py --extract reference.png   # print dominant colors to seed the palette
  python3 tools/art_check.py --measure-palette reference.png  # re-centre each named palette colour on the
    reference pixels nearest to it (within delta_e_tolerance). Prints the measured hex per name and the
    reference's own numbers, so card 0.7 can write them into style.json and set palette_status: measured.
  A provisional palette is a FAIL once the reference file exists (card 0.7 not done).
  python3 tools/art_check.py --swatch swatch_capture.png  # engine colour round-trip (CAM_Eval_Swatch)
    The capture shows the swatch sprite from make_art_calibration.py --swatch. Each cell's centre
    (inset by style.json swatch.inset) is averaged and compared with its palette hex. Any cell over
    swatch.delta_e_max (ΔE76) fails: fix tonemapping or post-process before judging any art.
  python3 tools/art_check.py --references [--json]   # the team's art references (pipeline/art/references.json,
    plus the images the current GDD embeds and every image under the team's art folders, Assets/ and Mockups/,
    references.json team_art): present or MISSING, then a `team art:` line with how many team images joined.
    Exit 1 while a required one is missing or a team-art image cannot be read.
  python3 tools/art_check.py --gate CAPTURE [--judge Saved/art-judge/judge-log.csv]
    The automated art gate. PASS needs all four: every required reference is present; the numeric check above
    passes on CAPTURE; the judge is calibrated (evals/art-judge/agreement.csv holds the calibration pairs of
    blind_pairwise.md for the pinned model, prompt and rubric, every row agreeing and order-stable); and the
    judge log holds the blind X/Y row `<capture stem>:target-keyart` (X = the capture, judged in both orders)
    with every rubric row true for X (`judge_rows_x` = all). Prints one `ART_GATE: PASS|FAIL ...` line.
Exit code 0 = pass, 1 = fail, 2 = usage/input error.
```

Tests: `tests/test_art_calibration.py`, `tests/test_art_check.py`, `tests/test_art_ship.py`, `tests/test_art_swatch.py`, `tests/test_art_thresholds.py`, `tests/test_day0_cards.py`, `tests/test_gdd_select.py`, `tests/test_smoke_visual.py`

### `tools/screen_check.py`

Usage text from the file:

```text
Deterministic "no debug or placeholder visuals" check for a screenshot of the DEFAULT build (stdlib only).

art_check.py scores the frame as a whole (palette, paper texture). This check looks for the local things a whole-frame
score can average away, and for the 16:9 lock:
  flat     a large region of one flat colour that is close to a filled rectangle (area >= flat_area_min of the frame,
           bounding-box fill >= rect_fill_min): an untextured primitive, a flat-fill gameplay zone (a solid teal wind
           box), a plain placeholder card. The art bible's etched style is never a flat fill (pipeline/art/art-bible.md)
  grey     a smaller flat near-neutral grey box (area >= grey_area_min): a hitbox or collision debug draw, an engine
           default primitive, a grey stand-in under an actor
  outline  a one-colour rectangle outline (a DrawDebugBox-style frame) whose box is >= outline_area_min of the frame
  aspect   the gameplay view inside the letterbox/pillarbox bars (near-black uniform strips in matching pairs at the
           frame edges) is 16:9 within --aspect-tol; with no bars the whole frame must be 16:9. A 2560x1080 screenshot
           with no bars is gameplay that was not locked to 16:9 (pipeline/unreal-rules.md, Display)
Bars are never flagged as flat. A region a human approved as part of the look (a HUD panel) is passed with
--ignore x,y,w,h (frame pixels); each ignore is printed so a reviewer sees it.

It runs by itself in every smoke (tools/ue_run.py smoke-log runs it on the hook's SMOKE_SHOT screenshot), so in the
daily and in kickoff; the PR pastes its line. Thresholds: pipeline/art/style.json `screen_check` (defaults below).

--strict (menu and tutorial captures) also fails small flat dots and boxes: placeholder stand-ins for control glyphs.
Usage: python3 tools/screen_check.py SHOT.png [--strict] [--aspect 16:9] [--aspect-tol 0.01] [--ignore x,y,w,h] [--json]
Prints `screen_check: PASS|FAIL image=<p> size=WxH view=WxH aspect=<a> bars=<none|letterbox|pillarbox> flat=<n>
grey=<n> outline=<n>`, one line per problem, and a FIX: line for the agent.
Exit 0 = pass, 1 = fail, 2 = usage or unreadable image.
```

Tests: `tests/test_art_ship.py`, `tests/test_screen_check.py`, `tests/test_smoke_visual.py`

### `tools/art_judge.py`

Usage text from the file:

```text
Automatic art judge (stdlib only): scores game art against the team's own reference images, so no human has to
approve a look. The references and what each one judges are in pipeline/art/references.json (references only,
never shipped: Official Rules §7(h)). art_check.py (palette, paper texture) and screen_check.py (no flat fills, no
debug draws, 16:9) run first and cannot be overridden; this judge adds what they cannot see.

  scene SHOT [--refs-root DIR ...]     a build screenshot against the key-art composition (references.json "scene"):
        owl large on the right, chest clock glowing gold inside it, Ella small on the left, a black jagged skyline
        band along the bottom, rust-red bolts, paper texture; plus a perceptual similarity to the scene references
        (16x9 luminance layout correlation and edge-orientation histogram on a downscaled frame). Prints
        `art_judge: scene PASS|FAIL score=<s> ...`, one line per miss and a FIX: line. The smoke runs it on every
        gameplay map's screenshot (tools/ue_run.py shot_checks), so the daily and kickoff do too.
  element ID CANDIDATE.png ... [--pick]  each candidate against that element's own references (Ella poses vs the
        Ella sheets, owl vs the owl refs, bolts and wand shots vs the effect refs, ...): silhouette mask overlap,
        edge-orientation histogram and palette fit on the first frame (a sheet's grid from its .sprite.json sidecar).
        --pick prints `art_judge: PICK <file> score=<s>` for the best passing candidate, or `art_judge: NONE` (exit 1:
        regenerate with tools/assetgen.py image and judge again; the same failure twice -> needs-human)
  coverage                             every reference in references.json is used by at least one judge element (or
        is judge_exempt with a reason: the pattern diagrams, the frame-grid data) and at least one card (a
        pipeline/day0-cards.md card, whose Done-when then runs art_judge.py, or an MVP item), and every element names
        known refs. Team art joined automatically (references.json team_art) is style context only and needs neither
        until it gets its own entry; a team-art image that cannot be read fails
Every reference is in this repo under pipeline/art/reference/ (Git LFS); --refs-root (repeatable, default this repo)
only matters for a copy elsewhere. A judge element with none of its references found FAILS: no reference is not a pass.
The per-card hard gate with the evidence line is tools/art_ref_check.py.
  calibrate [--write]                  the bar from the team's own art (Josh, 11 Nov): leave-one-out, each team image of an
        element scored against the element's other images; score_min = the lowest minus 0.02, detail_min (interior
        detail: a flat render or placeholder caps its score below any score_min) = the lowest team detail minus 0.02,
        scene similarity_min the same over the scene references. Only images under pipeline/art/reference/ count
        (the fixed set every repo has), so the numbers do not change with a repo's Assets/ studies. --write records
        every number in references.json.
The scene's layout ranges stay provisional until the first in-engine rebuild of the key art (card 0.10) is scored;
they are in references.json, so a recalibration is one reviewed edit.
Exit 0 = pass, 1 = fail, 2 = usage or unreadable input.
```

Tests: `tests/test_art_calibration.py`, `tests/test_art_check.py`, `tests/test_art_judge.py`, `tests/test_art_loop.py`, `tests/test_art_ship.py`, `tests/test_check_pr.py`, `tests/test_smoke_visual.py`

### `tools/art_ref_check.py`

Usage text from the file:

```text
Hard gate: art made or placed by a card matches that card's own references (stdlib only).

Loads pipeline/art/references.json, takes the references that list the card in `cards`, and judges with
tools/art_judge.py against those only:
  --scene SHOT          a build screenshot or eval capture: art_check.py, screen_check.py and the key-art composition
                        judge (art_judge.py scene, similarity against the card's own scene references)
  --element ID FILE...  generated art for one judge element (ella-up-open, owl, owl-bolt, wind-zone, ...): the best
                        file must score at least the element's score_min against the card's references for it
Prints one line per check and the evidence line
  art_ref_check: PASS|FAIL card=<id> target=<scene|element:ID> score=<s> min=<m> refs=<hash12> commit=<sha> file=<name>
refs= is the first 12 hex of references.json's sha256 and commit= the HEAD it ran on, so tools/check_pr.py (rule
artref), kickoff's art gate and the card checks refuse a PASS made on another commit or an older or smaller
reference set. A FAIL is a failed build: regenerate (tools/assetgen.py image), rescale or reposition, run again; the
same FAIL twice raises NEEDS HUMAN. No human approves a look.
Usage: python3 tools/art_ref_check.py --card 0.10c --element wind-zone Art/Source/Scene/Raw/wind-*.png
       python3 tools/art_ref_check.py --card 0.10 --scene Saved/Screenshots/CAM_Eval_StyleFrame.png
Exit 0 = PASS, 1 = FAIL, 2 = usage (unknown card, a card with no references, an element the card has no refs for).
```

Tests: `tests/fixtures/kickoff/stub_agent.py`, `tests/test_art_loop.py`, `tests/test_art_ship.py`

### `tools/art_loop.py`

Usage text from the file:

```text
The art loop: art work does not stop until it reaches the bar the references set (stdlib only).

Every art card is split into its smallest judgeable pieces: one per judge element its references cover (an owl pose,
an Ella pose, each projectile, the wind zone, the skyline, the paper) plus `scene` (the full frame) when it has a
composition reference (pipeline/art/references.json). For each piece:
  1. a BUILDER session makes or revises the piece (its card's owner role);
  2. the deterministic checks run: art_check.py, screen_check.py, art_ref_check.py (the card's own references) and,
     for gameplay sprites, hitbox_check.py. A FAIL goes straight back to the builder;
  3. a separate CRITIC session with fresh context judges BLIND: our output and one of the piece's references, renamed
     X.png and Y.png in a random order, in an empty folder with a fixed prompt (critic_prompt). The critic never sees
     the builder's notes, the round number, file names, or which image is ours. It answers binary: WINNER: X, Y or
     SAME (indistinguishable in style and quality), and GAP: the single biggest thing the loser lacks. A number score
     is a refused verdict;
     Each round has two blind pairs: ours against one of the piece's references, and ours against the piece's
     quality-bar image (references.json quality_bar: the top tier, for detail and finish);
  4. the loop passes when the critic picks neither the reference nor the quality bar over ours (it picks ours, or
     SAME, in both pairs) AND every deterministic check passes. There is no round cap: the exit is reaching the bar.
Stuck rule instead of a cap (D-new-no-round-cap): when STUCK_ROUNDS (3) rounds in a row bring no improvement on both
the critic (the reference still wins, with the same gap) and the deterministic score (no new best), the piece raises
NEEDS HUMAN with the first and the
latest image and the critic's gap list. Any improvement resets the count, so a piece that keeps getting better keeps
going. Every round is logged (piece, round, verdict, gap, scores) to Saved/Logs/pipeline/art-loop.jsonl and the
SQLite journal (tools/journal.py), so progress is visible.
Evidence (tools/check_pr.py rule artloop, kickoff's art gate): a card closes only with an
`art_loop: PASS card=<id> piece=<p> verdict=<ours|same> rounds=<n> refs=<hash12> commit=<sha>` line for each of its
pieces on the current commit and references.json.

Blender art (pipeline/art/blender/; Josh, 11 Nov): the builder's revision each round is a change to the Blender
scene (the recipe, stand_ins.py or the look: model detail, materials, lines, light), rendered again with
tools/assetgen.py blender. A sprite sheet (a .sprite.json sidecar with more than one frame) is judged three ways each
round: one frame (picked by the seed) against a piece reference, one frame against the quality bar, and the whole
sheet in motion against a reference sheet (`motion` pair: identity, line weight, palette and pivot hold frame to
frame). The deterministic checks are measured here, never declared: art_ref_check.py for the piece, and for a sprite
screen_check.py's flat/grey/outline rules and art_check.py's colour rules (on_palette, off_style, off_band; the
share rules belong to the full frame, the `scene` piece). A labelled placeholder or a practice stand-in never passes.
Ship gate: a passing round writes `<file stem>.artloop.json` next to the file (sha256 of its bytes, every pair's
outcome, every check, refs=, the commit judged). tools/check_pr.py (rule artship) fails a PR that adds or changes
shipped art (an image under Art/ outside Art/Source/, or Content/*/Art|UI|VFX) without that record and a pasted
`art_loop: PASS ... file=<path> sha=<sha12> ...` line for the header commit; tools/submission_check.py art (and
assets) fails the package on any shipped image without it. No label, sign-off or human approval passes a piece:
the stuck rule asks for help, it never lowers the bar.

Stricter bar (Josh, 11 Nov): every round is judged by a PANEL of 3 fresh blind critic sessions per pair, and all
must answer ours or SAME, against EVERY reference image of the element (the scene's for `scene`), the quality-bar
image, every reference sheet in motion (a sheet) and, for an element piece, its in-engine context: the newest
capture made after the piece (the smoke's screenshot), against the key art. Each session folder hides the pair
among calibration pairs (evals/art-judge/critic-calibration.json: a crude render against team art, which must win;
a near-identical pair, SAME); a session that misses one does not count. Answers are logged in the
evals/art-judge/agreement.csv columns (Saved/Logs/pipeline/critic-calibration.csv). The numeric element judge's
score_min and detail_min, and the scene's similarity_min, are calibrated from the team's own art
(tools/art_judge.py calibrate, leave-one-out).

  pieces --card ID                          the card's pieces
  blind --card ID --piece P --ours FILE --out DIR [--seed N] [--kind reference|quality_bar|motion|context]
                                            one calibrated critic folder (lettered pairs, prompt.md); the key goes
                                            to DIR + ".key.json", outside the critic's folder
  panel --card ID --piece P --ours FILE --out DIR [--round N]   every critic folder of one round (PANEL per pair);
                                            each session's answer goes to <folder>.answer.md
  verdict --panel DIR --card ID --piece P [--checks fail]   read every answer, check calibration, unseal the keys,
                                            measure the checks, log the round, print pass|continue|stuck; a pass
                                            writes the record
  evidence --card ID                        print the art_loop PASS lines of this commit (exit 1 if a piece has none)
Exit 0 = ok / pass, 1 = not passed (continue or stuck), 2 = usage.
```

Tests: `tests/test_art_loop.py`, `tests/test_art_ship.py`, `tests/test_check_pr.py`, `tests/test_honest_jam.py`

### `tools/sprite_check.py`

Usage text from the file:

```text
Art Director / Asset Specialist gate for exported sprite sheets and flipbook frames (PNG).

Thresholds live in pipeline/art/style.json under "sprite" (one set per kind: silhouette, fx, tile).

Checks, per frame:
  size        all frames the same size; equal to --size if given; sheet divisible by --grid
  pow2        sheet (or each frame file) is power-of-two sized, when style.json require_pow2 is true or --pow2
  background  the 1-px border ring is transparent (share of visible border pixels <= border_visible_max),
              and the frame has transparent pixels at all (a flat background means it was not cut out)
  fringe      share of visible pixels that are semi-transparent (alpha between alpha_clear_max and
              alpha_solid_min). Masked sprite materials cut alpha at one value, so a wide soft edge turns
              into ragged holes. This is not a pixel-art rule: the art bible wants painted, filtered edges.
  halo        share of edge pixels (semi-transparent, or transparent next to a visible pixel) that are light
              (L* >= halo_l_min), measured only when the solid pixels are darker than that on average.
              A light matte bleeds into dark silhouettes under bilinear filtering.
  fill        alpha-mask fill ratio = visible pixels / bounding box of visible pixels. Too low: wispy shape
              that will not read; too high: a box, background not removed.
  dark        share of visible pixels with L* <= dark_l_max (silhouettes are near-black, art bible pillar 2)
  empty       a frame with no visible pixels (trailing empty cells of a sheet are allowed)
  pivot       silhouette sheets with "anim" or "loop": true (one-shots too): the feet point of each frame
              moves at most sprite.pivot_drift_max_px across frames (max minus min). Feet point = bottom-center
              of the lowest sprite.pivot_feet_rows opaque rows (sidecar "feet_rows" overrides), so an umbrella
              that opens to one side does not move it. A sidecar may raise the limit with "pivot_drift_max_px"
              + "pivot_drift_reason".
  anim        sidecar "anim" names a row of style.json "anims"; frame count and "fps" must fit that row
  seam        kind tile: mean delta E76 between the left and right edge columns (and top/bottom with
              "tile_axes": "xy") is at most seam_delta_e_max, so copies side by side show no seam

Other modes (rules in style.json; detail in pipeline/art/import-rules.md):
  --sources CONTENT SOURCE  every asset folder under CONTENT (Content/UmbrellaElla/Art) that holds a .uasset has a
              layered source (.psd, .kra, .ase, .aseprite) under SOURCE/<same folder>/ outside Raw/ (Art/Source),
              or the Blender scene it was rendered from (a .blend anywhere under that folder, Raw/ included),
              so every imported asset can be edited and re-exported (asset-specialist.md checklist)
  --names DIR          asset names under DIR (Content/UmbrellaElla/Art) match style.json "naming"
  --import-report F    an editor dump of texture/sprite/flipbook settings (JSON) meets "unreal_import"
  --config DIR         Config/*.ini carry the Paper2D import defaults in "unreal_import.config"
  --uproject FILE      the .uproject enables Paper2D and does not list PaperZD ("unreal_import.uproject")
  --width-ratio OPEN CLOSED   umbrella open vs closed sheet: opaque box width ratio >= sprite.umbrella_width_ratio_min

Usage:
  python3 tools/sprite_check.py sheet.png --grid 128x128 [--frames 6] [--kind silhouette]
  python3 tools/sprite_check.py frame_01.png frame_02.png ... [--size 128x128]
  python3 tools/sprite_check.py --scan Art          # every PNG under Art/ needs a <name>.sprite.json sidecar
     sidecar: {"kind": "silhouette", "grid": [128, 128], "frames": 6, "size": [128, 128],
               "margin": 0, "spacing": 0, "loop": true, "anim": "IdleFloat", "fps": 8,
               optional "pivot_drift_max_px": 3, "pivot_drift_reason": "<why this sheet may drift more>",
               optional "feet_rows": 6}
     a PNG with no sidecar FAILS unless a folder on its path is in sprite.sidecar_exempt_dirs (Raw, Reference)
     a sidecar PNG that is still a Git LFS pointer is a SKIP; with --fail-lfs-pointer it is a FAIL (use in CI)
  add --require-dir to fail when the scanned folder does not exist; add --json for machine-readable output
Exit 0 = pass (or nothing to check), 1 = fail, 2 = usage/input error.
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: Sprite sheets with a .sprite.json sidecar (skips LFS pointers and a missing Art/; the TD human adds --require-dir on card 0.10b)

Tests: `tests/fixtures/kickoff/stub_agent.py`, `tests/test_assetgen.py`, `tests/test_honest_jam.py`, `tests/test_pipeline_check.py`, `tests/test_sprite_check.py`

### `tools/make_art_calibration.py`

Usage text from the file:

```text
Build the art-judge calibration set from the reference key art.

Writes known-bad variants next to the reference so both judges can be tested against
them. The LLM judge must reject all of them. The reference itself is the known-good G1.

  B1_colorful    hues rotated and saturation boosted ("colorful storybook" drift)
  B2_pixelated   downsampled 4x and upscaled with nearest-neighbour (pixel-art look)
  B4_grey_silh   near-black silhouettes lifted to mid grey
  B5_flat_white  paper texture replaced by flat near-white
  B6_gold_flood  top quarter of the frame painted accent gold (accents meant to be rare)
  B7_crushed     whole frame darkened to 25% (silhouettes lost in a black frame)

The numeric check must FAIL B1, B4, B5, B6 and B7 (B6 on accent_area, B7 on dark_share).

Usage: python3 tools/make_art_calibration.py pipeline/art/reference/target-keyart.png evals/art-judge/calibration
       python3 tools/make_art_calibration.py --swatch Art/Source/Swatch/Export/T_Swatch_Palette.png
  --swatch writes the palette-swatch sprite: one flat cell per style.json palette entry, in order,
  swatch.cols per row, swatch.cell_px square. art_check.py --swatch reads its in-engine capture.
```

Tests: `tests/test_art_check.py`, `tests/test_art_swatch.py`, `tests/test_art_thresholds.py`

### `tools/png.py`

Usage text from the file:

```text
Minimal PNG reader (stdlib only) so checks run on every team machine and in CI
without installing Pillow. Supports 8-bit, non-interlaced grayscale, RGB, RGBA,
gray+alpha and palette images. That covers Unreal HighResShot / Screenshot output
and normal exports from Aseprite, GIMP and Photoshop.
```

Tests: `tests/fixtures/kickoff/stubbins.py`, `tests/test_art_check.py`, `tests/test_gdd_select.py`, `tests/test_hitbox_check.py`
