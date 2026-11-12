> Generated from `pipeline/audio/style-target.md`, `pipeline/audio/style.json`, `pipeline/audio/sound-events.json`, `pipeline/audio/audio-rules.md`, `pipeline/audio/audio-rules.json`, `pipeline/audio/sound-list.csv`, `tools/audio_loop.py`, `tools/audio_critic_prompt.md`, `tools/audio_check.py`, `tools/audio_style_check.py`, `tools/audio_import.py`, `tools/ue/audio_dump.py`, `pipeline/audio/ue/audio_dump.py` at `f8c8edc` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Audio Pipeline

A readable copy for people. Agents load these rules from the repo paths listed below.

## About this pipeline

- **Purpose:** Every sound the game makes, on one gothic orchestral bar, with a mix that keeps every warning audible.
- **Owner:** Audio role; the audio owner (human) approves by ear in the packaged build.
- **Inputs:** The sound list, the event coverage map, the style target, the audio rules, the GDD sound needs, supplied files.
- **Outputs:** Source WAVs, sound assets, provenance rows, critic verdicts, mix approvals.
- **Gates:** `audio_check.py --list`, `--events`, `--docs` and `--scan` and `audio_style_check.py check` in CI; the editor dump check; the builder and critic loop (`audio_loop.py close`, required on audio PRs); the human final listen.

## Built from

- Style target and coverage: `pipeline/audio/style-target.md`, `pipeline/audio/style.json`, `pipeline/audio/sound-events.json`
- Audio rules and sound list: `pipeline/audio/audio-rules.md`, `pipeline/audio/audio-rules.json`, `pipeline/audio/sound-list.csv`
- Builder and critic loop: `tools/audio_loop.py`, `tools/audio_critic_prompt.md`
- Commands and checks: `tools/audio_check.py`, `tools/audio_style_check.py`, `tools/audio_import.py`, `tools/ue/audio_dump.py`, `pipeline/audio/ue/audio_dump.py`

## Style target and coverage

### `pipeline/audio/style-target.md`

#### Audio style target (on demand: Audio, QA and Build, reviewers of audio PRs)

The quality bar for every sound and every music stem. Machine copy: `pipeline/audio/style.json` (gate file; a human
changes it by PR). `tools/audio_style_check.py` measures takes against it, `tools/assetgen.py` builds every audio
prompt from it, and `tools/audio_loop.py` runs the builder and critic rounds against it. Status: **proposed**
(section 6). The technical rules (format, peaks, loudness match, voices, telegraph timing) stay in
`pipeline/audio/audio-rules.md`; this file sets how the game must sound.

##### 1. The bar
Josh's bar: the quality and feel of the soundtrack and sound design of a top-tier gothic horror action game (his
reference is Bloodborne). Gothic and orchestral: low strings and brass, choir, church bells and clockwork. Large, heavy
reverb spaces. Visceral, weighty impacts. Dread and tension that build phase by phase.

The bar is **described, never sampled**. No copyrighted game audio is stored in this repo, linked from it, played to the
critic or fed to a generator. Prompts never name a game, studio, composer or "in the style of"
(`style.json` `brand.prompt_banned`; `build_prompt` fails such a prompt, and so does the provenance rule).

##### 2. Brand (beats the bar where they differ)
Umbrella Ella is an etched gothic storybook (`pipeline/art/art-bible.md`): a small girl under an umbrella against a huge
clockwork owl, the Keeper of Time, in wind over a belfry.
- Always: clockwork and time (ticks, ratchets, gears, chimes, bells); moving air; cloth, canvas and wood for the
  umbrella; one palette (low strings, low brass, choir, bells, music box, clock). Ella's magic is small, warm and
  bright (gold-white in the art); the owl is huge, dark and metallic (rust red is danger).
- Never: electronic or synth timbres, modern drums or guitars, modern UI blips, sci-fi lasers, coin or power-up
  sounds, gore, screams or pain voices, words or lyrics, cartoon sounds, a real person's voice.
- Readability beats mood (GDD SH1.0 MOVE-04): every telegraph cuts through the loudest music; hurt, catch and heal never sound
  alike; a sound always means the same thing (audio-rules.md section 2, escalation by stems only).

##### 3. Families (production terms; numbers in style.json)
Every live sound-list row is in exactly one family (`audio_check.py --events` fails a row with none). A family has one
prompt, plus its own prompt for each member that sounds different (`prompts`); the ranges are shared.
| Family | Members (examples) | Instruments and character | Register | Space (RT60) | Transient |
|---|---|---|---|---|---|
| music_intro | MusicIntro | string drone, sul ponticello, far bell, clock pulse, hushed choir; unease | low | cathedral 3-5 s | soft |
| music_contest | MusicContest | low brass ostinato, spiccato, rising choir, timpani; the fight | low-mid | hall 2.5-4 s | punchy |
| music_desperation | MusicDesperation | string tremolo, full choir, bell clusters, ratchet and metal, brass stabs; dread | full | cathedral 3-5 s | dense |
| music_title | MusicTitle | music box over cellos, slow bell, wind; melancholy | high and low | room 2-3 s | soft |
| stinger | SurvivedSting, FailSting | bell toll, choir resolve (Survived) or low brass fall (Fail) | full | cathedral 3-6 s | bell |
| owl_telegraph | the windups | ratchet into a click, wing heave, pendulum swoop; crescendo to the danger point | 1-5 kHz | hall 0.6-1.5 s | builds |
| owl_attack | launch, travel, fade | spring release and gear clank, gear whirr, wind-down tick | low-mid | stone hall 0.6-2 s | sharp |
| owl_body | OwlWingLoop | huge slow wingbeats, brass joint creak | low | hall 1-2 s | slow |
| clockwork | ClockTickLoop, OwlGearSlip | escapement tick (locked to the music tempo), gear slip | mid-high | room 0.4-1.2 s | very sharp |
| bell | PhaseChime, EndEvent, EncounterStart, Restart | church and tower bells, hum partials | low + partials | cathedral 2-6 s | strike |
| wind | bed, safe current, gust, enter, exit | moaning wind through arches; kind lift vs hard buffet | broad, weight < 1 kHz | open + stone | slow |
| umbrella | open, close, shield, catch, heal, tear, creak | canvas and ribs, close to the ear; catch is a deep thump, heal a music-box mend | mid | small 0.1-0.8 s | tactile |
| ella | fall, bump, low health | air rush and cloth, soft knock, heartbeat with a faltering tick | broad / low | small | soft |
| wand | WandBolt and its trail | plucked celesta or music box with a spark; never tiring at 0.65 s | 2-8 kHz | small hall | sharp |
| hit | HitOwl, HitClock, HitWing, PlayerHurt, EllaDown | heavy thud, brass clank, leather slap, rib crack; never a scream | low + mid crack | stone hall 0.5-2 s | hard |
| ui | menus, pause | escapement tick, small bell, page turn, gear tooth; a storybook, never a computer | mid-high | small | sharp |
| ambience | BelfryAmbience | far bells, clockwork in the walls, wind in louvres | low and wide | cathedral 3-6 s | none |
Music stems are vertical layers that start on the bar, so all three share one tempo (66-84 BPM) and one length. Dread
builds by adding layers, register and density, never by changing the tempo.

##### 4. What is measured (`tools/audio_style_check.py`)
`python3 tools/audio_style_check.py check Audio/Source` prints one PASS or FAIL line per take and
`audio_style check: PASS files=<n> commit=<sha> dirty=no`. A take fails when any number is outside its family's range:
- `lufs`: integrated loudness (BS.1770 K-weighting, gated; under 0.4 s ungated). Too soft or too loud for its role.
- `centroid_hz`, `low_share` (< 250 Hz), `high_share` (> 4 kHz): brightness and weight (a thin hit, a harsh wind).
- `crest_db`: punch (a squashed impact or a flat tick); `attack_ms`: transient sharpness at the onset (one-shots).
- `decay_s`: reverb tail as an RT60 estimate (a dry bell, a cathedral-sized UI click; one-shots).
- `seconds`; for stems also `tempo_bpm` (shared range, stems agree within 1.5 BPM), `lra_db` (dynamic range) and
  equal length within 20 ms.
The numbers only catch what anyone can measure. They never prove a take is good: that is the critic's job. Both must
pass. Break-on-purpose tests: `tests/test_audio_style.py` (small synthetic WAVs).

##### 5. The loop (builder, critic, stuck rule)
Each audio card is split into pieces: one piece per sound id, one per music stem. Per piece:
1. A BUILDER agent makes or revises the takes: `tools/assetgen.py sfx|music --sound <Id>` (prompt from style.json;
   `--prompt` adds a revision such as the critic's gap), or processes a supplied file (section 7).
2. `python3 tools/audio_loop.py round --card <id> --piece <Id>` measures the takes and writes a blind critic packet in
   `Saved/AudioLoop/` (never committed): the takes renamed `X_NN`, up to 3 approved sounds of the game renamed `R<n>`
   (same family first, for consistency), spectrograms, the written target for the family, the brand rules and the
   numbers (`tools/audio_critic_prompt.md`). No sound id, no history, no builder notes.
3. A SEPARATE CRITIC agent, in a new session with fresh context, reads only that folder and answers pass or fail plus
   the single biggest gap. Pass needs every row A1-A8 true. `audio_loop.py verdict` records it and refuses a critic
   session that is the builder's or that judged an earlier round of the piece, and refuses takes that changed after
   the packet was made.
4. Repeat until the latest round has a critic pass AND a measured pass on the same files. No round cap.
- Stuck rule: when the last 3 rounds (`style.json` `loop.stuck_rounds`) all failed and none improved (no lower
  measured distance than every round before, and the critic named the same gap again), `verdict` prints
  `NEEDS HUMAN: Audio-owner listen to <Id> ... files ... #<issue> <UTC>` and exits 4. The audio owner listens and
  answers with `audio_loop.py resume --by <name> --note "..."`; the critic still decides.
- Enforced in code: `python3 tools/audio_loop.py close --card <id>` is the only way a card's audio is done. It fails
  unless every piece's latest round passed both, the takes on disk are the ones the critic heard, the audio files are
  committed, and the measured check passes again now. It prints `AUDIO LOOP: PASS piece=<Id> ... commit=<sha>` per
  piece, the `audio_style check: PASS ...` line and `audio_loop close: PASS card=<id> ... commit=<sha>`.
  `tools/check_pr.py` (rule `audio`) fails a PR that changes a sound without those lines for the evidence header
  commit, with a critic that is not the builder, for every changed sound id.
- The critic may be a model that cannot hear. Then it judges the spectrograms and numbers and says so (`basis`).
- Human checkpoint, kept: the audio owner's mix approval by ear in the packaged build (`pipeline/human-checkpoints.md`,
  `pipeline/roles/audio.md`, Day 4, laptop and headphones). It is the final listen, not the bar: a sound reaches it
  only after the loop closed.

##### 6. Calibration (status proposed -> measured)
The ranges were set from the written bar, not measured from any recording. When the audio owner approves the first
take of a family, the Audio role runs `audio_style_check.py measure` on it and proposes ranges around the approved
takes in a PR (a gate-file change: kickoff applies the gate patch, `tools/git_gate.py apply --auto`). When every family has one approved take, `status` becomes `measured`.

##### 7. Supplied audio (team decision, 2026-11-10: Rick supplies prepared sound effects)
Supplied files go through the same bar as generated ones. Steps (`tools/audio_import.py`):
1. The supplier drops files into `Audio/Import/` (any name).
2. `audio_import.py match` maps them to sound-list rows by name; it lists the rest with every row's event and target
   character and a best guess, and the agent matches them by what they sound like in `Audio/Import/map.csv`.
3. `audio_import.py apply --author <name> --made <date> --licence <text>` fits each file to its row and family:
   channels, rate, trim and end fade (one-shots), loop crossfade (loops), reverb when the tail is shorter than the
   family's range, loudness to the middle of the family range (never above -1 dBFS), and extra takes by small pitch and
   level changes when the row needs more takes. Each take gets a provenance row: origin `supplied`, the supplier as
   author, the source file and the steps.
4. The takes then go through sections 4 and 5 like any other. The agent fixes a failing take (apply options, edits);
   it generates only rows with no supplied file (`audio_import.py todo`); `assetgen.py` refuses a row that has one.
- Official Rules §7(h): audio made before the jam is pre-jam content. It is declared, not blocked: `apply` with a
  `--made` date before the jam start adds the take to `pipeline/submission/credits.md` "Sourced assets" and to the
  "Assets made or picked before the jam" table of `docs/pre-jam-declaration.md`, and prints a `PRE-JAM:` line.
  Sourced assets are noted on the submission and are not scored. `submission_check.py assets` still checks the dates.

##### 8. Coverage (everything that makes a sound has one)
`pipeline/audio/sound-events.json` maps every event, state, attack, feature, screen, settings row and menu action in
the GDD (§3, §4, §7, §8), `docs/feature-manifest.json`, `pipeline/unreal/gameplay-code.md`, `pipeline/ui/menus.md` and
`pipeline/ui/signals.json` to sound-list rows. `python3 tools/audio_check.py --events` fails a source item with no key,
a key with no live row, a row no key uses, and a row with no style family. `silent` needs a reason (dev-only or
visual-only items); `pending` is only for a feature that is not approved, and fails once it is. At run time the
Feedback Adapter prints `AUDIO: event key=<key> sound=<Id> t=<s>` (card 0.5a logger); `--log` fails an event that fired
with no sound, an unknown key, or a sound that is not its key's.

##### 9. Keys
One audio API key (`ELEVENLABS_API_KEY` or `STABILITY_API_KEY`) on every machine that runs kickoff
(`pipeline/human-checkpoints.md`, set once per machine): the jam perks include no audio tool. Without a key
`assetgen.py` writes a procedural placeholder and prints a `NOTE:` line; a placeholder never passes the bar.

### `pipeline/audio/style.json`

