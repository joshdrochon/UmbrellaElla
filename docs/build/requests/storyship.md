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

## Cue file sync (reviewer round 1)
`Content/UmbrellaElla/UI/Story/StoryCues.tsv` and `StoryRules.cpp` `DefaultText` now carry the seven `lines.csv` texts.
`story_check.py --table` only reads Key/SourceString string tables, so the cue file is checked with `--scan` (PASS).
The opening caption follows GDD NAR-04 word for word ("Mother: Keep it open, Ella. It'll protect you from the owl.").

## Critic defect: S2 on the opening caption (cycle 1, 2026-11-12)
The blind critic failed `story-opening-mother` on S2 ("Mother:" label; it wants "Her mother:"). GDD NAR-04 (APPROVED_P0,
`docs/gdd/GDD-SH1.0.md:607`) specifies the exact caption "Mother: Keep it open, Ella. It'll protect you from the owl."
The GDD outranks the critic (AGENTS.md section 2), so the line stays as the GDD words it. The other six lines passed all rows.
Decision for the design owner: keep the GDD caption (shipped), or change NAR-04 to "Her mother:". No decision row opened.
