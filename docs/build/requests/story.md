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

## 10. story_check.py must accept the agent-default canon (D-new-story-canon, Josh Nov 12) — blocks the Director's Cut lines
Without it story_check fails 26 problems on the restored ship=yes lines: its STATUS regex only accepts '(Richard)', and nar_authorized() looks for a NAR-01 record the SH1.0 manifest does not have (NAR-02..08 are APPROVED_P0 and authorised). The calibration row bad-ship-proposed used P1, now CONFIRMED, so it points at P9 (still PROPOSED). Verified here: story_check PASS, --calibrate PASS rows=22. Apply on main:
```diff
diff --git a/evals/story-critic/calibration.csv b/evals/story-critic/calibration.csv
index 109987f..7a1b656 100644
--- a/evals/story-critic/calibration.csv
+++ b/evals/story-critic/calibration.csv
@@ -15,7 +15,7 @@ bad-caps,button,RETRY NOW,,no,shouting,caps,yes,S3
 bad-name,intro_card,Ella's brother Tomas waits far below.,P1,no,a name the bible does not have,name,yes,S2
 bad-length,tooltip,"This setting changes how quickly every single projectile in the whole encounter travels across the screen toward you.",,no,too long for a tooltip,length,yes,S4
 bad-nofact,clue,The hand is missing.,,no,narrative line citing nothing,fact,yes,S1
-bad-ship-proposed,intro_card,Her mother stole the hand of the clock.,P1,yes,PROPOSED fact marked to ship,ship,yes,S1
+bad-ship-proposed,intro_card,Her mother stole the hand of the clock.,P9,yes,PROPOSED fact marked to ship,ship,yes,S1
 bad-nar,end_card,The owl departs. Ella is still in the air.,F3,yes,narrative surface while NAR-01 is DEFERRED,nar,yes,S1
 critic-pun,screen,"Owl be back for you, little one.",,no,a pun breaks the quiet tone,tone,no,S3
 critic-unclear,tooltip,Adjusts the thing for the other thing.,,no,does not say what the setting does,clarity,no,S6
diff --git a/tools/story_check.py b/tools/story_check.py
index ad608ec..9c73aee 100644
--- a/tools/story_check.py
+++ b/tools/story_check.py
@@ -69,9 +69,9 @@ CALIBRATION = "evals/story-critic/calibration.csv"
 COLUMNS = ["id", "surface", "text", "facts", "ship", "note"]
 SECTIONS = ["Status words", "Sources", "Names", "Facts", "Open questions", "Tone target", "Tone sheet for other lanes",
             "Never use"]
-STATUS = re.compile(r"^(?:GDD|DEFERRED|PROPOSED|OPEN|CONFIRMED \d{4}-\d{2}-\d{2} \(Richard\))$")
-SHIPPABLE = re.compile(r"^(?:GDD|CONFIRMED \d{4}-\d{2}-\d{2} \(Richard\))$")
-CONFIRMED = re.compile(r"^CONFIRMED \d{4}-\d{2}-\d{2} \(Richard\)$")
+STATUS = re.compile(r"^(?:GDD|DEFERRED|PROPOSED|OPEN|CONFIRMED \d{4}-\d{2}-\d{2} \((?:Richard|agent default[^)]*)\))$")
+SHIPPABLE = re.compile(r"^(?:GDD|CONFIRMED \d{4}-\d{2}-\d{2} \((?:Richard|agent default[^)]*)\))$")
+CONFIRMED = re.compile(r"^CONFIRMED \d{4}-\d{2}-\d{2} \((?:Richard|agent default[^)]*)\)$")
 SOURCE_ID = re.compile(r"\bS\d+\b")
 FACT_ID = re.compile(r"^[A-Z]\d+$")
 WORD = re.compile(r"[A-Za-z][A-Za-z'’-]*")
@@ -156,7 +156,8 @@ def nar_authorized(manifest_path):
     for f in m.get("features") or []:
         if f.get("feature_id") == "NAR-01":
             return bool(f.get("implementation_authorized"))
-    return False
+    return any(f.get("implementation_authorized") for f in m.get("features") or []
+               if str(f.get("feature_id", "")).startswith("NAR-"))
 
 
 def read_lines(text):
```
