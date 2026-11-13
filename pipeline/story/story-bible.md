# Story bible — Umbrella Ella

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


The one source for the world, the names and the voice of every word a player sees: in-game text, store page copy and
video narration. The Story role keeps it (`pipeline/roles/story.md`). `tools/story_check.py` reads the Names and Facts
tables below; their layout is fixed.

Where this file and the GDD disagree, the GDD wins (AGENTS.md section 2). Narrative is NAR-01, DEFERRED, with no
implementation authority (the GDD SH1.0 revision note (every filled requirement APPROVED_P0)). So nothing here is canon until Richard (game design owner) confirms it.

## Status words
| Status | Meaning | May ship? |
|---|---|---|
| GDD | Stated by the current GDD snapshot (`docs/gdd/CURRENT`). Cite the section. | yes |
| CONFIRMED <YYYY-MM-DD> (Richard) | Richard confirmed it. The PR that sets it has his `STORY CONFIRM:` line (`tools/check_pr.py` rule story). | yes |
| CONFIRMED <YYYY-MM-DD> (agent default; team may override) | Confirmed by the agent default in `D-new-story-canon` (Josh, Nov 12: no one waits for sign-off). Counts as CONFIRMED for shipping until the team overrides it; the team or Richard can change it at any time. | yes |
| DEFERRED | Listed in the GDD's narrative inventory as an idea, with no authority (NAR-01). | no |
| PROPOSED | A design proposal: from the team's #story chat, a teammate's study, or written by the story agent. | no |
| OPEN | No answer yet. A row in `docs/decisions.md` holds the question. | no |

A line in `pipeline/story/lines.csv` with `ship=yes` may use only names and facts marked GDD or CONFIRMED (Richard or agent default)
(`story_check.py` fails it otherwise). Narrative surfaces (intro card, end card, clue, store description, narration)
also wait for NAR-01 to be authorised in `docs/feature-manifest.json`.

## Sources
| ID | Source | What it gives |
|---|---|---|
| S1 | GDD 1.3 (`docs/gdd/GDD-1.3.md`) sections 1, 2, 7A, 9 and Appendix inventory | The mechanics the story must fit; tone "Gothic storybook / clockwork"; the narrative inventory, all DEFERRED |
| S2 | GDD B1.0 (`docs/gdd/GDD-B1.0.md`) | "The Last Hour" as a provisional encounter or chapter title |
| S3 | Discord #story, one post by Ricky, 2026-11-09 19:43 PST, titled "nUMBeR ELLA" | The premise, the world, the owl's motive and the ending (rows P1-P9) |
| S4 | Ricky's Ella study (mask, glowing eyes), shared with the team | A look for Ella (row P10) |
| S6 | GDD SH1.0 (`docs/gdd/GDD-SH1.0.md`) | The current design: controls (MOVE-05, MOVE-06, MOVE-08), weapons (MOVE-12), health (SURV-05, SURV-07), growth (FLOW-15, SURV-06), credits |
| S5 | `pipeline/art/art-bible.md` | Visual tone: ink on aged paper, near-black silhouettes, gold/amber and rust accents only |

