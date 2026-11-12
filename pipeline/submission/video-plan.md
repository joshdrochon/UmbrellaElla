# Gameplay video plan (30-60 s)

The jam: "a 30–60 second gameplay video" and "Show gameplay in the first five seconds." Size: Official Rules §7(c), "Resolution of the Video must match 1920x1080 or higher"; §1(e), "between 30-60 seconds"; §7(i), English audio and text (`docs/jam-rules.md`).
Owner: Asset Specialist cuts it; the packaging and submission owner (human) signs it off.
Schedule: the cut is its own card, "Video cut" (Asset Specialist, 2 h, starts at G3, due G4; requested in `pipeline/day0-cards.md`). Footage is captured daily before that (below).
Done at G4 means checks 1-4 exit 0 and are pasted in the G4 gate record.
Done when: all four checks below pass, and the link is on the jam submission.

## Checks
1. `python3 tools/submission_check.py video <file>` exits 0: 30-60 s, video at least 1920x1080, an audio stream.
2. `python3 tools/submission_check.py loudness <file>` exits 0: integrated loudness -14 LUFS +- 2.
3. Human sign-off, pasted on the tracker:
   `VIDEO first-frame=gameplay logo-first=no gameplay-by=<s> end=logo+CTA music=yes sfx-beats=yes by=<name>`.
   `python3 tools/submission_check.py signoff "<that line>"` exits 0 (gameplay-by is 5 s or less).
   The first frame is the owl attacking, not a logo, title card or black.
4. `python3 tools/submission_check.py footage --day 4 --final` exits 0 (every beat below was captured).

## Shot list (in order)
| # | Time | Shot | Audio | Source clip |
|---|---|---|---|---|
| 1 | 0-5 s | Owl bolt volley: amber clock flash, red bolts cross the screen, Ella closes and drops under them | Music; bolt-hit SFX audible | `volley` |
| 2 | 5-15 s | Rise and fall: open to climb, close to dive, wand shots hitting the clock | Music | `rise`, `fall` |
| 3 | 15-25 s | Gust ride: wing gust telegraph, Ella catches the lift | Music; gust SFX | `gust` |
| 4 | 25-35 s | Torn umbrella: critical tier, weak lift, a narrow escape | Music | `torn` |
| 5 | 35-45 s | Desperation phase, then the owl pauses and leaves; "Survived" card | Music; owl-departure and "Survived" SFX audible | `end` |
| 6 | last 3-5 s | Game logo, then the call to action: "Play it on itch.io" with the page link | Music out | Title capture |

Audio rule: one game music track runs under the whole cut. Game SFX stay in the mix; music never covers the SFX on shots 1 and 5.
`music=yes` and `sfx-beats=yes` in the sign-off mean the human heard both. If the game has no music by G4, the video uses the game SFX only and says so in Known limitations.
Cut at most 60 s. Cut shots 2 and 4 shorter first; never cut shot 1 or 5.
Theme: one shot or the end card shows the theme, as written on the `Theme in game:` line of `docs/jam-brief.md`.
No HUD, no debug overlay, no smoke or eval text, no mouse cursor: every clip comes from a `-CaptureMode` run.

## Capture switch (`-CaptureMode`)
- Non-Shipping only. On a packaged Development build it hides the HUD (health pips included), debug text, pipeline indicators and the cursor.
- It logs one line: `CAPTURE_MODE hud=off debug=off cursor=off`. `python3 tools/submission_check.py capture <game log>` exits 0 on that log.
- Who builds it: Gameplay Dev, Day-0 card 0.6c in the `Smoke/**` lane, due G1 (requested; not on the board yet). [VERIFY: needs Unreal; not built yet]
- `python3 tools/submission_check.py wiring` fails until that card is in `pipeline/day0-cards.md`. Until then the switch has no owner, and the Producer raises it at each day start.
- Done when: the check above passes on a real package log, and a pasted 1920x1080 capture shows no HUD health pips.
- Until it exists, no clip counts toward the footage log.

## Footage capture (during the jam)
- Clips come from a packaged Development build run with `-CaptureMode`, at 1920x1080 or more, with game audio.
- From Day 2 (after G1), the Asset Specialist saves 2 or more clean clips a day to the team's shared footage folder, named `<day>-<beat>-<sha>.mp4`
  with a beat from: volley, rise, fall, gust, torn, end. Capture far more than the cut uses.
- Each clip gets one line in `pipeline/submission/footage.md` the same day. The day-start `submission_check.py daily --day N-1` run fails without them.
- Clips are not committed to git (they are large); only the final video link goes on the submission.
