# artscale status
Done: `tools/build/art_scheduler.py` (+ `art_scheduler.sh start|stop|status|once|plan`), tests `tests/test_art_scheduler.py` (13: grouping, capacity, hand-off, restarts).
Reads main's art-inventory.csv, verifies passes with art_pass_verify on main and in each lane's worktree, groups unowned pieces (3-8, owner+family, lanes owner, owner2..),
appends them to ../UmbrellaElla-areas/art_groups.txt, caps by ART_MAX_LOOPS (6; no new loop while load1 > ART_MAX_LOAD 20), memory (ue_slot thresholds), image budget; logs to logs/art-scheduler.log.
Switch on (lead): `tools/build/art_scheduler.sh start` (stops art_keepalive; running loops are adopted by process name). Optional `art_models.txt` (`artenemy|claude-opus-5-5`) keeps escalated models.
Dry check against live state: `tools/build/art_scheduler.sh plan` (found 7 ungrouped artshots pieces -> artshots lane).
Not run: live start of loops (lead switches on).
