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

## Shared references
An art lane may add its own lane name to the `cards` list of a reference in `pipeline/art/references.json` that its
pieces are judged against (additions only; never edit or remove another lane's entries). That is in-lane, not a
cross-lane edit.

## Shared layers (Josh, Nov 13)
A piece built on another passed piece is judged only on what it adds. In `pipeline/art/references.json` an element may
carry `"base": "<piece>"`, `"base_mode": "reuse" | "repaint"` and `"new": "<what it adds>"` (the critic brief; `base_region`
`[x, y]` places the base inside a reuse piece). `reuse` (UI background, backdrop stages, gear on a shared body): the base's
shipped pixels must match inside the derived image (`tools/art_share.py reuse_check`, 98 percent of the base's opaque pixels
within 8/255); a failure means the base region was altered and the piece does not count, a pass lets the panel judge only the
added layer. `repaint` (Ella states, effect families): the piece is scored against the base's shipped image with
`art_judge.element_score` (silhouette, line style, value, aspect, off-palette and flat-fill gates) and needs the floor
measured from the base's own known-good references (leave-one-out minimum less 0.02); a pass judges only what differs, a
fail runs the full panel as before. `art_loop.panel_run` records the result in the round (`shared`), and
`art_pass_verify.py check` re-measures a reuse on the shipped files and still fails any derived pass whose base has no
verified pass.
