# Jam Brief: Umbrella Ella: The Stolen Hour

Every agent reads this first. If it disagrees with another document, add a decision row, build its default, say so in the PR.

## The game
- **What:** Umbrella Ella: The Stolen Hour (GDD SH1.0). A 2D side-view game for 13+: Ella rises under her umbrella, drops to shoot or absorb, rides harmless currents, and takes apart the Keeper of Time's wings, three hanging mechanisms and clock. Two modes share the complete Keeper fight: **Start Game** (one basic shot, straight to the Keeper) and **Director's Cut** (story, progression, four spells, a nine-chunk level with enemies, then the same Keeper). The Keeper leaves alive; no survival timer.
- **Engine:** Unreal Engine **5.8.4**. **Platform:** Windows. Submission: a Windows **Development** package (no Shipping).
- **Win:** the final clock hit (OWL-35); the Keeper withdraws alive, then story and credits (FLOW-04). **Lose:** the last life empties (FLOW-31). Retry: the current phase or checkpoint, 3 lives, full health (FLOW-09).
- **Design source:** the snapshot `docs/gdd/CURRENT` names (now `docs/gdd/GDD-SH1.0.md`); feature statuses in `docs/feature-manifest.json`. GDD 1.3 and B1.0 are history (D-new-gdd-sh10).

Content caps: none set by GDD SH1.0. Frame counts and sizes follow each receiving contract (ANIM-02); the Art Director sets the art budget.

## Jam facts (`docs/jam-rules.md` quotes them)
- Theme revealed Nov 11 (kickoff). Card 0.19 runs that day: 3 pitches in 1 hour, the game design owner picks one, a new GDD revision follows.
- No game building before the start, Nov 11 21:00 PST (D39). Tools, agents, MCP and the generic workbench (cards 0.25, 0.26) are allowed.
- From Nov 12, every agent prompt is logged (`tools/prompt_log.py`).
- Pre-jam work is declared in `docs/pre-jam-declaration.md`.
- We write the devlog (`pipeline/submission/devlog.md`, Glass Box).
- Submit a Windows Development build and a 30-60 s video by Nov 15, 5:59 PM PST. 7 equal criteria.

Theme: TBD
Theme in game: TBD

## Clock (card 0.0 sets it; times ISO 8601 with UTC offset, Hard stop a daily `HH:MM-HH:MM` window; time zone D-new-clock)
Submission deadline: 2026-11-15T17:59-08:00
Hard stop: 02:00-08:00
Card 0.9 cutoff: 2026-11-12T18:00-08:00

| Gate | Due |
|---|---|
| G1 | 2026-11-12T22:00-08:00 |
| G2 | 2026-11-13T22:00-08:00 |
| G3 | 2026-11-14T20:00-08:00 |
| G4 | 2026-11-15T14:00-08:00 |

Set by card 0.0 (agent default; D-new-clock).

Checked by `python3 tools/check_card.py --clock` (D-new-tune-day: G3 at least 20 h before the deadline).

## Sources of truth
Play: the GDD snapshot, its mirror `docs/feature-manifest.json`, then `docs/game-spec.md`. Look: the key art + `pipeline/art/art-bible.md` (D0).
Feel: `docs/feel-spec.md`. Keeper fight: `pipeline/level/encounter.md`. Progression oracle: `tools/progression_model.py`. Undecided: `docs/decisions.md`. Process: `AGENTS.md`.

