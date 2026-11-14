# Devlog: how we built it (Glass Box)

The jam: "Dev log link (optional, but required for the Glass Box modifier)." Glass Box = "Best dev log showing how you built your game."
Judges want to see the agent pipeline at work: real obstacles, with the record that shows them.

Owner: Producer (human). Published as an itch devlog post on the game's page; its link goes on the jam submission.
Check: `python3 tools/submission_check.py devlog --day N` exits 0 at each day's end (N = the day just ended).
Trigger: at each day start the Producer runs `python3 tools/submission_check.py daily --day N-1` and pastes it on the status line.
Wiring `check_card.py --status` to call `submission_check.status_hook()` is requested (Producer's tools lane). Until `submission_check.py wiring` shows it, the hand run is the only trigger.
Done when: `python3 tools/submission_check.py devlog --day 4 --published` exits 0 and the `Published:` link opens logged out.

Rules for the Producer:
- Each day, 3 or more real obstacles under that day. Each line names what broke, what the pipeline did, and links the proof:
  a PR, an issue (`#12`), a gate record (`gate-G1`), or an https link. A line without a link does not count.
- Plain words. No secrets, no personal emails, no local paths, no other projects.
- Show at least one agent mistake a gate caught, and one a gate missed.
- At G4, write the three sections below from the daily lines (3-6 bullets each), add 2 images (a gate record and a game capture), and publish.

Published: TBD

## Went right

## Went wrong

## Change next time

## Daily obstacles
### Day 1
### Day 2
### Day 3
### Day 4

## Frames toward the Other Realm study
- 2026-11-13 16:24 visualqa round 01 (Director's Cut route): framed/unkeyed stand-ins refused (art_slots admission), wind as thin ash-blue #555e60 ribbons in code, backdrop dimmed to the study's dark, cream blocks to island umber, lilac Keeper cube hidden. Composite: pipeline/qa/visual/composite-01-dc_route.png
