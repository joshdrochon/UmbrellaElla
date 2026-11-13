# Area: artvideo

Started by the build lead from this brief (2026-11-13). It is the definition of done.

Area artvideo (Josh approved): a video-animation trial, built so it becomes the method for every animated piece if it works. Provider fal (key FAL_KEY in ~/.umbrella-ella.env, loaded in the same command as the call: set -a; . ~/.umbrella-ella.env; set +a; never print or log it).
1. tools/assetgen.py: a 'video' mode on the fal provider: image-to-video with the currently supported Veo model on fal. Check fal's live model page (free GET to https://api.fal.ai/v1/models?endpoint_id=...) for the non-deprecated Veo image-to-video endpoint and its per-second price; fixed model id, refuse others; audio off; prompt asks for a flat chroma-green background; about 2 s. Its own per-piece cap 1 USD inside fal's 74.84 USD counter (the shared IMAGE_SPEND_FILE). Provenance row: model, prompt, input image, seed, cost. git merge origin/area/imagetiers first (it adds fal and the spend guards) and build on it.
2. Input: our own in-jam Ella still that won its blind pairs (ella-up-open, from area/artella: git merge origin/area/artella or read it from there); never pre-jam art (the ART-03 guard applies).
3. tools/build/video_to_strip.py: extract frames at a chosen fps, chroma-key and despill, register frames on the anchor (reuse the frame registration and jitter code from main), pick N frames (8 and 12), write a sprite strip and sidecar the art slots can load, plus a loop check (first/last frame distance). Tests.
4. Trial on Ella idle: the mp4, the keyed frames, an 8-frame and a 12-frame strip, and a looping GIF over paper and dark backgrounds. Judge the strip with the normal blind panel through tools/art_loop.py plus the jitter check, no shortcuts.
5. Save everything under pipeline/art/proof/artvideo/ella-idle/ and list the files in your status. If it passes, the strip loads through the existing Ella slot, and document the method in docs/build/art-image-model.md ('Animated pieces from video'). Keep the still images either way.
At most 2 paid video calls before you report. Merge main first. Commit after each step, then stop.
