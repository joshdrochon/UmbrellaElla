> Generated from `pipeline/story/story-bible.md`, `pipeline/story/lines.csv`, `pipeline/story/story.json`, `tools/story_critic_prompt.md`, `evals/story-critic/README.md`, `evals/story-critic/calibration.csv`, `tools/story_check.py` at `f8c8edc` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Story Pipeline

A readable copy for people. Agents load these rules from the repo paths listed below.

## About this pipeline

- **Purpose:** One story bible and every player-facing word (in-game text, store page, video narration), checked by a machine gate and a separate blind critic.
- **Owner:** Story role (an agent); Richard (game design owner) confirms what is canon.
- **Inputs:** The GDD snapshot, the team's #story channel (pasted on the card by a human), the art bible, the menu list.
- **Outputs:** `pipeline/story/story-bible.md`, `pipeline/story/lines.csv`, the tone sheet for the art, audio and menu lanes.
- **Gates:** `story_check.py` in CI and on every story PR; the blind critic's STORY_CRITIC PASS line (`check_pr.py` rule story, `check_card.py` rule story); Richard's STORY CONFIRM line for canon.

## Built from

- Story bible and lines: `pipeline/story/story-bible.md`, `pipeline/story/lines.csv`, `pipeline/story/story.json`
- Critic: `tools/story_critic_prompt.md`, `evals/story-critic/README.md`, `evals/story-critic/calibration.csv`
- Commands and checks: `tools/story_check.py`

## Story bible and lines

### `pipeline/story/story-bible.md`

#### Story bible — Umbrella Ella

> GDD SH1.0 note (D-new-gdd-sh10): lines on this page that still describe the GDD 1.3 encounter (one owl bolt, the front shield, the 90 s survival timer, wear stages, the 1.3 QA-01..QA-28 tests) are history. The current design is `docs/gdd/GDD-SH1.0.md` and `docs/feature-manifest.json`, which win; the owning role re-files this page against the SH1.0 Rule IDs on its next card.


The one source for the world, the names and the voice of every word a player sees: in-game text, store page copy and
video narration. The Story role keeps it (`pipeline/roles/story.md`). `tools/story_check.py` reads the Names and Facts
tables below; their layout is fixed.

Where this file and the GDD disagree, the GDD wins (AGENTS.md section 2). Narrative is NAR-01, DEFERRED, with no
implementation authority (the GDD SH1.0 revision note (every filled requirement APPROVED_P0)). So nothing here is canon until Richard (game design owner) confirms it.

##### Status words
| Status | Meaning | May ship? |
|---|---|---|
| GDD | Stated by the current GDD snapshot (`docs/gdd/CURRENT`). Cite the section. | yes |
| CONFIRMED <YYYY-MM-DD> (Richard) | Richard confirmed it. The PR that sets it has his `STORY CONFIRM:` line (`tools/check_pr.py` rule story). | yes |
| DEFERRED | Listed in the GDD's narrative inventory as an idea, with no authority (NAR-01). | no |
| PROPOSED | A design proposal: from the team's #story chat, a teammate's study, or written by the story agent. | no |
| OPEN | No answer yet. A row in `docs/decisions.md` holds the question. | no |

A line in `pipeline/story/lines.csv` with `ship=yes` may use only names and facts marked GDD or CONFIRMED
(`story_check.py` fails it otherwise). Narrative surfaces (intro card, end card, clue, store description, narration)
also wait for NAR-01 to be authorised in `docs/feature-manifest.json`.

##### Sources
| ID | Source | What it gives |
|---|---|---|
| S1 | GDD 1.3 (`docs/gdd/GDD-1.3.md`) sections 1, 2, 7A, 9 and Appendix inventory | The mechanics the story must fit; tone "Gothic storybook / clockwork"; the narrative inventory, all DEFERRED |
| S2 | GDD B1.0 (`docs/gdd/GDD-B1.0.md`) | "The Last Hour" as a provisional encounter or chapter title |
| S3 | Discord #story, one post by Ricky, 2026-11-09 19:43 PST, titled "nUMBeR ELLA" | The premise, the world, the owl's motive and the ending (rows P1-P9) |
| S4 | Ricky's Ella study (mask, glowing eyes), shared with the team | A look for Ella (row P10) |
| S5 | `pipeline/art/art-bible.md` | Visual tone: ink on aged paper, near-black silhouettes, gold/amber and rust accents only |