```json
{
  "version": "audio-style/1",
  "status": "proposed",
  "note": "Machine copy of pipeline/audio/style-target.md. Gate file (pipeline/agent-ops/gates.json): a human changes it by PR. tools/audio_style_check.py measures every take against its family's ranges; tools/assetgen.py builds every audio prompt from it; tools/audio_loop.py runs the builder and critic rounds. Ranges are proposals set by ear from the written bar, not measured from any reference recording. The first takes the audio owner approves recalibrate them (style-target.md section 6); then status becomes measured. A metric missing from a family is not checked for it. attack_ms and decay_s apply to one-shots only; tempo_bpm, lra_db and stem length apply to music stems only.",
  "bar": "Gothic orchestral horror at the level of a top-tier boss-fight score and sound design: low strings and brass, choir, church bells and clockwork, large stone reverb, heavy impacts, dread that builds by phase. Described here, never sampled: no reference recording is stored, linked or fed to a generator.",
  "brand": {
    "world": "Umbrella Ella: an etched gothic storybook. A small girl under an umbrella against a huge clockwork owl, the Keeper of Time, in wind over a belfry. Ink on aged paper (pipeline/art/art-bible.md).",
    "always": [
      "clockwork and time: ticks, escapements, ratchets, gears, chimes, bells",
      "wind and air: every space has moving air",
      "paper, canvas and wood: the umbrella is cloth on ribs, the world is a storybook",
      "one palette: low strings, low brass, choir, bells, music box, clock; nothing outside it",
      "Ella's magic is small, warm and bright (gold-white); the owl is huge, dark and metallic"
    ],
    "never": [
      "electronic or synth timbres, EDM, dubstep, trap or rock drums, electric guitar",
      "modern UI blips, sci-fi lasers, video-game coin or power-up sounds",
      "gore, screams, human pain voices, words or intelligible lyrics",
      "cartoon boings, comedy slide whistles",
      "a real person's voice or a named performer's style"
    ],
    "prompt_banned": [
      "bloodborne",
      "fromsoftware",
      "from software",
      "dark souls",
      "elden ring",
      "sekiro",
      "souls-like",
      "soulslike",
      "in the style of",
      "yharnam",
      "soundtrack from",
      "ost"
    ],
    "prompt_suffix": "Original sound for an etched gothic storybook game. No vocals with words, no electronic sounds, no modern UI tones."
  },
  "metrics": {
    "lufs": "integrated loudness, ITU-R BS.1770 K-weighting with gating (files under 0.4 s: ungated), LUFS",
    "centroid_hz": "mean spectral centroid of the active part, Hz (brightness)",
    "low_share": "share of spectral energy below 250 Hz, 0-1 (weight)",
    "high_share": "share of spectral energy above 4 kHz, 0-1 (air and edge)",
    "crest_db": "peak to RMS of the active part, dB (punch; low = dense or squashed)",
    "attack_ms": "10% to 90% rise of the 5 ms envelope at the first onset, ms (transient sharpness)",
    "decay_s": "reverb tail estimate: twice the time the smoothed envelope takes to fall from -5 dB to -35 dB under its peak (an RT60 estimate), s",
    "seconds": "file length, s",
    "tempo_bpm": "autocorrelation tempo of the onset envelope, 50-200 BPM search, BPM",
    "lra_db": "loudness range: 95th minus 10th percentile of 3 s short-term loudness, dB (dynamic range)"
  },
  "music": {
    "stems": [
      "MusicIntro",
      "MusicContest",
      "MusicDesperation"
    ],
    "tempo_bpm": [
      66,
      84
    ],
    "stem_tempo_tol_bpm": 1.5,
    "stem_length_tol_s": 0.02,
    "why": "The stems are vertical layers that start on the bar (audio-rules.md section 2), so all three share one tempo and one length. Dread builds by adding layers, register and density, never by changing tempo."
  },
  "families": {
    "music_intro": {
      "members": [
        "MusicIntro"
      ],
      "character": "Phase 1 layer (0-25%). Unease, not yet danger. Low string drone and sul ponticello swells, one distant church bell every few bars, the chest-clock tick as a pulse, a hushed wordless choir far back. Minor key, sparse, lots of air.",
      "instruments": "cellos and basses, violas sul ponticello, distant church bell, clock tick, wordless choir (ah/oo)",
      "register": "low and low-mid; nothing bright above the bell partials",
      "reverb": "cathedral, RT60 about 3-5 s, the choir and bell far back",
      "prompt": "slow gothic orchestral horror underscore, low string drone with sul ponticello swells, a distant church bell, steady clockwork tick pulse, hushed wordless choir far away, minor key, sparse and uneasy, large cathedral reverb, seamless loop",
      "seconds": 32,
      "ranges": {
        "lufs": [
          -28,
          -19
        ],
        "centroid_hz": [
          250,
          1800
        ],
        "low_share": [
          0.25,
          0.8
        ],
        "crest_db": [
          10,
          26
        ],
        "lra_db": [
          3,
          16
        ],
        "seconds": [
          16,
          180
        ]
      }
    },
    "music_contest": {
      "members": [
        "MusicContest"
      ],
      "character": "Phase 2 layer (25-70%), plays on top of the intro. The fight is on. Low brass ostinato, string spiccato on the pulse, choir rises to mid register, timpani and low tom on the downbeats, a bell on each phrase.",
      "instruments": "horns and trombones, string spiccato, mixed choir, timpani, low tom, church bell",
      "register": "low to mid, brass punch around 200-800 Hz",
      "reverb": "large hall, RT60 about 2.5-4 s",
      "prompt": "gothic orchestral battle layer, driving low brass ostinato, spiccato strings on the pulse, rising wordless choir, timpani hits on the downbeat, church bell on each phrase, minor key, dark and urgent, large hall reverb, seamless loop",
      "seconds": 32,
      "ranges": {
        "lufs": [
          -25,
          -16
        ],
        "centroid_hz": [
          350,
          2500
        ],
        "low_share": [
          0.2,
          0.75
        ],
        "crest_db": [
          10,
          24
        ],
        "lra_db": [
          3,
          14
        ],
        "seconds": [
          16,
          180
        ]
      }
    },
    "music_desperation": {
      "members": [
        "MusicDesperation"
      ],
      "character": "Phase 3 layer (70-100%), plays on top of both. Dread at its height. High string tremolo, full choir, bell clusters, clockwork ratchet and anvil-like metal on the off-beats, brass stabs. Same tempo; more layers, higher register.",
      "instruments": "violin tremolo, full choir, bell cluster, clock ratchet, metal hits, brass stabs, timpani rolls",
      "register": "full range; the top end opens up",
      "reverb": "cathedral, RT60 about 3-5 s",
      "prompt": "climactic gothic orchestral horror layer, high string tremolo, full wordless choir, clustered church bells, clockwork ratchet and metal hits on the off-beats, brass stabs, timpani rolls, minor key, frantic dread, cathedral reverb, seamless loop",
      "seconds": 32,
      "ranges": {
        "lufs": [
          -23,
          -14
        ],
        "centroid_hz": [
          500,
          3500
        ],
        "low_share": [
          0.12,
          0.65
        ],
        "crest_db": [
          9,
          22
        ],
        "lra_db": [
          2,
          12
        ],
        "seconds": [
          16,
          180
        ]
      }
    },
    "music_title": {
      "members": [
        "MusicTitle"
      ],
      "character": "Title screen. A storybook opening: a music-box melody over low strings, one slow bell, wind. Melancholy and mysterious, not yet threatening.",
      "instruments": "music box, cellos, celesta, slow church bell, soft wind",
      "register": "music box high, strings low; no mids crowding",
      "reverb": "large room, RT60 about 2-3 s",
      "prompt": "melancholy gothic music box lullaby over low cellos, slow church bell, soft wind, mysterious storybook mood, large room reverb, seamless loop",
      "seconds": 40,
      "ranges": {
        "lufs": [
          -28,
          -18
        ],
        "centroid_hz": [
          300,
          3000
        ],
        "crest_db": [
          10,
          26
        ],
        "lra_db": [
          2,
          16
        ],
        "seconds": [
          16,
          180
        ]
      }
    },
    "stinger": {
      "members": [
        "SurvivedSting",
        "FailSting"
      ],
      "character": "End cards. Survived: the bell tolls, the choir resolves to a major chord, wind settles. Fail: a low brass fall and one dull bell, the choir drops away, the clock stops.",
      "instruments": "church bell, choir, low brass, strings, clock stop",
      "register": "full; Survived ends bright, Fail ends low",
      "reverb": "cathedral, RT60 about 3-6 s; the tail rings out",
      "prompt": "short gothic orchestral sting, church bell toll with choir and low strings, cathedral reverb tail",
      "prompts": {
        "SurvivedSting": "triumphant but solemn gothic sting, church bell toll, wordless choir resolving to a major chord, wind settling, cathedral reverb tail",
        "FailSting": "grim gothic sting, low brass falling, one dull church bell, choir dropping away, a clock mechanism stopping, cathedral reverb tail"
      },
      "seconds": 5,
      "ranges": {
        "lufs": [
          -22,
          -13
        ],
        "centroid_hz": [
          250,
          2500
        ],
        "crest_db": [
          10,
          26
        ],
        "attack_ms": [
          0,
          60
        ],
        "decay_s": [
          1.5,
          8.0
        ],
        "seconds": [
          2,
          9
        ]
      }
    },
    "owl_telegraph": {
      "members": [
        "GustWindup",
        "TalonWarning",
        "CastWarning",
        "RearMidpointClack",
        "ClockBeat"
      ],
      "character": "The tells. Each one must cut through the full desperation mix and name its attack blind. Bolt: clockwork ratchet winding up into a metal click at the release point. Gust: a wing heave, air drawn in. Arc: a lower swinging pendulum swoop. Crescendo shape: the loudest moment is the end, where danger starts.",
      "instruments": "ratchet and escapement, wound spring, wing air, pendulum swoosh, metal click",
      "register": "upper mid, 1-5 kHz, above the music",
      "reverb": "medium hall, RT60 about 0.6-1.5 s, shorter than the music so the tell stays sharp",
      "prompt": "ominous clockwork ratchet winding up fast into a sharp metal click, crescendo, dark and mechanical, medium stone hall reverb",
      "prompts": {
        "GustWindup": "a huge owl drawing its wings back, heavy air sucked in, rising whoosh with a creak of brass joints, ominous crescendo, medium stone hall reverb"
      },
      "seconds": 0.8,
      "ranges": {
        "lufs": [
          -20,
          -11
        ],
        "centroid_hz": [
          900,
          5000
        ],
        "high_share": [
          0.03,
          0.45
        ],
        "crest_db": [
          8,
          22
        ],
        "attack_ms": [
          5,
          700
        ],
        "decay_s": [
          0.2,
          2.0
        ],
        "seconds": [
          0.4,
          1.4
        ]
      }
    },
    "owl_attack": {
      "members": [
        "OwlBoltLaunch",
        "OwlBoltTravelLoop",
        "KeeperYellowLaunch",
        "TalonSlash",
        "FrontCastLaunch",
        "MiddleCastLaunch",
        "RearCastLaunch"
      ],
      "character": "The owl's projectiles. Launch: a heavy spring release with a gear clank, lower and heavier than Ella's shot. Travel: a low spinning-gear whirr. Fade: the gear winds down and ticks out. Rust-red danger in sound: dark, metallic, mid-low.",
      "instruments": "spring release, gear clank, spinning gear whirr, wind-down tick",
      "register": "low-mid, 150-1500 Hz body",
      "reverb": "large stone hall, RT60 about 0.6-2 s",
      "prompt": "heavy clockwork spring release with a gear clank, dark metallic, weighty, large stone hall reverb",
      "prompts": {
        "OwlBoltTravelLoop": "low spinning clockwork gear whirr, dark metallic hum, seamless loop"
      },
      "seconds": 0.8,
      "ranges": {
        "lufs": [
          -26,
          -13
        ],
        "centroid_hz": [
          300,
          3500
        ],
        "low_share": [
          0.1,
          0.7
        ],
        "crest_db": [
          8,
          24
        ],
        "attack_ms": [
          0,
          25
        ],
        "decay_s": [
          0.2,
          2.5
        ],
        "seconds": [
          0.2,
          4
        ]
      }
    },
    "owl_body": {
      "members": [
        "KeeperHoot",
        "OwlWingLoop",
        "TalonRecovery"
      ],
      "character": "The owl itself: huge slow wingbeats, feathers and old leather, a creak of brass joints on each stroke. Felt more than heard.",
      "instruments": "wing whoosh, feather rustle, brass joint creak",
      "register": "low, below 500 Hz mostly",
      "reverb": "large hall, RT60 about 1-2 s",
      "prompt": "huge slow owl wingbeats, heavy feather whoosh with a creak of old brass joints, low and ominous, large hall reverb, seamless loop",
      "seconds": 6,
      "ranges": {
        "lufs": [
          -32,
          -20
        ],
        "centroid_hz": [
          120,
          1500
        ],
        "low_share": [
          0.25,
          0.9
        ],
        "crest_db": [
          6,
          22
        ],
        "seconds": [
          2,
          30
        ]
      }
    },
    "clockwork": {
      "members": [
        "LifeLost",
        "ChainTravel",
        "CastReturn",
        "ClockBeatRepeat",
        "WingsBreak",
        "MechanismBreak",
        "StunZap",
        "StunRecover",
        "ClockOpen",
        "ClockClose",
        "TimeSlowStart",
        "TimeSlowEnd",
        "EyeExpose",
        "BlackoutStart",
        "BlackoutEnd",
        "ClockTickLoop",
        "AirMillLoop",
        "ShutterWarning",
        "ShutterClose",
        "ShutterOpen"
      ],
      "character": "The Keeper of Time's mechanism. Tick: a dry, exact, heavy escapement tick at a steady rate (lock it to the music tempo). Gear slip: teeth skipping, a spring lurch, a broken tick.",
      "instruments": "escapement tick, pendulum, gear train, spring",
      "register": "mid to high transient, low body",
      "reverb": "medium room, RT60 about 0.4-1.2 s",
      "prompt": "large antique clock escapement ticking steadily, heavy brass mechanism, close and exact, medium stone room reverb, seamless loop",
      "prompts": {},
      "seconds": 4,
      "ranges": {
        "lufs": [
          -34,
          -18
        ],
        "centroid_hz": [
          700,
          6000
        ],
        "crest_db": [
          12,
          32
        ],
        "attack_ms": [
          0,
          8
        ],
        "decay_s": [
          0.1,
          1.5
        ],
        "seconds": [
          0.3,
          16
        ]
      }
    },
    "bell": {
      "members": [
        "Restart",
        "EncounterStart",
        "PhaseChime",
        "EndEvent",
        "CheckpointReached"
      ],
      "character": "Church and clock-tower bells. Phase chime: one toll with a low hum partial. End event: the clock strikes, threats stop, a long ring-out. Start: one deep toll. Restart: the bell rings backwards and a clock rewinds.",
      "instruments": "church bell, tower clock strike, hum partials",
      "register": "low fundamental with bright partials",
      "reverb": "cathedral, RT60 about 2-6 s",
      "prompt": "single deep church bell toll with long ringing partials, gothic belfry, cathedral reverb",
      "prompts": {
        "PhaseChime": "one church bell toll with a low hum partial, solemn, cathedral reverb",
        "EndEvent": "a tower clock striking with a deep bell, long ring-out, cathedral reverb",
        "EncounterStart": "single deep church bell toll that starts a fight, ominous, cathedral reverb",
        "Restart": "a church bell ringing backwards and a clock mechanism rewinding fast, cathedral reverb"
      },
      "seconds": 4,
      "ranges": {
        "lufs": [
          -24,
          -13
        ],
        "centroid_hz": [
          250,
          3000
        ],
        "crest_db": [
          10,
          26
        ],
        "attack_ms": [
          0,
          40
        ],
        "decay_s": [
          1.2,
          8.0
        ],
        "seconds": [
          1,
          9
        ]
      }
    },
    "wind": {
      "members": [
        "GustCatch",
        "WindZoneLoop",
        "WindExit",
        "GustRelease",
        "GustLoop",
        "GustEnd",
        "BellowsWarning",
        "BellowsGust",
        "BellowsRecover",
        "WindBed"
      ],
      "character": "Air over a belfry. Bed: a low moaning wind with slow swells, always there. Safe current: a rising, lifting airflow, brighter and kinder than the gust. Gust: a hard buffeting wall of wind with flapping. Enter and exit: a short whoosh in, a falling whoosh out.",
      "instruments": "wind, air through stone arches, canvas flap in gusts",
      "register": "broad noise, weight below 1 kHz, no harsh hiss",
      "reverb": "open air with stone reflections, RT60 about 0.5-2 s",
      "prompt": "cold wind moaning through gothic stone arches, slow swells, no voices, seamless loop",
      "prompts": {
        "WindZoneLoop": "a rising, lifting current of air, gentle and buoyant, brighter than a storm, seamless loop",
        "GustCatch": "short soft whoosh of air lifting an umbrella upward",
        "WindExit": "short falling whoosh as air lets go",
        "GustLoop": "hard buffeting wall of wind with canvas flapping, forceful, seamless loop",
        "GustEnd": "a strong gust dying away, flapping cloth settling"
      },
      "seconds": 10,
      "ranges": {
        "lufs": [
          -34,
          -16
        ],
        "centroid_hz": [
          150,
          2800
        ],
        "high_share": [
          0.0,
          0.3
        ],
        "crest_db": [
          5,
          20
        ],
        "attack_ms": [
          10,
          900
        ],
        "decay_s": [
          0.2,
          3.0
        ],
        "seconds": [
          0.3,
          60
        ]
      }
    },
    "umbrella": {
      "members": [
        "UmbrellaOpen",
        "UmbrellaClose",
        "UmbrellaFlap",
        "AbsorbStart",
        "AbsorbLoop",
        "AbsorbStop",
        "ShieldCatch",
        "ShieldHeal",
        "UmbrellaRepair",
        "UmbrellaCreak"
      ],
      "character": "Cloth on wooden and brass ribs, close to the listener. Open: a canvas whump and rib snap. Close: a soft fold and click. Shield: ribs lock forward. Catch: a deep canvas thump that swallows the bolt (never the hurt sound). Heal: a warm music-box mend after the catch. Tear: fabric rip. Creak: strained ribs.",
      "instruments": "canvas, waxed cloth, wooden and brass ribs, catch spring, music box for the mend",
      "register": "mid, 300-3000 Hz; catch has low weight",
      "reverb": "small, RT60 about 0.1-0.8 s; the umbrella is near, the world is far",
      "prompt": "old cloth umbrella snapping open, canvas whump and wooden rib click, close and tactile, short small-room reverb",
      "prompts": {
        "UmbrellaClose": "old cloth umbrella folding shut, soft canvas fold and a wooden catch click, close and tactile",
        "UmbrellaFlap": "cloth umbrella canopy fluttering in steady air, soft and continuous, seamless loop",
        "ShieldCatch": "a projectile swallowed by a taut canvas umbrella, deep soft thump with weight, no metal",
        "ShieldHeal": "warm music box phrase rising after a soft thump, mending, gentle and bright",
        "UmbrellaCreak": "strained wooden umbrella ribs creaking under wind, worn canvas, seamless loop",
        "UmbrellaRepair": "cloth being stitched and a rib clicking back into place, gentle"
      },
      "seconds": 0.6,
      "ranges": {
        "lufs": [
          -28,
          -14
        ],
        "centroid_hz": [
          300,
          4000
        ],
        "crest_db": [
          8,
          24
        ],
        "attack_ms": [
          0,
          40
        ],
        "decay_s": [
          0.05,
          1.2
        ],
        "seconds": [
          0.1,
          8
        ]
      }
    },
    "ella": {
      "members": [
        "EllaFallLoop",
        "FreeFallRush",
        "HopWhoosh",
        "DashWhoosh",
        "LowHealthLoop",
        "SafeLanding",
        "EllaBump"
      ],
      "character": "Ella herself: small and light against the huge owl. Fall: air rushing past a small body and a fluttering coat. Bump: a soft knock on stone. Low health: a slow heartbeat with a faltering clock tick under the music.",
      "instruments": "air rush, cloth flutter, soft knock, heartbeat, faltering tick",
      "register": "fall is broad air; bump and heartbeat low",
      "reverb": "small to medium, RT60 about 0.1-1 s",
      "prompt": "air rushing past a small falling figure, fluttering cloth, soft, seamless loop",
      "prompts": {
        "EllaBump": "a soft knock of a small body against old stone, light, no voice",
        "LowHealthLoop": "slow heartbeat with a faltering clock tick, muffled, tense, seamless loop"
      },
      "seconds": 3,
      "ranges": {
        "lufs": [
          -34,
          -16
        ],
        "centroid_hz": [
          100,
          3000
        ],
        "crest_db": [
          5,
          24
        ],
        "attack_ms": [
          0,
          300
        ],
        "decay_s": [
          0.05,
          1.5
        ],
        "seconds": [
          0.1,
          20
        ]
      }
    },
    "wand": {
      "members": [
        "WandBolt",
        "SmallBlastImpact",
        "WandBoltFade",
        "StreamStart",
        "StreamLoop",
        "StreamRelease",
        "TwinStarsFire",
        "TwinStarsImpact",
        "NeedleFire",
        "NeedlePierce"
      ],
      "character": "Ella's gold-white magic. Small, warm, bright: a plucked celesta or music-box note with a soft spark, fired every 0.65 s, so it must never tire the ear. Higher and lighter than any owl sound.",
      "instruments": "celesta or music-box pluck, soft spark, tiny chime",
      "register": "high, 2-8 kHz; little low end",
      "reverb": "small hall, RT60 about 0.2-0.8 s",
      "prompt": "small warm magical spark shot, plucked celesta note with a soft glittering tail, gentle and bright, small hall reverb",
      "prompts": {
        "WandBoltFade": "tiny magical spark fading out with a soft glitter"
      },
      "seconds": 0.4,
      "ranges": {
        "lufs": [
          -30,
          -16
        ],
        "centroid_hz": [
          1500,
          8000
        ],
        "low_share": [
          0.0,
          0.25
        ],
        "crest_db": [
          10,
          28
        ],
        "attack_ms": [
          0,
          12
        ],
        "decay_s": [
          0.05,
          1.2
        ],
        "seconds": [
          0.05,
          4
        ]
      }
    },
    "hit": {
      "members": [
        "PlayerHurt",
        "EllaDown",
        "OutOfBounds",
        "HitOwl",
        "HitWing",
        "HitClock",
        "HitProtected",
        "GlassCrack",
        "EyeHit"
      ],
      "character": "Visceral and weighty. Owl body: a heavy thud into feathers and leather over iron. Clock: a bright brass clank with a bell partial. Wing: a leathery slap and feather burst. Player hurt: a sharp crack of the canopy ribs and a breathless jolt, never a scream. Defeat: the umbrella crumples, a long fall into dark.",
      "instruments": "low thud, metal clank, leather slap, rib crack, sub drop",
      "register": "low weight (below 250 Hz) plus a mid crack",
      "reverb": "large stone hall, RT60 about 0.5-2 s",
      "prompt": "heavy visceral impact, deep thud with a metallic clank, weighty and dark, large stone hall reverb",
      "prompts": {
        "HitClock": "bright brass clank on an old clock face with a bell partial, weighty, stone hall reverb",
        "HitWing": "leathery slap into a huge wing with a burst of feathers, weighty, stone hall reverb",
        "PlayerHurt": "sharp crack of umbrella ribs and a breathless jolt, no scream, no voice, weighty",
        "EllaDown": "an umbrella crumpling and a long fall into darkness, low sub drop, no voice"
      },
      "seconds": 0.8,
      "ranges": {
        "lufs": [
          -24,
          -12
        ],
        "centroid_hz": [
          150,
          3500
        ],
        "low_share": [
          0.12,
          0.8
        ],
        "crest_db": [
          10,
          28
        ],
        "attack_ms": [
          0,
          10
        ],
        "decay_s": [
          0.2,
          3.0
        ],
        "seconds": [
          0.15,
          5
        ]
      }
    },
    "ui": {
      "members": [
        "SpellSelect",
        "SpellUnavailable",
        "UiMove",
        "UiSelect",
        "UiBack",
        "PauseIn",
        "PauseOut",
        "UiOpen",
        "UiClose",
        "UiSliderTick",
        "UiTransition",
        "UiBlocked",
        "SettingsSaved",
        "BindingCaptured",
        "BindingConflict",
        "TutorialPrompt",
        "TutorialStep",
        "TutorialDone",
        "TutorialSkip",
        "XpGain",
        "LevelUpClock",
        "WeaponUnlock",
        "UpgradePurchase",
        "UpgradeRefund",
        "RunStart",
        "RunComplete",
        "StoryTextAppear",
        "StoryPageReveal",
        "StoryAdvance",
        "SceneTransition"
      ],
      "character": "A storybook and a clock, never a computer. Move: a soft escapement tick. Select: a small bell or music-box note. Back: a lower tick-tock. Open and close: a page turn. Slider: a fine gear-tooth click per step. Transition: a page turn with a wind breath. Pause in: the clock stops and the room goes muffled; pause out: it starts again.",
      "instruments": "escapement tick, small bell, music box, paper page turn, gear tooth",
      "register": "mid-high, 800-5000 Hz, never harsh",
      "reverb": "small, RT60 about 0.05-0.6 s",
      "prompt": "soft antique clock escapement tick, single and close, warm wood and brass, tiny room",
      "prompts": {
        "UiSelect": "single small bright bell note, warm, like a music box, tiny room",
        "UiBack": "a lower soft tick-tock of an antique clock, tiny room",
        "UiOpen": "an old paper book page turning open, soft, tiny room",
        "UiClose": "an old paper book page turning closed, soft, tiny room",
        "UiSliderTick": "one fine brass gear tooth click, very short",
        "UiTransition": "a page turn with a soft breath of wind, storybook",
        "PauseIn": "an antique clock stopping, the room going muffled",
        "PauseOut": "an antique clock starting to tick again, the room opening up"
      },
      "seconds": 0.2,
      "ranges": {
        "lufs": [
          -34,
          -18
        ],
        "centroid_hz": [
          500,
          6000
        ],
        "crest_db": [
          8,
          28
        ],
        "attack_ms": [
          0,
          15
        ],
        "decay_s": [
          0.02,
          1.0
        ],
        "seconds": [
          0.03,
          2.5
        ]
      }
    },
    "ambience": {
      "members": [
        "RefugeLoop",
        "MillAmbience",
        "BossApproach",
        "RealmClocks"
      ],
      "character": "The arena's room: a high stone belfry at night. Far bells now and then, old clockwork turning in the walls, wind in the louvres. Quiet, wide, always moving.",
      "instruments": "distant bells, clockwork room tone, wind",
      "register": "low and wide; nothing that masks the tells",
      "reverb": "cathedral, RT60 about 3-6 s",
      "prompt": "ambience of a high gothic stone belfry at night, distant church bells, old clockwork turning in the walls, wind through wooden louvres, quiet and wide, no voices, seamless loop",
      "seconds": 30,
      "ranges": {
        "lufs": [
          -40,
          -24
        ],
        "centroid_hz": [
          100,
          2500
        ],
        "crest_db": [
          5,
          26
        ],
        "seconds": [
          8,
          180
        ]
      }
    },
    "enemy": {
      "members": [
        "HitEnemy",
        "WardenWarning",
        "WardenShot",
        "WardenMove",
        "WardenDisable",
        "FloodWarning",
        "FloodShot",
        "FloodStiltMove",
        "FloodDisable",
        "CourierFlightLoop",
        "CourierWarning",
        "CourierShot",
        "CourierDisable",
        "CourierWithdraw"
      ],
      "character": "The owl's projectiles. Launch: a heavy spring release with a gear clank, lower and heavier than Ella's shot. Travel: a low spinning-gear whirr. Fade: the gear winds down and ticks out. Rust-red danger in sound: dark, metallic, mid-low.",
      "instruments": "spring release, gear clank, spinning gear whirr, wind-down tick",
      "register": "low-mid, 150-1500 Hz body",
      "reverb": "large stone hall, RT60 about 0.6-2 s",
      "prompt": "heavy clockwork spring release with a gear clank, dark metallic, weighty, large stone hall reverb",
      "prompts": {},
      "seconds": 0.8,
      "ranges": {
        "lufs": [
          -26,
          -13
        ],
        "centroid_hz": [
          300,
          3500
        ],
        "low_share": [
          0.1,
          0.7
        ],
        "crest_db": [
          8,
          24
        ],
        "attack_ms": [
          0,
          25
        ],
        "decay_s": [
          0.2,
          2.5
        ],
        "seconds": [
          0.2,
          4
        ]
      }
    }
  },
  "loop": {
    "stuck_rounds": 3,
    "critic_packet_neighbours": 3,
    "why": "Each sound id (each stem) is one piece. A builder agent makes or revises it; a separate critic with fresh context hears it blind against this file and the approved sounds. The piece closes only when the latest critic verdict is pass and the measured check passes on the same files. No round cap; after stuck_rounds rounds with no improvement the piece goes to needs-human with its files."
  }
}
```

