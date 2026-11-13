# Area: imagetiers

Started by the build lead from this brief (2026-11-12). It is the definition of done.

Area imagetiers (Josh approved). In tools/assetgen.py (and tools/keys.py if needed), as the default behaviour:
1. Tiers: drafts use Google's cheap flash image model (check which of gemini-2.5-flash-image / gemini-3.1-flash-image exists on our key with a free model-list call and use that exact id); final candidates use gemini-3-pro-image-preview. A flag --tier draft|final (default draft); art_loop's final-candidate step passes final. Record tier and exact model id in provenance.
2. OpenRouter as a second provider for the SAME Google models only: a fixed mapping from our model id to OpenRouter's id for that same Google model; refuse any other model (raise, no fallback); record provider and model in provenance. Key OPENROUTER_API_KEY from ~/.umbrella-ella.env loaded the same way as GEMINI_API_KEY (set -a; . file; set +a in the calling shell); never print, log or commit any key value. If OpenRouter does not offer the exact model for a tier (check its model list, free), that tier never uses OpenRouter; write that in your status.
3. Spend: the shared counter (IMAGE_SPEND_FILE) records provider per call; Gemini keeps its cap (33.82 USD); OpenRouter has its own hard cap 19.89 USD in the same counter file; refuse a call that would cross either. Use OpenRouter for a tier only when the Gemini cap is near (remaining < the cost of 5 final calls).
4. Tests: a non-matching OpenRouter model is rejected; the tier picks the right model; each cap refuses at its limit; provider/model land in provenance. No paid calls in tests; at most one paid draft call per provider to prove it works, logged in your status with its cost.
Merge main first. Targeted tests only. Commit after each step, then stop.
