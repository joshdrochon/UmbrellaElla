# Critic calibration, before and after (13 Nov, check defect 2)

Real sessions (`claude -p`, claude-sonnet-5-5, fresh each), piece `vfx-gold-impact`, 12 calibrated folders each, seeds 7000-7011,
same harness for both (`art_loop.blind` + `judge`).

| | sessions | calibrated | share |
|---|---|---|---|
| before (old prompt, unrelated crude render as the bad pair) | 12 | 10 | 0.833 |
| after (new prompt, crude copy of the team image as the bad pair) | 12 | 12 | 1.000 |

Earlier real logs (Saved/Logs/pipeline/critic-calibration.csv of the art worktrees): artfx 3/9 (0.33), artui 13/17, artella 52/65,
artscene 103/117, artshots 141/160. Small sample here (12); the rule below covers the remainder: an uncalibrated session is
redrawn (at most `REDRAW_MAX` = 6 extra per pair) and its vote is never counted, so a round counts only PANEL calibrated votes.
