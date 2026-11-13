# sndhit status

Round 2 (critic prompt audio-critic/3, event named in packet): fresh blind critics on every take. 15 of 18 PASS with measured checks (audio_style_check, audio_check --scan) clean on the same files: CourierDisable, EyeHit, FloodDisable, GlassCrack, HitClock, HitEnemy, HitProtected, HitWing, MechanismBreak, NeedlePierce, ShutterClose, SmallBlastImpact, TwinStarsImpact, WandBoltFade, WardenDisable. Provenance origin for these is generated/synthesized in jam.
HitClock and GlassCrack were regenerated (recipes in pipeline/audio/build/sndhit.py), then given level/end-fade fixes; the critic re-judged the fixed files.

Still failing (tracked placeholders in provenance.csv):
| Sound | Gap |
|---|---|
| EllaDown | sub drop plus rib-crack transient; clean noise from the tail |
| OutOfBounds | one clean low thud and descending sub drop, short mid crack, no noise bed |
| WingsBreak | layered break with distinct metal and wood material, not a noise burst (judged on the older packet; needs a new round) |

Tried for EllaDown/OutOfBounds: quieter API noise layers and lower reverb wet; the candidates then failed the style check (attack, low_share, level). Recipes are reverted to the originals plus lower reverb wet; the committed placeholder takes are kept. ElevenLabs returned 429 (concurrent limit) at times.
Not done: import into Content/UmbrellaElla/Audio (the importer is the arena lane's); new recipes for the 3 above.

BLOCKED (ElevenLabs): `quota_exceeded` (HTTP 401) on new layer generation. EllaDown, OutOfBounds, WingsBreak recipes now add synthesized metal/brass ring layers (untested; only cached API layers could be mixed), takes stay committed placeholders. Resume: when credits return, `sndhit.py regen <Id>` for these three, then `sndhit.py critic <Id>` / new loop round and a fresh critic.