##### Names
| Name | Kind | Status | Source | Notes |
|---|---|---|---|---|
| Ella | player character | DEFERRED | S1 Appendix narrative inventory; S3 | GDD 1.3 names her only in the DEFERRED narrative inventory, though every repo name uses it. Until Richard confirms the name, shipped text says "she" or nothing. |
| the owl | opponent | GDD | S1 sections 1, 7A | Huge, clockwork, a clock in its chest. Always "the owl" in text until a name is CONFIRMED. |
| Keeper of Time | epithet for the owl | PROPOSED | S1 "clockkeeper"; S3 "an ancient keeper of time and death" | A title, not a name. Needs a human trademark search before it ships. |
| Mother | Ella's mother (no given name) | PROPOSED | S3 | Never on screen yet. Write "her mother" in text; "Mother" only if Ella speaks to her. |
| Umbrella Ella | game title candidate | OPEN | repo working name | D-new-story-canon picks the title. |
| nUMBeR ELLA | game title candidate | PROPOSED | S3 | Wordplay on umbra, umbrella and the hour's number. Mixed case is part of it. |
| The Last Hour | chapter or encounter title | DEFERRED | S2 | Provisional only. |
| UMBRELLA / OWL | design document title | GDD | S1 cover | The GDD's own title, not a game title. |

The owl's own name is OPEN (D-new-owl-name). The name floated so far has a trademark risk and is on the deny list
(`## Never use` below): never write it in any text a player sees.

##### Facts
| ID | Fact | Status | Source | Never say (regex) |
|---|---|---|---|---|
| F1 | The player character is small and airborne under an umbrella; the owl is huge and clockwork, with a clock in its chest. | GDD | S1 section 1, 7A | |
| F2 | The open, upright umbrella lifts the player character. Closed or lowered, she falls. | GDD | S1 UMB-01, CORE-02 | |
| F3 | The owl cannot be killed. The player wins by lasting until the owl departs. | GDD | S1 END-01, QA-14 | |
| F4 | The umbrella shows the player's one health: it tears as she is hit. | GDD | S1 CORE-03, SURV-02 | |
| F5 | Holding the umbrella in front catches a bolt and mends it a little. | GDD | S1 DEF-01, SURV-03 | |
| F6 | The player character fires small gold shots while the umbrella is lowered. | GDD | S1 COM-01 | |
| F7 | The tone is gothic storybook and clockwork; play needs no story. | GDD | S1 section 1 Tone | |
| F8 | Story ideas in the GDD (the clockkeeper, a night-to-dawn hour, a stolen clock hand in the umbrella, a mysterious departure, chapter framing) are ideas only. | DEFERRED | S1 Appendix inventory | |
| P1 | Ella was meant to die. Her mother would not accept it and stole, from the owl, the clock hand that marked Ella's last hour. | PROPOSED | S3 | |
| P2 | Her mother made the stolen hand into the umbrella. Its umbra, a perfect shadow, hides Ella from the light of truth, and so from death. | PROPOSED | S3 | |
| P3 | Ella knows nothing of the theft. She believes her mother gave her the umbrella to keep her safe from a terrifying owl. | PROPOSED | S3 | \bElla\s+(?:knows\|knew\|learns\|learned\|realises\|realizes\|discovers)\s+(?:the\s+truth\|about\s+the\s+theft\|she\s+was\s+meant) |
| P4 | The world is the edge of reality, where the living pass into the afterlife. Ella hangs above an endless abyss. | PROPOSED | S3 | |
| P5 | The light of truth falls like rain and weighs down everything whose time has come. Under the open umbrella Ella is shaded and rises; closed, the light's weight pulls her down. This matches F2. | PROPOSED | S3 | |
| P6 | The owl comes to take back the missing hand and set time right. To Ella he is a monster; to him she is a life whose time has ended. Neither is evil. | PROPOSED | S3 | \b(?:evil\|wicked)\s+(?:owl\|keeper)\b |
| P7 | The umbrella wears away as the owl's attacks grow. This matches F4. | PROPOSED | S3 | |
| P8 | In the end the owl gives up the chase and goes back into the dark. Ella lives but is still between worlds. Nothing is settled: the owl may only have put off his judgment. | PROPOSED | S3 | \bElla\s+(?:returns\|goes\|flies)\s+home\b |
| P9 | The heart of it: her mother defied death out of love, the owl seeks to restore what was taken, and Ella fights for a life she does not know she was meant to lose. | PROPOSED | S3 (the post's closing line) | |
| P10 | Ella wears a mask and her eyes glow. | PROPOSED | S4 | |

Fit with the GDD: P5, P7 and P8 map onto F2, F4 and F3 with no rule change. P10 needs the Art Director: the art
bible allows only gold/amber and rust accents, and the owl's eyes are already amber (readability rule: Ella must not
read like the owl).

