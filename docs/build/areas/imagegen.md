# Image model provider for art loops. Branch area/imagegen. Read docs/build/worker-rules.md first.
Decision D-new-art-image-model (Josh, Nov 12). Provider change: Josh has prepaid Gemini credits, so the DEFAULT provider
is `gemini` (Gemini API image generation / Imagen, key GEMINI_API_KEY via tools/keys.py); `openai` stays optional.
Build, with no paid calls (no key yet):
1. An `openai` provider in tools/assetgen.py `image` (gpt-image): reads OPENAI_API_KEY from the environment through
   tools/keys.py like the ElevenLabs audio path (never read, print or log a key value), accepts input images, writes the
   full provenance row (tool, model_version, prompt, seed, input_images, date, licence = the provider's output terms) and a
   prompt log line (tools/prompt_log.py). Add the provider to the asset tools list (asset-tools.json) the way ElevenLabs is.
2. GDD ART-03 / BG-02 guard: refuse any input image that is pre-jam (provenance date before the jam start, or a file under
   pipeline/art/reference/, or a quality-bar image) with a clear message; in-jam images we made may be inputs.
3. A per-run spend counter: every image call adds its cost (from the provider's published price per image, recorded in
   asset-tools.json) to ONE counter shared by every worker (the file named by env IMAGE_SPEND_FILE, written with a lock; tools/build/start_area.sh
   sets it); at the hard TOTAL cap (env IMAGE_SPEND_CAP_USD, no default: no cap means no paid call)
   every further image call stops with a clear message. The cap comes from the lead with Josh's Spend OK.
4. Tests with a fake client (no network): provenance row complete, prompt logged, a pre-jam input refused, an in-jam input
   accepted, the cap stops calls, no key -> a clear "no key" result (no placeholder pretending to be art).
Lane: tools/assetgen.py, tools/keys.py (read path only), asset-tools.json, tests/test_assetgen*.py. Done: tests OK, no network.