### `pipeline/audio/sound-events.json`

```json
{
 "note": "Gate file. Every thing in the game that can make a sound, mapped to its sound-list rows. tools/audio_check.py --events reads the sources below and fails when one of their events, states, attacks, features, screens, settings rows or menu actions has no key here, when a key names a sound that is not a live row, when a row is in no key, and when a row has no style family in pipeline/audio/style.json. At run time the Feedback Adapter prints `AUDIO: event key=<key> sound=<id> t=<s>` for each key it handles; `--log` fails a key that fired with sound=none, an unknown key or a sound that is not mapped to it. `silent` needs a reason and is only for things that never make a noise in the shipped game. `pending` is only for a feature that is not approved yet (EXPERIMENT, PROPOSED, DEFERRED in docs/feature-manifest.json); it fails the moment the feature is approved.",
 "sources": {
  "event": "docs/feature-manifest.json `events` and the event list in pipeline/unreal/gameplay-code.md",
  "state": "GDD SH1.0 MOVE-19: the four Shoot / Absorb modes",
  "attack": "the pipeline/level/encounter.json baseline preset attacks (GDD SH1.0 section 5)",
  "feature": "docs/feature-manifest.json `features`",
  "screen": "pipeline/ui/menus.md `Screens` line",
  "setting": "pipeline/ui/menus.md item 8 settings rows",
  "ui": "pipeline/ui/menus.md menu actions: focus, Confirm, Back, Quit",
  "signal": "pipeline/ui/signals.json: each sound_id must be a live row (ui_check.py signals checks the rest)"
 },
 "keys": {
  "attack:clock-double-beat": {
   "sounds": [
    "ClockBeat",
    "ClockBeatRepeat"
   ]
  },
  "attack:gust-band": {
   "sounds": [
    "GustWindup",
    "GustRelease",
    "GustLoop",
    "GustEnd"
   ]
  },
  "attack:mech-front-cast": {
   "sounds": [
    "CastWarning",
    "FrontCastLaunch",
    "ChainTravel",
    "CastReturn"
   ]
  },
  "attack:mech-middle-curve": {
   "sounds": [
    "CastWarning",
    "MiddleCastLaunch",
    "ChainTravel",
    "CastReturn"
   ]
  },
  "attack:mech-rear-two-stage": {
   "sounds": [
    "CastWarning",
    "RearCastLaunch",
    "RearMidpointClack",
    "ChainTravel",
    "CastReturn"
   ]
  },
  "attack:red-fan": {
   "sounds": [
    "OwlBoltLaunch",
    "OwlBoltTravelLoop"
   ]
  },
  "attack:talon-rake": {
   "sounds": [
    "TalonWarning",
    "TalonSlash",
    "TalonRecovery"
   ]
  },
  "attack:yellow-packet": {
   "sounds": [
    "KeeperYellowLaunch"
   ]
  },
  "event:AnimationCue": {
   "silent": "carries the sound of the action it cues"
  },
  "event:BackgroundLooped": {
   "silent": "a background layer wraps; no sound"
  },
  "event:BossAttackTelegraphed": {
   "sounds": [
    "GustWindup",
    "TalonWarning",
    "CastWarning",
    "ClockBeat"
   ]
  },
  "event:BossPartDestroyed": {
   "sounds": [
    "WingsBreak",
    "MechanismBreak"
   ]
  },
  "event:BossTargetHit": {
   "sounds": [
    "HitOwl",
    "HitWing",
    "HitClock",
    "GlassCrack",
    "EyeHit"
   ]
  },
  "event:CatchAttempt": {
   "silent": "an internal check; its outcome plays CatchSucceeded or nothing"
  },
  "event:CatchFailed": {
   "silent": "a missed catch is silent; the shot keeps flying (its own sounds)"
  },
  "event:CatchSucceeded": {
   "sounds": [
    "ShieldCatch"
   ]
  },
  "event:CheckpointReached": {
   "sounds": [
    "CheckpointReached"
   ]
  },
  "event:CheckpointRetried": {
   "sounds": [
    "Restart"
   ]
  },
  "event:EncounterCompleted": {
   "sounds": [
    "EndEvent",
    "SurvivedSting"
   ]
  },
  "event:LevelGained": {
   "sounds": [
    "LevelUpClock"
   ]
  },
  "event:LifeLost": {
   "sounds": [
    "LifeLost"
   ]
  },
  "event:LiftAvailabilityChanged": {
   "sounds": [
    "UmbrellaFlap"
   ]
  },
  "event:ModeSelected": {
   "sounds": [
    "UiSelect"
   ]
  },
  "event:PhaseStarted": {
   "sounds": [
    "PhaseChime"
   ]
  },
  "event:PlayerDefeated": {
   "sounds": [
    "EllaDown",
    "FailSting"
   ]
  },
  "event:PlayerHealthChanged": {
   "sounds": [
    "PlayerHurt",
    "ShieldHeal",
    "UmbrellaCreak",
    "LowHealthLoop"
   ]
  },
  "event:ProjectileContact": {
   "sounds": [
    "SmallBlastImpact",
    "HitOwl",
    "HitWing",
    "HitClock",
    "HitProtected",
    "PlayerHurt",
    "ShieldCatch",
    "WandBoltFade"
   ]
  },
  "event:ProjectileSpawned": {
   "sounds": [
    "WandBolt",
    "OwlBoltLaunch",
    "KeeperYellowLaunch",
    "OwlBoltTravelLoop"
   ]
  },
  "event:RunCompleted": {
   "sounds": [
    "RunComplete"
   ]
  },
  "event:TestPresetLoaded": {
   "silent": "workbench only"
  },
  "event:UmbrellaConfigChanged": {
   "sounds": [
    "UmbrellaOpen",
    "UmbrellaClose"
   ]
  },
  "event:WindEntered": {
   "sounds": [
    "GustCatch"
   ]
  },
  "event:WindExited": {
   "sounds": [
    "WindExit"
   ]
  },
  "event:XPAwarded": {
   "sounds": [
    "XpGain"
   ]
  },
  "extra:level-and-hazards": {
   "sounds": [
    "HitEnemy"
   ],
   "why": "Director's Cut level, enemies and hazards (GDD SH1.0 section 5)"
  },
  "extra:other": {
   "sounds": [
    "UiSelect"
   ],
   "why": "spells, story, progression, ambience and music rows not tied to one source key"
  },
  "feature:ANIM-02": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ANIM-03": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ANIM-04": {
   "sounds": [
    "UmbrellaCreak",
    "LowHealthLoop"
   ]
  },
  "feature:ANIM-05": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ANIM-06": {
   "sounds": [
    "OwlWingLoop",
    "GlassCrack"
   ]
  },
  "feature:ANIM-07": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ANIM-08": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ANIM-09": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ANIM-10": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ART-03": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ART-04": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ART-05": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ART-06": {
   "sounds": [
    "WindBed"
   ]
  },
  "feature:ART-07": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ART-08": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ART-09": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:ART-10": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:BG-02": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:BG-03": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:BG-04": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:BG-05": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:BG-06": {
   "sounds": [
    "RealmClocks"
   ]
  },
  "feature:CAM-03": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:CAM-04": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:CAM-05": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:CAM-06": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:CAM-07": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:CAM-08": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:COM-05": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:COM-06": {
   "sounds": [
    "WandBolt",
    "SmallBlastImpact",
    "WandBoltFade"
   ]
  },
  "feature:COM-07": {
   "sounds": [
    "StreamStart",
    "StreamLoop",
    "StreamRelease"
   ]
  },
  "feature:COM-08": {
   "sounds": [
    "TwinStarsFire",
    "TwinStarsImpact"
   ]
  },
  "feature:COM-09": {
   "sounds": [
    "NeedleFire",
    "NeedlePierce"
   ]
  },
  "feature:COM-10": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:COM-11": {
   "sounds": [
    "SpellUnavailable"
   ]
  },
  "feature:COM-12": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:COM-13": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:COM-14": {
   "sounds": [
    "HitEnemy",
    "WardenWarning",
    "WardenShot",
    "WardenMove",
    "WardenDisable"
   ]
  },
  "feature:COM-15": {
   "sounds": [
    "FloodWarning",
    "FloodShot",
    "FloodStiltMove",
    "FloodDisable"
   ]
  },
  "feature:COM-16": {
   "sounds": [
    "CourierFlightLoop",
    "CourierWarning",
    "CourierDisable"
   ]
  },
  "feature:COM-17": {
   "sounds": [
    "CourierShot",
    "CourierWithdraw"
   ]
  },
  "feature:COM-18": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:CORE-04": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:CORE-05": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:CORE-06": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-02": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-03": {
   "sounds": [
    "TutorialPrompt",
    "TutorialStep",
    "TutorialDone",
    "TutorialSkip"
   ]
  },
  "feature:FLOW-04": {
   "sounds": [
    "MusicTitle",
    "SurvivedSting"
   ]
  },
  "feature:FLOW-05": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-06": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-07": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-08": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-09": {
   "sounds": [
    "Restart",
    "CheckpointReached"
   ]
  },
  "feature:FLOW-10": {
   "sounds": [
    "RunStart"
   ]
  },
  "feature:FLOW-11": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-12": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-13": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-14": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-15": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-16": {
   "sounds": [
    "WeaponUnlock"
   ]
  },
  "feature:FLOW-17": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-18": {
   "sounds": [
    "UpgradeRefund"
   ]
  },
  "feature:FLOW-19": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-20": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-21": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-22": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-23": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-24": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-25": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-26": {
   "sounds": [
    "SafeLanding",
    "MillAmbience"
   ]
  },
  "feature:FLOW-27": {
   "sounds": [
    "RefugeLoop"
   ]
  },
  "feature:FLOW-28": {
   "sounds": [
    "EncounterStart",
    "BossApproach"
   ]
  },
  "feature:FLOW-29": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-30": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-31": {
   "sounds": [
    "LifeLost",
    "EllaDown",
    "FailSting"
   ]
  },
  "feature:FLOW-32": {
   "sounds": [
    "ShieldHeal",
    "UmbrellaRepair"
   ]
  },
  "feature:FLOW-33": {
   "sounds": [
    "PlayerHurt"
   ]
  },
  "feature:FLOW-34": {
   "sounds": [
    "UiTransition",
    "MusicTitle"
   ]
  },
  "feature:FLOW-35": {
   "sounds": [
    "PauseIn",
    "PauseOut"
   ]
  },
  "feature:FLOW-36": {
   "sounds": [
    "UiOpen"
   ]
  },
  "feature:FLOW-37": {
   "sounds": [
    "UiSliderTick"
   ]
  },
  "feature:FLOW-38": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-39": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-40": {
   "sounds": [
    "UiClose"
   ]
  },
  "feature:FLOW-41": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-42": {
   "sounds": [
    "UpgradePurchase"
   ]
  },
  "feature:FLOW-43": {
   "sounds": [
    "SettingsSaved"
   ]
  },
  "feature:FLOW-44": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-45": {
   "sounds": [
    "BindingConflict"
   ]
  },
  "feature:FLOW-46": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-47": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:FLOW-48": {
   "sounds": [
    "XpGain",
    "LevelUpClock"
   ]
  },
  "feature:FLOW-49": {
   "sounds": [
    "RunComplete"
   ]
  },
  "feature:HAZ-02": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-03": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-04": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-05": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-06": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-07": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-08": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-09": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-10": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-11": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-12": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-13": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-14": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-15": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-16": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-17": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-18": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-19": {
   "sounds": [
    "EllaBump",
    "AirMillLoop"
   ]
  },
  "feature:HAZ-20": {
   "sounds": [
    "ShutterWarning",
    "ShutterClose",
    "ShutterOpen"
   ]
  },
  "feature:HAZ-21": {
   "sounds": [
    "BellowsWarning",
    "BellowsGust",
    "BellowsRecover"
   ]
  },
  "feature:HAZ-22": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-23": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-24": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-25": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-26": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-27": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-28": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-29": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-30": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-31": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-32": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-33": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-34": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-35": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-36": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-37": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-38": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-39": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-40": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:HAZ-41": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:MOVE-04": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:MOVE-05": {
   "sounds": [
    "UmbrellaOpen",
    "UmbrellaClose",
    "FreeFallRush"
   ]
  },
  "feature:MOVE-06": {
   "sounds": [
    "HopWhoosh",
    "DashWhoosh"
   ]
  },
  "feature:MOVE-07": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:MOVE-08": {
   "sounds": [
    "SpellSelect"
   ]
  },
  "feature:MOVE-09": {
   "sounds": [
    "UiMove",
    "UiSelect",
    "UiBack",
    "UiBlocked"
   ]
  },
  "feature:MOVE-10": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:MOVE-11": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:MOVE-12": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:MOVE-13": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:MOVE-14": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:MOVE-15": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:MOVE-16": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:MOVE-17": {
   "sounds": [
    "BindingCaptured"
   ]
  },
  "feature:MOVE-18": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:MOVE-19": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:MOVE-20": {
   "sounds": [
    "WindExit"
   ]
  },
  "feature:MOVE-21": {
   "sounds": [
    "UmbrellaFlap",
    "EllaFallLoop"
   ]
  },
  "feature:MOVE-22": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:NAR-02": {
   "sounds": [
    "StoryTextAppear",
    "StoryPageReveal",
    "StoryAdvance"
   ]
  },
  "feature:NAR-03": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:NAR-04": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:NAR-05": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:NAR-06": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:NAR-07": {
   "sounds": [
    "SceneTransition"
   ]
  },
  "feature:NAR-08": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:OWL-06": {
   "sounds": [
    "MusicIntro",
    "MusicContest",
    "MusicDesperation"
   ]
  },
  "feature:OWL-07": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:OWL-08": {
   "sounds": [
    "KeeperHoot",
    "ClockTickLoop"
   ]
  },
  "feature:OWL-09": {
   "sounds": [
    "HitOwl",
    "HitWing",
    "WingsBreak"
   ]
  },
  "feature:OWL-10": {
   "sounds": [
    "PhaseChime"
   ]
  },
  "feature:OWL-11": {
   "sounds": [
    "OwlBoltLaunch",
    "OwlBoltTravelLoop"
   ]
  },
  "feature:OWL-12": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:OWL-13": {
   "sounds": [
    "KeeperYellowLaunch"
   ]
  },
  "feature:OWL-14": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:OWL-15": {
   "sounds": [
    "GustWindup"
   ]
  },
  "feature:OWL-16": {
   "sounds": [
    "GustRelease",
    "GustLoop"
   ]
  },
  "feature:OWL-17": {
   "sounds": [
    "GustEnd"
   ]
  },
  "feature:OWL-18": {
   "sounds": [
    "TalonWarning"
   ]
  },
  "feature:OWL-19": {
   "sounds": [
    "TalonSlash"
   ]
  },
  "feature:OWL-20": {
   "sounds": [
    "TalonRecovery"
   ]
  },
  "feature:OWL-21": {
   "sounds": [
    "CastWarning"
   ]
  },
  "feature:OWL-22": {
   "sounds": [
    "FrontCastLaunch",
    "ChainTravel"
   ]
  },
  "feature:OWL-23": {
   "sounds": [
    "CastReturn"
   ]
  },
  "feature:OWL-24": {
   "sounds": [
    "MiddleCastLaunch"
   ]
  },
  "feature:OWL-25": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:OWL-26": {
   "sounds": [
    "RearCastLaunch"
   ]
  },
  "feature:OWL-27": {
   "sounds": [
    "RearMidpointClack"
   ]
  },
  "feature:OWL-28": {
   "sounds": [
    "ClockBeat",
    "ClockBeatRepeat"
   ]
  },
  "feature:OWL-29": {
   "sounds": [
    "HitClock",
    "HitProtected",
    "ClockOpen",
    "ClockClose"
   ]
  },
  "feature:OWL-30": {
   "sounds": [
    "MechanismBreak",
    "StunZap",
    "StunRecover"
   ]
  },
  "feature:OWL-31": {
   "sounds": [
    "TimeSlowStart",
    "TimeSlowEnd"
   ]
  },
  "feature:OWL-32": {
   "sounds": [
    "EyeExpose",
    "EyeHit",
    "BlackoutStart",
    "BlackoutEnd"
   ]
  },
  "feature:OWL-33": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:OWL-34": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:OWL-35": {
   "sounds": [
    "EndEvent"
   ]
  },
  "feature:SURV-05": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:SURV-06": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:SURV-07": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:UMB-05": {
   "sounds": [
    "AbsorbStart",
    "AbsorbLoop",
    "AbsorbStop",
    "ShieldCatch"
   ]
  },
  "feature:VFX-02": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:VFX-03": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:VFX-04": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:VFX-05": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:VFX-06": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:VFX-07": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:VFX-08": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:VFX-09": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:VFX-10": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:VFX-11": {
   "silent": "a rule, data or presentation contract; the actions it governs carry their own sounds"
  },
  "feature:WIND-03": {
   "sounds": [
    "GustCatch",
    "WindZoneLoop",
    "OutOfBounds"
   ]
  },
  "screen:fail-card": {
   "sounds": [
    "FailSting"
   ]
  },
  "screen:pause": {
   "sounds": [
    "PauseIn",
    "PauseOut"
   ]
  },
  "screen:play": {
   "sounds": [
    "EncounterStart"
   ]
  },
  "screen:quit": {
   "sounds": [
    "UiBack"
   ]
  },
  "screen:restart": {
   "sounds": [
    "Restart"
   ]
  },
  "screen:settings": {
   "sounds": [
    "UiOpen",
    "UiClose",
    "SettingsSaved"
   ]
  },
  "screen:statistics": {
   "sounds": [
    "RunComplete"
   ]
  },
  "screen:title": {
   "sounds": [
    "MusicTitle",
    "UiTransition"
   ]
  },
  "screen:tutorial": {
   "sounds": [
    "TutorialPrompt",
    "TutorialStep",
    "TutorialDone",
    "TutorialSkip"
   ]
  },
  "screen:win-ending-and-credits": {
   "sounds": [
    "SurvivedSting",
    "MusicTitle",
    "StoryTextAppear"
   ]
  },
  "setting:controller": {
   "sounds": [
    "BindingCaptured",
    "BindingConflict"
   ]
  },
  "setting:credits": {
   "sounds": [
    "UiOpen"
   ]
  },
  "setting:game-options": {
   "sounds": [
    "UiOpen"
   ]
  },
  "setting:reduced-motion": {
   "sounds": [
    "UiSelect"
   ]
  },
  "setting:sound": {
   "sounds": [
    "UiSliderTick"
   ]
  },
  "setting:text-size": {
   "sounds": [
    "UiSliderTick"
   ]
  },
  "state:absorbing-fall": {
   "sounds": [
    "AbsorbStart",
    "AbsorbLoop",
    "AbsorbStop"
   ]
  },
  "state:fast-free-fall": {
   "sounds": [
    "FreeFallRush"
   ]
  },
  "state:overhead-rise": {
   "sounds": [
    "UmbrellaOpen",
    "UmbrellaFlap"
   ]
  },
  "state:shooting-fall": {
   "sounds": [
    "UmbrellaClose",
    "EllaFallLoop"
   ]
  },
  "ui:back": {
   "sounds": [
    "UiBack"
   ]
  },
  "ui:confirm": {
   "sounds": [
    "UiSelect"
   ]
  },
  "ui:focus": {
   "sounds": [
    "UiMove"
   ]
  },
  "ui:quit": {
   "sounds": [
    "UiBack"
   ]
  }
 }
}
```

