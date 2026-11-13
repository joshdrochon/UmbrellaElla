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

## Blocked: the proof (3 paid calls) needs GEMINI_API_KEY in the generating shell
`python3 tools/keys.py status`: GEMINI_API_KEY missing (env and keychain). worker-rules.md says only the arena area may
source `~/.umbrella-ella.env`, so this worker did not. Cap and counter are set (IMAGE_SPEND_CAP_USD=33.82,
logs/image-spend.json, no calls yet). Needs from the lead, one of:
- run the commands below in one shell that sources the key file (lean: the key never enters a worker session), or
- tell this worker it may source `~/.umbrella-ella.env` in the one generating shell, like the audio areas.
Not run because of this: image-models, the 3 calls, art_ref_check, the blind panel, the consistency verdict,
the cost per image.

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
