# itch page spec

Owner: packaging and submission owner (human). Due: G4. The page stays Draft until that human previews it, then sets it public and submits to the jam.
Done when: `python3 tools/submission_check.py page` exits 0, the preview is done, and the jam submission shows the page.

## Images (in `pipeline/submission/page/`, Git LFS)
- `cover.png`: at least 630x500, ratio 315:250. Taken from a packaged `-CaptureMode` run (no HUD; `video-plan.md`), cropped to the owl and Ella.
  It must read like the key art (`pipeline/art/reference/target-keyart.png`): sepia parchment, ink silhouettes, the amber chest clock, red bolts.
  The Art Director (human) approves it against the key art.
- `shot-<beat>.png`: 3 to 5 screenshots at 1920x1080 or more from the packaged build, each a different beat from:
  volley, rise, fall, gust, torn, end. No two the same file. All from `-CaptureMode` runs: no HUD, no debug text.
- Gameplay only: no title, menu, pause or end-card screens. `shot-end.png` shows the owl leaving with Ella in flight, no card text.
  The packaging owner checks this by eye; the tool checks only names, sizes and duplicates.

## Page fields
| Field | Value |
|---|---|
| Title | TBD (the game design owner decides; the GDD's working title is "The Last Hour") |
| Short description | TBD (one line: survive the clockwork owl's last hour with a fragile umbrella) |
| Genre | Action |
| Tags | TBD (up to 10, e.g. boss-fight, umbrella, survival, 2D, unreal-engine) |
| Controls | TBD (the controls in `docs/jam-brief.md` once row DEC-02 in `docs/decisions.md` (attack trigger, GDD SH1.0 section 11 open decisions) is DECIDED; never from a GDD file directly. `submission_check.py page` fails while D1 is open, and while D1 still asks the old falling-attack question instead of automatic fire vs player-fired shot) |
| Theme | TBD (copy the `Theme:` and `Theme in game:` lines of `docs/jam-brief.md`; `submission_check.py theme`) |
| Team name | TBD |
| Video link | TBD (`video-plan.md`) |
| Devlog link | TBD (`devlog.md`) |
| AI disclosure | Code, art and audio made with AI agents and tools; see the devlog. (Default. Official Rules §7(a) allow AI tools and §9 uses the disclosure "for context only", `docs/jam-rules.md` row AI.) |
| Pre-jam declaration | TBD (paste from `docs/pre-jam-declaration.md`) |
| Credits | TBD (paste from `credits.md`) |

## Files next to the exe
Owner: packaging and submission owner (human). Text: `README.txt` and `LICENSE.txt` in this folder. `tools/ue/package.ps1` copies both next to the game exe in every package.
README.txt copies Title, Controls, Team, Credits and Theme from this page; no pipeline text. LICENSE.txt default: all rights reserved, free to play, third-party assets under their own licences.
`python3 tools/submission_check.py files` exits 0 from Day 0; `files --final` exits 0 at G4 (no TBD).

## Team (Official Rules §1(a), §1(c): 1 to 5 Entrants, full name and email of each, one Team Owner)
Card 0.0 collects these. Emails are entered on the jam form only, never committed. Each member confirms §5 (18 or over, an active Epic Account that is not a Cabined Account).
The Team Owner submits for the team (§15(a)) and receives any prize (§13).
`submission_check.py page` fails on any TBD or `n` in Email, a one-word name, fewer than 1 or more than 5 rows, or not exactly one Team Owner `y`.
| Full name | Role | Team Owner (y/n) | Epic email collected (y/n) |
|---|---|---|---|
| TBD | TBD | n | n |

## Credits by role
One line per role, with names. Every member in the Team table is named at least once. `submission_check.py page` fails on a missing role, a TBD, or a member left out.
Third-party assets come from `credits.md`.
- Game design: TBD
- Programming: TBD
- Art: TBD
- Audio: TBD
- Production: TBD
- QA: TBD
