# Area: artscale

Started by the build lead from this brief (2026-11-12). It is the definition of done.

Area artscale. Josh: the pipeline must auto-scale art loops to the work; nobody should have to ask. Build tools/build/art_scheduler.py and make it the default (replace ../UmbrellaElla-areas art_keepalive with it, started by a tools/build script):
- Reads docs/build/art-inventory.csv on main and the pass records: every unpassed piece must have exactly one owning art-loop session.
- Groups unpassed pieces into loops of about 3-8 pieces by owner lane and piece family; a group file lists lane -> pieces (start from ../UmbrellaElla-areas/art_groups.txt, which the lead wrote by hand: 13 loops). Lane names <owner>, <owner>2, <owner>3 ...
- Runs as many loops as the machine allows: bounded by memory (tools/build/ue_slot.sh slot count / free memory) and both image spend caps; target 14+ concurrent. Starts a missing loop with tools/build/start_area.sh and the standard art-loop brief (scope = its pieces; first merge origin/area/<owner> and main).
- When a loop's pieces all pass (verified by tools/build/art_pass_verify.py), it stops that loop and gives the slot to the next unowned group; a loop whose session exits with work left is restarted (bounded restarts; escalation to Opus per worker-rules after triage is the lead's call, keep the loop's model).
- One line per decision to ../UmbrellaElla-areas/logs/art-scheduler.log (the lead's watch reads it).
- Tests for grouping, capacity, hand-off on pass.
Merge main first. Targeted tests only. Commit, stop; the lead switches it on.
