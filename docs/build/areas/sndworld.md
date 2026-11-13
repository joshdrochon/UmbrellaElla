# Audio lane sndworld: ambience, music sounds. Branch area/sndworld. Read docs/build/worker-rules.md first.
Josh: nobody listens or reviews by hand; build every sound to the bar. Your sounds (12 from pipeline/audio/sound-list.csv,
tier not cut; the audio area owns the first 11 and MusicTitle stays Josh-approved):
WindZoneLoop, GustLoop, ClockTickLoop, AirMillLoop, RefugeLoop, MusicIntro, MusicContest, MusicDesperation, WindBed, MillAmbience, BossApproach, RealmClocks
For each: generate its takes with the ElevenLabs tooling (tools/assetgen.py sfx|music --sound <Id>; prompts from
python3 tools/audio_style_check.py prompt <Id>; key: source ~/.umbrella-ella.env ONLY in the one shell that runs generation,
never print it), loop with tools/audio_loop.py and the blind audio critic (fresh session in the packet folder,
tools/audio_critic_prompt.md v2) until the critic passes AND audio_check --scan and audio_style_check pass on the same files.
Recipes and layering helpers: pipeline/audio/build/ (the audio area's; reuse, do not fork). Import into
Content/UmbrellaElla/Audio/<Id>/ with tools/build/assets/arena_audio_import.py. One provenance row per take, kept sorted by
asset_path in pipeline/art/provenance.csv (insert in place, so parallel lanes rarely touch the same lines); a passing take's
origin is its generated origin, a failing one "placeholder: <gap>". Highest tier first (P0, then P1, then P2).
Triage before calling anything stuck (docs/build/worker-rules.md). Commit after each passing sound.
Lane: Audio/Source/<your ids>/**, Content/UmbrellaElla/Audio/<your ids>/**, your rows in pipeline/art/provenance.csv.