## Names
| Name | Kind | Status | Source | Notes |
|---|---|---|---|---|
| Ella | player character | CONFIRMED 2026-11-12 (agent default; team may override) | S1 Appendix narrative inventory; S3 | GDD 1.3 names her only in the DEFERRED narrative inventory, though every repo name uses it. Until Richard confirms the name, shipped text says "she" or nothing. |
| the owl | opponent | GDD | S1 sections 1, 7A | Huge, clockwork, a clock in its chest. Always "the owl" in text until a name is CONFIRMED. |
| Keeper of Time | epithet for the owl | PROPOSED | S1 "clockkeeper"; S3 "an ancient keeper of time and death" | A title, not a name. Needs a human trademark search before it ships. |
| Mother | Ella's mother (no given name) | CONFIRMED 2026-11-12 (agent default; team may override) | S3 | Never on screen yet. Write "her mother" in text; "Mother" only if Ella speaks to her, or as the speaker label on a caption she speaks (GDD NAR-04: "Mother: Keep it open."). |
| Umbrella Ella | game title (start of "Umbrella Ella The Stolen Hour") | CONFIRMED 2026-11-12 (agent default; Josh decided the title, D-new-title-text) | repo working name | `docs/decisions.md` D-new-title-text. |
| nUMBeR ELLA | game title candidate | PROPOSED | S3 | Wordplay on umbra, umbrella and the hour's number. Mixed case is part of it. |
| The Last Hour | chapter or encounter title | DEFERRED | S2 | Provisional only. |
| UMBRELLA / OWL | design document title | GDD | S1 cover | The GDD's own title, not a game title. |
| Absorb | control name | GDD | S6 MOVE-05 | Hold to catch yellow shots while dropping; they heal. Shown in controls. |
| Hop, Dash, Ride | control names | GDD | S6 MOVE-06 | Hop rises overhead; Dash moves back or forward while falling; Ride holds on to a harmless wind current. |
| Small Blasts, Streamed Blast, Twin Stars, Needle Spell | spell names (Spell 1 to 4) | GDD | S6 MOVE-08, MOVE-12 | The four weapons of Director's Cut. Start Game has only Small Blasts. Text never says what they are in the story (Q4). |
| Keeper | the owl, as the GDD names the encounter | GDD | S6 section 1, OWL-06 | In settings and tuning labels ("Keeper part health"). Story text still says "the owl". It has wings, three hanging mechanisms and a clock (phases 1 to 3). |
| Trim | control name | GDD | S6 MOVE-05 area, Vertical trim | Left stick up or down, W or S: rise a little more or less while dropping. |
| Suction | absorb reach | GDD | S6 Absorb section, SURV-06 | The range and cone in which Absorb catches yellow shots. |
| Lives | health count | GDD | S6 SURV-05, SURV-07 | Three lives, each three hits; one clock shows them. |
| Points, Level, Experience | growth terms | GDD | S6 FLOW-15, FLOW-49 | Director's Cut: a level gives one point, spent at a refuge or between runs. |
| Director's Cut | game mode | GDD | S6 section 1, FLOW-49 | The airborne journey with growth. Title menu item (D-new-title-text). |
| Rick Rispoli | real person, credit | CONFIRMED 2026-11-12 (agent default; team may override) | GDD SH1.0 credits; jam brief | Executive Producer. A team member named in the credits with their consent as entrants; not a story name. |
| Richard | real person, credit | CONFIRMED 2026-11-12 (agent default; team may override) | GDD SH1.0 credits | Producer. Team member named in the credits. |
| Josh Rochon | real person, credit | CONFIRMED 2026-11-12 (agent default; team may override) | jam brief people table | Technical Lead. Team member named in the credits. |

The owl's own name is OPEN (D-new-owl-name). The name floated so far has a trademark risk and is on the deny list
(`## Never use` below): never write it in any text a player sees.

