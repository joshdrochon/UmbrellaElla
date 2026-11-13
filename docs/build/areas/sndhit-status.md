# sndhit status

All 18 sounds PASS: blind critic (audio-critic/3, fresh session per sound) plus audio_style_check on the same bytes. Critic records are committed in pipeline/audio/critic/<Id>.json; provenance origin is 'generated in jam' for every take.

Round 3/4 (after merging main's critic fixes: neighbours exclude placeholders, enemy family target = Roadwarden, Floodstrider, Sky Courier):
- EllaDown, OutOfBounds, WingsBreak: rebuilt with no new API calls. Noise layers cut back; added synthesised layers (brass swell falling in pitch + chime partial; steeply falling tone + wind rush; escapement tick series + spring lurch). Recipes in pipeline/audio/build/sndhit.py (`falling()` helper).
- HitEnemy (new enemy target): added a synth broadband strike at onset and slow/fast decaying gear partials; spring wash shortened.
- WardenDisable, FloodDisable, CourierDisable re-judged under the new target: pass unchanged.

Layer cache for reproducing: /tmp/gen-sndhit (API layers for the three previously blocked sounds were reused; missing candidate indices copied from existing ones, so the takes differ by synth pitch only). ElevenLabs credits are still out; a rebuild needs that cache or fresh credits.
Not done: import into Content/UmbrellaElla/Audio (the arena lane's importer).
