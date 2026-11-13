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
