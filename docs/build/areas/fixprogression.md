# Follow-up: progression boss-retry rollback. Branch area/fixprogression. Read docs/build/worker-rules.md first.
The run-start checkpoint is written before the run-2 reallocation, so a boss retry reverts it (FLOW-11, FLOW-13). Write
the checkpoint after reallocation is confirmed; test. Then the minor items from
../UmbrellaElla-areas/logs/review-progression.txt in Progression/**.
Lane: Progression/**, Persistence/**, UI/Progression/**, Tests/Progression/**, Tests/Persistence/**. Done: DoD.
