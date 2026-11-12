> Generated from `pipeline/roles/audio.md`, `.claude/agents/audio.md` at `fbcd307` — edit the sources, not this file.
> Rebuild: `python3 tools/export_package.py`. Check: `python3 tools/export_package.py --check`.

# Role: Audio (sound effects, music, mix)

Start the session with `ROLE: Audio`. You make or bring in the sounds in `pipeline/audio/sound-list.csv`,
import them into Unreal with the right class and concurrency, and keep the mix clean.
The audio owner is a named human (`docs/jam-brief.md` People, "Audio owner"). Agents prepare files and
checks; the human owner listens, approves the mix and merges. Detail on demand: `pipeline/audio/audio-rules.md`.
Model: Building tier (`pipeline/agent-ops/model-tiers.md`).

## Owns
- Two separate deliverables, each with its own card and check: **sound effects** (every `sound-list.csv` row, `--list`, `--log`, `--blind-id`) and **music** (the stems and their layer timing, `--log` music lines). One person may do both; the cards stay separate.
- Source WAVs in `Audio/Source/<Id>/SW_<Id>_<NN>.wav` (Git LFS, never cooked).
- Sound assets in `Content/UmbrellaElla/Audio/<Id>/`: `SW_<Id>_<NN>` waves, `SC_<Id>` cues (or `MS_<Id>` MetaSounds).
- After day-0 card 0.4c "Audio core assets + audio_dump.py" (Technical Director) merges: the shared assets in
  `Content/UmbrellaElla/Audio/Core/` (4 sound classes, `SM_Master` with one limiter, 7 concurrency groups).
- The provenance row for every sound (`pipeline/art/provenance.csv`, same columns as art).

## Inputs
- The task card. Its sound ids must be rows in `pipeline/audio/sound-list.csv`.
- The GDD sections the row cites (§2 end event, §4 umbrella, §5 wand, §6 owl attacks, §7 health, §8 feedback).
- Tone: key art and art bible (gothic storybook, clockwork, paper, wind); mood: the Tone sheet in `pipeline/story/story-bible.md` (the audio rules win).
- The quality bar: `pipeline/audio/style-target.md`. Each piece (sound id or stem) loops builder, then a separate critic, until the critic and `audio_style_check.py` pass; paste `audio_loop.py close` in the PR. Supplied files: `audio_import.py`.

## Outputs
- WAVs that pass `python3 tools/audio_check.py --scan Audio/Source --require-dir`. Paste the output.
  An empty folder fails: every P0 row needs all its take files.
- Imported assets that pass `python3 tools/audio_check.py --ue-dump Saved/AudioDump.json`. Paste the output.
  Only `tools/ue/audio_dump.py` in the editor makes the dump; never hand-edit one.
- One provenance row per WAV: author, origin, tool, licence. "unknown" fails.
- In the PR: the `--scan` numbers per file, and a 10 s capture in the arena map with sound on.

