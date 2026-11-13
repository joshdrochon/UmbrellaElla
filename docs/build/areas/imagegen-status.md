# imagegen status (D-new-art-image-model)

## Done (no paid call, fake client only)
- Area file 1-4 (commit 3490f5b): gemini (default) and openai providers in `tools/assetgen.py image`, key through
  tools/keys.py (never printed), full provenance row + `<stem>.request.json` + prompt log line, GDD ART-03 / BG-02
  pre-jam input guard, one shared locked spend counter (IMAGE_SPEND_FILE) with the hard total cap
  (IMAGE_SPEND_CAP_USD), clear NO KEY / NO CAP / NO COUNTER / CAP REACHED results, never a placeholder.
- Lead's method (docs/build/art-image-model.md), commit 5bb1cb5:
  - aspect ratio always sent; gemini 3.x needs `--image-size` (it sets the price); 1:4, 4:1, 1:8, 8:1 only on 3.1 flash.
  - prices: 2.5 flash $0.039; 3 Pro $0.134 at 1K/2K, $0.24 at 4K; 3.1 flash $0.067 at 1K (0.5K/2K/4K [VERIFY]).
  - Pro thinking tokens counted: 25% of the image price reserved before the call, then settled from the reply's
    `thoughtsTokenCount` ($12/M) and `promptTokenCount` ($2/M on Pro). An overrun above the reserve is still counted.
  - `image-models`: the free models.list on the key, each image model marked priced or UNPRICED.
  - `clean --chroma 00FF00`: HSV key, mask grown 1-2 px, edge despill; FAIL when the corners are not the key colour;
    WARN on green inside the subject or key colour enclosed by it; `--via rembg` fallback (rembg not installed here).
    2752x1536 in 13 s, pure Python.
  - `frames --count N`: one keyed strip cut into N equal frames on one bottom-centre baseline; records figure heights
    and their spread (scale drift) in `<stem>.frames.json`. Then `sheet`.
- Tests: `tests/test_assetgen_image.py` (15), `tests/test_assetgen_image_method.py` (15): all OK.
  `affected_tests.py --run`: one failure, `test_assetgen.AudioSteps.test_no_credits_left_...`. It fails the same
  way on plain `main` (checked in a detached main worktree): it counts main's 6 real audio placeholders. Not this area.

## Blocked: the key's Google project has no paid quota (Nov 13 01:57 UTC; cause `env`)
Lead unblocked the key (worker-rules.md ae9ad62). Done since: main merged; `tools/keys.py` strips whitespace and one
pair of matching quotes (test `KeyAsPasted`); the key loads (53 chars, env) with `set -a; . ~/.umbrella-ella.env`
(the file's GEMINI line has no `export`, so a plain `source` does not reach python). The FAIL line now carries the
vendor's message (it read the body twice before and lost it; test added).
- `image-models` (free) works: 6 image models. Priced: gemini-2.5-flash-image, gemini-3-pro-image-preview,
  gemini-3.1-flash-image-preview. UNPRICED (refused until priced): gemini-3-pro-image, gemini-3.1-flash-image,
  gemini-3.1-flash-lite-image (GA names; price them in asset-tools.json before use).
- Call 1 (turnaround, gemini-3-pro-image-preview 21:9 2K) failed twice, same error, refunded, $0.00 spent:
  `HTTP 429 ... Quota exceeded for metric: generativelanguage.googleapis.com/generate_content_free_tier_input_token_count, limit: 0`.
  The key's project is on the free tier: the prepaid credits are not attached to it, and the free tier gives 0 for
  this model. Stopped per the same-failure-twice rule; calls 2 and 3 not tried (they depend on call 1).
- Lead's fallback, one call on gemini-2.5-flash-image (free tier), turnaround prompt from the runbook, 21:9, no
  image size: same refusal, refunded, counter $0.000:
  `HTTP 429 ... generate_content_free_tier_input_token_count, limit: 0`. The free tier gives 0 on 2.5 flash too, so
  no model on this key can make an image until billing is linked. Stopped after that one call, as the lead asked.
  Not run: key/despill/cut/scale on a 2.5 flash sheet, art_ref_check.
- Needs (Josh): in AI Studio, link the key's project to the billing account that holds the prepaid credits (or make
  a key in the project that has them). Then rerun the runbook below unchanged.
