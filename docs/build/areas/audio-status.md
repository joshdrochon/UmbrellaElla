# Audio status (area/audio)

## Josh approval, Nov 12 2026
SW_MusicTitle_00 listened to by Josh: "sounding really good". Approved. provenance.csv keeps the generated row with
origin `generated in jam; approved by Josh (listened) 2026-11-12`; the `placeholder: audio critic fail` row is deleted.
Never regenerate or replace it. It is the known-good music reference for the critic.

## Critic sanity on music (audio-critic/2, `claude -p`, packet folder only, Bash/Edit/Write disallowed)
Packets built with tools/audio_loop.py on copies of Audio/Source with only MusicTitle swapped.
| sample | style check | critic verdict |
|---|---|---|
| MusicTitle_00 (approved), run 1 | PASS | pass, A1..A8 true |
| MusicTitle_00 (approved), run 2 (fresh session) | PASS | pass, A1..A8 true (agrees with itself) |
| hard-clipped copy (crest 0.37 dB) | FAIL crest | fail, all rows false |
| copy + white noise wash (centroid 11.7 kHz) | FAIL centroid, crest, lufs | fail, all rows false |
Result: the v2 prompt is calibrated for music; no prompt or packet change needed. Bar not loosened.
Caveat: the bad samples also fail the numbers, which the critic may not override, so this proves the picture reading,
not subtle cases.

## Done / left
- recipes for all 11 pieces are in pipeline/audio/build/recipes.py (layered regeneration via regen.py).
- WandBolt regenerated earlier (commit 33bc966). Others: see below.

## Audio core assets (Nov 12 2026)
`tools/build/assets/arena_audio_core.py` creates Content/UmbrellaElla/Audio/Core: SCL_SFX/Telegraph/UI/Music, SM_Master
(+ SMFX_MasterLimiter, Limiter mode), SCON_WandBolt/Launch/Hit/Hurt/Telegraph/State/UI from audio-rules.json, and SCON_Default.
Config/DefaultEngine.ini [/Script/Engine.AudioSettings] DefaultSoundConcurrencyName = SCON_Default. Rows removed:
the smoke-concurrency decision row (decisions.md) and its tools/ue/smoke-allow.txt line.
Evidence: editor run exit clean ("arena_audio_core: done"); tools/ue/audio_dump.py then `audio_check.py --ue-dump` reports
no core, group or unread errors; only the 8 old cue names (Shot, Hit, ...) fail the SW_/SC_ naming rule (arena cue imports, not mine).
Not run: packaged smoke (build lead).

## Provenance: one row per take (review round, Nov 12 2026)
The ledger had 2 to 3 rows per Audio path; audio_check keeps the last, so a merge re-added MusicTitle's placeholder row.
Now one row per path (25 rows). `pipeline/audio/build/provenance.py generated|placeholder|dedupe` rewrites rows in place
and refuses to touch a row marked "approved by Josh". `audio_check.py --scan` fails on two rows for one WAV
(`duplicate_provenance`; tests `test_two_provenance_rows_for_one_take_fail`, `test_repo_ledger_has_one_row_per_take`).
On the pre-fix ledger the check reports 24 duplicated paths.
| piece | origin now | basis |
|---|---|---|
| MusicTitle | generated in jam; approved by Josh (listened) 2026-11-12 | Josh |
| HitOwl | generated | area critic pass, gate critic pass |
| KeeperHoot, EndEvent, LevelUpClock | generated | area critic pass; gate critic has not judged them yet |
| WandBolt, PlayerHurt, OwlBoltLaunch, ShieldCatch | placeholder: gate gap (full text, not cut at 120) | gate critic fail (logs/audio-critic-audio.txt) |
| FailSting, SurvivedSting | placeholder | not regenerated yet |
OwlBoltLaunch and ShieldCatch: the area critic (sonnet) passed them, the gate critic (opus) failed the same bytes. The
gate critic is the one that decides a merge, so they are placeholders. The area loop now runs the critic on the gate's
model (CRITIC_MODEL) so the two agree.
Also: pipeline/audio/ue/audio_dump.py synced to tools/ue/audio_dump.py (main added -nocrashreports; the byte-match test failed).

