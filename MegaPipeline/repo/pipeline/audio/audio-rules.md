# Audio rules (on demand: Audio, Gameplay Dev for sound events, QA and Build, TD)

Load this for any card that adds a sound, a sound event, or audio settings. The quality bar (how every sound must
sound, the builder and critic loop, supplied files, event coverage) is `pipeline/audio/style-target.md`. Numbers live in
`pipeline/audio/audio-rules.json`; the sound list is `pipeline/audio/sound-list.csv`. Both are gate files:
agents do not edit them during the jam. Status: **proposed**. No engine was installed when they were written,
so every Unreal property and console command below is [VERIFY]. Day-0 card 0.4c (section 2) closes them all:
`grep -c VERIFY pipeline/audio/audio-rules.md` prints 0, each name confirmed on 5.8.4 with output pasted,
before the jam freezes `audio-rules.json`.

## 1. Sound list
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

## 2. Unreal setup (day-0 card 0.4c "Audio core assets + audio_dump.py", then the audio owner keeps it)
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

## 3. Log lines the game prints (category `LogUmbrellaElla`, Development builds)
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

## 4. In-context checks (QA and Build, packaged Development build, Windows)
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

## 5. Why these numbers
- -1 dBFS peak per file and on the master: room for sums and for lossy encoding of the video.
- ±3 dB per family: closer than most players notice, loose enough for hand-made takes.
- 0.2 s telegraph lead: the GDD wants readable tells; sound reaches the player faster than sight, so it starts first.
- One group per family: auto-fire (3 voices, 0.05 s retrigger) stays readable and can never take a hurt's or a
  windup's slot. Hurt is 1 voice because the player is invulnerable just after a hit.
- 24 voices: well under engine defaults, so a leak shows long before sounds drop out.
- Layers on the bar: a phase change lands in time and never swaps tracks with a jump.

## 6. Blind sound ID (owner: QA and Build; at G3, in the packaged build)
Run it inside the G3 cold playtest, with the same players, right after their play; no separate recruiting.
The set: every P0 and P1 one-shot, plus every telegraph that is not `cut` (`audio_check.blind_id_set`), about 37 sounds.
Play each sound once, alone, in random order, with no picture. The player says what it is; the tester writes the
list id the player meant, or `?`. One row per sound per player in a CSV: `player,sound,answer` (format:
`tests/fixtures/audio/blind_id_pass.csv`). Then `python3 tools/audio_check.py --blind-id <file>`.
Pass: at least 3 cold players, each hears every sound in the set, names at least 90% correctly, names all
3 windups, and names every `must_name` sound (`PlayerHurt`, `UmbrellaTear`). Done when the output is pasted into
the playtest record. `players_floor` in the rules sets how few players turn the FAIL into a note (now 3, so no
softening; a team decision).

## 7. Plan (one audio card per day; ids in `pipeline/audio/sound-list.csv`)
- Day 1: placeholder `OwlBoltWindup` and `WandBolt` (both P0) in the packaged build. Fallback files are fine.
  `--log` passes on the OwlBolt telegraph line. `GustWindup` is P1: it comes with the gust card.
- Day 2: P0 sounds final; `--scan --require-dir` and `--ue-dump` pass.
- Day 3: level match. `--scan` passes with no RMS outliers; music layers in; `--log` passes on a packaged run.
- Day 4 morning: fixes only, no new sounds. Mix approved by the human audio owner.

## 8. Cut order (when the Producer calls an audio cut)
1. `ArcWindup`, together with the Arc attack. 2. Music down to `MusicContest` alone, looping from 0%.
3. `SurvivedSting`. P2 rows (`ChargeWindup`, `ChargeRelease`, `UmbrellaRepair`) are never built unless a
list-change card moves them up a tier. Each cut sets the row's tier to `cut` on a list-change card. P0 sounds are never cut.
With music cut, the `--log` stem check prints a note unless `--require-music` is set.
