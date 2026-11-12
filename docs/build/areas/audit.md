# Rule ID audit (read-only code). Branch area/audit. Read docs/build/worker-rules.md first.
For every one of the 204 Rule IDs in docs/feature-manifest.json (owner area: docs/build/areas.py), decide from the code
on main, the tests and each docs/build/areas/*-status.md: built (behaviour present and a test reads it), partial (code
but no test, a stand-in, or part of the rule), not built, or blocked (art pending Josh's decision, story text pending
canon, playtest-only measurement). Write docs/build/rule-status.csv: id,area,status,evidence (file or test name),note.
Then a summary line per status in docs/build/rule-status.md. Do not change code. Commit, stop.