## Provenance matches the critic (Nov 12 2026, evening)
Supersedes the table above: all 10 regenerated pieces passed the blind critic on the gate's model, on the bytes now in
Audio/Source, and every row reads its generated origin (MusicTitle: Josh's approval row, untouched).
- Committed critic records: `pipeline/audio/critic/<Id>.json`, one file per sound id (parallel lanes do not collide),
  each record keyed by the hash of the takes it judged (`audio_check.takes_hash`, the hash audio_loop stores).
  `pipeline/audio/build/provenance.py record <Id>` copies the rounds on the current bytes from Saved/AudioLoop;
  `promote.sh <Id>` runs it before writing the generated rows.
- `tools/audio_check.py --scan` (in the gate as audio_scan) now fails when the latest record on a piece's current bytes
  passes and a take is marked `placeholder:`, and when it fails and a take is marked generated. Bytes with no record and
  rows "approved by" a person are left alone. `provenance.py placeholder` refuses on passed bytes; `generated` needs a pass.
- Evidence (commit of this section, host=mac): main's ledger against these takes and records -> 6 FAIL lines
  (OwlBoltLaunch x3, ShieldCatch x3 "marked placeholder, but the blind critic passed these bytes"); this branch's ledger -> 0.
  Tests: tests/test_audio_check.py `test_passed_take_marked_placeholder_fails`, `test_passed_take_with_generated_origin_passes`,
  `test_placeholder_is_fine_when_the_pass_was_on_other_bytes_or_missed_the_numbers`, `test_a_later_fail_on_the_same_bytes_wins`,
  `test_failed_take_marked_generated_fails_and_an_approved_take_is_left_alone`, `test_repo_ledger_matches_the_critic_records`,
  `test_loop_and_check_hash_the_takes_the_same_way`.
| piece | bytes | latest record |
|---|---|---|
| WandBolt | e1cef8e48304 | pass, AUDIO-R2C-WandBolt r1 (2 passes) |
| HitOwl | 00c2c44a33f6 | pass, AUDIO-1 r2 |
| ShieldCatch | 90c1994d619f | pass, AUDIO-R2C-ShieldCatch r1 (2 passes) |
| PlayerHurt | 29f8d8b9be5c | pass, AUDIO-R2C-PlayerHurt r2 (2 passes) |
| OwlBoltLaunch | 73723fc0e252 | pass, AUDIO-R2C-OwlBoltLaunch r1 (2 passes) |
| KeeperHoot | 7425ba529a2e | pass, AUDIO-1 r2 |
| EndEvent | 260569f40943 | pass, AUDIO-1 r1 |
| LevelUpClock | 3903360f2f9c | pass, AUDIO-1 r5 |
| FailSting | 136f8ab9c9e8 | pass, AUDIO-R2C-FailSting r1 (2 passes) |
| SurvivedSting | 8f254fc2d687 | pass, AUDIO-R2C-SurvivedSting r1 (2 passes) |
Open for the lead (docs/build/requests/audio.md): the gate marks a placeholder without writing a record, so a gate fail
on bytes an area critic passed would now fail audio_scan until the gate records its verdict. Default built: the latest
recorded verdict on the same bytes wins.

## Content re-import (Nov 12 2026, evening)
The cue assets were from 13:59, before the regenerated takes. Re-imported with tools/build/assets/arena_audio_import.py
(headless editor, exit 0, "Python script executed successfully"): Shot, Hit, Absorb, AbsorbFail, KeeperHit, KeeperAttack,
StartMusic, EndMusic rewritten; LevelUp is new. LFS locks held on those 8 files (lockable files are read-only without one).
Not run: audio_dump / `audio_check --ue-dump` on the new assets, packaged smoke (build lead).

## Left
- Nothing in the 11 pieces. `audio_check --scan Audio/Source` still reports 63 "P0 sound has no file" lines: the sounds
  of the six new lanes (sndstate, sndui, sndhit, sndlaunch, sndtele, sndworld).
- The gate critic has not judged the current bytes of the 10 pieces yet.

## Music through one persistent component (Nov 12 2026, night)
- `UUmbrellaCueSubsystem` no longer plays StartMusic with PlaySound2D (the "orphaned sound StartMusic" warning). Music cues
  (`IsMusicCue`) go to `RestartMusic`: stop, then play on one persistent non-auto-destroy `UAudioComponent` that is reused
  across mode changes. `EndMusic` stops the music first, then plays the sting. Deinitialize stops it.
- Tests (pass, `UmbrellaElla.Audio` tests=2 failed=0): `UmbrellaElla.Audio.MusicCueIsLooped`,
  `UmbrellaElla.Audio.World.MusicRestartReusesOneComponent` (same component across restarts, start count, stop, null sound).
  The test is tolerant of no audio device (component null); the player-side warning is not run here.
- StartMusic asset re-imported from the approved SW_MusicTitle_00.wav with arena_audio_import.py. Read back in the editor:
  StartMusic ch=2 dur=40.040 s looping=True (source: 2 ch, 48 kHz, 40.04 s). Other cues re-imported unchanged-bytes.
Not run: packaged smoke (build lead).

## Every listed sound has a cue mapping (Nov 12 2026, night)
- `pipeline/audio/build/cue_table.py write` generates `Public/Feedback/Audio/UmbrellaCueData.h` from sound-list.csv (non-cut rows),
  audio-rules.json (concurrency asset, class) and its ROUTES (bus event + Detail/Target match). Rows with no bus event yet are
  Direct (`UUmbrellaCueSubsystem::PlaySoundById`, for the lane that owns the trigger): HopWhoosh, DashWhoosh, OutOfBounds, UI sounds, ambience,
  health-state loops, stems, enemy and hazard sounds.
- `UUmbrellaCueSubsystem` subscribes to every routed event, plays a random take `SW_<Id>_NN` from `/Game/UmbrellaElla/Audio/<Id>/`
  with the row's pitch jitter, SCON_* concurrency and SCL_* class; loops are persistent components, one group ("move", "wind") at a time;
  `WindExited` stops the wind group; music rows go through the one music component. When no per-sound take is imported the old flat cue
  asset (Shot, Hit...) still plays, so nothing goes quiet before the lanes import.
- `arena_audio_import.py` now also imports every take in Audio/Source into that folder (loop rows get the looping flag).
- Tests (pass, `UmbrellaElla.Audio` tests=4): `EveryListedSoundHasACueMapping` (reads the csv), `BusEventsRouteToTheirSounds`;
  python `tests/test_audio_cue_table.py` (table is current, every live row mapped, every sound with a non-failing take mapped,
  class/concurrency/loop/takes match the rules, events exist in the manifest).
- Not run: the import in the editor (new takes are not on this branch), packaged smoke.