## Facts
| ID | Fact | Status | Source | Never say (regex) |
|---|---|---|---|---|
| F1 | The player character is small and airborne under an umbrella; the owl is huge and clockwork, with a clock in its chest. | GDD | S1 section 1, 7A | |
| F2 | The open, upright umbrella lifts the player character. Closed or lowered, she falls. | GDD | S1 UMB-01, CORE-02 | |
| F3 | The owl cannot be killed. The player wins by lasting until the owl departs. | GDD | S1 END-01, QA-14 | |
| F4 | The umbrella shows the player's one health: it tears as she is hit. | GDD | S1 CORE-03, SURV-02 | |
| F5 | Holding the umbrella in front catches a bolt and mends it a little. | GDD | S1 DEF-01, SURV-03 | |
| F6 | The player character fires small gold shots while the umbrella is lowered. | GDD | S1 COM-01 | |
| F7 | The tone is gothic storybook and clockwork; play needs no story. | GDD | S1 section 1 Tone | |
| F9 | On the keeper's arrival the player sees the clock's single remaining hand and an empty place beside it, with a matching bronze shaft detail. It is a clue to look at, not an explanation. | GDD | S1 NAR-06 | |
| F10 | Absorb, Hop, Dash and Ride are the controls: hold Absorb to catch yellow shots and heal; Hop rises; Dash moves while falling; Ride holds on to a harmless wind current. | GDD | S6 MOVE-05, MOVE-06 | |
| F11 | Director's Cut has four spells (Small Blasts, Streamed Blast, Twin Stars, Needle Spell) and growth: each level gives a point spent at a refuge or between runs on hits per life, lives, recovery, damage reduction, suction range, suction cone or the damage of each of the four spells. Director's Cut cycles spells with [ and ] or the D-pad, or keys 1 to 4. | GDD | S6 MOVE-08, MOVE-12, FLOW-15, SURV-06, SURV-07 | |
| F12 | Health is three lives of three hits each, shown by one clock. | GDD | S6 SURV-05, SURV-07 | |
| F13 | Journey Complete is the Director's Cut results screen, shown after a win. It counts enemies defeated, experience earned, deaths, distance flown, shots fired, shots fired at you (enemy shots aimed at Ella), damage taken and health restored. The owl itself is never killed (F3). | GDD | S6 FLOW-49 | |
| F14 | Beyond the umbrella and shots, the Keeper fight has hostile gusts, enemy shots, wings, three hanging mechanisms, a clock, a three-second eye blackout, and a 1.2 second stun when a mechanism breaks. Basic shots never run out. | GDD | S6 MOVE-05, OWL-06, OWL-30 | |
| F15 | In Rick's story the owl may only have put off his judgment, or something about Ella has challenged even his understanding of time. | GDD | S6 section 6 (the story text) | |
| F8 | Story ideas in the GDD (the clockkeeper, a night-to-dawn hour, a stolen clock hand in the umbrella, a mysterious departure, chapter framing) are ideas only. | DEFERRED | S1 Appendix inventory | |
| P1 | Ella was meant to die. Her mother would not accept it and stole, from the owl, the clock hand that marked Ella's last hour. | CONFIRMED 2026-11-12 (agent default; team may override) | S3 | |
| P2 | Her mother made the stolen hand into the umbrella. Its umbra, a perfect shadow, hides Ella from the light of truth, and so from death. | CONFIRMED 2026-11-12 (agent default; team may override) | S3 | |
| P3 | Ella knows nothing of the theft. She believes her mother gave her the umbrella to keep her safe from a terrifying owl. | CONFIRMED 2026-11-12 (agent default; team may override) | S3 | \bElla\s+(?:knows\|knew\|learns\|learned\|realises\|realizes\|discovers)\s+(?:the\s+truth\|about\s+the\s+theft\|she\s+was\s+meant) |
| P4 | The world is the edge of reality, where the living pass into the afterlife. Ella hangs above an endless abyss. | CONFIRMED 2026-11-12 (agent default; team may override) | S3 | |
| P5 | The light of truth falls like rain and weighs down everything whose time has come. Under the open umbrella Ella is shaded and rises; closed, the light's weight pulls her down. This matches F2. | CONFIRMED 2026-11-12 (agent default; team may override) | S3 | |
| P6 | The owl comes to take back the missing hand and set time right. To Ella he is a monster; to him she is a life whose time has ended. Neither is evil. | CONFIRMED 2026-11-12 (agent default; team may override) | S3 | \b(?:evil\|wicked)\s+(?:owl\|keeper)\b |
| P7 | The umbrella wears away as the owl's attacks grow. This matches F4. | CONFIRMED 2026-11-12 (agent default; team may override) | S3 | |
| P8 | In the end the owl gives up the chase and goes back into the dark. Ella lives but is still between worlds. Nothing is settled: the owl may only have put off his judgment. | CONFIRMED 2026-11-12 (agent default; team may override) | S3 | \bElla\s+(?:returns\|goes\|flies)\s+home\b |
| P9 | The heart of it: her mother defied death out of love, the owl seeks to restore what was taken, and Ella fights for a life she does not know she was meant to lose. | PROPOSED | S3 (the post's closing line) | |
| P10 | Ella wears a mask and her eyes glow. | PROPOSED | S4 | |

Fit with the GDD: P5, P7 and P8 map onto F2, F4 and F3 with no rule change. P10 needs the Art Director: the art
bible allows only gold/amber and rust accents, and the owl's eyes are already amber (readability rule: Ella must not
read like the owl).

