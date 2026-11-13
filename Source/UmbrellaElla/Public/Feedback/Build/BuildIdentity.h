#pragma once

#include "CoreMinimal.h"
#include "BuildIdentity.generated.h"

namespace UmbrellaBuildConst
{
	/** Output height the units-per-pixel figure is qualified at. */
	static constexpr float QualifiedOutputHeight = 1080.0f;
}

/** The build identity record (revision, profile, platform, screen/camera scale, packaging, asset manifest). Lane e. */
USTRUCT()
struct UMBRELLAELLA_API FBuildIdentity
{
	GENERATED_BODY()

	UPROPERTY()
	FString EngineVersion;

	UPROPERTY()
	FString Configuration;

	UPROPERTY()
	FString Platform;

	/** World units per screen pixel at the fixed camera and 1080p output (units are not pixels). */
	UPROPERTY()
	float UnitsPerPixel = 0.0f;

	UPROPERTY()
	float CameraAspectRatio = 0.0f;

	UPROPERTY()
	FString Packaging;

	/** Source revision compiled in (UMBRELLAELLA_BUILD_COMMIT, "unknown" outside a stamped build). */
	UPROPERTY()
	FString Revision;

	/** asset_manifest= value from the package's BUILD_INFO.txt, "unknown" when absent. */
	UPROPERTY()
	FString AssetManifest;

	/** Plain text record, one key=value per line. */
	FString ToText() const;

	/** The value of key= on its own line in BUILD_INFO text; empty when the key is missing. */
	static FString ParseBuildInfoValue(const FString& Text, const FString& Key);

	/** Fill from the running build and the arena tuning. */
	static FBuildIdentity Capture();
};
