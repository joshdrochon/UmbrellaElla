# imagetiers status

Done (tools/assetgen.py, tools/keys.py, tests/test_assetgen_tiers.py):
- Tiers: `--tier draft|final`, default draft. Draft = `gemini-2.5-flash-image`, final = `gemini-3-pro-image-preview`.
  Both exist on our key (`assetgen.py image-models`, Nov 12; `gemini-3.1-flash-image` exists but has no price row, so unused).
  Final needs `--image-size` (Pro rule). Tier, provider and exact model id go in the provenance `origin`
  (`provider=.. tier=.. model=..`), `model_version`, `<stem>.request.json` and the counter call.
- OpenRouter: `--provider openrouter`. Fixed map `OPENROUTER_MODELS` (our id -> `google/<same id>`), any other model
  raises `ImageRefused`, no fallback. Both tiers' models are on OpenRouter's model list (checked Nov 12), so both
  tiers may use it. Key `OPENROUTER_API_KEY` (added to `keys.IMAGE_KEYS`, scrubbed from sessions).
- Spend: counter calls carry `provider`. Gemini/openai keep `IMAGE_SPEND_CAP_USD`; OpenRouter has its own cap 19.89
  (`IMAGE_SPEND_OPENROUTER_CAP_USD` overrides) in the same file. Each refuses a call that would cross its cap.
  A `gemini` call moves to OpenRouter only if the model is mapped, an OpenRouter key exists, and Gemini's
  remaining cap < 5 final calls (5 x $0.134 = $0.67); otherwise it stays on Gemini.
- Tests: `python3 -m unittest tests.test_assetgen_tiers` (8, fake client, no paid calls).

Paid proof calls:
- Gemini draft: 1 call, $0.039, `pipeline/art/proof/ImageProof/tier_draft_proof.png`.
- OpenRouter draft: NOT run. `OPENROUTER_API_KEY` is not in `~/.umbrella-ella.env`. Add it, then run
  `assetgen.py image --provider openrouter ...` once. The OpenRouter request shape (chat completions, `modalities`,
  `image_config`, `data:` URL reply) is from its docs and is only tested against the fake client.

Left / not done:
- art_loop's "final-candidate step passes final": `tools/art_loop.py` contains no image-generation call (workers run
  `assetgen.py image` themselves), so there is nothing there to change. Callers for final candidates pass `--tier final
  --image-size ..`. Outside this lane; say if you want it wired somewhere.
