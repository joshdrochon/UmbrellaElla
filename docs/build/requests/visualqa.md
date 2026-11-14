# Requests from visualqa

## B11: "Director's Cut" HUD title draws over Ella at the ceiling (agentplay 67011eb2) - for flow

File: `Source/UmbrellaElla/Private/Flow/UmbrellaPlayerController.cpp`, `case EFlowScreen::Playing` (the SBox with
`HAlign_Center` / `VAlign_Top` and the "Director's Cut" STextBlock). Not visualqa's lane.

What visualqa did in its own lane: the camera margin (`UFrameCompositionSubsystem::ApplyCameraMargin`) keeps the
umbrella tip inside the frame. It is only ~7 px at 640x360, so the title band (top ~15 px) still covers her body at z 1036.

Choice for flow / Josh (lean: A):
- A. Show the title for a few seconds when a Director's Cut run starts, then remove it (Ella starts mid-height, left).
  Smallest change; the mode is already named on the purchase screen.
- B. Move it to the top-right corner. Still collides when Ella is at the top right.
- C. Hide it while Ella's projected sprite overlaps the title box. Exact, but needs Ella's screen position in flow.

Diff for A (new tuning value in `FlowTuning.h`, `float ModeTitleSeconds = 3.0f;`): in `case EFlowScreen::Playing`,
after `AddViewportWidget(ScreenWidget.ToSharedRef());`, add a world timer that calls
`GEngine->GameViewport->RemoveViewportWidgetContent(ScreenWidget.ToSharedRef())` (and resets `ScreenWidget`) once
`ModeTitleSeconds` of game time have passed and the screen is still `Playing`. Test: Flow.World, the title widget is gone
after the timer, and present before it.
