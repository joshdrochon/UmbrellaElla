# Art priority (Josh, Nov 13)

Every art loop works the highest-ranked unpassed piece it owns first; when a loop frees up, the next loop goes to the
highest-ranked unpassed piece nobody owns. Rank = how much the player sees it. Piece ids are the art-loop pieces in
`docs/build/art-inventory.csv`.

The ranking is a default, not a straitjacket (Josh): deviate when it saves time overall, e.g. batch pieces that share a
base, a layer or a panel session, keep a loop on a piece it is close to passing, or finish a quick near-done piece before a
hard high-rank one. Log the reason in your status when you deviate.

| Rank | Piece | What |
|---|---|---|
| 1 | ella-up-open | Ella idle/float, on screen all the time |
| 2 | ella-motion | Ella moving (float, drift) |
| 3 | ella-attack | Ella attacking, most frequent action |
| 4 | wand-shot | Ella's main shot |
| 5 | vfx-gold-impact | her shot's hit |
| 6 | bg-base | backdrop base layer, every scene |
| 7 | paper | paper ground, every scene |
| 8 | skyline | skyline, every scene |
| 9 | owl | the Keeper's body |
| 10 | ui-hud-clock | HUD clock, always visible in play |
| 11 | ella-shield | Ella shielding |
| 12 | umbrella | the umbrella |
| 13 | ella-closed | Ella with the umbrella closed |
| 14 | ui-title | title screen, first thing seen |
| 15 | enemy-sundial | most common enemy |
| 16 | owl-bolt | the Keeper's main shot |
| 17 | bolt-hit | the Keeper's shot hitting |
| 18 | vfx-keeper-warning | Keeper attack tell |
| 19 | vfx-keeper-strike | Keeper strike |
| 20 | keeper-wing | Keeper wings |
| 21 | keeper-talon | Keeper talons |
| 22 | world-solids | platforms and solids in every level |
| 23 | bg-land | backdrop land layer |
| 24 | bg-architecture | backdrop architecture layer |
| 25 | bg-atmosphere | backdrop atmosphere layer |
| 26 | wind-zone | wind fields, every level |
| 27 | wind-lines | wind streak lines |
| 28 | vfx-gust | gust |
| 29 | vfx-gust-puff | gust puff |
| 30 | ui-xp-ring | XP ring |
| 31 | yellow-shot | yellow shots |
| 32 | vfx-gold-fade | shot fade |
| 33 | ella-hurt | Ella hurt |
| 34 | ella-condition | Ella's health/condition look |
| 35 | enemy-armillary | second enemy |
| 36 | enemy-repeater | third enemy |
| 37 | vfx-part-hit | enemy part hit |
| 38 | vfx-part-break | enemy part break |
| 39 | ella-down | Ella down |
| 40 | ui-pause | pause screen |
| 41 | ui-defeated | defeated screen |
| 42 | keeper-clock | Keeper clock face |
| 43 | keeper-mech-front | Keeper mechanism front |
| 44 | keeper-mech-middle | Keeper mechanism middle |
| 45 | keeper-mech-rear | Keeper mechanism rear |
| 46 | keeper-damage | Keeper damage states |
| 47 | vfx-clock-beat | clock beat |
| 48 | vfx-clock-open | clock open |
| 49 | vfx-eye-exposed | Keeper eye exposed |
| 50 | bg-clock | backdrop clock |
| 51 | bg-water | backdrop water |
| 52 | bg-clock-water-wind | backdrop clock, water and wind |
| 53 | world-mill | Broken Mill |
| 54 | vfx-stream-start | stream beam start |
| 55 | vfx-stream-sustain | stream beam sustain |
| 56 | stream-beam | stream beam |
| 57 | vfx-needle-channel | needle channel |
| 58 | vfx-needle-pierce | needle pierce |
| 59 | vfx-needle-sliver | needle sliver |
| 60 | vfx-light-shaft | light shaft |
| 61 | vfx-light-spill | light spill |
| 62 | vfx-umbra | umbra |
| 63 | vfx-stun | stun |
| 64 | vfx-slow | slow |
| 65 | vfx-blocked | blocked |
| 66 | enemy-courier | courier enemy |
| 67 | enemy-floodstrider | floodstrider enemy |
| 68 | ui-level-up | level-up screen |
| 69 | ui-spell-wheel | spell wheel |
| 70 | ui-purchase | purchase screen |
| 71 | ui-settings | settings screen |
| 72 | ui-story-text | story text panel |
| 73 | ui-tutorial | tutorial screen |
| 74 | umbrella-repair | umbrella repair |
| 75 | ella-transition | Ella transition |
| 76 | vfx-keeper-recovery | Keeper recovery |
| 77 | world-refuge | refuge |
| 78 | bg-start-end | start and end backdrop |
| 79 | scene | whole-scene composition |
| 80 | menu-screen | menu screen |
| 81 | vfx-blackout | blackout |
| 82 | vfx-departure | Keeper departure |
| 83 | vfx-restoration | restoration |
| 84 | keeper-departure | Keeper departure pose |
| 85 | ui-journey-complete | Journey Complete screen |
| 86 | ui-credits | credits |

## Animation bar (Josh, Nov 13)
The Ella idle video is the animation bar. Once its owner approval is recorded (pipeline/art/approvals.json, the
24-frame strip), that strip and its GIF preview become the motion quality reference in every animated piece's panel:
motion smoothness, frame-to-frame consistency and style. The lead wires it in after the approval lands.

## Polish (only if time allows, after every piece passes)
- ella-idle: a slight umbrella sway in the idle loop (Josh, Nov 13). Not now.