Not run: the 3 images, art_ref_check, the blind panel, the consistency verdict, ours-vs-model notes, cost per image.

## Proof runbook (exact; outputs under Art/Source/ImageProof/, not the Ella art lane)
Locked style block and identity block, the same words in all three prompts; set them in the shell first:

    S="Style: dark painterly etched storybook illustration for a 2D side-view game sprite; ink and wash with fine etched
cross-hatching; a near-black silhouette that reads by shape alone (charcoal, soot and umber darks, interior detail
dark-on-dark), subdued bronze and warm ivory only as thin rim light; a clean 2-3 px warm ivory #EDE3CF outline around
the whole figure. Background: one perfectly flat solid pure green #00FF00 filling the canvas edge to edge: no gradient,
no paper texture, no grain, no vignette, no ground, no cast or drop shadow, no glow or light spill on the background.
Nothing in the figure is green: no green cloth, light, reflection or tint. No text, labels, numbers, grid lines, frames
or watermark."

    I="Ella: an adult woman, slim, airborne (never standing on ground), wearing a bent pointed witch hat, long dark brown
hair, a separate scarf, a layered worn dark dress, dark stockings and boots. Her face is fully concealed under a dark
cloth / mesh mask; two small separate gold #E9C46A eye glints are the only light on her. One slender umbrella: black
canopy with thin light ivory stripes, a small pointed crown finial at the canopy tip, and a separate narrow pierced
diamond (lozenge) clock-hand terminal at the free end of the shaft. Both hands grip the one shaft. No wand. Body,
hands, cloth and metal stay dark."

    python3 tools/assetgen.py image-models        # free; if a newer image model is listed, price it first
    # 1: canonical turnaround (text only)
    python3 tools/assetgen.py image --model gemini-3-pro-image-preview --aspect 21:9 --image-size 2K \
      --out Art/Source/ImageProof/ella_turnaround.png \
      --prompt "$S $I A character turnaround sheet of Ella: five items in one row, evenly spaced with wide green gaps,
    same height and scale, feet on one shared invisible baseline, toes pointing down as she floats: front view,
    three-quarter view, side profile facing right, back view, each holding the closed umbrella upright in both hands;
    then on the far right the same umbrella alone, open, seen from the side."
    # 2: idle (UP_OPEN, ANIM-03 overhead rise) strip, the sheet as the reference
    python3 tools/assetgen.py image --model gemini-3-pro-image-preview --aspect 21:9 --image-size 2K \
      --input Art/Source/ImageProof/ella_turnaround.png --out Art/Source/ImageProof/ella_idle_strip.png \
      --prompt "$S $I The attached sheet is Ella: keep her costume, proportions, mask, hat and umbrella exactly. One
    horizontal animation strip of 3 frames of Ella's idle hover, side view facing right, in one row, evenly spaced with
    wide flat green gaps, figures never touching, the same scale and line weight in every frame: she hangs below the
    open umbrella held straight overhead in both hands, canopy fully open above her, weight hanging, toes down.
    Frame 1 legs together; frame 2 legs in a small V split, dress swaying; frame 3 legs together, canopy a little higher.
    No kicking."
    # 3: ella-attack (ATTACK_DESCENT, Small Blasts) strip, same refs
    python3 tools/assetgen.py image --model gemini-3-pro-image-preview --aspect 21:9 --image-size 2K \
      --input Art/Source/ImageProof/ella_turnaround.png --out Art/Source/ImageProof/ella_attack_strip.png \
      --prompt "$S $I The attached sheet is Ella: keep her costume, proportions, mask, hat and umbrella exactly. One
    horizontal animation strip of 3 frames of Ella's attack while slowly falling, side view facing right, in one row,
    evenly spaced with wide flat green gaps, figures never touching, the same scale and line weight in every frame:
    both hands on the one shaft, the umbrella held level like a lance, the open canopy behind her on her left, the
    diamond clock-hand terminal at the front right end. Frame 1 ready; frame 2 one small separate gold #E9C46A magic
    pulse leaves the canopy ahead of her; frame 3 recoil, the pulse gone. The pulse is the only bright thing."
    # cut, frame, check (per strip; idle shown)
    python3 tools/assetgen.py clean --chroma 00FF00 --grow 2 --in Art/Source/ImageProof/ella_idle_strip.png \
      --out Art/Source/ImageProof/ella_idle_keyed.png
    python3 tools/assetgen.py frames --in Art/Source/ImageProof/ella_idle_keyed.png --count 3 \
      --out-dir Art/Source/ImageProof/Raw/Idle --stem ella_idle
    python3 tools/art_ref_check.py --card 0.10b --element ella-up-open Art/Source/ImageProof/Raw/Idle/ella_idle_0*.png
    python3 tools/art_ref_check.py --card 0.10b --element ella-attack Art/Source/ImageProof/Raw/Attack/ella_attack_0*.png
    python3 tools/art_loop.py panel --card 0.10b --piece ella-up-open --ours <frame> --out <dir>   # then one fresh
    # blind critic session per folder, then: python3 tools/art_loop.py verdict --panel <dir> --card 0.10b --piece ...

