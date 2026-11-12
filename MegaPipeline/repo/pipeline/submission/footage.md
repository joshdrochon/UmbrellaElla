# Footage log (clips for the video, cover and screenshots)

Owner: Asset Specialist. Rules: `pipeline/submission/video-plan.md`, "Footage capture".
Check: `python3 tools/submission_check.py footage --day N` exits 0 at each day's end. The day-start `submission_check.py daily --day N-1` run covers it (`devlog.md`, Trigger).
Done when: `python3 tools/submission_check.py footage --day 4 --final` exits 0 (2 or more clips a day from Day 2, every beat at least once).

One line per clip, under its day: `- <day>-<beat>-<sha>.mp4`, beat from volley, rise, fall, gust, torn, end.
Only clips from a `-CaptureMode` run count (the run's `CAPTURE_MODE` line passed `submission_check.py capture`).
The clips themselves live in the team's shared footage folder, never in git.

## Clips
### Day 1
### Day 2
### Day 3
### Day 4
