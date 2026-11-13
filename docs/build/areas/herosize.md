# Area: herosize

Started by the build lead from this brief (2026-11-12). It is the definition of done.

Lead: gate FAIL (work), read the newest ../UmbrellaElla-areas/logs/gate-herosize*.log: bake_defaults: MoveWorldTests.cpp assigns HeroSize and HitboxScale on the shipped tuning (the // bake: default is the one source of the shipped value, pipeline/unreal-rules.md): tests build their own tuning object or use the documented override path; HAZ-14.across has 2 bake markers (one default per key). pipeline_check adds 1 new problem: run python3 tools/pipeline_check.py and fix yours. Run python3 tools/build/quality_gate.py until 0 new FAIL. Targeted tests only. Merge main first. Commit, stop.
