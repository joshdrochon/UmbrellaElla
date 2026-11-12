import json
m=json.load(open('../../docs/feature-manifest.json'))
fs=m['features']
ids=",\n".join("\t"+f['feature_id'].replace('-','_') for f in fs)
open('Public/Harness/UmbrellaFeatureFlags.h','w').write(f"""#pragma once

#include "CoreMinimal.h"

/**
 * Feature flags, one per docs/feature-manifest.json record (generated from manifest {m['manifest_version']}
 * by docs/build/gen_feature_flags.py; regenerate, never hand-edit). Gameplay code checks IsFeatureEnabled(EFeatureId::X).
 * Defaults are the manifest default_enabled. The workbench (UMBRELLAELLA_WORKBENCH) may add per-run overrides later.
 */
enum class EFeatureId : uint8
{{
{ids},
	Count
}};

UMBRELLAELLA_API bool IsFeatureEnabled(EFeatureId Id);

/** The manifest_version the flag table was made from (smoke line manifest=). */
UMBRELLAELLA_API const TCHAR* GetFeatureManifestVersion();

/** Manifest Rule ID for a flag, e.g. TEXT("OWL-06"). */
UMBRELLAELLA_API const TCHAR* GetFeatureRuleId(EFeatureId Id);
""")
vals="\n".join(f"\t\t{{ EFeatureId::{f['feature_id'].replace('-', '_')}, {'true' if f['default_enabled'] else 'false'} }}, // bake: {f['feature_id']}.enabled" for f in fs)
names=",\n".join(f"\t\tTEXT(\"{f['feature_id']}\")" for f in fs)
open('Private/Harness/UmbrellaFeatureFlags.cpp','w').write(f"""#include "Harness/UmbrellaFeatureFlags.h"

namespace
{{
	struct FFeatureDefault
	{{
		EFeatureId Id;
		bool bEnabled;
	}};

	constexpr FFeatureDefault FeatureDefaults[] = {{
{vals}
	}};

	const TCHAR* const GFeatureRuleIds[] = {{
{names}
	}};

	static_assert(UE_ARRAY_COUNT(FeatureDefaults) == static_cast<int32>(EFeatureId::Count), "flag table out of sync with the manifest");
}}

bool IsFeatureEnabled(EFeatureId Id)
{{
	const int32 Index = static_cast<int32>(Id);
	return Index >= 0 && Index < static_cast<int32>(EFeatureId::Count) && FeatureDefaults[Index].bEnabled;
}}

const TCHAR* GetFeatureManifestVersion()
{{
	return TEXT("{m['manifest_version']}");
}}

const TCHAR* GetFeatureRuleId(EFeatureId Id)
{{
	const int32 Index = static_cast<int32>(Id);
	return (Index >= 0 && Index < static_cast<int32>(EFeatureId::Count)) ? GFeatureRuleIds[Index] : TEXT("none");
}}
""")
print(len(fs))
