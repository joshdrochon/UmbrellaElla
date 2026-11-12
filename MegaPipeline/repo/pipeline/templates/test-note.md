# Test note (GDD 1.3 Appendix C)

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


One note per run. A tester (the GDD SH1.0 credits (FLOW-39), QA-12) writes it; the workbench exports it as JSON. Check it with
`python3 tools/manifest_check.py --note <note>.json` (exit 0). No personal data beyond the tester's team name.

| Field | What to record | JSON key |
|---|---|---|
| Build / run | Commit SHA, GDD revision, test ID, feature preset, random seed, date | `commit`, `gdd_revision`, `test_id` (QA-nn or T-nn), `preset` (T-nn), `seed`, `date` (YYYY-MM-DD) |
| What changed | The ONE important variable changed versus the comparison run | `what_changed` (one string) |
| Observed | Controls, visual clarity, failure reason, surprising interactions and reproducible steps. Failure reason is one of: player confusion, unfair pressure, unresponsive controls, bug (GDD B §11) | `observed` |
| Ratings | Fun, fairness, readability and responsiveness, each 1–5 (team scale) | `ratings.fun`, `ratings.fairness`, `ratings.readability`, `ratings.responsiveness` |
| Decision | Keep, revise, remove, retest. Include owner and a short rationale | `decision`, `owner`, `rationale` |

```json
{"commit": "abc1234", "gdd_revision": "1.3", "test_id": "QA-04", "preset": "T-03", "seed": 7, "date": "2026-11-13",
 "what_changed": "catch_window 0.2 s -> 0.3 s", "observed": "caught 4 of 6; failure reason: unresponsive controls",
 "ratings": {"fun": 4, "fairness": 3, "readability": 4, "responsiveness": 2},
 "decision": "retest", "owner": "Rick", "rationale": "window felt late"}
```
A note never promotes a feature (GDD SH1.0 section 12: notes are supporting evidence only). It is evidence for the design owner and the technical owner.