Choice made in the runbook: all three calls on 3 Pro at 21:9 2K (identity holds best, takes refs), not 3.1 flash at
4:1. 3 frames fit 21:9 at about 7:9 per cell. Expected spend about $0.45 (3 x $0.134 + thinking + inputs).

## Left after the key
The 3 calls, art_ref_check, the full blind panel, the consistency verdict (identity across sheet/idle/attack, scale
spread from frames.json), the "ours" problems triage and the cost per image from logs/image-spend.json, here.

## Proof run on gemini-3-pro-image-preview (Nov 13, after Josh linked billing; main merged at 028308f)
Billing link works: all 3 calls returned images, no 429. Shared counter: $0.416 of the $33.82 cap.

Cost per image (3168x1344, 21:9 2K, from logs/image-spend.json):
| call | inputs | thinking tokens | cost |
|---|---|---|---|
| 1 turnaround | 0 | 293 | $0.138 |
| 2 idle strip | 1 (sheet) | 278 | $0.139 |
| 3 attack strip | 1 (sheet) | 326 | $0.139 |
About $0.139 per image; the 25% thinking reserve is far above real use (about $0.004).

Checks (frames 01 used for the panel):
- clean: all three WARN on enclosed key px (idle 24686: the gap between arm and body, real).
- frames: idle height spread 6.3%, attack 8.5% (attack frame 3 is shorter).
- art_ref_check: idle PASS (0.695-0.732, min 0.398, closest ella-rising); attack FAIL (0.2, min 0.448).
- screen_check: PASS both. art_check colour rules: FAIL both (off_band 0.124 idle, 0.139 attack, max 0.01):
  the bronze/ivory rim light and brown ink sit outside the gold and rust bands.
