# Audio to the bar. Branch area/audio. Read docs/build/worker-rules.md first.
Josh: nobody listens or reviews by hand; build to the bar and do not stop. All 11 sound pieces on main failed the blind
audio critic and are tracked placeholders (pipeline/art/provenance.csv origin "placeholder: audio critic fail (<gap>)";
the gaps are there). Regenerate each with the ElevenLabs tooling (tools/assetgen.py sfx|music --sound <Id>, prompts from
python3 tools/audio_style_check.py prompt <Id>; key: source ~/.umbrella-ella.env ONLY in the one shell that runs
generation, never print it). Fix what the critic named: clean pitched sources, layering, low-end weight, levels, tails.
Loop per piece with tools/audio_loop.py (start/round/verdict/close; the critic is a FRESH session you start in the packet
folder with tools/audio_critic_prompt.md, --disallowedTools Bash Edit Write) until the critic passes AND
audio_check --scan and audio_style_check pass on the same files. A passing piece gets its provenance origin back from
placeholder to the generated origin; re-import into Content/UmbrellaElla/Audio with tools/build/assets/arena_audio_import.py.
Critic sanity (Josh): if the critic looks defective (the same piece failing for different reasons each round, reasons that contradict the GDD or the references, reasons it cannot judge, a piece that measurably meets every number but keeps failing, calibration drift), test the critic: it must pass the reference itself, fail a known-bad sample, and agree with itself on the same piece twice. Fix a real defect in its prompt, packet or calibration and write the fix and the evidence in docs/build/areas/<you>-status.md (the lead copies it to the build log). Never loosen the bar. The audio critic sees spectrograms and numbers, not sound: first prove it can tell a known-good approved take from
a known-bad one (e.g. a clipped or noise-only version) before trusting its fails.
Lane: Audio/Source/**, Content/UmbrellaElla/Audio/**, pipeline/audio/**, provenance rows for Audio/, Feedback/Audio/**.