## Audio rules and sound list

### `pipeline/audio/audio-rules.md`

#### Audio rules (on demand: Audio, Gameplay Dev for sound events, QA and Build, TD)

Load this for any card that adds a sound, a sound event, or audio settings. The quality bar (how every sound must
sound, the builder and critic loop, supplied files, event coverage) is `pipeline/audio/style-target.md`. Numbers live in
`pipeline/audio/audio-rules.json`; the sound list is `pipeline/audio/sound-list.csv`. Both are gate files:
agents do not edit them during the jam. Status: **proposed**. No engine was installed when they were written,
so every Unreal property and console command below is [VERIFY]. Day-0 card 0.4c (section 2) closes them all:
`grep -c VERIFY pipeline/audio/audio-rules.md` prints 0, each name confirmed on 5.8.4 with output pasted,
before the jam freezes `audio-rules.json`.

##### 1. Sound list
One row per sound the game plays. Columns: `id` (PascalCase), `family` (for loudness match), `kind`
(`oneshot` or `loop`), `class` (SFX, Telegraph, Music, UI), `channels`, `takes`, `pitch_jitter`, `gdd` (section),
`tier` (P0/P1/P2 from GDD §10, or `cut`), `event` (what triggers it), `owner`, `done_when`, `fallback`.
- `fallback`: P0 rows and every Telegraph row name their CC0 file, `pipeline/art/fallback/audio/SW_<Id>_00.wav`
  (11 files today: the 9 P0 rows plus `GustWindup` and `ArcWindup`; `--list --release` names each missing one).
  Card 0.15 makes those files, each with a provenance row. Other rows may say `none`. `TBD-0.15` passes during the jam.
  `--list --release` fails on any `TBD`, on `none` in a P0 or Telegraph row, and on a fallback file that does not exist.
