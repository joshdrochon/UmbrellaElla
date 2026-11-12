# Blind pairwise art judge (X/Y)

The LLM half of the art gate. The numeric half (`tools/art_check.py`, `tools/sprite_check.py`) runs
first and its FAIL is final. This protocol only decides what numbers cannot: shape language,
readability, lighting consistency, artifacts. Nothing here has been run against a model yet; it is the protocol to run.
The judge model is pinned in `evals/art-judge/README.md` ("Judge pin").

Prompt: `tools/art_judge_prompt.md` (prompt `art-judge-xy/3`, rubric `rubric/2`).
Art gate run: X = the in-engine capture, Y = the key art (`pipeline/art/reference/target-keyart.png`); the team's
pictures in `pipeline/art/references.json` with `judge: true` go in as style context, never as candidates.

## What the judge answers
- Eleven boolean rubric rows (R1–R11), each pinned to a line in `pipeline/art/art-bible.md` or a key in
  `pipeline/art/style.json`, per image, each with a location. A `true` without a location is `false`.
- One comparison: which of X and Y is closer to the standard, or `tie`.
- No numeric scores. A judge that returns a number instead of a boolean is a failed run.

## Order and blinding
1. The runner names the two images `X` and `Y` only. File names, dates, PR numbers, "old/new",
   "anchor" and "known-bad" never reach the judge.
2. Order is random per run, from a seed written in the run record. Each pair is judged twice, in
   both orders (A as X, then B as X). Both orders must give the same winner and the same per-image
   booleans. A flip on any row is a disagreement: that row is reported as "unstable", the verdict
   on that pair does not count, and a human decides.
3. One session per pair. The judge never sees its own earlier verdicts.

## Calibration set (run before a judging session; void the session if it fails)
| Pair | Expected `closer` | Expected rubric rows |
|---|---|---|
| anchor vs B1_colorful | anchor | B1: R3 false |
| anchor vs B2_pixelated | anchor | B2: R9 false |
| anchor vs B4_grey_silh | anchor | B4: R2 false |
| anchor vs B5_flat_white | anchor | B5: R1 false |
| anchor vs B6_gold_flood | anchor | B6: R4 false |
| anchor vs B7_crushed | anchor | B7: R2 false |
| anchor vs anchor (same image) | tie | identical booleans in both positions |

Known-bad images come from `python3 tools/make_art_calibration.py <anchor or reference> <out dir>`.
The anchor is the key art reference until G2 exists, then G2: the first in-engine style frame that passed
`art_check.py --gate`, saved in `evals/art-judge/anchors/`. No human picks either one.

Bar: 7/7 pairs correct in both orders (14/14 runs), and the expected false row hit in each.

## Ground truth
The calibration set is the ground truth: the team's own key art and the known-bad images made from it, so no human
verdict is needed (Josh, 2026-11-10: art direction is not a human checkpoint).
- Each calibration pair is logged with the judge's verdict in `evals/art-judge/agreement.csv` with columns
  `date,pair_id,seed,model,prompt_version,rubric_version,judge_closer,judge_rows_x,judge_rows_y,order_stable,expected_closer,note`.
- Report agreement as `matches / pairs` on `closer`, counting unstable pairs as misses. Bar: 7/7.
- A calibration miss voids the judge: `art_check.py --gate` FAILs until a new pin passes the full set.

## Pinning
A calibration result is valid only for one exact (model id, `prompt_version`, `rubric_version`),
written at the top of each run record. Changing any of the three, or editing `art-bible.md` or the
style.json thresholds the rubric cites, voids the calibration: re-run the full set.

## Stability
Run one borderline pair 3 times with different seeds. If the winner or any row flips, the rubric row
that flipped is too vague: the Art Director agent splits or rewords it in a gate patch (kickoff applies it, `tools/git_gate.py apply --auto`),
which bumps `rubric_version`.
