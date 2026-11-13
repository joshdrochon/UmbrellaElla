# Area: testvisuals

Started by the build lead from this brief (2026-11-13). It is the definition of done.

Lead, batching (replaces my earlier batching note): per batch of 5 clauses: 1. one build with the 5 new tests, all must pass; 2. one build with all 5 clauses broken together, each of the 5 tests must fail; 3. restore, one build, all pass. That's 3 Unreal runs per 5 clauses. A test that still passes in step 2 is unproven and gets redone. Clauses provable by a Python test skip Unreal. Merge origin/main before each batch; commit the 5 with their clause-proof rows.
