#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "HarnessSubsystem.generated.h"

/** Card 0.3: the harness seam the smoke hook reads (pipeline/unreal-rules.md, Smoke hook contract). Card 0.27 fills the
 *  flag table and GManifestVersion in Harness/; the hook enumerates them, so no card edits Smoke/ for a new flag. */
enum class EFeatureId : uint8
{
	Count
};

extern const TCHAR* GManifestVersion;

UCLASS()
class UMBRELLAELLA_API UHarnessSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	static const UHarnessSubsystem* Get(const UWorld* World);

	bool IsFeatureEnabled(EFeatureId Id) const;

	/** Calls Visit once per flag-table entry with its ID and its manifest name. */
	void ForEachFlag(TFunctionRef<void(EFeatureId, const FString&)> Visit) const;

	const TCHAR* ManifestVersion() const { return GManifestVersion; }
};