## MVP — the game is "done" when all of these are true in a packaged build
**GDD SH1.0 approves every filled requirement as APPROVED_P0** (Rick, 2026-11-12): every line is P0, never cut. Build only after the start (D39). Numbers: manifest `approved_parameters`. The tag ends each line with its gate; `tools/check_card.py` reads it (D-new-sh10-g1).
1. Start screen with Start Game and Start Director's Cut; Start Game goes straight to the Keeper with one basic shot (FLOW-02, FLOW-34, ART-04). [G1]
2. Ella's four-state movement and inputs: rise, shoot-fall, absorb-fall, free fall, hop, dash, ride, trim, fixed-right fire (MOVE-04..MOVE-07, MOVE-11, MOVE-13..MOVE-15, MOVE-18..MOVE-22, WIND-03, CORE-04, CORE-05). [G1]
3. Small Blasts, the one unlimited basic shot, fired only while dropping (COM-05, COM-06, COM-10). [G1]
4. Health: one clock HUD with health and life hands, 3 hits x 3 lives, damage 1 / 1.25 / 1.5, lift by health, yellow heals (SURV-05, SURV-07, UMB-05, FLOW-30..FLOW-33). [G1]
5. The complete Keeper fight: wings, three mechanisms, clock, every attack and effect, phase checkpoints, the living departure (OWL-06..OWL-35, FLOW-09). [G1]
6. Pause (Continue, Settings, Quit), defeat retry and the win ending: story text over the background, then credits (FLOW-04, FLOW-35, NAR-07). [G1]
7. First-start tutorials in both modes, Pause then Skip at every step (FLOW-03, MOVE-16). [G2]
8. Player settings in both modes: Sound, Controller remap, Credits, Back and Save (MOVE-08..MOVE-10, MOVE-17, FLOW-36, FLOW-37, FLOW-39..FLOW-41, FLOW-43, FLOW-45). [G2]
9. Director's Cut level: the nine-chunk route, refuges, traps, camera, the Broken Mill room, procedural placement (FLOW-24..FLOW-29, FLOW-46, FLOW-47, HAZ-02..HAZ-41, CAM-03..CAM-08). [G2]
10. Regular enemies: Roadwarden (three types), Floodstrider, Sky Courier, male and female, red and yellow shots (COM-12..COM-18, ART-10, ANIM-08). [G2]
11. Director's Cut story: caption, text narration, light and umbra, the clock-hand clue, ending, Final Hour line (NAR-02..NAR-08). [G2]
12. Director's Cut progression: kills-only XP, the level-62 curve, stat tracks, checkpoint rules, persistence, run scaling, Final Hour, the XP ring (FLOW-05..FLOW-23, FLOW-42, FLOW-48, SURV-06). [G3]
13. The four Director's Cut spells with unlocks at levels 1 / 10 / 20 / 30 and the spell wheel (COM-07..COM-09, COM-11, MOVE-12). [G3]
14. Director's Cut win statistics (Journey Complete) and the Director-only developer Game Options (FLOW-38, FLOW-44, FLOW-49). [G3]
15. Final art, animation, VFX and audio at the key-art bar; no `_PH` left (ANIM-02..ANIM-07, ANIM-09, ANIM-10, ART-03, ART-05..ART-09, BG-02..BG-06, VFX-02..VFX-11, CORE-06). [G3]

Acceptance (GDD SH1.0 section 10): QA-29..QA-42 with recorded build, profile and seed.
Gate checks, not MVP items (D7): the title, pause, win and fail screens (defeat retry), `pipeline/qa/playtests.md`.

Stretch (never P0): stretch cards start automatically once every MVP item passes; GDD SH1.0 approves every filled requirement as APPROVED_P0, so the stretch list is:
none
Not authorized (GDD SH1.0): a fifth weapon, ammunition or stored energy, steering or mouse aiming in the normal modes, a boss tutorial on arrival, XP in Start Game, killing the Keeper.