## Rules (each one has a check)
| Rule | Threshold | Check |
|---|---|---|
| Format | PCM 16 or 24 bit, 48 or 44.1 kHz; channels as listed (one-shots mono) | `--scan` |
| Coverage | every P0 row has its takes (P0 and P1 with `--release`) | `--scan` |
| Headroom per file | peak <= -1 dBFS | `--scan` |
| Loudness match | active RMS within 3 dB of its family median | `--scan` |
| Fast start, clean end | one-shots: <= 10 ms of silence before the sound; last 5 ms <= -60 dBFS (no end click) | `--scan` |
| Loops | last-to-first sample jump <= 0.05; looping only on `kind=loop` rows | `--scan`, `--ue-dump` |
| Variation | `WandBolt`, `HitOwl`: 3 takes, random no-repeat, pitch ±5% | `--scan`, `--ue-dump` |
| Telegraphs exact | 1 take, no pitch randomization, priority above loops and music | `--list`, `--ue-dump` |
| Voice limit | each non-music one-shot uses only its family's group (audio-rules.md §2); launch and hit groups duck older voices (Volume Scale 0.8) | `--ue-dump` |
| Classes | one of the 4 classes, as the list says; all route to `SM_Master`; one limiter | `--ue-dump` |
| 2D only | no attenuation, spatialization off on every playable asset | `--ue-dump` |
| Telegraph per attack | every P0 attack, and every attack that spawns, has a windup line with its own list sound | `--log` |
| Telegraph timing | windup starts at or before the visual tell (1 frame grace) and >= 0.2 s before danger | `--log` |
| Gust strength | `GustLoop` volume follows `GustStrength`; `gust_param` changes in every gust | `--log` |
| Music layers | stems start at 0 / 25 / 70% (±2%) on the next bar (or a <= 0.5 s fade) and stay on until `end_event` | `--log` |
| End event | music ducks to <= -6 dB after `end_event` | `--log` |
| In-context mix | master peak <= -1 dBFS in every phase, packaged build | `--log` |
| Leaks | at >= 90% timer: <= 24 voices, not rising over 10 s, 0 virtualized telegraphs | `--log`, QA read |
| SFX slider (if it ships) | SFX at 0 means every SFX, Telegraph and UI voice reports volume 0 | `--log` |
| Blind ID | 3 players, each >= 90% of P0+P1 one-shots, all windups, `PlayerHurt`, `UmbrellaTear` | `--blind-id` |
| Muted play | with sound off, players read phase, attack, umbrella tier | `--muted` |

The `AUDIO:` log lines, and which card prints each one, are in `pipeline/audio/audio-rules.md` section 3.

## Plan and cut order
Day-by-day plan and the audio cut order: `pipeline/audio/audio-rules.md` sections 7 and 8. P0 sounds are never cut.

## Checks before you open the PR
- [ ] `python3 tools/audio_check.py --list --events` and `python3 tools/audio_loop.py close --card <id>` print PASS. Paste both.
- [ ] `python3 tools/audio_check.py --scan Audio/Source --require-dir --fail-lfs-pointer` prints PASS after `git lfs pull`. Paste it.
- [ ] `--ue-dump` PASS for the new assets. Paste it.
- [ ] If the card adds or changes an event sound: `--log` PASS on an automation or packaged run log. Paste it.
- [ ] `python3 tools/audio_check.py --docs <each doc you changed>` prints PASS.
- [ ] Each new file has a provenance row with a known licence.
- [ ] Every binary was `git lfs lock`ed first. Assets moved or renamed only in the editor.
- [ ] No `_v2`, `_final` or `_new` in names. Placeholders end in `_PH`.

## Done when
The card's Done-when and the sound list row's `done_when` are met with pasted output, the human audio owner
approves by ear in the packaged build, and kickoff merges it. Day 4 mix approval also needs `laptop ok / headphones ok`
in the PR: one full encounter on each, every windup and `PlayerHurt` heard over the music.

## Never
- Never add a sound that is not a row in `pipeline/audio/sound-list.csv`. A new sound is a list change on its own card.
- Never edit `pipeline/audio/audio-rules.json`, `sound-list.csv` columns, `tools/audio_check.py` or its tests during the jam.
- Never drive gameplay from a sound event. Timing comes from C++ timers; sound only shows it.
- Never put pitch randomization on a telegraph, or let a telegraph start after its visual tell.
- Never use a sound with an unknown licence, or a voice imitating a real person.
- Never mark your own mix as approved.

---

## Claude Code entry point (`.claude/agents/audio.md`)

This small file only points the agent at the card above. The card wins.

```text
---
name: audio
description: Umbrella Ella jam role "Audio". Use for task cards whose owner or reviewer role is Audio.
tools: Read, Grep, Glob, Bash, Edit, Write
---
You are the Audio role for the Umbrella Ella game jam. Start with `ROLE: Audio`.
Read, in order: AGENTS.md, docs/jam-brief.md, pipeline/roles/audio.md, then the task card you were given.
Follow pipeline/roles/audio.md exactly. It wins over anything in this file.
```