- `feel.json` and `encounter.json` name sounds `SFX_<Id>`, with an `id` from this list. CI runs `audio_check.py --docs` on both.
- Cutting a sound sets its tier to `cut` on its own list-change card (kickoff merges it). A P0 row is never cut.
- A doc that names a sound uses its asset name (`SC_HitOwl`, `SW_WandBolt_00`). `audio_check.py --docs <files>`
  fails a name that is not in the list, and any sound line that still points at the old design.

##### 2. Unreal setup (day-0 card 0.4c "Audio core assets + audio_dump.py", then the audio owner keeps it)
Owner: Technical Director. Reviewer: the audio owner. After: card 0.4a. Lane: `Content/UmbrellaElla/Audio/Core/**`,
`pipeline/audio/audio-rules.md` (removing [VERIFY] tags only). Done when:
- the editor run of `tools/ue/audio_dump.py` writes `Saved/AudioDump.json`, and its `engine` field reads 5.8.x;
- `python3 tools/audio_check.py --ue-dump Saved/AudioDump.json` prints PASS (output pasted). That needs the
  dump's `unread` list empty: the tool lists every editor field it could not read, so a wrong [VERIFY] name fails;
- `grep -c VERIFY pipeline/audio/audio-rules.md` prints 0.
The tool's source is `pipeline/audio/ue/audio_dump.py`, copied byte for byte to `tools/ue/` before the jam
(`tests/test_audio_check.py` fails if they differ). If a field name is wrong on 5.8.4, fix it before the freeze.
- Sound classes in `Content/UmbrellaElla/Audio/Core/`: `SCL_SFX` (root), `SCL_Telegraph` and `SCL_UI` as children of
  `SCL_SFX`, `SCL_Music` (root). Both roots use `SM_Master` as default submix. [VERIFY `USoundClass` Parent and Default Submix]
- `SM_Master`: the only submix that sums everything, with one Submix Dynamics Processor in Limiter mode
  (a compressor does not count). [VERIFY `SubmixEffectChain`, `DynamicsProcessorType`]
- Concurrency: one asset per family, so a wand bolt can never block or steal a hurt or a windup. Every non-music
  one-shot lists exactly its own group (by id first, then by family; `audio-rules.json` "concurrency"). All use
  Stop Lowest Priority and Voice Steal Release 0.03 s. `SCON_Launch` and `SCON_Hit` also set Volume Scale 0.8, so each
  new voice turns the older ones down and a burst of 4 owl bolts does not sum to full level; the others keep 1.0.
  The dump reports `volume_scale`; `--ue-dump` fails a group whose value differs. [VERIFY the 5.8.4 `FSoundConcurrencySettings` names, incl. `volume_scale`]

  | Group | Sounds | Max | Retrigger |
  |---|---|---|---|
  | `SCON_WandBolt` | WandBolt | 3 | 0.05 s |
  | `SCON_Launch` | launch family (OwlBoltLaunch) | 4 | 0.05 s |
  | `SCON_Hit` | hit family (HitOwl, HitClock, HitWing) | 4 | 0 |
  | `SCON_Hurt` | PlayerHurt | 1 | 0 |
  | `SCON_Telegraph` | the 3 windups | 2 | 0 |
  | `SCON_State` | Umbrella*, EndEvent | 2 | 0.05 s |
  | `SCON_UI` | UiSelect | 2 | 0.05 s |
- Priority: telegraphs above every loop and music asset (fixture uses 3.0 vs 1.0).
- Variation (`WandBolt`, `HitOwl`): a Random node with 3 waves and no repeats, then a Modulator at pitch 0.95-1.05.
  Telegraphs have pitch min = max = 1.0. Loops and varied sounds are SoundCues: the dump tool does not read
  MetaSound graphs.
- Hit surfaces: `HitClock`, `HitWing` and `HitOwl` (body) are three sounds, so the player hears which part was hit (GDD §5).
- 2D only: the camera is fixed, so no sound pans or fades with distance. Every playable asset has no attenuation
  and spatialization off. The dump reports `spatialize: false` and `attenuation: null` for each one; a missing field
  fails. [VERIFY `bAllowSpatialization` and `AttenuationSettings` on `USoundBase`]
- Gust strength: `SC_GustLoop` volume follows gust strength through one cue parameter (or one MetaSound float input)
  named `GustStrength`, 0 to 1. Strong gusts wear the umbrella (GDD §4), so the player must hear the strength.
- Music layers: the 3 stems are vertical layers. Each one starts on the next bar through Quartz and keeps playing
  until `end_event`. If Quartz is cut, a stem fades in over at most 0.5 s. [VERIFY Quartz clock API in 5.8.4]
- Escalation (GDD §8 "escalating urgency"): the three stems are the only escalation. No single sound effect pitches up,
  speeds up or gets louder with the timer, so each sound always means the same thing. `--log` checks the stems start on time.
- Dump format: `tests/fixtures/audio/ue_dump_pass.json`. The dump names `tool: tools/ue/audio_dump.py`, the engine
  version (5.8.x) and the commit. No hand-written dumps. A dump with no assets fails.

