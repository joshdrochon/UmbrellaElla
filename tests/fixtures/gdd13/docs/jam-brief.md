# Jam Brief: UMBRELLA / OWL ("The Last Hour" is a provisional title)

Every agent reads this first. If it disagrees with another document, add a decision row, build its default, say so in the PR.

## The game
- **What:** a single-screen 2D aerial survival encounter against one clockwork owl (GDD 1.3). Only an open, upright umbrella lifts; everything else falls at normal gravity, never faster. Survive until the owl leaves; no boss kill.
- **Engine:** Unreal Engine **5.8.4**. **Platform:** Windows. Submission: a Windows **Development** package (no Shipping).
- **Win:** survive until the owl departs (END-01). **Lose:** health reaches zero, or the player crosses the bottom boundary (CORE-03). Retry returns to READY.
- **Design source:** the snapshot `docs/gdd/CURRENT` names (now `docs/gdd/GDD-1.3.md`); feature statuses in `docs/feature-manifest.json`.

Content caps: flipbook frames 60 in total. More owl patterns than the one base bolt need a decision row (D-new-caps).

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
Hard stop: TBD
Card 0.9 cutoff: TBD

| Gate | Due |
|---|---|
| G1 | TBD |
| G2 | TBD |
| G3 | TBD |
| G4 | TBD |

Checked by `python3 tools/check_card.py --clock` (D-new-tune-day: G3 at least 20 h before the deadline).

## Sources of truth
Play: the GDD snapshot, its mirror `docs/feature-manifest.json`, then `docs/game-spec.md`. Look: the key art + `pipeline/art/art-bible.md` (D0).
Feel: `docs/feel-spec.md`. Owl: `pipeline/level/encounter.md`. Undecided: `docs/decisions.md`. Process: `AGENTS.md`.

## MVP — the game is "done" when all of these are true in a packaged build
**GDD 1.3 §2 approves these as APPROVED_P0** (Richard, 8 Nov). Build only after the start (D39). Numbers: manifest `approved_parameters`.
1. Fixed 16:9 arena, safe top/sides, bottom defeat. [G1]
2. UP_OPEN rises (default on release); attack and shield descent fall naturally, no fast fall (UMB-01, CORE-02). [G1]
3. Steering in every state (CORE-01). [G1]
4. One 100 HP value shown as umbrella wear; bottom defeat (CORE-03, SURV-02). [G1]
5. Restart back to READY (FLOW-01). [G1]
6. Survive 90 s ACTIVE time; the owl departs (END-01). [G1]
7. One telegraphed owl bolt; CLOCK and BODY hit regions (OWL-01, OWL-05). [G2]
8. Dev-only test harness (QA-BASE, card 0.27). [G2]
9. Hold ATTACK: auto-fire +X (COM-01, UMB-02). [G1]
10. Hold SHIELD: block and heal; shield wins (DEF-01, SURV-03). [G2]
11. Safe upward wind (WIND-01). [G1]
12. Sprite loops and two background layers (ANIM-01, BG-01). [G2]

Acceptance (GDD 1.3 §12 step 19): a new player survives or fails a full loop; a warning precedes every danger.
Gate checks, not MVP items (D7): title, pause, Survived and fail screens, `pipeline/qa/playtests.md`.

Stretch (never P0): stretch cards start automatically once every MVP item passes, in the listed order, each behind its flag, off:
owl gust (OWL-02) → sideways catch → body hit consequences → wind wear → wear reduces lift → clock interrupt → wing changes wind → background motif → art-set selector → umbrella inversion → returning projectile → steam vent
Not authorized (GDD 1.3 Appendix D): aim angle, extra fast fall, scrolling camera, owl kill, mobile.

## Cut list (first to go at the top)
1. Any unstarted stretch item, last in the stretch order first
2. Music cut to one loop, then dropped (keep sound effects)
3. Visual polish above the P0 minimum (BG-01 may go static, §7A)
4. Any second owl pattern

Never cut: any MVP item (all are APPROVED_P0) and a packaged build.
Trigger: a gate over 2 hours late cuts the next item, without debate.

## Top risks (the Producer reviews them at each gate)
| Risk | Trigger | Fallback | Owner |
|---|---|---|---|
| The package fails or differs from the editor | Package or smoke fails | Submit the last good gate zip | Packaging and submission owner |
| Paper2D or a setting misbehaves on 5.8.4 | A [VERIFY] item fails | Decision row; TD workaround same day | Technical Director, human |
| A teammate can't compile C++ | Card 0.9 fails | Non-C++ cards only (D24) | Scope decision-maker |
| The theme changes P0 | Card 0.19 picks a pitch that changes P0 | New GDD revision the same day; `gdd_impact.py` lists the cards to re-file (DEC-10) | Game design owner |
| Art or audio late | MVP art or sounds missing at G2 | CC0 set, card 0.15 (D-new-fallback) | Art Director |
| Human review is the bottleneck | `--queue` fails twice (D-new-port-3) | Pause new agent cards | Producer / time keeper, human |

## People (fill in; card 0.0)
Rows marked **BLOCKER** stop Day 1.
| Role | Person | Confirmed? | Day-1 blocker |
|---|---|---|---|
| Scope decision-maker (final call on cuts) | Rick (proposed) | no | BLOCKER |
| Creative director (tie-breaker on look, feel and theme; D34) | Rich (proposed) | no | before Nov 11 |
| Producer / time keeper, human (D-new-producer) | TBD | no | BLOCKER |
| Integration owner (merges to main, keeps it building; one integrator owns cross-lane edits) | TBD | no | BLOCKER |
| Packaging and submission owner | TBD | no | BLOCKER |
| Windows packaging machine (owner, machine name, OS) | TBD | no | BLOCKER |
| Game design owner (GDD 1.3 §14 design owner and approver: mechanics, GDD revisions, DEC rows, P0) | Richard (GDD 1.3 §14) | no | BLOCKER |
| Technical Director, human (code-owner seat, D26; GDD 1.3 §14 pipeline and AI lead, design reviewer assisting) | Josh (GDD 1.3 §14) | no | BLOCKER |
| GDD contributor and build execution (GDD 1.3 §14) | Rick | no | |
| Human testers (GDD 1.3 §14, QA-12) | Richard and the design reviewer (D-new-gddb-people) | no | before G2 |
| Audio owner (approves the mix by ear) | TBD | no | before card 0.4c |
| Playtest lead | TBD | no | before G1 |

## Team hours (card 0.0: one row per teammate)
| Person | Hours D1/D2/D3/D4 | Away windows | Built UE C++ before (y/n) | Confirmed? |
|---|---|---|---|---|
| TBD | TBD | TBD | TBD | no |

## Hard limits
- Main opens in the editor and packages at every merge. A broken main stops feature work until fixed.
- No agent merges or accepts its own work.
- Every "works" claim carries evidence: command output, a test result, or a capture.
