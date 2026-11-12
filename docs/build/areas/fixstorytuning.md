# Follow-up: story numbers into the shared tuning. Branch area/fixstorytuning. Read docs/build/worker-rules.md first.
Add `UPROPERTY(Config, EditAnywhere) FStoryTuning Story;` to `Core/UmbrellaTuning.h` (FStoryTuning lives in
Public/Story/StoryTuning.h once area/story is on main; merge main; if it is not there yet, wait for 'Merge area/story'
in git log main, checking every few minutes, max 60 min). Story readers use GetDefault<UUmbrellaTuning>()->Story.
No story text changes. `bake_preset.py defaults` 0. Lane: Core/UmbrellaTuning.h, Story/** readers only. Done: DoD.
