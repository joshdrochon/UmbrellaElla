# Dev-only sound labels. Branch area/soundlabel. Read docs/build/worker-rules.md first.
Josh: in playtests the team cannot tell which sound is playing. In workbench and Development builds ONLY (inside
`#if UMBRELLAELLA_WORKBENCH`, so the submission target compiles it out; workbench-check must still pass), a toggle key
(F9, through an Enhanced Input action, no raw key polling) shows each sound as it plays in a small on-screen list inside the
16:9 view: sound ID, game event, take number; each line fades after about 3 s. The same line goes to the game log
(LogUmbrellaElla, e.g. `SOUND_LABEL id=<Id> event=<Event> take=<NN>`). Hook it in the cue subsystem
(Feedback/Audio/UmbrellaCueSubsystem) so every sound, music included, is covered. Off by default.
Tests: playing a cue adds a label line and a log line; the toggle hides it; with UMBRELLAELLA_WORKBENCH=0 nothing is built.
Lane: Feedback/Audio/** (the hook), a new Feedback/Audio/SoundLabel* widget, Content/UmbrellaElla/Input/Debug/** if you need
an input asset, tests. Done: worker-rules DoD plus `python3 tools/ue_run.py workbench-check` passes.
