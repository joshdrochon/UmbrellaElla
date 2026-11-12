# Area: story (Director's Cut story and run flow screens)

Branch `area/story`. Read `docs/build/worker-rules.md` first. Added Nov 12 14:10 (Josh: 8 workers).

## Rule IDs (Director's Cut, G2/G3)
NAR-02 .. NAR-08 (text narration, single story delivery, opening mother caption, light and umbra, the Keeper clock-hand
clue, living departure ending, retry and new-run story), FLOW-49 (Journey Complete statistics on a Director's Cut win).

## GDD sections
6 (Story and dialogue: nUMBeR ELLA, story planning fields, story presentation requirements, Director's Cut in-play
story delivery), 7 "Director's Cut win results". Check: `python3 tools/story_check.py --help`.

## File lane (only these)
- `Source/UmbrellaElla/{Public,Private}/Story/**`, `DirectorsCut/**`, `UI/Story/**`
- `Source/UmbrellaElla/Private/Tests/Story/**`
- `Content/UmbrellaElla/UI/Story/**`, `pipeline/story/**`, `docs/build/areas/story-status.md`, `docs/build/requests/story.md`

## What to build
- A story subsystem that holds the story facts and cues as data (text in a committed data file, not hard-coded in
  logic) and reacts to events: ModeSelected (Director's Cut start: opening caption), PhaseStarted/CheckpointReached
  (in-play delivery), BossPartDestroyed (clock-hand clue), EncounterCompleted (living departure ending), CheckpointRetried
  and RunCompleted (retry/new-run story). Story never decides combat success (CORE-04).
- C++ widgets for captions, text narration and the Journey Complete statistics screen (FLOW-49). The flow area owns the
  title, pause and Start Game win screen; for Director's Cut, flow calls your public `ShowDirectorsCutEnding()` if it
  exists (write the request in `docs/build/requests/story.md` with the exact function you expose).
- Text must stay inside the 16:9 view and be at least 18 px.

## Done
Worker-rules DoD, plus tests: each event shows the right cue once, the ending shows after EncounterCompleted in
Director's Cut only, the statistics screen reads the run's numbers, `tools/story_check.py` clean if it applies.
