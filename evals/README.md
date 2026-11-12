# Evals

Rick's pipeline doc: "an agent saying 'approved' is not proof that the code is good." These evals
test the judges before we trust them. The bars are in docs/audit.md section 5.

| Eval | What it proves | Run | Bar |
|---|---|---|---|
| `reviewer/` | The Dev Lead prompt catches planted Unreal C++ bugs and approves clean changes | `python3 tools/run_reviewer_eval.py` (Claude Code) or `--cmd "codex exec -"` | Every blocker caught, recall ≥ 0.80, every defective change blocked, clean approve rate ≥ 0.80 |
| `art-judge/` | The art checks reject off-style frames and accept on-style ones | see `art-judge/README.md` | 100% of known-bad rejected, 100% of known-good accepted |
| `tests/` (unit) | The guardrail scripts themselves fail when they should (we broke them on purpose to test the tests) | `python3 -m unittest discover -s tests` | all pass |

Rules:
- Re-run the reviewer eval whenever the Dev Lead card, `pipeline/unreal-rules.md` or `pipeline/unreal/*.md`, or the model changes. Paste `_summary.json` in the PR.
- A defective case is never softened to make a reviewer pass. A case found to be mislabeled (a "clean" case with a real bug)
  may be fixed, with the reason written in `reviewer/results.md`. All cases share the same evidence and context lines so the wording does not reveal which are clean.
- Cases in `reviewer/cases/` are hand-made, not from Unity or any other project.
- The reviewer-eval cases are written by a different agent session than the one that writes or edits the Dev Lead prompt (`pipeline/roles/dev-lead.md`). A session that changed the prompt never adds or edits a case, so the prompt cannot be tuned to cases it wrote.

## Reviewer case kinds (`reviewer/cases/NN-*/`)
Each case has `change.diff`, `task.md` and `expected.json`. Cases 01–15 came first; 16–35 were written later to be harder.
| Kind | expected.json | Counts as caught when |
|---|---|---|
| Code defect | `"clean": false`, `"defects": [{id, severity, file, lines, keywords}]` | a finding names that file, a line within 3 of `lines`, and one keyword |
| Code defect seen in two places | as above, plus `"also": [{file, lines}]` (e.g. the ini side of an ini/header mismatch) | a finding hits the main place or any `also` place |
| Evidence defect | `"clean": false`, `"defects": []`, `"checks": {"tests": "missing" or "fail", "build": ...}`, and an `evidence.txt` | the verdict is request_changes and `checks_seen` has that key with a value other than `pass`. Each key is one blocker |
| Clean | `"clean": true`, no defects, no checks | the verdict is approve |

`evidence.txt` replaces the default author evidence (all pass) for that case only. Evidence cases cover: tests shown only as a
screenshot, a test that did not run, a build log that shows an error under an "exit 0" claim, a test count below main, and a
header/reflection change built only with Live Coding. Their code is clean, so the only reason to block is the evidence.
Clean cases must follow every rule in `pipeline/unreal-rules.md`, `pipeline/unreal/*.md` and the Dev Lead card, including the code-layout lanes and
`UmbrellaElla.<Area>.<Behavior>` test names. Task cards 16–35 also state the card's lane and Done-when; every case in that
range uses the same wording, so the card does not reveal which cases are clean.

Not yet covered (add as the project grows): a Blueprint with event-graph logic, an asset change with no sidecar, a binary
asset in a code PR, a frame-count cooldown, `ensure()` used for normal control flow (the rule's wording also bans the common
`if (!ensure(Ptr)) return;` guard, so a case would be debatable until the rule is clarified).

## Role gates and how each was shown to fail
Every gate has a clean input it passes and inputs broken on purpose that it must catch. The tests
below are the proof; re-run them, don't trust this table.

| Gate (role) | Command | Shown to fail by |
|---|---|---|
| Module boundaries (Technical Director) | `python3 tools/module_check.py` (exit 2 = no `Source/`, CI skips) | `tests/test_module_check.py`: `tests/fixtures/modules/clean` gives 0 findings; `broken_a`…`broken_g` each give findings of only their own rule (a private include ×2, b missing dep ×2, c public leak ×2, d missing `_API`, e generated.h not last, f raw UObject member ×4, g IWYU not Full), plus a wrong-name generated.h. C++ standard rules: h-v by `STYLE_CASES`, w-z, A-H, J and L by `STANDARD_CASES`, I by its own test, each caught by its own rule only, plus correct-form cases that must pass; `broken_wz_epic_standard` gives exactly the critic's 15 findings. Rule K runs only with `--rules K` |
| Task card ready (Producer) | `python3 tools/check_card.py <card>`; CI lints the card a PR closes | `tests/test_check_card.py`: template-shape and issue-form good cards pass; 11 broken cards (empty / missing / placeholder field, UE-000, MVP 14, unknown role, owner = reviewer, no lane, whole-repo lane, vague Done-when, `_No response_`) each fail with their own kind |
| Art numbers (Art Director) | `python3 tools/art_check.py --json <capture>` | `tests/test_art_thresholds.py`: for each of the 6 thresholds in `style.json`, a frame just inside passes and a frame just past it fails on that threshold only; `make_art_calibration.py` variants B1, B4–B7 of a passing frame all fail |
| Sprite sheets (Art Director, Asset Specialist) | `python3 tools/sprite_check.py <sheet> --grid WxH` or `--scan Art` | `tests/test_sprite_check.py`: good sheet and frames pass; mismatched frame sizes, wrong declared size, sheet not divisible by grid, non-power-of-two when required, wrong frame count, empty middle frame, opaque background, shape touching the edge, wide soft fringe, light matte halo, wispy shape, solid box and a light-colored silhouette each fail |
| PR body (all roles) | `python3 tools/check_pr.py [body] --changed files.txt` | `tests/test_check_pr.py`: good body passes; missing or partial evidence header, stale commit, package path (`.umap`, `Config/**`, `Build.cs`, `Target.cs`, `.uproject`, or card Done-when) without package + `SMOKE_OK`, a `Source/` change with no `-DisableUnity` build log line, a Not-done line with no link, and a missing or empty `Next:` each fail |
| Source/Config hygiene (all roles) | `python3 tools/pipeline_check.py` | `tests/test_pipeline_check.py`: clean Source/Config passes; bare TODO, `TODO(name)`, warning pragma without a decision row, `ROLE:` line each fail; `_PH` is a note, and a problem with `--release`; LFS byte total read from pointers |
| Unreal scripts (TD, QA and Build) | `tools/ue/*.sh`, `*.ps1` via `tools/ue_run.py` | `tests/test_ue_scripts.py` (fake engine and game): timeout → 124, dirty tree refused before UAT runs, `--allow-dirty`, `BUILD_INFO.txt` written only on success, cook error, smoke fails on exit code, hang, no `SMOKE_OK`, each of `Ensure condition failed` / `Fatal error` / `Accessed None`. `.ps1` checked by text for the same steps only (no PowerShell here) |
| LLM art judge (Art Director) | protocol in `art-judge/blind_pairwise.md`, prompt `tools/art_judge_prompt.md`; the whole gate is `python3 tools/art_check.py --gate` | not run yet: needs a pinned model; the calibration anchor is the key art until G2 (no human anchor). `tests/test_art_check.py` ArtGateTests covers the gate's four parts |

Known limit: flat near-white paper (B5) fails `art_check.py` as `accent_area`, because near-white is
within tolerance of the `spark-white` accent. The right image fails, with a misleading reason.
