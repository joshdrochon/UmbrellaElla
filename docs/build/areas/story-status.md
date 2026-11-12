# Story status

## Done (commit on area/story)
NAR-02..NAR-08, FLOW-49. Build exit 0, `UmbrellaElla.Story.*` 9 tests PASS, module_check 0, manifest_check 0, story_check PASS.
- Cue table `Content/UmbrellaElla/UI/Story/StoryCues.tsv` (compiled copy in `StoryCueTable::DefaultText()`, test keeps them equal).
- `FStoryModel` (rule core), `UStorySubsystem` (bus, widgets, saved flags), `UStoryCaptionWidget`, `UJourneyCompleteWidget`.
- Tests (`Private/Tests/Story/StoryTests.cpp`): CueTable, OpeningOncePerRun (NAR-04/08), StartGameHasNoStory (NAR-02),
  InPlayCues (NAR-03/05/06), EndingSequence (NAR-07), SkipRules (NAR-04/07), JourneyStatistics (FLOW-49), ProgressRoundTrip, World.ReactsToBus.

## Left / open
- Flow wiring and the other lanes' event contracts: see `docs/build/requests/story.md`.
- Credits is a timed placeholder. Ending script, timings and cue placement are the story lane's drafts (GDD says OPEN).
- All new lines in `lines.csv` are ship=no (Ella and the story facts are not CONFIRMED in the bible).
- Stats caveats: first hit of a run is not counted as damage without a health baseline; enemies counted per XPAwarded;
  distance sampled from the first player's pawn per tick, steps over 2000 units ignored as teleports.
- Widgets not looked at in the editor (no screenshot); layout uses tuning margins and fonts of 18 px or more.
