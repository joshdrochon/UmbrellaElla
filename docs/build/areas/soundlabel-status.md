# soundlabel status
Done: dev-only sound labels. F9 (Enhanced Input action built in code) toggles an on-screen list (id | event | take NN,
8 lines, 3 s life, last 1 s fading, top-left of the view); every sound the cue subsystem starts, music included, adds a
line and writes `SOUND_LABEL id=<Id> event=<Event> take=<NN>` to LogUmbrellaElla (logged even while hidden). Off by default.
All of it is inside `#if UMBRELLAELLA_WORKBENCH` (Feedback/Audio/SoundLabelBoard, SoundLabelHud, hook in UmbrellaCueSubsystem).
Tests (`UmbrellaElla.SoundLabel.*`, 5): line formats and take parse, toggle/fade/cap, F9 key, cue play adds label+log line
and the toggle hides it, every file is wrapped in the workbench guard.
Checks: build exit 0, full suite 281 pass, module_check 0, manifest_check 0, workbench-check PASS, pipeline_check 0.
Not run: a UMBRELLAELLA_WORKBENCH=0 (submission target) compile, and a visual check of the list in a running game.
Event text is the bus event type; sounds played by id with no bus event show `event=Direct`.

## Review round (changes)
- Submission target `UmbrellaElla` (UMBRELLAELLA_WORKBENCH=0), Mac Development, commit 7aa72817 + this slice: `Result: Succeeded`, 47 s. The workbench code compiles out.
- `TEST_FILTER=UmbrellaElla.SoundLabel`: `PASS tests=6 failed=0` (5 old + `ListSitsInsideThe16By9View`). "281 pass" was the full suite on the earlier run; this run is the filtered one.
- Editor build `build exit: 0`, module_check 0.
- `python3 tools/ue_run.py workbench-check`: FAIL 1, not in this lane: `Settings/DeveloperOptions.cpp:154` uses `#if defined(UMBRELLAELLA_WORKBENCH) && ...`. Settings lane owns it; fix is `#if UMBRELLAELLA_WORKBENCH`. Nothing of the soundlabel files is flagged.
- Minors fixed: unused include, include order, Arm comment. List now offset into the centred 16:9 view (`UmbrellaSoundLabel::ViewOrigin`); labels stop aging while the world is paused.
- Not run: a look at the list in a running game.
