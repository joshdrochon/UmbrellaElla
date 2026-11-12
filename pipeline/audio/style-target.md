# Audio style target (on demand: Audio, QA and Build, reviewers of audio PRs)

The quality bar for every sound and every music stem. Machine copy: `pipeline/audio/style.json` (gate file; a human
changes it by PR). `tools/audio_style_check.py` measures takes against it, `tools/assetgen.py` builds every audio
prompt from it, and `tools/audio_loop.py` runs the builder and critic rounds against it. Status: **proposed**
(section 6). The technical rules (format, peaks, loudness match, voices, telegraph timing) stay in
`pipeline/audio/audio-rules.md`; this file sets how the game must sound.

## 1. The bar
Josh's bar: the quality and feel of the soundtrack and sound design of a top-tier gothic horror action game (his
reference is Bloodborne). Gothic and orchestral: low strings and brass, choir, church bells and clockwork. Large, heavy
reverb spaces. Visceral, weighty impacts. Dread and tension that build phase by phase.

The bar is **described, never sampled**. No copyrighted game audio is stored in this repo, linked from it, played to the
critic or fed to a generator. Prompts never name a game, studio, composer or "in the style of"
(`style.json` `brand.prompt_banned`; `build_prompt` fails such a prompt, and so does the provenance rule).

## 2. Brand (beats the bar where they differ)
Umbrella Ella is an etched gothic storybook (`pipeline/art/art-bible.md`): a small girl under an umbrella against a huge
clockwork owl, the Keeper of Time, in wind over a belfry.
- Always: clockwork and time (ticks, ratchets, gears, chimes, bells); moving air; cloth, canvas and wood for the
  umbrella; one palette (low strings, low brass, choir, bells, music box, clock). Ella's magic is small, warm and
  bright (gold-white in the art); the owl is huge, dark and metallic (rust red is danger).
- Never: electronic or synth timbres, modern drums or guitars, modern UI blips, sci-fi lasers, coin or power-up
  sounds, gore, screams or pain voices, words or lyrics, cartoon sounds, a real person's voice.
- Readability beats mood (GDD SH1.0 MOVE-04): every telegraph cuts through the loudest music; hurt, catch and heal never sound
  alike; a sound always means the same thing (audio-rules.md section 2, escalation by stems only).

## 3. Families (production terms; numbers in style.json)
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

## 4. What is measured (`tools/audio_style_check.py`)
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

## 5. The loop (builder, critic, stuck rule)
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

## 6. Calibration (status proposed -> measured)
The ranges were set from the written bar, not measured from any recording. When the audio owner approves the first
take of a family, the Audio role runs `audio_style_check.py measure` on it and proposes ranges around the approved
takes in a PR (a gate-file change: kickoff applies the gate patch, `tools/git_gate.py apply --auto`). When every family has one approved take, `status` becomes `measured`.

## 7. Supplied audio (team decision, 2026-11-10: Rick supplies prepared sound effects)
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

## 8. Coverage (everything that makes a sound has one)
`pipeline/audio/sound-events.json` maps every event, state, attack, feature, screen, settings row and menu action in
the GDD (§3, §4, §7, §8), `docs/feature-manifest.json`, `pipeline/unreal/gameplay-code.md`, `pipeline/ui/menus.md` and
`pipeline/ui/signals.json` to sound-list rows. `python3 tools/audio_check.py --events` fails a source item with no key,
a key with no live row, a row no key uses, and a row with no style family. `silent` needs a reason (dev-only or
visual-only items); `pending` is only for a feature that is not approved, and fails once it is. At run time the
Feedback Adapter prints `AUDIO: event key=<key> sound=<Id> t=<s>` (card 0.5a logger); `--log` fails an event that fired
with no sound, an unknown key, or a sound that is not its key's.

## 9. Keys
One audio API key (`ELEVENLABS_API_KEY` or `STABILITY_API_KEY`) on every machine that runs kickoff
(`pipeline/human-checkpoints.md`, set once per machine): the jam perks include no audio tool. Without a key
`assetgen.py` writes a procedural placeholder and prints a `NOTE:` line; a placeholder never passes the bar.