##### 3. Log lines the game prints (category `LogUmbrellaElla`, Development builds)
The checker reads `AUDIO: <event> key=value ...` anywhere on a line. The feature card that adds an attack, the
gust or the music adds its lines. The lines with no feature (`master_peak`, `voices`, `slider`, `voice`) come from
Gameplay Dev day-0 card 0.5a "Audio telemetry" (after card 0.5, reviewer QA and Build). Lane: one C++ file pair under
`Source/UmbrellaElla/Private/Audio/` that prints every line below (feature cards call it, they do not format lines).
Done when: an automation test calls the logger once per event below, and `python3 tools/audio_check.py --log
<that test's log>` prints PASS (pasted); on a packaged Development run, `master_peak`, `voices` and `voice` values
come from the master submix and the audio device, not constants (log lines pasted). A full packaged `--log` PASS
comes later, from the attack, gust and music cards, which list 0.5a in "After".
| Event | Keys | Printed when |
|---|---|---|
| `telegraph` | `attack` (OwlBolt, Gust, Arc), `sound` (that attack's windup id), `sound_t`, `visual_t`, `danger_t` (s, game time) | each windup |
| `spawn` | `attack`, `t` | danger starts: first projectile spawns, or the gust zone turns on |
| `gust_param` | `value` (0-1), `t` | each time `GustStrength` is set |
| `stem` | `name`, `t_norm` (0-1), `t`, `layered=1`, `start` (`bar` or `fade`), `fade_s` (with fade) | each music stem starts |
| `stem_stop` | `name`, `t` | a stem stops |
| `end_event` | `t` | the owl's end event triggers |
| `duck` | `music_db`, `t` | music bus is ducked |
| `master_peak` | `phase` (intro, contest, desperation), `dbfs` | at the end of each phase, the phase's peak from the master submix envelope [VERIFY submix envelope follower] |
| `voices` | `t`, `t_norm`, `active`, `virtual_telegraph` | every 10 s from 90% timer, from the audio device [VERIFY] |
| `slider` / `voice` | `class`, `value` / `name`, `class`, `volume` | test sets a slider, then lists active voices |
| `event` | `key` (a `pipeline/audio/sound-events.json` key, e.g. `state:SHIELD_DESCENT`), `sound` (the id it started, or `none`), `t` | the Feedback Adapter handles an event, state change, screen or menu action |

`--log` fails when: a P0 attack (P0 and P1 with `--release`) or any attack with a `spawn` line has no `telegraph`
line; a telegraph uses another attack's sound; a gust has fewer than 2 different `gust_param` values between its
spawn and the next gust; a stem lacks `layered=1` or a valid `start`; a `stem_stop` comes before `end_event`;
`virtual_telegraph` is above 0; any phase has no `master_peak` line or a peak above -1 dBFS; an `event` line has
`sound=none` or a key or sound that `sound-events.json` does not pair (no `event` lines: a note, a failure with `--release`).
Example run that passes: `tests/fixtures/audio/run_pass.log`.

##### 4. In-context checks (QA and Build, packaged Development build, Windows)
1. Run one full encounter with `-log`. Then `python3 tools/audio_check.py --log <Saved/Logs/...log>`. Paste it.
2. At the 90% timer mark, also type `au.Debug.Sounds 1` (or `stat SoundWaves`, or open Audio Insights) and write
   two numbers in the playtest record: active voices, and virtualized voices of class `SCL_Telegraph`. [VERIFY command names]
   Fail: more than 24 active, higher 10 s later, or any virtualized telegraph voice.
3. Blind sound ID (section 6).
4. Muted play (owner QA and Build, at G3, same cold players): one run with sound off. Per player, write yes or no:
   could they name the phase, the incoming attack, and the umbrella tier from the screen alone (GDD §7: never
   timing by music alone). CSV `player,phase,attack,umbrella_tier` (format `tests/fixtures/audio/muted_pass.csv`).
   `python3 tools/audio_check.py --muted <file>` must print PASS: every cell is yes. A no is a `cue` bug for the
   Art Director or Integrator, not an audio fix.
5. Speakers (Day 4 mix approval): the audio owner plays one full encounter on laptop speakers and one on headphones,
   and writes `laptop ok / headphones ok` in the PR. Ok means every windup and `PlayerHurt` is heard over the music
   on both. Judges often listen on laptops.
Judge by numbers first, then by ear. A mix that "sounds fine" with a failing number is not done.

##### 5. Why these numbers
- -1 dBFS peak per file and on the master: room for sums and for lossy encoding of the video.
- ±3 dB per family: closer than most players notice, loose enough for hand-made takes.
- 0.2 s telegraph lead: the GDD wants readable tells; sound reaches the player faster than sight, so it starts first.
- One group per family: auto-fire (3 voices, 0.05 s retrigger) stays readable and can never take a hurt's or a
  windup's slot. Hurt is 1 voice because the player is invulnerable just after a hit.
- 24 voices: well under engine defaults, so a leak shows long before sounds drop out.
- Layers on the bar: a phase change lands in time and never swaps tracks with a jump.

##### 6. Blind sound ID (owner: QA and Build; at G3, in the packaged build)
Run it inside the G3 cold playtest, with the same players, right after their play; no separate recruiting.
The set: every P0 and P1 one-shot, plus every telegraph that is not `cut` (`audio_check.blind_id_set`), about 37 sounds.
Play each sound once, alone, in random order, with no picture. The player says what it is; the tester writes the
list id the player meant, or `?`. One row per sound per player in a CSV: `player,sound,answer` (format:
`tests/fixtures/audio/blind_id_pass.csv`). Then `python3 tools/audio_check.py --blind-id <file>`.
Pass: at least 3 cold players, each hears every sound in the set, names at least 90% correctly, names all
3 windups, and names every `must_name` sound (`PlayerHurt`, `UmbrellaTear`). Done when the output is pasted into
the playtest record. `players_floor` in the rules sets how few players turn the FAIL into a note (now 3, so no
softening; a team decision).

##### 7. Plan (one audio card per day; ids in `pipeline/audio/sound-list.csv`)
- Day 1: placeholder `OwlBoltWindup` and `WandBolt` (both P0) in the packaged build. Fallback files are fine.
  `--log` passes on the OwlBolt telegraph line. `GustWindup` is P1: it comes with the gust card.
- Day 2: P0 sounds final; `--scan --require-dir` and `--ue-dump` pass.
- Day 3: level match. `--scan` passes with no RMS outliers; music layers in; `--log` passes on a packaged run.
- Day 4 morning: fixes only, no new sounds. Mix approved by the human audio owner.

##### 8. Cut order (when the Producer calls an audio cut)
1. `ArcWindup`, together with the Arc attack. 2. Music down to `MusicContest` alone, looping from 0%.
3. `SurvivedSting`. P2 rows (`ChargeWindup`, `ChargeRelease`, `UmbrellaRepair`) are never built unless a
list-change card moves them up a tier. Each cut sets the row's tier to `cut` on a list-change card. P0 sounds are never cut.
With music cut, the `--log` stem check prints a note unless `--require-music` is set.

### `pipeline/audio/audio-rules.json`

```json
{
  "note": "Gate file for tools/audio_check.py. Agents never edit it during the jam. Unreal names and enums are [VERIFY] until the audio-core day-0 card reads them from 5.8.4.",
  "list": {
    "tiers": [
      "P0",
      "P1",
      "P2",
      "cut"
    ],
    "fallback_required_tiers": [
      "P0"
    ],
    "fallback_required_classes": [
      "Telegraph"
    ],
    "fallback_none": "none",
    "fallback_dir": "pipeline/art/fallback/"
  },
  "wav": {
    "name_regex": "^SW_([A-Z][A-Za-z0-9]*)_(\\d{2})(_PH)?\\.wav$",
    "sample_rates": [
      48000,
      44100
    ],
    "bit_depths": [
      16,
      24
    ],
    "peak_dbfs_max": -1.0,
    "gate_dbfs": -40.0,
    "lead_silence_ms_max": 10,
    "tail_ms": 5,
    "tail_dbfs_max": -60.0,
    "family_rms_db_tol": 3.0,
    "loop_wrap_jump_max": 0.05
  },
  "coverage": {
    "tiers": [
      "P0"
    ],
    "release_tiers": [
      "P0",
      "P1"
    ]
  },
  "classes": {
    "names": [
      "SCL_SFX",
      "SCL_Telegraph",
      "SCL_Music",
      "SCL_UI"
    ],
    "by_list_class": {
      "SFX": "SCL_SFX",
      "Telegraph": "SCL_Telegraph",
      "Music": "SCL_Music",
      "UI": "SCL_UI"
    },
    "sfx_slider_covers": [
      "SCL_SFX",
      "SCL_Telegraph",
      "SCL_UI"
    ],
    "master_submix": "SM_Master",
    "limiter_effect_regex": "(?i):limiter$",
    "limiters_on_master": 1
  },
  "concurrency": {
    "why": "One asset per family, so a wand bolt never blocks or steals a hurt or a windup. Groups only limit sounds that share them. Launch and hit groups duck older voices (volume_scale 0.8), so a burst of 4 does not sum to full level.",
    "assets": {
      "SCON_WandBolt": {
        "max_count": 3,
        "retrigger_time": 0.05,
        "resolution_rule": "StopLowestPriority",
        "voice_steal_release_time": 0.03
      },
      "SCON_Launch": {
        "max_count": 4,
        "retrigger_time": 0.05,
        "resolution_rule": "StopLowestPriority",
        "voice_steal_release_time": 0.03,
        "volume_scale": 0.8
      },
      "SCON_Hit": {
        "max_count": 4,
        "retrigger_time": 0.0,
        "resolution_rule": "StopLowestPriority",
        "voice_steal_release_time": 0.03,
        "volume_scale": 0.8
      },
      "SCON_Hurt": {
        "max_count": 1,
        "retrigger_time": 0.0,
        "resolution_rule": "StopLowestPriority",
        "voice_steal_release_time": 0.03
      },
      "SCON_Telegraph": {
        "max_count": 2,
        "retrigger_time": 0.0,
        "resolution_rule": "StopLowestPriority",
        "voice_steal_release_time": 0.03
      },
      "SCON_State": {
        "max_count": 2,
        "retrigger_time": 0.05,
        "resolution_rule": "StopLowestPriority",
        "voice_steal_release_time": 0.03
      },
      "SCON_UI": {
        "max_count": 2,
        "retrigger_time": 0.05,
        "resolution_rule": "StopLowestPriority",
        "voice_steal_release_time": 0.03
      }
    },
    "by_id": {
      "WandBolt": "SCON_WandBolt",
      "PlayerHurt": "SCON_Hurt",
      "ChargeRelease": "SCON_WandBolt",
      "OwlBoltFade": "SCON_Launch",
      "ArcFade": "SCON_Launch",
      "WandBoltFade": "SCON_WandBolt"
    },
    "by_family": {
      "launch": "SCON_Launch",
      "hit": "SCON_Hit",
      "telegraph": "SCON_Telegraph",
      "state": "SCON_State",
      "ui": "SCON_UI"
    }
  },
  "asset_name_regex": "^(SW|SC|MS)_([A-Z][A-Za-z0-9]*)(_\\d{2})?(_PH)?$",
  "dump": {
    "tool": "tools/ue/audio_dump.py",
    "engine_regex": "^5\\.8",
    "spatialize": false,
    "attenuation": null,
    "unread_max": 0
  },
  "variation": {
    "pitch_jitter_max": 0.05,
    "takes_min": 3
  },
  "attacks": {
    "OwlBolt": "OwlBoltWindup",
    "Gust": "GustWindup",
    "Arc": "ArcWindup"
  },
  "telegraph": {
    "lead_s_min": 0.2,
    "visual_tolerance_s": 0.017
  },
  "gust": {
    "attack": "Gust",
    "min_changes": 1
  },
  "music": {
    "stems": {
      "MusicIntro": 0.0,
      "MusicContest": 0.25,
      "MusicDesperation": 0.7
    },
    "t_norm_tol": 0.02,
    "duck_db_max": -6.0,
    "start_modes": [
      "bar",
      "fade"
    ],
    "fade_s_max": 0.5
  },
  "voices": {
    "t_norm_min": 0.9,
    "max_active": 24,
    "sample_gap_s": 10.0,
    "virtual_telegraph_max": 0
  },
  "mix": {
    "master_peak_dbfs_max": -1.0,
    "phases": [
      "intro",
      "contest",
      "desperation"
    ]
  },
  "blind_id": {
    "players_min": 3,
    "players_floor": 3,
    "per_player_min": 0.9,
    "telegraph_min": 1.0,
    "must_name": [
      "PlayerHurt",
      "UmbrellaTear"
    ],
    "tiers": [
      "P0",
      "P1"
    ]
  },
  "stale_doc_refs": [
    "enemy defeat",
    "8 key sounds",
    "docs/game-spec.md"
  ],
  "muted": {
    "fields": [
      "phase",
      "attack",
      "umbrella_tier"
    ],
    "players_min": 1
  }
}
```

### `pipeline/audio/sound-list.csv`

```csv
id,family,kind,class,channels,takes,pitch_jitter,gdd,tier,event,owner,done_when,fallback
UmbrellaOpen,state,oneshot,SFX,1,3,0.05,GDD SH1.0 MOVE-05 rise,P0,Shoot and Absorb released: the canopy opens (fabric and mechanism),Audio owner,SW_UmbrellaOpen_00..02 pass --scan,pipeline/art/fallback/audio/SW_UmbrellaOpen_00.wav
UmbrellaClose,state,oneshot,SFX,1,3,0.05,GDD SH1.0 MOVE-05 drop,P0,Shoot or Absorb held: the canopy closes,Audio owner,SW_UmbrellaClose_00..02 pass --scan,pipeline/art/fallback/audio/SW_UmbrellaClose_00.wav
UmbrellaFlap,motion,loop,SFX,1,1,0,GDD SH1.0 MOVE-21 rise,P0,rising under the open umbrella,Audio owner,SW_UmbrellaFlap_00 passes --scan,TBD
EllaFallLoop,motion,loop,SFX,1,1,0,GDD SH1.0 MOVE-21 fall,P0,ordinary fall (shooting or absorbing),Audio owner,SW_EllaFallLoop_00 passes --scan,TBD
FreeFallRush,motion,loop,SFX,1,1,0,GDD SH1.0 MOVE-05 fast free fall,P0,"both held: fast free fall, rush of air",Audio owner,SW_FreeFallRush_00 passes --scan,TBD
HopWhoosh,state,oneshot,SFX,1,3,0.05,GDD SH1.0 MOVE-06 hop,P0,overhead hop,Audio owner,SW_HopWhoosh_00..02 pass --scan,TBD
DashWhoosh,state,oneshot,SFX,1,3,0.05,GDD SH1.0 MOVE-06 falling dash,P0,falling dash forward or back,Audio owner,SW_DashWhoosh_00..02 pass --scan,TBD
GustCatch,state,oneshot,SFX,1,3,0.05,GDD SH1.0 WIND-03 safe current,P0,WindEntered: entering a harmless current (Ride held),Audio owner,SW_GustCatch_00..02 pass --scan,pipeline/art/fallback/audio/SW_GustCatch_00.wav
WindZoneLoop,ambience,loop,SFX,2,1,0,GDD SH1.0 WIND-03 ride,P0,riding a harmless current; never the hostile gust sound,Audio owner,SW_WindZoneLoop_00 passes --scan,TBD
WindExit,state,oneshot,SFX,1,3,0.05,GDD SH1.0 MOVE-20 leave current,P0,leaving a current,Audio owner,SW_WindExit_00..02 pass --scan,TBD
AbsorbStart,state,oneshot,SFX,1,3,0.05,GDD SH1.0 UMB-05,P0,Absorb held while dropping: suction starts,Audio owner,SW_AbsorbStart_00..02 pass --scan,TBD
AbsorbLoop,state,loop,SFX,1,1,0,GDD SH1.0 UMB-05,P0,suction continues,Audio owner,SW_AbsorbLoop_00 passes --scan,TBD
AbsorbStop,state,oneshot,SFX,1,3,0.05,GDD SH1.0 UMB-05,P0,Absorb released,Audio owner,SW_AbsorbStop_00..02 pass --scan,TBD
ShieldCatch,state,oneshot,SFX,1,3,0.05,GDD SH1.0 UMB-05 yellow catch,P0,"a yellow shot is caught (also at full health, FLOW-32)",Audio owner,SW_ShieldCatch_00..02 pass --scan,pipeline/art/fallback/audio/SW_ShieldCatch_00.wav
ShieldHeal,state,oneshot,SFX,1,3,0.05,GDD SH1.0 FLOW-32 repair,P0,the catch heals the umbrella (health hand moves toward III),Audio owner,SW_ShieldHeal_00..02 pass --scan,pipeline/art/fallback/audio/SW_ShieldHeal_00.wav
UmbrellaRepair,state,oneshot,SFX,1,3,0.05,GDD SH1.0 FLOW-32 reserve rebuilt,P1,healing restores a spent reserve life,Audio owner,SW_UmbrellaRepair_00..02 pass --scan,none
PlayerHurt,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 FLOW-33 hit,P0,Ella or her umbrella takes damage,Audio owner,SW_PlayerHurt_00..02 pass --scan,pipeline/art/fallback/audio/SW_PlayerHurt_00.wav
UmbrellaCreak,state,oneshot,SFX,1,3,0.05,GDD SH1.0 ANIM-04 damaged umbrella,P1,damaged-umbrella feedback (secondary cosmetic),Audio owner,SW_UmbrellaCreak_00..02 pass --scan,none
LowHealthLoop,state,loop,SFX,1,1,0,GDD SH1.0 ANIM-04 living critical state,P1,the last life is low,Audio owner,SW_LowHealthLoop_00 passes --scan,none
LifeLost,state,oneshot,SFX,1,3,0.05,GDD SH1.0 FLOW-31 reserve consumed,P0,a life is used: the life hand advances,Audio owner,SW_LifeLost_00..02 pass --scan,TBD
EllaDown,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 FLOW-31 defeat,P0,defeat: both hands at XII,Audio owner,SW_EllaDown_00..02 pass --scan,TBD
OutOfBounds,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 WIND-03 lethal bottom,P0,falling out of bounds,Audio owner,SW_OutOfBounds_00..02 pass --scan,TBD
Restart,state,oneshot,SFX,1,3,0.05,GDD SH1.0 FLOW-09 retry,P0,checkpoint or phase retry,Audio owner,SW_Restart_00..02 pass --scan,TBD
SafeLanding,state,oneshot,SFX,1,3,0.05,GDD SH1.0 FLOW-26 harmless land,P1,touching down on solid harmless land,Audio owner,SW_SafeLanding_00..02 pass --scan,none
EllaBump,state,oneshot,SFX,1,3,0.05,GDD SH1.0 HAZ-19 collision,P1,collision with a structure,Audio owner,SW_EllaBump_00..02 pass --scan,none
WandBolt,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-06 Small Blasts,P0,each Small Blasts emission,Audio owner,SW_WandBolt_00..02 pass --scan,pipeline/art/fallback/audio/SW_WandBolt_00.wav
SmallBlastImpact,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-06 impact,P0,a Small Blasts pulse hits,Audio owner,SW_SmallBlastImpact_00..02 pass --scan,TBD
WandBoltFade,trail,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-06 range expiry,P1,a player shot expires: the miss,Audio owner,SW_WandBoltFade_00..02 pass --scan,none
StreamStart,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-07 Streamed Blast,P1,beam startup,Audio owner,SW_StreamStart_00..02 pass --scan,none
StreamLoop,launch,loop,SFX,1,1,0,GDD SH1.0 COM-07,P1,sustained beam,Audio owner,SW_StreamLoop_00 passes --scan,none
StreamRelease,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-07,P1,beam release,Audio owner,SW_StreamRelease_00..02 pass --scan,none
TwinStarsFire,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-08 Twin Stars,P1,paired emission,Audio owner,SW_TwinStarsFire_00..02 pass --scan,none
TwinStarsImpact,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-08,P1,a star hits,Audio owner,SW_TwinStarsImpact_00..02 pass --scan,none
NeedleFire,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-09 Needle Spell,P1,needle emission,Audio owner,SW_NeedleFire_00..02 pass --scan,none
NeedlePierce,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-09 penetration,P1,a valid piercing hit,Audio owner,SW_NeedlePierce_00..02 pass --scan,none
SpellSelect,ui,oneshot,UI,1,1,0,GDD SH1.0 MOVE-08 spell select,P1,a spell is selected,Audio owner,SW_SpellSelect_00 passes --scan,none
SpellUnavailable,ui,oneshot,UI,1,1,0,GDD SH1.0 COM-11 locked spell,P1,a locked spell is chosen,Audio owner,SW_SpellUnavailable_00 passes --scan,none
HitOwl,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-09 hit metal,P0,a shot damages a wing or mechanism (metal),Audio owner,SW_HitOwl_00..02 pass --scan,pipeline/art/fallback/audio/SW_HitOwl_00.wav
HitWing,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-09 wing,P0,a shot hits a living wing,Audio owner,SW_HitWing_00..02 pass --scan,TBD
HitClock,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-29 clock hit,P0,a shot damages the open clock (glass),Audio owner,SW_HitClock_00..02 pass --scan,TBD
HitProtected,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-29 protected target,P0,a shot is consumed by protection,Audio owner,SW_HitProtected_00..02 pass --scan,TBD
HitEnemy,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-14 enemy equipment,P1,a shot hits an enemy's equipment,Audio owner,SW_HitEnemy_00..02 pass --scan,none
KeeperHoot,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-08 Keeper voice,P1,"arrival, reaction and distress hoots (deep, otherworldly)",Audio owner,SW_KeeperHoot_00..02 pass --scan,none
OwlWingLoop,motion,loop,SFX,1,1,0,GDD SH1.0 ANIM-06 hover,P0,quiet mechanical hovering and wing movement,Audio owner,SW_OwlWingLoop_00 passes --scan,TBD
OwlBoltLaunch,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-11 red,P0,a red fan is launched (distinct from yellow),Audio owner,SW_OwlBoltLaunch_00..02 pass --scan,pipeline/art/fallback/audio/SW_OwlBoltLaunch_00.wav
OwlBoltTravelLoop,motion,loop,SFX,1,1,0,GDD SH1.0 OWL-11 red travel,P1,red shots in flight,Audio owner,SW_OwlBoltTravelLoop_00 passes --scan,none
KeeperYellowLaunch,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-13 yellow,P0,"yellow packets are launched (catchable, different sound from red, OWL-14)",Audio owner,SW_KeeperYellowLaunch_00..02 pass --scan,TBD
GustWindup,telegraph,oneshot,Telegraph,1,1,0,GDD SH1.0 OWL-15 gust warning,P0,wing gather and load,Audio owner,SW_GustWindup_00 passes --scan; --log telegraph line with lead >= 0.2 s,pipeline/art/fallback/audio/SW_GustWindup_00.wav
GustRelease,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-16 gust release,P0,the wing flap releases the front,Audio owner,SW_GustRelease_00..02 pass --scan,TBD
GustLoop,ambience,loop,SFX,2,1,0,GDD SH1.0 OWL-16 moving gust,P0,the hostile front moves left (never the safe-current sound),Audio owner,SW_GustLoop_00 passes --scan,TBD
GustEnd,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-17 gust cleared,P1,the gust expires or is cleared,Audio owner,SW_GustEnd_00..02 pass --scan,none
TalonWarning,telegraph,oneshot,Telegraph,1,1,0,GDD SH1.0 OWL-18 talon warning,P0,the empty claw draws back,Audio owner,SW_TalonWarning_00 passes --scan; --log telegraph line with lead >= 0.2 s,TBD
TalonSlash,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-19 talon strike,P0,the committed rake,Audio owner,SW_TalonSlash_00..02 pass --scan,TBD
TalonRecovery,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-20 talon recovery,P0,harmless retraction,Audio owner,SW_TalonRecovery_00..02 pass --scan,TBD
CastWarning,telegraph,oneshot,Telegraph,1,1,0,GDD SH1.0 OWL-21 cast warning,P0,a mechanism cast locks its destination,Audio owner,SW_CastWarning_00 passes --scan; --log telegraph line with lead >= 0.2 s,TBD
FrontCastLaunch,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-22 front cast,P0,the front armillary head launches,Audio owner,SW_FrontCastLaunch_00..02 pass --scan,TBD
MiddleCastLaunch,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-24 middle cast,P0,the middle cage launches on its curve,Audio owner,SW_MiddleCastLaunch_00..02 pass --scan,TBD
RearCastLaunch,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-26 rear cast,P0,the rear gear's first and second strokes,Audio owner,SW_RearCastLaunch_00..02 pass --scan,TBD
RearMidpointClack,telegraph,oneshot,Telegraph,1,1,0,GDD SH1.0 OWL-27 midpoint clack,P0,the safe pause; must not sound finished,Audio owner,SW_RearMidpointClack_00 passes --scan; --log telegraph line with lead >= 0.2 s,TBD
ChainTravel,motion,loop,SFX,1,1,0,GDD SH1.0 OWL-22 chain,P0,the chain pays out,Audio owner,SW_ChainTravel_00 passes --scan,TBD
CastReturn,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-23 return and settle,P0,harmless return home and settling,Audio owner,SW_CastReturn_00..02 pass --scan,TBD
ClockBeat,telegraph,oneshot,Telegraph,1,1,0,GDD SH1.0 OWL-28 double beat,P0,the first volley of the double beat (hand XII to III),Audio owner,SW_ClockBeat_00 passes --scan; --log telegraph line with lead >= 0.2 s,TBD
ClockBeatRepeat,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-28 repeat,P0,the repeating beat on the same paths,Audio owner,SW_ClockBeatRepeat_00..02 pass --scan,TBD
WingsBreak,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-09 wings depleted,P0,the wings break,Audio owner,SW_WingsBreak_00..02 pass --scan,TBD
MechanismBreak,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-30 mechanism break,P0,a hanging mechanism breaks and falls,Audio owner,SW_MechanismBreak_00..02 pass --scan,TBD
StunZap,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-30 stun,P0,electrical stun,Audio owner,SW_StunZap_00..02 pass --scan,TBD
StunRecover,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-30 recovery,P0,stun ends,Audio owner,SW_StunRecover_00..02 pass --scan,TBD
ClockOpen,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-29 opening,P0,clock protection opens,Audio owner,SW_ClockOpen_00..02 pass --scan,TBD
ClockClose,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-29 closing,P0,clock protection closes,Audio owner,SW_ClockClose_00..02 pass --scan,TBD
GlassCrack,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 ANIM-06 glass stages,P0,the clock glass cracks,Audio owner,SW_GlassCrack_00..02 pass --scan,TBD
TimeSlowStart,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-31 slow,P0,time slows (x0.35),Audio owner,SW_TimeSlowStart_00..02 pass --scan,TBD
TimeSlowEnd,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-31 slow ends,P0,time returns to normal,Audio owner,SW_TimeSlowEnd_00..02 pass --scan,TBD
EyeExpose,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-32 eye,P0,the eye is exposed,Audio owner,SW_EyeExpose_00..02 pass --scan,TBD
EyeHit,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-32 eye hit,P0,a hit on the exposed eye,Audio owner,SW_EyeHit_00..02 pass --scan,TBD
BlackoutStart,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-32 blackout,P0,blackout starts,Audio owner,SW_BlackoutStart_00..02 pass --scan,TBD
BlackoutEnd,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-32 restore,P0,"blackout ends, the damaged body returns",Audio owner,SW_BlackoutEnd_00..02 pass --scan,TBD
ClockTickLoop,ambience,loop,SFX,2,1,0,GDD SH1.0 OWL-08 chest clock,P1,the Keeper's chest clock runs,Audio owner,SW_ClockTickLoop_00 passes --scan,none
EncounterStart,state,oneshot,SFX,1,3,0.05,GDD SH1.0 FLOW-28 boss arrival,P0,the Keeper arrives,Audio owner,SW_EncounterStart_00..02 pass --scan,TBD
PhaseChime,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-10 phase change,P0,a new phase and its checkpoint,Audio owner,SW_PhaseChime_00..02 pass --scan,pipeline/art/fallback/audio/SW_PhaseChime_00.wav
EndEvent,state,oneshot,SFX,1,3,0.05,GDD SH1.0 OWL-35 completion,P0,final clock completion; the Keeper leaves alive (never a death sound),Audio owner,SW_EndEvent_00..02 pass --scan,pipeline/art/fallback/audio/SW_EndEvent_00.wav
WardenWarning,telegraph,oneshot,Telegraph,1,1,0,GDD SH1.0 COM-14 Roadwarden warning,P1,Roadwarden brace / aim warning,Audio owner,SW_WardenWarning_00 passes --scan; --log telegraph line with lead >= 0.2 s,TBD
WardenShot,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-14 Roadwarden shot,P1,Roadwarden red or yellow shot,Audio owner,SW_WardenShot_00..02 pass --scan,none
WardenMove,motion,loop,SFX,1,1,0,GDD SH1.0 COM-14 Roadwarden movement,P1,Roadwarden movement and equipment,Audio owner,SW_WardenMove_00 passes --scan,none
WardenDisable,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-14 Roadwarden disable,P1,Roadwarden non-graphic defeat,Audio owner,SW_WardenDisable_00..02 pass --scan,none
FloodWarning,telegraph,oneshot,Telegraph,1,1,0,GDD SH1.0 COM-15 Floodstrider warning,P1,Floodstrider brace / aim warning,Audio owner,SW_FloodWarning_00 passes --scan; --log telegraph line with lead >= 0.2 s,TBD
FloodShot,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-15 Floodstrider shot,P1,Floodstrider red or yellow shot,Audio owner,SW_FloodShot_00..02 pass --scan,none
FloodStiltMove,motion,loop,SFX,1,1,0,GDD SH1.0 COM-15 Floodstrider movement,P1,Floodstrider movement and equipment,Audio owner,SW_FloodStiltMove_00 passes --scan,none
FloodDisable,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-15 Floodstrider disable,P1,Floodstrider non-graphic defeat,Audio owner,SW_FloodDisable_00..02 pass --scan,none
CourierFlightLoop,motion,loop,SFX,1,1,0,GDD SH1.0 COM-16 flight,P1,Sky Courier propellers,Audio owner,SW_CourierFlightLoop_00 passes --scan,none
CourierWarning,telegraph,oneshot,Telegraph,1,1,0,GDD SH1.0 COM-16 warning,P1,Courier hover / aim warning,Audio owner,SW_CourierWarning_00 passes --scan; --log telegraph line with lead >= 0.2 s,TBD
CourierShot,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-17 packet,P1,Courier red or yellow packet,Audio owner,SW_CourierShot_00..02 pass --scan,none
CourierDisable,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-16 disable,P1,Courier non-graphic defeat,Audio owner,SW_CourierDisable_00..02 pass --scan,none
CourierWithdraw,state,oneshot,SFX,1,3,0.05,GDD SH1.0 COM-17 withdrawal,P1,Courier withdraws after eight packets,Audio owner,SW_CourierWithdraw_00..02 pass --scan,none
AirMillLoop,ambience,loop,SFX,2,1,0,GDD SH1.0 HAZ-19 air mill,P1,rotating machinery and blades,Audio owner,SW_AirMillLoop_00 passes --scan,none
ShutterWarning,telegraph,oneshot,Telegraph,1,1,0,GDD SH1.0 HAZ-20 shutter warning,P1,crank / tension warning,Audio owner,SW_ShutterWarning_00 passes --scan; --log telegraph line with lead >= 0.2 s,TBD
ShutterClose,hit,oneshot,SFX,1,3,0.05,GDD SH1.0 HAZ-20 strike,P1,the shutter closes,Audio owner,SW_ShutterClose_00..02 pass --scan,none
ShutterOpen,state,oneshot,SFX,1,3,0.05,GDD SH1.0 HAZ-20 recovery,P1,the shutter reopens,Audio owner,SW_ShutterOpen_00..02 pass --scan,none
BellowsWarning,telegraph,oneshot,Telegraph,1,1,0,GDD SH1.0 HAZ-21 pressure warning,P1,nozzle pressure warning,Audio owner,SW_BellowsWarning_00 passes --scan; --log telegraph line with lead >= 0.2 s,TBD
BellowsGust,launch,oneshot,SFX,1,3,0.05,GDD SH1.0 HAZ-21 gust,P1,the hostile bellows gust,Audio owner,SW_BellowsGust_00..02 pass --scan,none
BellowsRecover,state,oneshot,SFX,1,3,0.05,GDD SH1.0 HAZ-21 recovery,P1,no-fire recovery,Audio owner,SW_BellowsRecover_00..02 pass --scan,none
CheckpointReached,state,oneshot,SFX,1,3,0.05,GDD SH1.0 FLOW-09 checkpoint,P1,a refuge checkpoint is reached,Audio owner,SW_CheckpointReached_00..02 pass --scan,none
RefugeLoop,ambience,loop,SFX,2,1,0,GDD SH1.0 FLOW-27 refuge,P1,the quiet refuge / recovery source,Audio owner,SW_RefugeLoop_00 passes --scan,none
UiMove,ui,oneshot,UI,1,1,0,GDD SH1.0 MOVE-09 navigate,P0,menu navigation,Audio owner,SW_UiMove_00 passes --scan,TBD
UiSelect,ui,oneshot,UI,1,1,0,GDD SH1.0 MOVE-09 select,P0,select / confirm,Audio owner,SW_UiSelect_00 passes --scan,TBD
UiBack,ui,oneshot,UI,1,1,0,GDD SH1.0 MOVE-09 back,P0,back,Audio owner,SW_UiBack_00 passes --scan,TBD
PauseIn,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-35 pause,P0,pause opens,Audio owner,SW_PauseIn_00 passes --scan,TBD
PauseOut,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-35 continue,P0,resume,Audio owner,SW_PauseOut_00 passes --scan,TBD
UiOpen,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-36 settings,P0,a menu screen opens,Audio owner,SW_UiOpen_00 passes --scan,TBD
UiClose,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-40 back,P0,a menu screen closes,Audio owner,SW_UiClose_00 passes --scan,TBD
UiSliderTick,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-37 sliders,P0,a slider step,Audio owner,SW_UiSliderTick_00 passes --scan,TBD
UiTransition,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-34 start,P0,Start to play,Audio owner,SW_UiTransition_00 passes --scan,TBD
UiBlocked,ui,oneshot,UI,1,1,0,GDD SH1.0 MOVE-09 blocked,P1,a blocked action,Audio owner,SW_UiBlocked_00 passes --scan,none
SettingsSaved,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-43 save,P1,settings saved,Audio owner,SW_SettingsSaved_00 passes --scan,none
BindingCaptured,ui,oneshot,UI,1,1,0,GDD SH1.0 MOVE-17 remap,P1,a binding is captured,Audio owner,SW_BindingCaptured_00 passes --scan,none
BindingConflict,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-45 duplicate binding,P1,a binding conflict warning,Audio owner,SW_BindingConflict_00 passes --scan,none
TutorialPrompt,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-03 tutorial,P1,a tutorial prompt,Audio owner,SW_TutorialPrompt_00 passes --scan,none
TutorialStep,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-03 step,P1,a tutorial step completed,Audio owner,SW_TutorialStep_00 passes --scan,none
TutorialDone,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-03 graduation,P1,tutorial graduation,Audio owner,SW_TutorialDone_00 passes --scan,none
TutorialSkip,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-03 skip,P1,tutorial skipped from Pause,Audio owner,SW_TutorialSkip_00 passes --scan,none
XpGain,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-48 XP ring,P1,XP earned,Audio owner,SW_XpGain_00 passes --scan,none
LevelUpClock,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-48 level-up clock sound,P1,level gained: the clock pulse sound,Audio owner,SW_LevelUpClock_00 passes --scan,none
WeaponUnlock,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-16 unlock,P1,a spell unlocks,Audio owner,SW_WeaponUnlock_00 passes --scan,none
UpgradePurchase,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-42 purchase,P1,an upgrade is bought,Audio owner,SW_UpgradePurchase_00 passes --scan,none
UpgradeRefund,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-18 refund,P1,an upgrade is refunded (run 2 onward),Audio owner,SW_UpgradeRefund_00 passes --scan,none
RunStart,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-10 new run,P1,a Director's Cut run starts,Audio owner,SW_RunStart_00 passes --scan,none
RunComplete,ui,oneshot,UI,1,1,0,GDD SH1.0 FLOW-49 Journey Complete,P1,a run completes,Audio owner,SW_RunComplete_00 passes --scan,none
StoryTextAppear,ui,oneshot,UI,1,1,0,GDD SH1.0 NAR-02 text narration,P2,story text appears,Audio owner,SW_StoryTextAppear_00 passes --scan,none
StoryPageReveal,ui,oneshot,UI,1,1,0,GDD SH1.0 NAR-02,P2,the rest of a page appears,Audio owner,SW_StoryPageReveal_00 passes --scan,none
StoryAdvance,ui,oneshot,UI,1,1,0,GDD SH1.0 NAR-02,P2,story advances,Audio owner,SW_StoryAdvance_00 passes --scan,none
SceneTransition,ui,oneshot,UI,1,1,0,GDD SH1.0 NAR-07,P2,scene transition (optional),Audio owner,SW_SceneTransition_00 passes --scan,none
MusicTitle,music,loop,Music,2,1,0,GDD SH1.0 FLOW-34 / FLOW-04 Start and End music,P0,Start screen and the credits roll (ART-04 same background),Audio owner,SW_MusicTitle_00 passes --scan,TBD
MusicIntro,music,loop,Music,2,1,0,GDD SH1.0 OWL-06 wings phase music,P2,"Keeper fight music, wings (scope to confirm)",Audio owner,SW_MusicIntro_00 passes --scan,none
MusicContest,music,loop,Music,2,1,0,GDD SH1.0 OWL-06 mechanisms phase music,P2,"Keeper fight music, mechanisms (scope to confirm)",Audio owner,SW_MusicContest_00 passes --scan,none
MusicDesperation,music,loop,Music,2,1,0,GDD SH1.0 OWL-06 clock phase music,P2,"Keeper fight music, clock (scope to confirm)",Audio owner,SW_MusicDesperation_00 passes --scan,none
SurvivedSting,ui,oneshot,Music,2,1,0,GDD SH1.0 FLOW-04 win ending,P1,the win ending begins (not Ella's death),Audio owner,SW_SurvivedSting_00 passes --scan,none
FailSting,ui,oneshot,Music,2,1,0,GDD SH1.0 FLOW-31 defeat,P1,defeat,Audio owner,SW_FailSting_00 passes --scan,none
WindBed,ambience,loop,SFX,2,1,0,GDD SH1.0 ART-06 cliff and open air,P1,open air and wind bed,Audio owner,SW_WindBed_00 passes --scan,none
MillAmbience,ambience,loop,SFX,2,1,0,GDD SH1.0 FLOW-26 mill and rooftops,P2,rooftops and mill machinery (to discuss),Audio owner,SW_MillAmbience_00 passes --scan,none
BossApproach,ambience,loop,SFX,2,1,0,GDD SH1.0 FLOW-28 quiet arrival,P2,boss-approach ambience (to discuss),Audio owner,SW_BossApproach_00 passes --scan,none
RealmClocks,ambience,loop,SFX,2,1,0,GDD SH1.0 BG-06 distant clocks,P2,optional distant clock sounds in the Other Realm,Audio owner,SW_RealmClocks_00 passes --scan,none
OwlBoltWindup,telegraph,oneshot,Telegraph,1,1,0,GDD 1.3 §7B OWL-01 warning (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,amber clock flash starts,Audio owner,--log telegraph line for OwlBolt with lead >= 0.2 s,pipeline/art/fallback/audio/SW_OwlBoltWindup_00.wav
OwlBoltFade,trail,oneshot,SFX,1,1,0,GDD 1.3 §7B despawn OWL-01 (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,an owl bolt despawns without a contact (lifetime or bounds),Audio owner,SC_OwlBoltFade in the dump with SCON_Launch; audio_loop close PASS for OwlBoltFade,none
ArcWindup,telegraph,oneshot,Telegraph,1,1,0,§6 returning arc (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,red arc trail starts,Audio owner,--log telegraph line for Arc with lead >= 0.2 s,pipeline/art/fallback/audio/SW_ArcWindup_00.wav
ArcLaunch,launch,oneshot,SFX,1,1,0,§6 returning arc (OWL-04) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,the returning arc spawns,Audio owner,SC_ArcLaunch in the dump with SCON_Launch; audio_loop close PASS for ArcLaunch,none
ArcTravelLoop,motion,loop,SFX,1,1,0,§6 returning arc (OWL-04) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,the returning arc is in flight,Audio owner,loop wrap passes --scan; audio_loop close PASS for ArcTravelLoop,none
ArcFade,trail,oneshot,SFX,1,1,0,§6 returning arc (OWL-04) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,the returning arc despawns without a contact,Audio owner,SC_ArcFade in the dump with SCON_Launch; audio_loop close PASS for ArcFade,none
ShieldRaise,state,oneshot,SFX,1,1,0,GDD 1.3 §3 SHIELD_DESCENT DEF-01 (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,umbrella turns to the front shield (SHIELD_DESCENT entered),Audio owner,SC_ShieldRaise in the dump with SCON_State; audio_loop close PASS for ShieldRaise,none
UmbrellaTear,state,oneshot,SFX,1,1,0,§4 (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,umbrella moves down a tier (intact damaged critical),Audio owner,named by every player in the blind ID test (--blind-id),none
ChargeWindup,launch,loop,SFX,1,1,0,§5 open note: PC shooting (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,fire held to charge a shot (only if the PC shooting scheme is picked),Audio owner,loop wrap passes --scan; looping set only on this asset,none
ChargeRelease,launch,oneshot,SFX,1,1,0,§5 open note: PC shooting (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,charged shot fires,Audio owner,SC_ChargeRelease in the dump with SCON_WandBolt,none
OwlGearSlip,state,oneshot,SFX,1,1,0,§8 owl condition (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,the owl's condition drops a step,Audio owner,SC_OwlGearSlip in the dump with SCON_State,none
WandBoltTravelLoop,motion,loop,SFX,1,1,0,GDD 1.3 §7B COM-01 (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,a wand bolt is in flight,Audio owner,loop wrap passes --scan; audio_loop close PASS for WandBoltTravelLoop,none
BelfryAmbience,ambience,loop,SFX,2,1,0,GDD 1.3 §7 arena; BG-01 backdrop (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0) (GDD 1.3 history; not in GDD SH1.0),cut,always on in the arena: far bells and clockwork room tone,Audio owner,loop wrap passes --scan; audio_loop close PASS for BelfryAmbience,none
```

## Builder and critic loop

### `tools/audio_loop.py`

Usage text from the file:

```text
Builder and critic loop for audio cards. Stdlib only. Target: pipeline/audio/style.json; prose and the full rule:
pipeline/audio/style-target.md section 5.

An audio card is split into pieces: one piece per sound id (each music stem is its own piece). For each piece:
  1. the BUILDER agent makes or revises the takes (tools/assetgen.py sfx|music --sound <Id>, prompts from style.json);
  2. `round` measures them (tools/audio_style_check.py) and writes a blind critic packet: the takes renamed X_NN, a
     few approved sounds renamed R<n>, spectrograms, the written target, the numbers. No ids, no history, no notes;
  3. a SEPARATE CRITIC agent (a new session, fresh context, never the builder's session and never a critic of an
     earlier round of this piece) reads only that packet (tools/audio_critic_prompt.md) and answers pass or fail plus
     the single biggest gap; `verdict` records it;
  4. repeat until the critic passes AND the measured check passes on the same files. There is no round cap.
Stuck rule: when the last `stuck_rounds` rounds (style.json loop, now 3) all failed and none improved (no lower
measured distance than every round before it, and the critic named the same gap again), the piece is stuck:
`verdict` prints a `NEEDS HUMAN: Audio-owner ...` line with the files and exits 4. The audio owner listens and decides.
`close` is the only way a card's audio is done: every piece's latest round passed both, the files on disk are the
ones the critic heard, the audio files are committed, and the measured check passes again now. It prints the lines
tools/check_pr.py requires on an audio PR (`AUDIO LOOP: PASS ...`, `audio_style check: PASS ...`,
`audio_loop close: PASS card=<id> ... commit=<sha>`). A piece whose every take is a tracked placeholder (the audio API
could not make it: no key, an HTTP error, no credits left; provenance origin `placeholder: <reason>`) has nothing for a
critic to judge: `close` prints `AUDIO PLACEHOLDER: piece=<Id> ...` for it instead, and the MVP 15 audio card
regenerates it (tools/audio_check.py --placeholders lists them, --release fails them).

Usage:
  audio_loop.py start   --card UE-12 --issue 12 --ids WandBolt,HitOwl --builder <session id>
  audio_loop.py round   --card UE-12 --piece WandBolt
  audio_loop.py verdict --card UE-12 --piece WandBolt --critic <session id> (--reply reply.json |
                        --verdict pass|fail --gap "one sentence")
  audio_loop.py status  --card UE-12
  audio_loop.py resume  --card UE-12 --piece WandBolt --by <audio owner> --note "what to change"   (after a stuck)
  audio_loop.py close   --card UE-12
Common: --root (repo), --audio DIR (default Audio/Source), --state DIR (default Saved/AudioLoop, never committed).
Exit 0 = ok, 1 = fail, 2 = usage or input error, 4 = stuck (needs a human).
```

Tests: `tests/test_audio_loop.py`

### `tools/audio_critic_prompt.md`

#### Audio critic prompt (blind, one piece)

Prompt version: `audio-critic/1`. Any edit to this file bumps the version. `tools/audio_loop.py round` fills the
`{...}` slots and writes the result to `brief.md` inside the critic packet. The critic is a fresh agent session that
reads only the packet folder: never the card, the PR, the builder's notes, earlier rounds or file names outside it.

---

You are the audio critic for one sound in a game. You did not make it and you do not know who did, how many tries it
took, or what changed. Judge only what is in this folder.

Files:
- `X_00.wav` (and `X_01.wav`, `X_02.wav` when the sound has takes): the sound under review. `X_00.png` etc.: its
  spectrogram (time left to right, low pitch at the bottom, dark = loud).
- `R1.wav`, `R2.wav`, ... with their `.png`: sounds already approved for this game. They are not targets for this
  sound; they show the world it has to sit in. Some may be from other families.

If you can listen to audio, listen to every file. If you cannot, judge from the spectrograms and the numbers, and
say so in `basis`.

The target for this sound, written by the team (from `pipeline/audio/style.json`):

{family_target}

Brand rules for every sound in this game:

{brand}

Measured numbers for X (from `tools/audio_style_check.py`; a range failure there is final and you cannot override it):

{numbers}

Answer each question true or false, with a short reason:

| id | question (true = meets the target) |
|---|---|
| A1 | The instruments and materials are the ones the target names, and nothing from the brand's never list |
| A2 | Register and brightness match the target (low where it says low, no harsh top where it says none) |
| A3 | The space matches: the reverb size and tail length the target asks for |
| A4 | The transient and weight match: sharp where it says sharp, heavy where it says heavy |
| A5 | It reads instantly as the event it is for, and could not be mistaken for another sound in this game |
| A6 | It sits in the same world as R1.. (same palette, same kind of space, same level of finish) |
| A7 | It is finished: no artifacts, clicks, warble, smeared transients, garbled voices or obvious generator noise |
| A8 | It reaches the bar: it would not sound out of place in a top-tier gothic orchestral horror boss fight |

Then one verdict: `pass` only if every row is true. Otherwise `fail`, and name the single biggest gap: the one change
that would most move this sound toward the target, in one sentence a sound designer can act on.

Reply with only this JSON object:
```
{"rows": {"A1": [true, "why"], ..., "A8": [true, "why"]},
 "verdict": "pass" | "fail",
 "biggest_gap": "one sentence, or none on a pass",
 "basis": "listened" | "spectrogram and numbers"}
```

## Commands and checks

### `tools/audio_check.py`

Usage text from the file:

```text
Audio gate for THE LAST HOUR. Stdlib only. Rules: pipeline/audio/audio-rules.json.
Sound list: pipeline/audio/sound-list.csv. Detail: pipeline/audio/audio-rules.md.

Modes:
  --list                 sound-list.csv is well formed (columns, classes, kinds, tiers, takes, jitter);
                         P0 and Telegraph rows never have fallback `none`; with --release every
                         fallback is a file under pipeline/art/fallback/ that exists, or `none`
  --scan DIR             every WAV under DIR (Audio/Source) is named SW_<Id>_<NN>.wav, its <Id> is in
                         the sound list, and it passes: PCM 16/24 bit, 44.1/48 kHz, channels as listed,
                         peak <= -1 dBFS, leading silence <= 10 ms and last 5 ms <= -60 dBFS (one-shots),
                         no click at the loop
                         point (loops), active RMS within 3 dB of its family median, take count per id,
                         and a provenance row (author, origin, licence) in pipeline/art/provenance.csv; a row whose
                         tool is an allowed audio source (asset-tools.json: ElevenLabs, Stable Audio, synthesis,
                         ffmpeg, SoX, Audacity, Fab) has that source's licence, and a generated take names one.
                         Every P0 row (P0 and P1 with --release) needs all its take files: an empty
                         folder fails
  --ue-dump JSON         an editor dump of sound assets (format: tests/fixtures/audio/ue_dump_pass.json):
                         every asset has one of the 4 sound classes, every non-music one-shot uses its
                         own family's concurrency asset with its exact settings (incl. volume_scale), telegraphs outrank ambience
                         and have no pitch jitter, variation ids pick from >= 3 takes with no repeats,
                         the SFX/Telegraph/UI classes sit under SCL_SFX, all classes route to SM_Master,
                         and SM_Master has one limiter. The dump names tools/ue/audio_dump.py, the
                         engine version and the commit; every playable asset is 2D (spatialize false,
                         attenuation null); the dump's `unread` list (editor fields it could not read) is empty
  --log FILE             an automation or packaged-build log with `AUDIO:` lines: a telegraph line with the
                         list's own windup sound for every P0 attack (P0+P1 with --release) and every
                         attack with a spawn line, lead times, gust_param changes in every gust, music
                         stems as layers on their phase thresholds that never stop before end_event,
                         music duck after the end event, master peak in every phase (intro, contest, desperation), voice count
                         at 90% (no virtualized telegraph voices), SFX slider at 0
  --blind-id CSV         blind sound ID record (player,sound,answer): >= 3 players, each names >= 90% of
                         the P0+P1 one-shots, 100% of the telegraphs and every must_name sound
  --muted CSV            muted playtest record (player,phase,attack,umbrella_tier, each yes or no): every
                         state a sound signals is also read on screen with sound off
  --events               coverage: every event, state, attack, feature, screen, settings row and menu action in
                         the GDD (docs/gdd/CURRENT), docs/feature-manifest.json, pipeline/unreal/gameplay-code.md,
                         pipeline/ui/menus.md and pipeline/ui/signals.json has a key in pipeline/audio/sound-events.json
                         naming live sound-list rows (or `silent` with a reason, or `pending` on a feature that is
                         not approved yet); every live row is used by a key and has exactly one style family in
                         pipeline/audio/style.json. With --log, each `AUDIO: event key=<key> sound=<id>` line must
                         play one of its key's sounds (sound=none or an unknown key fails)
  --docs FILE...         sound names in docs and data JSON (SW_/SC_/MS_/SFX_<Id>) exist in the sound list, and no line
                         about sound points at the old design (enemy defeat, MVP 10, docs/game-spec.md)
  --placeholders         list the tracked placeholder takes: procedural takes tools/assetgen.py made when the audio
                         API could not (provenance origin `placeholder: <reason>`); with --scan --release each one fails
Flags: --release (TBD fallbacks, missing music and tracked placeholder takes are errors), --require-music,
       --fail-lfs-pointer, --require-dir, --rules, --list-file, --provenance.
Exit 0 = pass, 1 = fail, 2 = usage or input error.
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: Audio sound list and sound names in docs and data (Audio)
- `.github/workflows/pipeline-checks.yml`: Audio source WAVs (skips LFS pointers and a missing Audio/Source; add --require-dir once card 0.15 or the first audio card merges)

Tests: `tests/fixtures/kickoff/stub_agent.py`, `tests/test_assetgen.py`, `tests/test_audio_check.py`, `tests/test_audio_events.py`, `tests/test_audio_import.py`, `tests/test_audio_style.py`, `tests/test_honest_jam.py`, `tests/test_pipeline_check.py`

### `tools/audio_style_check.py`

Usage text from the file:

```text
Audio quality bar, measured. Stdlib only. Target: pipeline/audio/style.json (prose: pipeline/audio/style-target.md).

Every take SW_<Id>_<NN>.wav belongs to the style family that lists <Id> in style.json. Each family sets ranges for the
numbers below; a take outside any range of its family fails. These numbers catch a take that is off the bar in a way
anyone can measure (too dry, too bright, too soft, no punch, wrong tempo). They never prove a take is good: that is the
critic's verdict (tools/audio_loop.py). Both must pass.

Measured (style.json "metrics" has the exact definitions):
  lufs         integrated loudness, BS.1770 K-weighting, 400 ms gated blocks (ungated under 0.4 s)
  centroid_hz  spectral centroid (brightness);  low_share / high_share: energy below 250 Hz / above 4 kHz
  crest_db     peak to RMS (punch);  attack_ms: 10-90% rise at the onset (transient sharpness; one-shots)
  decay_s      reverb tail: 2 x the -5 to -35 dB fall of the envelope after its peak (an RT60 estimate; one-shots)
  seconds      length;  tempo_bpm and lra_db (loudness range) for music stems
Music stems (style.json "music"): every stem's tempo is inside the shared range, the stems agree within
stem_tempo_tol_bpm and their lengths within stem_length_tol_s, because they are layers that start on the bar.

Usage:
  audio_style_check.py check DIR [--ids A,B] [--fail-lfs-pointer]   every take under DIR (Audio/Source); prints one
                       PASS/FAIL line per take and `audio_style check: PASS files=<n> commit=<sha> dirty=<yes|no>`
  audio_style_check.py measure WAV [--json]                          the numbers for one file
  audio_style_check.py prompt ID [--extra "..."]                     the generation prompt for sound ID (assetgen uses it)
Exit 0 = pass, 1 = fail, 2 = usage or input error.
```

Run in CI by:

- `.github/workflows/pipeline-checks.yml`: Audio quality bar, measured (pipeline/audio/style-target.md; skips LFS pointers and a missing Audio/Source)

Tests: `tests/test_audio_import.py`, `tests/test_audio_style.py`, `tests/test_pipeline_check.py`

### `tools/audio_import.py`

Usage text from the file:

```text
Supplied audio: a teammate's prepared sound files go into the game through the same bar as generated ones.
Stdlib only (ffmpeg only to read a file that is not WAV). Rule: pipeline/audio/style-target.md section 7.

  1. The supplier drops files into Audio/Import/ (any name; WAV, or MP3/OGG/FLAC/AIFF with ffmpeg installed).
  2. `match` maps each file to a sound-list row by name (WandBolt.wav, SW_WandBolt_00.wav, wand_bolt_2.wav). Files it
     cannot place are listed with every row's event and style character, and a best guess; the agent decides and
     writes `<file>,<Id>` lines to Audio/Import/map.csv (`#` lines are comments).
  3. `apply` processes each mapped file into Audio/Source/<Id>/SW_<Id>_<NN>.wav: the row's channels, 44.1/48 kHz,
     16-bit; one-shots trimmed to start at once and end in silence, loops cross-faded at the wrap; reverb added when
     the tail is shorter than the family's decay_s range; loudness set to the middle of the family's LUFS range
     (never above -1 dBFS peak); extra takes made by small pitch and level changes when the row needs more takes
     than were supplied. Each output gets a provenance row: origin `supplied`, the supplier as author, the source
     file, the steps. A file made before the jam start is declared, not blocked: a row in
     pipeline/submission/credits.md "Sourced assets" and in docs/pre-jam-declaration.md (Official Rules 7(h)).
  4. The takes then go through the same loop as every sound: tools/audio_style_check.py and tools/audio_loop.py
     (critic vs the style target). The agent fixes a failing take by re-running apply with other options
     (--reverb, --lufs) or edits; it generates (tools/assetgen.py) only for a row with no supplied file
     (`todo` lists them; assetgen refuses a row that has a supplied take).

Usage:
  audio_import.py match [--in Audio/Import]
  audio_import.py apply --author NAME --made YYYY-MM-DD --licence TEXT [--in Audio/Import] [--ids A,B]
                        [--reverb auto|off|<seconds>] [--lufs auto|<value>]
  audio_import.py todo                                  rows with no take and no supplied file (to generate)
Exit 0 = ok, 1 = a file failed or is unmatched, 2 = usage or input error.
```

Tests: `tests/test_assetgen.py`, `tests/test_audio_import.py`

### `tools/ue/audio_dump.py`

Usage text from the file:

```text
Editor dump of the audio setup for `tools/audio_check.py --ue-dump`.

Source: pipeline/audio/ue/audio_dump.py (audio lane). Copied byte for byte to tools/ue/audio_dump.py before the jam,
because tools/ is frozen during it. tests/test_audio_check.py fails if the two differ.
Run in the editor on the project, then check the result:
  UnrealEditor-Cmd <Project>.uproject -run=pythonscript -script=tools/ue/audio_dump.py   [VERIFY 5.8.4 spelling]
  python3 tools/audio_check.py --ue-dump Saved/AudioDump.json
Format: tests/fixtures/audio/ue_dump_pass.json. Every editor property name below is [VERIFY] on 5.8.4.
A property that cannot be read is never guessed: its name goes in the dump's `unread` list, and
audio_check fails while that list is not empty. So the first editor run shows which names are wrong.
```

Tests: `tests/test_audio_check.py`

### `pipeline/audio/ue/audio_dump.py`

Usage text from the file:

```text
Editor dump of the audio setup for `tools/audio_check.py --ue-dump`.

Source: pipeline/audio/ue/audio_dump.py (audio lane). Copied byte for byte to tools/ue/audio_dump.py before the jam,
because tools/ is frozen during it. tests/test_audio_check.py fails if the two differ.
Run in the editor on the project, then check the result:
  UnrealEditor-Cmd <Project>.uproject -run=pythonscript -script=tools/ue/audio_dump.py   [VERIFY 5.8.4 spelling]
  python3 tools/audio_check.py --ue-dump Saved/AudioDump.json
Format: tests/fixtures/audio/ue_dump_pass.json. Every editor property name below is [VERIFY] on 5.8.4.
A property that cannot be read is never guessed: its name goes in the dump's `unread` list, and
audio_check fails while that list is not empty. So the first editor run shows which names are wrong.
```

Tests: `tests/test_audio_check.py`
