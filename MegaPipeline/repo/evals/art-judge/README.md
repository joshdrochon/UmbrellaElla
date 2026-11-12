# Art judge eval

The art loop's critic (`tools/art_loop.py`) uses this blind X/Y protocol per piece: ours against one of the piece's references from `pipeline/art/references.json`, labels stripped, order random, a fresh session that sees nothing of the builder. `tools/art_judge.py` and `tools/art_ref_check.py` are its deterministic half.

Two judges, in order. The numeric one runs first and cannot be overridden.

1. **Numeric:** `tools/art_check.py` on each in-engine capture (palette, hue bands, accent area, silhouettes).
2. **LLM judge:** the Art Director role in a fresh session, using the gate list in
   `pipeline/roles/art-director.md` and the blind X/Y protocol: the capture as X against the key art as Y, with the
   team's own art (`pipeline/art/references.json`, `python3 tools/art_check.py --references`) as style context.
   Pass/fail per gate with a location in the image. No 1–10 scores (numeric scores drift between runs and hide
   which gate failed).

No human signs off art (Josh, 2026-11-10). `python3 tools/art_check.py --gate <capture>` runs the whole gate: the
team's references are present, the numeric check passes, the judge is calibrated (below) and the capture's X/Y row
has every rubric row true. The Art Director agent re-places or regenerates until it prints `ART_GATE: PASS`.

## Calibration (run before judging; void the review if it fails)
Build the set once the reference is in the repo:
```
python3 tools/make_art_calibration.py pipeline/art/reference/target-keyart.png evals/art-judge/calibration/
```
| Image | Expected numeric | Expected LLM judge |
|---|---|---|
| reference (G1, the key art) | PASS | approve: the known-good anchor until G2 exists (the judge is blind to where an image came from) |
| first in-engine style frame that passed `art_check.py --gate` (G2, add to `anchors/`) | PASS | approve |
| B1_colorful | FAIL | request_changes |
| B2_pixelated | may pass (shape problem) | request_changes (pixel-art auto-fail) |
| B4_grey_silh | FAIL | request_changes |
| B5_flat_white | FAIL | request_changes |
| B6_gold_flood | FAIL (`accent_area`) | request_changes |
| B7_crushed | FAIL (`dark_share`) | request_changes |

Each review session: shuffle the candidate with 1 known-good in-engine anchor and 2 known-bad images, unlabelled.
The review counts only if the judge approves the anchor and rejects both known-bad. Until G2 exists the anchor is
the key art reference; the known-bad images are made from it (`make_art_calibration.py`).

Bars (see docs/audit.md section 5):
- 100% of known-bad images rejected, 100% of known-good approved, across the full set (7/7-style agreement).
- Pin the judge as (model, prompt version). Re-run the full calibration set when either changes.
- Stability: run one borderline capture 3 times. If the verdict flips, the gate FAILs and the Art Director agent splits the
  gate wording (a prompt change: a gate patch, new rubric version, re-run the calibration).
- Revisions are judged blind as X/Y in both orders; both orders must agree. Full protocol, rubric rows and the pairwise calibration set: [`blind_pairwise.md`](blind_pairwise.md).

## Judge pin
Judge pin: model `claude-opus-5-5`, prompt `art-judge-xy/3`, rubric `rubric/2`.
The model id is proposed (decision requested). Every `agreement.csv` row's `model` must equal it, and the prompt
and rubric versions must equal the header of `tools/art_judge_prompt.md` (`tests/test_art_judge_record.py`).
A new pin voids the calibration: re-run the full set.

## Run record (required before an art verdict counts)
One schema for `evals/art-judge/agreement.csv`, the same as `blind_pairwise.md` "Agreement with the human":
`date,pair_id,seed,model,prompt_version,rubric_version,judge_closer,judge_rows_x,judge_rows_y,order_stable,expected_closer,note`.
A calibration pair (`blind_pairwise.md` table) is one row: `expected_closer` is the table's expected winner, `note` is `calibration`.
A row agrees when `judge_closer` equals `expected_closer` and `order_stable` is `yes`.
Until the file holds one full run for the pinned judge with every row agreeing, `art_check.py --gate` FAILs and no art
verdict counts. This file is a gate path: the run is recorded as a gate patch kickoff applies once per pin (`tools/git_gate.py apply --auto`).
A candidate's own X/Y row (`pair_id` `<capture stem>:target-keyart`, X = the capture, `judge_rows_x` = `all` when every
rubric row is true, else the false rows; `expected_closer` `-`, `note` `gate`) goes in the judge log
`Saved/art-judge/judge-log.csv`, which `art_check.py --gate --judge` reads.
`tests/test_art_judge_record.py` fails if `anchors/` has files but no such run is recorded, if a row disagrees,
or if this file and `blind_pairwise.md` list different columns.

`tests/test_art_check.py` runs the numeric half of this table automatically once
`pipeline/art/reference/target-keyart.png` exists.