- Blind panel (12 fresh Sonnet sessions, answers in Art/Source/ImageProof/Panel/*/*.answer.md):
  idle: verdict=reference (the reference beats ours), calibration 4/6 (2 sessions answered "A: SAME" without
  "WINNER:", counted as refusals; not rerun). attack: verdict=reference, calibration 6/6; ours beat the quality bar
  but lost to the reference. Both rounds -> continue. Neither piece can pass yet: no in-engine capture (context).

Consistency verdict: FAIL for the set.
- Sheet holds identity well: same hat, mask, gold glints, layered dress, boots, ivory outline in all four views.
- Idle keeps the identity (hat, mask, dress, boots, diamond terminal) but not the pose: one hand on the shaft, she
  stands/walks under the umbrella like a pedestrian instead of hanging below it; legs walk in frame 2.
- Attack keeps the costume and the level two-hand lance pose, but the strip is broken: ghost copies of the sheet's
  heads/torsos bleed in above each frame, green-tinted, so the cut frames carry stray hats (all 3 critics named it).
  The canopy sits behind her as asked, the pulse in frame 2 is the right gold.

Ours-vs-model notes (what is the model, what is our prompt/tools):
- Model: hair is a short bob in every image, not long (identity block says long). Closed umbrella held tip-down like
  a cane on the sheet; finial is a plain spike, never a crown. Back view drops the umbrella.
- Model: a reference image + 21:9 strip makes 3 Pro copy the sheet's layout into the strip (attack ghosts). Ours to
  try: send the single side-profile figure cropped from the sheet as the input, not the whole sheet.
- Ours (prompt): "hangs below the open umbrella held straight overhead in both hands" lost to the umbrella-walk
  prior; the idle prompt needs the arms-up pose stated as the first thing, and "feet do not touch, no walking".
- Ours (palette): the style block asks for bronze and warm ivory rim light, which art_check counts as off-band.
  The style block and the art_check bands disagree; that is a rule question for the Art Director, not a retry.
- Ours (tool): `clean`/`frames` provenance rows say tool "GIMP 3"; they are pure Python in tools/assetgen.py.
  Fix the provenance tool field (my lane, follow-up).

Not done: any retry (the lead asked for 3 calls only), in-engine capture, art loop round 2.

## Round 2 (Nov 13; main merged at c2f1142; outputs under Art/Source/ImageProof/R2/)
Done first: provenance tool name fixed (clean/frames/crop write "tools/assetgen.py (pure Python)", not GIMP 3; tests);
new `assetgen.py crop` (one figure from a painted sheet, the strip reference). Prompt review per
docs/build/art-image-model.md: draft prompts in Art/Source/ImageProof/prompt.md, a fresh Sonnet session in an empty
/tmp folder (copies of the key art, the umbrella crop, Ella-Rising-02, Ella-Shooting-03, round 1 outputs, the art
bible, GDD ART-03..07, ANIM-02..05, Ella shared identity, Small Blasts body; Bash/Edit/Write disallowed) wrote
prompt-review.md; applied in full with its three leans: idle 4 frames (style.json IdleFloat [4, 6]), two in-jam
inputs (side profile + open umbrella cropped from the new sheet), the pulse kept as a separate object. (A first
review session ran on Opus by mistake; discarded unread, rerun on Sonnet per worker-rules.)

Calls (3 Pro, 21:9, 2K): sheet $0.141, idle $0.141, attack $0.141. Shared counter $0.840 of $33.82.

| | round 1 | round 2 |
|---|---|---|
| Sheet: hair | short bob | long, to mid-back, all views |
| Sheet: back view | dropped the umbrella | holds it |
| Sheet: finial | plain spike | still a spike (collar added); crown only in attack frame 1 |
| Idle pose | one hand, walking under the umbrella | same: one hand, walking (pose wording failed twice) |
| Idle identity | kept | kept (hat, mask, long hair, scarf, diamond terminal) |
| Idle height spread | 6.3% | 0.1% |
| Idle art_ref_check | PASS 0.695-0.732 | PASS 0.729-0.744 |
| Attack identity | kept costume; ghost heads from the sheet | no ghosts, but no hat, no mask: bare visible face (breaks GDD ART-06) |
| Attack layout | ghosts | each frame inside a drawn black box; legs walking |
| Attack pose | level lance at chest | shaft at hip, canopy behind, pulse ahead of the terminal (as asked) |
| Attack height spread | 8.5% | 12.5% (box borders cut as figures) |
| Attack art_ref_check | FAIL 0.2 | FAIL 0.2 |
| art_check off_band (max 0.01) | 0.124 / 0.139 | 0.070 / 0.084 (still FAIL) |
| Panel idle | reference wins, cal 4/6 | reference wins (both pairs), cal 5/6 |
| Panel attack | reference wins, beat QB, cal 6/6 | reference wins, beat QB, cal 5/6 |
| Cost | $0.416 | $0.424 |

Consistency verdict: FAIL for the set. The sheet now holds the full identity; the idle strip keeps it; the attack
strip loses hat and mask (a bare face), so the three images are not one character.

Ours vs model:
- Idle walk, same failure twice: ours first. The side-profile input shows her standing, umbrella closed at her side;
  the model copied that stance over the text ("do not copy the pose" did not hold). Next to try: no figure input on
  the idle call (text + the open-umbrella crop only), or a sheet whose side view already hangs from an open umbrella.
- Attack face: model (the input shows the mask, and I asks for it); ours possible: the prompt grew to ~550 words with
  the identity block last. Next to try: identity block before the frame list, shorter frame text.
- Attack boxes: model (S asks for no frames or grid lines). Our `frames` reads each box as one figure; a box-strip
  needs cropping by thirds first.
- Finial: model; three wordings now, still a spike on the sheet.
- off_band: still the style block's bronze/ivory rim vs the art_check bands; rule question for the Art Director.
- screen_check aspect FAIL when run standalone on a sprite frame (round 1's frame too); the art_loop verdict runs it
  in sprite mode and passes. Not a defect in the art.

ROUND2: not improved
