# Story requests (to the build lead / owning lanes)

1. Core `UmbrellaTuning.h`: add `#include "Story/StoryTuning.h"` and
   `UPROPERTY(Config, EditAnywhere, Category = "Story") FStoryTuning Story;`. Until then story reads `FStoryTuning::Get()`.
2. Flow: on a Director's Cut win call `UStorySubsystem::ShowDirectorsCutEnding()` (`World->GetSubsystem<UStorySubsystem>()`).
   It also starts by itself on `EncounterCompleted` in Director's Cut, so the call is idempotent. Bind
   `GetTryAgainDelegate()` / `GetMainMenuDelegate()` for the Journey Complete buttons.
3. Flow: before routing a Confirm/Skip press to play, ask `IsSkipPressForStory()`; if true call `HandleSkipPressed()` and
   swallow the press (opening caption must not fire/hop). Consume the start confirmation the same way.
4. Flow: a Try Again must broadcast `ModeSelected` (Detail `DirectorsCut`) so story resets stats and shows the caption once.
5. Progression/enemies: each enemy defeat must broadcast `XPAwarded` (Amount = XP); story counts one defeat per event.
6. Health: `PlayerHealthChanged` Value = health on the current life, Amount = lives left (story reads exactly that).
   Story misses the first hit of a run unless it knows full health: expose it, or broadcast once at run start.
7. Credits owner: story holds a timed placeholder Credits stage (`CreditsSeconds`); replace with the real roll.
