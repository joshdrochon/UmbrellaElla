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
8. Flow: once the Director's Cut world is up, call `World->GetSubsystem<UStorySubsystem>()->BeginNewRun(EUmbrellaPlayMode::DirectorsCut)`.
   Nothing on main broadcasts `ModeSelected`, and a mode picked on the title screen may fire before this world exists.
   Story still listens to `ModeSelected`; a late one for the same untouched run is ignored, so the opening shows once.
9. Keeper/flow: `PhaseStarted` Detail must be exactly `wings`, `mechanisms`, `clock` (EncounterDirectorSubsystem PhaseName).
   The NAR-06 clue keys on `PhaseStarted.wings` (`StoryCues.tsv`); any other spelling means the clue never shows.

## PROPOSED facts avoided (design owner: confirm to let lines use them)
Lines now use only GDD facts F1-F7. Not used, pending confirmation:
- P3 (her mother gave her the umbrella to keep her safe) and any "protects you": opening-mother says only "Keep it open." (F4: umbrella tears).
- P4 / P8 (edge of reality, still between worlds): ending-2 says only "She is alive."
- P8 / P1 (owl only postponed his judgment): ending-3 says only "The owl has gone." (F3).
- Owl damage (any wing falling away): shaft-clue shows gears only; F3 says the owl is not worn down.

## Rows needed by a held line (design owner: confirm to ship)
- story-light-shadow ("Its shadow follows.") needs P2/P5 (umbra, shade motif; PROPOSED). Kept as ship=no, not rewritten. Q5 in the bible is the open decision.
- All other lines checked word by word against GDD rows F1-F3; they use no PROPOSED row. They stay ship=no because the narrative surfaces wait on NAR-01 (DEFERRED).
