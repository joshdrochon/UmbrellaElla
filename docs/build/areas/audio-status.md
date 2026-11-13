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