##### Open questions
Each one is a row in `docs/decisions.md`; Richard answers. Until then the default holds and nothing in the row ships.
| ID | Question | Default until answered | Row |
|---|---|---|---|
| Q1 | Which #story rows (P1-P10) become canon? Is the player character's name Ella (GDD 1.3 lists it only as a DEFERRED idea)? | None: in-game text uses only GDD rows and no name for her | D-new-story-canon |
| Q2 | The game's title: Umbrella Ella, nUMBeR ELLA, or another? | Title screen and store page keep "TBD"; nothing ships with a title until confirmed | D-new-story-canon |
| Q3 | The owl's name, if any. | "the owl"; never the floated name on the deny list | D-new-owl-name |
| Q4 | What are Ella's gold shots in the story? The art bible calls them the "wand bolt"; the #story premise does not mention magic. | Text never explains the shots | D-new-story-canon |
| Q5 | Night-to-dawn hour (GDD idea) or falling light of truth (#story) as the visual motif? | Neither in text | D-new-story-canon |

##### Tone target
The voice a blind critic judges every line against (rubric row S3 in `tools/story_critic_prompt.md`).
- A storybook narrator: third person, plain words, short sentences. Quiet, tender, a little ominous.
- Concrete nouns from the world: umbrella, clock, hour, hand, light, shadow, wind, ink, paper, wings.
- Death is spoken of plainly and gently ("her hour", "her time had run out"). Teen-rated: no gore, no swearing (Official Rules section 8).
- No jokes, slang, gamer words, exclamation marks or shouting capitals (`story.json` banned_words, max_exclaim).
- Menu words are plain verbs: Play, Resume, Restart, Quit. Tooltips say what the setting does, in one line.
- Reference line for the voice (S3, the post's closing line): "Her mother defied death out of love, the owl seeks to
  restore what was taken, and Ella is left fighting for a life she doesn't know she was supposed to lose."

##### Tone sheet for other lanes
What the art, audio and menu agents take from this bible. It adds mood, never rules: the art bible, the audio rules
and `pipeline/ui/menus.md` still win.
| Lane | Take this | Never |
|---|---|---|
| Art | Melancholy, not horror. Ella small, guarded, unaware; the owl solemn, not cruel (P6). Light from above as a weight (P5, PROPOSED). | Gore; an evil-looking owl; a third accent hue for Ella's eyes (P10 waits for the Art Director) |
| Audio | Clockwork and hush: ticks, a slow music box, wind, the soft hiss of light like rain (P5, PROPOSED). The owl's sounds are heavy and old, not monstrous screams. | Comic stingers; triumphant fanfare at the end (the ending is unresolved, P8) |
| Menus | Few words, verbs first, no exclamation marks. The Survived card is quiet relief, not victory. | "Victory", "You win", "Game over" in big letters |

##### Never use
The deny list in `pipeline/story/story.json` (Official Rules 15(d): no trademarks). Today: Strixon (undecided owl name,
trademark risk), Duolingo, Duo the Owl, Hedwig, Hogwarts, Harry Potter, Owlbear, Woodsy Owl, Mary Poppins, Disney,
Coraline, Fortnite, Rolex. `story_check.py` fails any line that contains one, and fails this bible if one appears
outside this section.

### `pipeline/story/lines.csv`

```csv
id,surface,text,facts,ship,note
```

### `pipeline/story/story.json`

```json
{
  "_about": "Machine rules for every player-facing word: in-game text, store page copy and video narration. tools/story_check.py reads it. A gate file (pipeline/agent-ops/gates.json): an agent changes it by a gate patch kickoff applies through the tool checks (tools/git_gate.py apply --auto), and its reviewer role reviews the PR. The story agent proposes a change on its card; it never edits this file. Names and facts are not here: they live in pipeline/story/story-bible.md, which the story agent writes.",
  "rubric_version": "story-rubric/1",
  "stuck_cycles": 3,
  "_stuck_about": "No cycle cap (D-new-no-round-cap, superseding D21): the builder/critic loop runs until PASS. needs-human to Richard only when the newest stuck_cycles critic cycles in a row are FAIL with the same false rows and no fewer of them (tools/story_check.py --stuck).",
  "_deny_about": "Never written anywhere a player can see, in any status, ship or not (Official Rules 15(d): no trademarks except the Unreal Engine logo). Matched case-insensitive on whole words. 'Strixon' is an undecided owl name with a trademark risk: it stays here until a human clears it in docs/decisions.md and removes it by PR. The rest are third-party marks or characters near our theme (owls, umbrellas, clocks, gothic storybook). A human adds to this list; never remove a term without a written reason in the commit message.",
  "deny": [
    {"term": "Strixon", "why": "undecided owl name with a trademark risk; never locked or shipped (D-new-owl-name)"},
    {"term": "Duolingo", "why": "trademark (owl mascot)"},
    {"term": "Duo the Owl", "why": "trademarked mascot"},
    {"term": "Hedwig", "why": "a character from a trademarked franchise (owl)"},
    {"term": "Hogwarts", "why": "trademarked franchise"},
    {"term": "Harry Potter", "why": "trademarked franchise"},
    {"term": "Owlbear", "why": "a trademarked tabletop game creature"},
    {"term": "Woodsy Owl", "why": "a protected government mascot"},
    {"term": "Mary Poppins", "why": "trademarked character (umbrella flight)"},
    {"term": "Disney", "why": "trademark"},
    {"term": "Coraline", "why": "trademarked film and book title"},
    {"term": "Fortnite", "why": "trademark"},
    {"term": "Rolex", "why": "trademark (clocks)"}
  ],
  "_banned_about": "Off-tone words for a quiet gothic storybook (art bible: ink on paper; GDD SH1.0 section 1 Tone). Whole words or phrases, case-insensitive. Each one fails story_check on every line.",
  "banned_words": ["awesome", "cool", "lol", "omg", "dude", "noob", "loot", "xp", "level up", "power-up", "power up",
                   "headshot", "gg", "pwned", "epic win", "let's go", "yay", "wow", "boom", "okay", "ok", "super",
                   "badass", "boss fight", "boss battle", "game over"],
  "max_exclaim": 0,
  "max_caps_run": 3,
  "_allow_caps_about": "Capitalised words that are not story names: key and button names, settings labels and screen titles from pipeline/ui/menus.md. A capitalised word in the middle of a sentence that is neither here nor a name row in the story bible fails as 'name not in the bible'. ALL-CAPS words longer than max_caps_run letters fail unless listed here.",
  "allow_caps": ["Esc", "Enter", "Space", "Shift", "Tab", "Ctrl", "Alt", "LMB", "RMB", "R2", "L2", "A", "D", "P", "R",
                 "Options", "Menu", "SFX", "UI", "PC", "Windows", "Play", "Quit", "Resume", "Settings", "Restart",
                 "Back", "Confirm", "Survived", "Pause", "Controls", "Music", "Hold", "Toggle", "On", "Off", "Remap",
                 "Screen", "Text", "Game", "Speed", "Projectile", "Umbrella", "Wear", "Shake", "English", "Title",
                 "I", "Unreal", "Engine"],
  "_surfaces_about": "Every row of pipeline/story/lines.csv names one surface. max_words caps its length. story = true means the line is narrative (NAR-01): it ships only once docs/feature-manifest.json NAR-01 is implementation_authorized, and it must cite at least one bible fact.",
  "surfaces": {
    "title":       {"max_words": 4,   "story": false, "where": "title screen and store page title"},
    "button":      {"max_words": 3,   "story": false, "where": "menu buttons (pipeline/ui/menus.md)"},
    "screen":      {"max_words": 20,  "story": false, "where": "headings and one-line text on pause, Survived and fail screens"},
    "prompt":      {"max_words": 8,   "story": false, "where": "control prompts (Confirm / Back, key hints)"},
    "tooltip":     {"max_words": 14,  "story": false, "where": "settings row help text"},
    "intro_card":  {"max_words": 45,  "story": true,  "where": "opening card before play"},
    "end_card":    {"max_words": 45,  "story": true,  "where": "card after the owl departs"},
    "clue":        {"max_words": 12,  "story": true,  "where": "one in-world line or label"},
    "store_short": {"max_words": 20,  "story": false, "where": "itch page short description"},
    "store_long":  {"max_words": 150, "story": true,  "where": "itch page description"},
    "narration":   {"max_words": 25,  "story": true,  "where": "one video narration or caption line (pipeline/submission/video-plan.md)"}
  },
  "_contradictions_about": "Text that breaks an approved GDD rule, whatever the story says. Each one names the bible fact it protects; that fact must be a GDD row in the story bible. The bible may add more under its own Facts table (Never say column).",
  "contradictions": [
    {"fact": "F3", "regex": "\\b(?:kill|kills|killed|slay|slays|slew|slain|destroy|destroys|destroyed|defeat|defeats|defeated|vanquish\\w*)\\s+(?:the\\s+|that\\s+)?(?:great\\s+|ancient\\s+)?(?:owl|keeper)\\b", "why": "the owl cannot be killed or defeated; it departs (GDD 1.3 END-01, QA-14)"},
    {"fact": "F3", "regex": "\\b(?:owl|keeper)\\s+(?:dies|died|is dead|was slain|falls dead|perishes)\\b", "why": "the owl has no HP and never dies (GDD 1.3 QA-14)"},
    {"fact": "F3", "regex": "\\b(?:owl'?s?|boss)\\s+(?:health|hp|life bar|health bar)\\b", "why": "no owl health bar (GDD 1.3 Appendix D: owl kill/health bar not authorised)"},
    {"fact": "F2", "regex": "\\b(?:close|closes|closed|closing|lower|lowers|lowered|lowering)\\s+(?:the\\s+|her\\s+|your\\s+)?umbrella\\b[^.]{0,40}\\b(?:rise|rises|rising|climb|climbs|lift|lifts|soar|soars)\\b", "why": "only the open, upright umbrella lifts (GDD 1.3 UMB-01, CORE-02)"},
    {"fact": "F2", "regex": "\\b(?:open|opens|opened|opening)\\s+(?:the\\s+|her\\s+|your\\s+)?umbrella\\b[^.]{0,40}\\b(?:fall|falls|falling|sink|sinks|dive|dives)\\b", "why": "the open, upright umbrella lifts; it never makes Ella fall (GDD 1.3 UMB-01)"}
  ]
}
```

## Critic

### `tools/story_critic_prompt.md`

#### Story critic prompt (blind)

Prompt version: `story-critic/1`. Rubric version: `story-rubric/1` (below; the same string as `rubric_version` in
`pipeline/story/story.json`). An edit to the rubric bumps both, and the calibration in `evals/story-critic/README.md`
runs again before the critic's verdicts count.

Who runs it: a fresh Story session that did not write or edit the lines (`pipeline/roles/story.md`, quality loop).
The runner fills the `{...}` slots. It never tells the critic which lines are new, which session wrote them, or which
version is expected to win. Lines are labelled only by id; a revision pair is labelled `X` and `Y`.

---

You are judging player-facing text for a small game against a fixed story bible and tone target. You did not write
these lines. You do not know which lines are new or which version is preferred. Do not guess. Judge only the text.

The story bible (world, names, facts and their status, tone target):

{story_bible}

Surfaces and their word caps, the deny list and banned words (from story.json):

{story_json_surfaces_deny_banned}

The machine check already ran (`tools/story_check.py`). Its FAIL is final and you cannot override it; you still answer
every row:

{story_check_output}

For EACH line, answer every row with `true` or `false`. A `false` quotes the exact words that break it and names the
bible row (F1, P3, Tone target) or rule it breaks. A `true` needs no quote. No scores, no ratings, no 1-10 numbers.

| id | question (true = meets the standard) | source |
|---|---|---|
| S1 | Agrees with every bible fact, and states nothing the bible marks OPEN, or does not hold, as settled | bible Facts, Open questions |
| S2 | Uses only names from the bible's Names table; a name that is not GDD or CONFIRMED is on a line with ship=no | bible Names, Status words |
| S3 | Matches the tone target: plain, quiet, gothic storybook; no jokes, puns, slang, gamer words or shouting | bible Tone target |
| S4 | Fits its surface: within the word cap and readable at a glance on that screen | story.json surfaces |
| S5 | A 13-year-old understands it on one read; teen-rated (no gore, no swearing) | Official Rules section 8 |
| S6 | Does its surface's job: a button names an action, a tooltip says what the setting changes, a card tells one beat | `pipeline/ui/menus.md`; bible Tone target |
| S7 | Names no trademark, real person, brand or another work's character | Official Rules 15(d); story.json deny |
| S8 | Promises no mechanic the player will not find (only F2-F6: lift, fall, wear, shield, shots, the owl departs) | bible Facts F2-F6 |

For a revision pair (`X` and `Y`, the same id), also answer: which is closer to the standard, `X`, `Y` or `tie`.
The runner asks twice with the order swapped; both answers must agree, or the pair goes to a human.

Answer in this exact shape, one block per line id, then the verdict line:

```
<id>: S1 true | S2 true | S3 false "Awesome run" (Tone target: slang) | S4 true | S5 true | S6 true | S7 true | S8 true
...
STORY_CRITIC: PASS|FAIL lines=<count> bible=<bible hash> sheet=<sheet hash> rubric=story-rubric/1 cycle=<n> builder=<builder session> critic=<your session>
```

PASS only when every row of every line is `true`. The hashes and the builder session come from the runner; copy them
exactly. Then list, for each `false`, the smallest rewrite that would make it `true` (keep the rest unchanged).

### `evals/story-critic/README.md`

#### Story critic calibration

The critic (`tools/story_critic_prompt.md`) is trusted only after it catches known-bad lines. The machine half
(`tools/story_check.py`) is tested the same way, in the unit tests.

`calibration.csv` holds 22 lines, each written to break one rubric row or to pass:
- `kind=none`: good lines. `story_check.py` passes them; the critic must answer every row `true`.
- `machine=yes`: `story_check.py --calibrate` must fail each one with its `kind` (deny, contradiction, banned, exclaim,
  caps, name, length, fact, ship, nar). `tests/test_story_check.py` runs it in CI.
- `machine=no`: only a reader catches these (a pun, an unclear tooltip, a promised mechanic, invented lore). The critic
  must answer the `rubric` row `false` for each.

##### Run (before the first critic verdict of a session; void the session if it fails)
1. `python3 tools/story_check.py --calibrate` prints `story_check: calibrate PASS rows=<n>`.
2. A fresh Story session runs the critic prompt on `calibration.csv` (lines only; the `kind`, `machine`, `rubric` and
   `note` columns are removed and the rows shuffled, seed written in the PR).
3. Bar: every good row all `true`, every bad row `false` on its `rubric` row. 100%, no exceptions.
4. Paste the critic's verdict line and the bar result in the PR or card: `STORY_CALIBRATION: PASS rows=<n> seed=<n>`.

The calibration is valid only for one exact model id and the prompt and rubric versions at the top of the prompt.
Changing either, or the bible's Tone target, voids it. A row is never softened to let a critic pass; a mislabelled
row may be fixed with the reason in the commit message.

### `evals/story-critic/calibration.csv`

```csv
id,surface,text,facts,ship,note,kind,machine,rubric
good-button,button,Play,,no,menu verb,none,yes,none
good-tooltip,tooltip,"Hold the button to keep the umbrella shut, or press once to switch.",,no,says what the setting does,none,yes,none
good-intro,intro_card,"Her mother gave her an umbrella and one warning: never let the owl take it.",P2;P3,no,quiet and plain,none,yes,none
good-end,end_card,"The owl folds its wings and turns back into the dark. Ella is still between worlds, and her hour has not come.",F3;P8,no,unresolved ending,none,yes,none
bad-deny,narration,"Strixon, keeper of the hours, comes for Ella.",P6,no,deny-listed owl name,deny,yes,S7
bad-trademark,store_short,"Like Mary Poppins, but darker.",,no,third-party character,deny,yes,S7
bad-kill,end_card,Ella kills the owl and the night is over.,F3,no,owl cannot be killed,contradiction,yes,S1
bad-closed-rise,tooltip,Close the umbrella to rise faster.,,no,only the open umbrella lifts,contradiction,yes,S8
bad-learns,end_card,Ella learns the truth and forgives her mother.,P3;P9,no,settles what the bible leaves open,contradiction,yes,S1
bad-evil,narration,The evil owl hunts the innocent girl.,P6,no,the owl is not evil,contradiction,yes,S1
bad-banned,screen,"Awesome run, you survived.",,no,slang,banned,yes,S3
bad-exclaim,screen,You survived!,,no,exclamation mark,exclaim,yes,S3
bad-caps,button,RETRY NOW,,no,shouting,caps,yes,S3
bad-name,intro_card,Ella's brother Tomas waits far below.,P1,no,a name the bible does not have,name,yes,S2
bad-length,tooltip,"This setting changes how quickly every single projectile in the whole encounter travels across the screen toward you.",,no,too long for a tooltip,length,yes,S4
bad-nofact,clue,The hand is missing.,,no,narrative line citing nothing,fact,yes,S1
bad-ship-proposed,intro_card,Her mother stole the hand of the clock.,P1,yes,PROPOSED fact marked to ship,ship,yes,S1
bad-nar,end_card,The owl departs. Ella is still in the air.,F3,yes,narrative surface while NAR-01 is DEFERRED,nar,yes,S1
critic-pun,screen,"Owl be back for you, little one.",,no,a pun breaks the quiet tone,tone,no,S3
critic-unclear,tooltip,Adjusts the thing for the other thing.,,no,does not say what the setting does,clarity,no,S6
critic-promise,store_short,Collect feathers and upgrade your umbrella across twelve levels.,,no,promises mechanics the GDD does not have,mechanics,no,S8
critic-new-lore,intro_card,"Ella's father built the owl, long ago.",P1,no,invents lore the bible does not hold and states it as settled,lore,no,S1
```

## Commands and checks

### `tools/story_check.py`

Usage text from the file:

```text
Story and text check: every word a player sees agrees with the story bible, uses only its names, keeps the tone and
never names a trademark. Stdlib only. The machine half of the story gate; the blind critic
(tools/story_critic_prompt.md) judges what a regex cannot. A FAIL here is final: the critic cannot override it.

Files:
  pipeline/story/story-bible.md   world, names, facts, tone (the Story role writes it). Names and Facts tables are parsed:
                                  Names  | Name | Kind | Status | Source | Notes |
                                  Facts  | ID | Fact | Status | Source | Never say (regex) |   (escape a regex pipe as \|)
                                  Status: GDD, DEFERRED, PROPOSED, OPEN or `CONFIRMED <YYYY-MM-DD> (Richard)`.
  pipeline/story/lines.csv        every player-facing line: id,surface,text,facts,ship,note
  pipeline/story/story.json       deny list, banned words, surfaces and their word caps, allowed capitals, GDD
                                  contradictions (a gate file: humans change it)
  docs/feature-manifest.json      NAR-01: narrative surfaces ship only once it is implementation_authorized

Checks on the bible (kind in brackets):
  [bible]   the required sections exist; every Names and Facts row has a valid status and a source that exists;
            fact IDs are unique and every Never-say regex compiles; every story.json contradiction names a GDD fact
  [deny]    no deny-list term outside the bible's "## Never use" section, and that section lists every term
Checks on every line of lines.csv:
  [csv] header and columns; ids unique; a known surface; ship is yes or no; text not empty
  [deny] a deny-list term (Official Rules 15(d); "Strixon" is one) in any line, shipped or not
  [banned] an off-tone word; [exclaim] more than max_exclaim '!'; [caps] an ALL-CAPS word longer than max_caps_run
  [emoji] an emoji or pictograph; [length] more words than the surface allows
  [name] a capitalised word mid-sentence that is not a bible name and not in story.json allow_caps
  [contradiction] text that matches a story.json contradiction or a bible fact's Never-say regex
  [fact] a cited fact ID the bible lacks; a narrative surface (story=true) that cites no fact
  [ship] ship=yes with a cited fact, or a bible name in the text, whose status is not GDD or CONFIRMED
  [nar] ship=yes on a narrative surface while NAR-01 is not implementation_authorized

Usage:
  python3 tools/story_check.py                     bible + lines; prints
                                                   `story_check: PASS bible=<8 hex> sheet=<8 hex> lines=<n> names=<n> facts=<n>`
  python3 tools/story_check.py --scan FILE...      any text a player sees outside lines.csv (the UI string table
                                                   Content/UmbrellaElla/UI/ST_UI.csv, the itch page): deny, banned,
                                                   exclaim, caps, emoji, and names for CSV string tables. Prints
                                                   `story_check: PASS scan files=<n> strings=<n>`
  python3 tools/story_check.py --table CSV        a UI string table (Key and SourceString columns, card 0.20) matches
                                                   lines.csv: every key has a row with the same id and the same text.
                                                   Prints `story_check: PASS table keys=<n>`
  python3 tools/story_check.py --critic "LINE"     a STORY_CRITIC line is well formed and was made on this exact bible
                                                   and sheet by a session other than the builder's
  python3 tools/story_check.py --calibrate [CSV]   every known-bad row of evals/story-critic/calibration.csv that is
                                                   marked machine=yes fails with its kind; every good row passes
  python3 tools/story_check.py --stuck FILE...     the critic's answers, one file per cycle (oldest first). There is no
                                                   cycle cap (D-new-no-round-cap); prints `story_check: STUCK ...` (exit 4)
                                                   only when the newest story.json stuck_cycles (3) cycles in a row are
                                                   FAIL with the same false rows (the same gap) and no fewer of them,
                                                   else `story_check: not stuck` (exit 0)
  python3 tools/story_check.py --hash              prints `bible=<8 hex> sheet=<8 hex>`
  Options: --root R, --bible F, --lines F, --rules F, --manifest F
Exit 0 = PASS, 1 = problems, 2 = usage or unreadable input, 4 = stuck (--stuck: NEEDS HUMAN to Richard).
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: "Story text (Story role): bible, names, tone, deny list; the critic calibration set still fails where it should"

Tests: `tests/test_pipeline_check.py`, `tests/test_story_check.py`