## Cut list (first to go at the top)
1. Recorded or generated narration voice (optional in GDD SH1.0, NAR-02; text narration stays)
2. Extra ambience and music beyond the required Start / End music (ANIM-09; Ricky's sound list "to discuss")
3. Animation polish beyond each family's required actions (ANIM-02..ANIM-08 list the required ones)

Never cut: any MVP item (all are APPROVED_P0) and a packaged build.
Trigger: a gate over 2 hours late cuts the next item, without debate. GDD SH1.0 leaves its own scope-cut triggers OPEN (section 11).

## Top risks (the Producer reviews them at each gate)
| Risk | Trigger | Fallback | Owner |
|---|---|---|---|
| The package fails or differs from the editor | Package or smoke fails | Submit the last good gate zip | Packaging and submission owner |
| Paper2D or a setting misbehaves on 5.8.4 | A [VERIFY] item fails | Decision row; TD workaround same day | Technical Director, human |
| A teammate can't compile C++ | Card 0.9 fails | Non-C++ cards only (D24) | Scope decision-maker |
| A new GDD revision changes P0 | The design owner publishes a revision | Import it the same day (`docs/gdd/README.md`); `gdd_impact.py` lists the cards to re-file (D-new-gdd-sh10) | Game design owner |
| Art or audio late | MVP art or sounds missing at G2 | Tracked `_PH` placeholders (`pipeline/art/blender/characters.json` coverage), never shipped; CC0 set, card 0.15 (D-new-fallback) | Art Director |
| Human review is the bottleneck | `--queue` fails twice (D-new-port-3) | Pause new agent cards | Producer / time keeper, human |

## People (fill in; card 0.0)
Rows marked **BLOCKER** stop Day 1.
| Role | Person | Confirmed? | Day-1 blocker |
|---|---|---|---|
| Scope decision-maker (final call on cuts) | RickTheBuilder (Rick Rispoli) | default (agent) | BLOCKER |
| Creative director (tie-breaker on look, feel and theme; D34) | RickTheBuilder (Rick Rispoli; GDD SH1.0: "Rick's creative approval") | default (agent) | before Nov 11 |
| Producer / time keeper, human (D-new-producer) | Richard (GDD SH1.0 credits: Producer; GitHub login GetEmEtoG by elimination, the person edits the row) | default (agent) | BLOCKER |
| Integration owner (merges to main, keeps it building; one integrator owns cross-lane edits) | joshdrochon (Josh Rochon; GDD SH1.0 credits: Technical Lead) | default (agent) | BLOCKER |
| Packaging and submission owner | joshdrochon (Josh Rochon; the Mac G1 package and the zip, D-new-g1-mac-path; a human entrant submits, Official Rules §17) | default (agent) | BLOCKER |
| Windows packaging machine (owner, machine name, OS) | RickTheBuilder (owner; machine name and OS unset until the owner edits this row; no Windows machine is confirmed yet) | default (agent) | BLOCKER |
| Game design owner (GDD revisions, feature statuses, P0; D-new-sh10-design-owner) | RickTheBuilder (GDD SH1.0 revision note: "Rick approves all filled requirements") | default (agent) | BLOCKER |
| Technical Director, human (code-owner seat, D26) | joshdrochon (Josh Rochon; GDD SH1.0 credits: Technical Lead) | default (agent) | BLOCKER |
| GDD author (GDD SH1.0 document owner: Team Glass Umbrella) | RickTheBuilder | default (agent) | |
| Human testers (GDD SH1.0 HAZ-16, QA-29..QA-42 human checks) | Richard, RickTheBuilder | default (agent) | before G2 |
| Audio owner (approves the mix by ear) | Richard | default (agent) | before card 0.4c |
| Playtest lead | Richard | default (agent) | before G1 |

## Team hours (card 0.0: one row per teammate)
| Person | Hours D1/D2/D3/D4 | Away windows | Built UE C++ before (y/n) | Confirmed? |
|---|---|---|---|---|
| RickTheBuilder (Rick Rispoli) | 18/18/18/10 | none | n | default (agent) |
| Richard | 18/18/18/10 | none | n | default (agent) |
| joshdrochon (Josh Rochon) | 18/18/18/10 | none | y | default (agent) |


## Hard limits
- Main opens in the editor and packages at every merge. A broken main stops feature work until fixed.
- No agent merges or accepts its own work.
- Every "works" claim carries evidence: command output, a test result, or a capture.
