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

	/** Plain text record, one key=value per line. */
	FString ToText() const;

	/** Fill from the running build and the arena tuning. */
	static FBuildIdentity Capture();
};