## Open questions
Each one is a row in `docs/decisions.md`; Richard answers. Until then the default holds and nothing in the row ships.
| ID | Question | Default until answered | Row |
|---|---|---|---|
| Q1 | Which #story rows (P1-P10) become canon? Is the player character's name Ella (GDD 1.3 lists it only as a DEFERRED idea)? | Answered 2026-11-12 (agent default, Josh: no one waits): P1-P8, Ella and Mother are CONFIRMED; P9 and P10 stay PROPOSED. The team may override | D-new-story-canon |
| Q2 | The game's title: Umbrella Ella, nUMBeR ELLA, or another? | Title screen and store page keep "TBD"; nothing ships with a title until confirmed | D-new-story-canon |
| Q3 | The owl's name, if any. | "the owl"; never the floated name on the deny list | D-new-owl-name |
| Q4 | What are Ella's gold shots in the story? The art bible calls them the "wand bolt"; the #story premise does not mention magic. | Text never explains the shots | D-new-story-canon |
| Q5 | Night-to-dawn hour (GDD idea) or falling light of truth (#story) as the visual motif? | Answered 2026-11-12 (agent default): the falling light of truth (P5, CONFIRMED); the night-to-dawn hour stays DEFERRED | D-new-story-canon |

## Tone target
The voice a blind critic judges every line against (rubric row S3 in `tools/story_critic_prompt.md`).
- A storybook narrator: third person, plain words, short sentences. Quiet, tender, a little ominous.
- Concrete nouns from the world: umbrella, clock, hour, hand, light, shadow, wind, ink, paper, wings.
- Death is spoken of plainly and gently ("her hour", "her time had run out"). Teen-rated: no gore, no swearing (Official Rules section 8).
- No jokes, slang, gamer words, exclamation marks or shouting capitals (`story.json` banned_words, max_exclaim).
- Menu words are plain verbs: Play, Resume, Restart, Quit. Tooltips say what the setting does, in one line.
- Reference line for the voice (S3, the post's closing line): "Her mother defied death out of love, the owl seeks to
  restore what was taken, and Ella is left fighting for a life she doesn't know she was supposed to lose."

## Tone sheet for other lanes
What the art, audio and menu agents take from this bible. It adds mood, never rules: the art bible, the audio rules
and `pipeline/ui/menus.md` still win.
| Lane | Take this | Never |
|---|---|---|
| Art | Melancholy, not horror. Ella small, guarded, unaware; the owl solemn, not cruel (P6). Light from above as a weight (P5, PROPOSED). | Gore; an evil-looking owl; a third accent hue for Ella's eyes (P10 waits for the Art Director) |
| Audio | Clockwork and hush: ticks, a slow music box, wind, the soft hiss of light like rain (P5, PROPOSED). The owl's sounds are heavy and old, not monstrous screams. | Comic stingers; triumphant fanfare at the end (the ending is unresolved, P8) |
| Menus | Few words, verbs first, no exclamation marks. The Survived card is quiet relief, not victory. | "Victory", "You win", "Game over" in big letters |

## Never use
The deny list in `pipeline/story/story.json` (Official Rules 15(d): no trademarks). Today: Strixon (undecided owl name,
trademark risk), Duolingo, Duo the Owl, Hedwig, Hogwarts, Harry Potter, Owlbear, Woodsy Owl, Mary Poppins, Disney,
Coraline, Fortnite, Rolex. `story_check.py` fails any line that contains one, and fails this bible if one appears
outside this section.
