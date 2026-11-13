# storyflow requests

1. artui (`UI/Story/StoryWidgets.cpp`, `UJourneyCompleteWidget`): give Try Again default keyboard/controller focus when
   the widget is shown (e.g. `SetIsFocusable(true)` and set user focus to the Try Again `SButton` in `RebuildWidget`).
   Flow already calls `SetInputMode` with `GetStatisticsWidget()->TakeWidget()` as the focus target on the Statistics
   screen, but the widget is not focusable, so a keyboard or pad player cannot reach the buttons today.
2. artui: an on-screen Skip hint on the ending story and credits after a prior first win (keys:
   `FFlowRules::StorySkipKeys()`, Enter and gamepad View). Text goes through the story lane.
3. artfx (NAR-05 visual): poll `UStorySubsystem::IsLightShaftOn()` (`World->GetSubsystem<UStorySubsystem>()`) to show
   the light shaft and umbra; it is on in Director's Cut play and the ending hold, off once the ending background shows.
