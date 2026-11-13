# Painting art with the image model (D-new-art-image-model; active only after the lead says "Spend OK")
- Paint 2D sprites and screens with `tools/assetgen.py image` (default provider gemini, Josh's prepaid Gemini credits; openai optional); every run stops at the
  hard spend cap IMAGE_SPEND_CAP_USD the lead gives with Josh's Spend OK. The blind panel, the quality
  bar and art_ref_check are unchanged: a painted piece ships only when the panel passes it.
- Prompts are text only for anything pre-jam (GDD ART-03, BG-02): describe the key art's look in words (pipeline/art/
  art-bible.md, the references' `what` notes); never pass the key art, pipeline/art/reference/ or a quality-bar image as an
  input image. assetgen refuses them.
- In-jam images we made may be inputs, for frame consistency: pass your own first passing frame when painting the next
  frame of the same sheet.
- Clean and cut each output into a sprite sheet with consistent frames (tools/assetgen.py clean, sheet), fixed pivot, the
  receiving contract's frame count and size; sidecar .sprite.json; tools/sprite_check.py must pass.
- Blender stays for real 3D, the Keeper's articulated parts and frame-consistent motion.
- Every image gets its provenance row and prompt log line (assetgen writes both). Paid calls only after Spend OK.
- Spend: Josh's Spend OK (Nov 12) is a hard total cap of $33.82 across every image call by every worker; the shared counter
  (IMAGE_SPEND_FILE) stops all calls at the cap. Spend on the pieces furthest from the bar and most seen first: Ella's
  four states, the Keeper, scene/skyline, UI screens, then effects and enemies. Paint few, judge, then paint again.
- When something goes wrong (an API error, a bad output, a piece not passing), check whether it is on us first: our request,
  prompt and parameters; our post-processing (cutting, background, scaling, colour space); our critic or check. Only then
  blame the model or the provider. Write the verdict in your status file like the triage rule: "ours: <what>" or "model".

## Method (research, Nov 12; Google pricing and docs)
- Price per image: gemini-3-pro-image $0.134 (1K-2K; thinking tokens add about 10%, counted in the spend counter),
  gemini-3.1-flash-image $0.067 (1K), gemini-2.5-flash-image $0.039. The $33.82 cap is about 250 Pro images. Check
  whether newer image models are on the key (free model list) before choosing.
- No alpha output. Paint on flat #00FF00 (or magenta), no cast shadows, no green in the subject, a 2-3 px light outline;
  key in HSV, grow the mask 1-2 px, despill; rembg/BiRefNet as a fallback. Keep paper grain OFF the sprite background
  (it bleeds into the key); add the grain back in the material/shader.
- Consistency: paint one canonical in-jam turnaround sheet per character (Ella, the Keeper) first; feed it as a reference on
  every pose (Pro takes up to 14 refs). Identity holds; animation frames drift (limbs, scale, line weight), so paint each
  state's frames as ONE strip in one image (3.1 flash has 1:4, 4:1, 1:8), not frame by frame.
- No seed control: lock one written style block plus 1-2 of our own approved in-jam images as style refs on every call.
- Always set aspect_ratio and image_size ("1K"/"2K") explicitly.
- Frames per state: 2-4 (agent default D-new-anim-frames; GDD ANIM-02 leaves counts to each receiving contract).
- No retry cap per piece (loop to the bar), but log spend per piece and triage "ours vs model" when a piece goes flat.

## Prompt review before any paid call (Josh, Nov 12)
Before a piece's first paid image call, a FRESH session (not the builder) reviews its prompt and writes the review next to
the piece (Art/Source/<Asset>/prompt.md and prompt-review.md, committed):
- It looks at the key art and the piece's references (viewing to describe in words is fine; they are never input images,
  GDD ART-03) and checks every visible trait is in the prompt in words: silhouette, proportions, costume, hair, umbrella
  parts (canopy, ribs, shaft, finial, handle), palette, line/ink and paper treatment, lighting.
- It checks the art bible and the GDD rows for that piece (ANIM-03 for Ella's states, the Keeper rows, ART/BG rows).
- Gemini best practice: a narrative description, not a keyword list; the pose first; one fixed style block; camera and
  framing stated (view, distance, aspect); negative constraints written as positive descriptions ("feet off the ground"
  not "no walking").
- The builder applies the review, then calls. The prompt and review are committed with the piece.

## Context capture (the in-engine pair)
Every full art-loop round needs a `context` pair: an in-engine capture newer than the piece (`tools/art_loop.py`
find_capture reads `Saved/Logs/pipeline/*-shot.png` or `Saved/Screenshots/`). A lane makes it itself, nobody else:
1. Import the candidate into the piece's `_PH` asset slot in your worktree (same name, so the game loads it; it stays a
   tracked `_PH` until the panel passes it).
2. Run the game with a real renderer (not `-nullrhi`), through the one launcher:
   `tools/build/run_game.sh -SmokeShot=Saved/Logs/pipeline/<piece>-shot.png -SmokeQuitAfter=15 [-SmokeSection=S<n>] [-SmokeMap=...]`
   (640x360 windowed, no sound, no crash reporter). Pick the section or map where the piece is on screen; a VFX piece
   needs the moment it plays (use the section's scripted run or the playtest hooks).
3. Run the panel round; the context pair now finds the capture.

## Where candidates live
Raw paints, keyed cuts and every round's candidate go under `pipeline/art/proof/<lane>/<piece>/` (not shipped, not
checked as game art). `Art/Source/` holds only what the game ships: the tracked `_PH` placeholder or a piece whose panel
passed, each with its sidecar. The gate's sprite_check, art_inventory and prejam checks read `Art/Source/` as shipped,
so a candidate left there fails the merge.

## Frame registration and jitter
A painted strip jitters when each pose lands a few pixels off its neighbour or a size off. `tools/assetgen.py frames` now
registers every cut through `tools/frame_register.py`: the anchor is the bottom-centre of the lowest 8 mask rows (feet or
umbrella handle; `--anchor-band N` per element), the scale is the width of the lowest 14% of the mask (`--span height|width|N`
to change it; it ignores a raised arm or a wing beat), each frame is scaled about its anchor to the strip's median (a pose
change beyond 0.8-1.25x is left alone) and moved so every anchor sits on one pixel. The anchor goes into `<stem>.frames.json`
and the sheet's `.sprite.json` (`anchor`, `anchor_band`, `span_mode`); `--no-register` skips it. The check is in
`sprite_check` and `art_loop.sprite_checks`: anchor offset and scale drift between consecutive frames (a loop also last to first)
FAIL above `frame_register.JITTER_LIMITS` (3 px, 2%), measured once on the team's reference animations
(`pipeline/art/reference/Test_Assets`: Witch Cast and Owl Flap loops 0 px / 0%, the Witch Guard Transition 2.5 px as the largest
real motion; the numbers and source are in that file). Lanes cut with `frames` and need no script of their own.
