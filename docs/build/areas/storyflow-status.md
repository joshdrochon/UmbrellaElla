# storyflow status (area/storyflow)

## Done
NAR-04, NAR-07, FLOW-49, NAR-05 trigger. Build exit 0 (unity, 0 warnings); full `tools/ue/test.sh` PASS tests=256;
`UmbrellaElla.Story+UmbrellaElla.Flow` PASS tests=42; module_check 0; manifest_check 0; story_check PASS; ui_check ci PASS.

- One ending timeline. Flow owns the clock for both modes: Story screen = hold on Ella (`Story.EndingHoldSeconds`,
  2.5 s, no ending background), then the ending pages, then Credits (`Flow.CreditsSeconds`), then Journey Complete
  (new `EFlowScreen::Statistics`) in Director's Cut, Title in Start Game. Story no longer runs its own
  Hold/StoryText/Credits timers; flow calls `UStorySubsystem::EnterEndingStage()` (forward only) and the model follows.
  Story stops counting stats and captions at the win. `Story.CreditsSeconds` (placeholder roll) removed.
- Director's Cut ending pages are the story's `Ending.Story` lines (`GetEndingLines()`, `Story.EndingLineSeconds` each).
  Start Game keeps `FFlowStoryText` pages.
- Skip (NAR-04 / NAR-07): `IA_StorySkip` on IMC_Menu, keys Enter and gamepad View (`FFlowRules::StorySkipKeys()`,
  none used by gameplay, so a press never leaks into play). Flow asks `IsSkipPressForStory()` then `HandleSkipPressed()`.
  Opening: the first viewing is consumed but not skipped; later starts skip. Ending: after a prior first win, Skip from
  story or credits goes to Journey Complete; never in the hold or on the first win; never in Start Game.
- Journey Complete buttons bound: Try Again reloads the level with `?UmbrellaTryAgain` and starts a new Director's Cut
  run there (purchase screen first when there is something to spend; ModeSelected resets the stats). Main Menu = title.
- NAR-05 trigger: `UStorySubsystem::IsLightShaftOn()` is true in Director's Cut play and the ending hold, off from the
  ending background on. artfx polls it.
- Tests: Story.EndingSequence, Story.SkipRules, Story.LightShaftTrigger, Flow.EndingTimelineRules,
  Flow.World.DirectorsCutEndingOneTimeline, Flow.World.LaterWinSkipsToStatistics,
  Flow.World.StartGameEndingHasNoStatistics, Flow.World.OpeningSkipGoesToStory (story progress kept in memory).

## Defaults taken (GDD says OPEN or is silent; design owner may change)
1. The 2.5 s hold also plays in Start Game (one timeline for both modes).
2. Two ending texts stay: story lines in Director's Cut, flow's pages in Start Game.
3. Skip keys Enter and gamepad View only; Space/A are Hop, so they do not skip. No on-screen Skip prompt yet.
4. Try Again = reload the level and start Director's Cut at once.

## Left
- Journey Complete keyboard/controller focus: flow passes the widget to SetWidgetToFocus, but the widget is not
  focusable, so Try Again needs a default focus in the widget (artui lane; `docs/build/requests/storyflow.md`).
- Not run: packaged build, smoke, blind story critic (no story text changed).
