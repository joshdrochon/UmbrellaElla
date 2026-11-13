# fixstorytuning status
Done: UUmbrellaTuning has `FStoryTuning Story`; all story readers (Story/, UI/Story) use GetDefault<UUmbrellaTuning>()->Story; FStoryTuning::Get() removed. No text changes.
Proof: build exit 0 (warnings 0), UmbrellaElla.Story tests 11/11 pass, module_check 0, manifest_check 0, bake_preset defaults PASS.
Left: nothing.
