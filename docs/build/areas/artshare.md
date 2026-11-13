# Area: artshare

Started by the build lead from this brief (2026-11-13). It is the definition of done.

Area artshare (Josh approved; the art bar is unchanged). Shared-layer judging in tools/art_loop.py and tools/build/art_pass_verify.py (main already has the base-link rule: an element with "base": "<piece>" counts only when the base has a verified pass):
1. references.json element fields: "base": "<piece>" and "base_mode": "reuse" | "repaint".
2. reuse (the derived piece literally reuses the base's pixels: the UI background, layered backdrop stages, Roadwarden gear composited on a shared body): verify the reuse by pixels (the base's shipped image region matches inside the derived piece, a measured tolerance), then the panel judges only the added layer (the critic brief names what is new).
3. repaint (Ella states over the identity sheet, effect families over the family-style piece): a cheap consistency check against the passed base's image: identity/palette/line-style similarity (reuse tools/art_judge.py measures) above a threshold measured from the base's own known-good refs; pass -> the panel judges only what differs (the pose, the shape); fail -> the full panel as today.
4. Tests: a deliberately off-model derivative fails the consistency check; a reuse piece whose base region was altered fails the pixel check; a derived piece without a verified base never counts.
5. One paragraph in docs/build/art-image-model.md 'Shared layers'.
Targeted tests only. Merge main first. Commit, stop; the lead gates you first.
