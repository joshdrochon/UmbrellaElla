# Art judge prompt (blind X/Y)

Prompt version: `art-judge-xy/3`. Rubric version: `rubric/2` (below). Any edit to this file bumps
the version it touches, and the calibration in `evals/art-judge/blind_pairwise.md` must be re-run
before the judge's verdicts count again.

The runner fills the `{...}` slots. It never tells the judge which image is old, new, the anchor or a
known-bad image. Images are named only `X` and `Y`. For the art gate X is the in-engine capture and Y the key art;
`{style_references}` is every picture in `pipeline/art/references.json` with `judge: true`
(`python3 tools/art_check.py --references --json`, which adds the current GDD's embedded images).

---

You are judging two images of the same game scene, image X and image Y, against a fixed art standard.
The team's own art is attached as style context only (never one of X or Y): {style_references}. You do not know which one is newer, which one a person made, or which one is expected
to win. Do not guess. Judge only what is visible.

The standard is the art bible below and the numbers from `pipeline/art/style.json`:

{art_bible}

Palette and limits (from style.json): {style_json_palette_and_thresholds}

Numeric gate already run on both images (`tools/art_check.py --json`). A FAIL here is final and
you cannot override it; you still answer every question:
X: {art_check_json_x}
Y: {art_check_json_y}

For EACH image, answer every question with `true` or `false` and a location in the image
("bottom-left rock band", "Ella, centre-left"). A `true` with no location counts as `false`.
No scores, no ratings, no 1–10 numbers.

| id | question (true = meets the standard) | source |
|---|---|---|
| R1 | Background is aged, mottled paper; not flat, not white | art bible pillar 1, auto-fail "white or flat background" |
| R2 | Ella, enemies, ground and hazards read as near-black silhouettes; interior detail is dark-on-dark | pillar 2; style.json `dark_l_max`, `dark_share_*` |
| R3 | The only saturated hues are gold/amber and rust red | pillar 3; style.json `hue_gate`, `off_style_max` |
| R4 | Gold/amber and rust are small accents, not large areas | style.json `accent_area_max` |
| R5 | Umbrella open vs closed is readable from the silhouette alone | readability rule 1 (open width ≥ 1.8× closed) |
| R6 | Player shots (gold-white) and danger (rust) are in different hue families | readability rule 2 |
| R7 | Spikes differ from walkable rock by shape and a rust edge | readability rule 4 |
| R8 | Wind lines and sparkles are faint decoration and cannot be mistaken for gameplay objects | pillar 4 |
| R9 | Painted edges are smooth: no pixel-art stair-stepping or Nearest-filter shimmer | import settings; auto-fail "pixel-art look" |
| R10 | No watermark, signature, garbled text, extra limbs, melted gears or other AI artifacts | auto-fail list |
| R11 | Every asset is lit the same way: interior highlights and dark-on-dark detail all suggest one light from the front, slightly above; no normal-map or lit-material shading | art bible Import settings (no normal maps, one assumed light) |

Then answer one comparison question: `closer`: which image is closer to the standard, `X`, `Y` or
`tie`, decided only by the rubric rows where the two images differ. If no row differs, answer `tie`.

Reply with only this JSON object:
```
{"X": {"R1": [true, "where"], ..., "R11": [true, "where"]},
 "Y": {"R1": [true, "where"], ..., "R11": [true, "where"]},
 "closer": "X" | "Y" | "tie",
 "deciding_rows": ["R3", ...]}
```
