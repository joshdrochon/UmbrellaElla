# File hygiene checklist (Project Librarian, run by any human or agent before a gate)

Rick's pipeline doc: this role proposes cleanup with reasons and never deletes or moves files
automatically, because Unreal references need care.

- [ ] `python3 tools/pipeline_check.py` reports 0 problems.
- [ ] No new top-level folders outside the layout in `pipeline/unreal-rules.md`.
- [ ] Asset names follow `T_`, `SPR_`, `FB_`, `BP_`, `IA_`, `IMC_`, `L_` prefixes.
- [ ] Zero redirectors on main (Fix Up Redirectors run in the editor after any move).
- [ ] The last `DAILY` line has `validate=PASS(err 0, ...)` (DataValidation, `tools/ue/validate.*`). Paste it.
- [ ] No stray Markdown: agent notes, plans and logs live in the PR or issue, not new files.
- [ ] Every committed capture or log is referenced by a PR, issue or doc; otherwise propose deleting it.
- [ ] `git lfs locks` shows no lock older than a day without an open PR.
- [ ] Every asset has a row in `pipeline/art/provenance.csv`.
- [ ] No `_v2`, `_final`, `_new` or `_old` in any file or asset name. Versions live in git.
- [ ] Every `_PH` placeholder is listed with the card that replaces it (D-new-port-8).
- [ ] No new file or class named `*Helpers*`, `*Utils*`, `*Types*` or `*Manager*` unless a card named it.
- [ ] Every `TODO` reads `TODO(UE-<id>)` or `TODO(D<n>)`. Every stub reads `// STUB(UE-<id>)` and is listed in its PR's "Not done".
- [ ] No pipeline text in shipped content: no `ROLE:`, role names or agent notes in UI strings, credits or level text.
- [ ] Rejected AI generations are outside `Content/`, so they are never cooked.

Output: a comment listing proposed moves/deletions, each with a reason. A human does them in the editor.
