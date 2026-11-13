#pragma once

#include "CoreMinimal.h"

class UObject;
class UStaticMeshComponent;

/** Engine-cube placeholders for the Broken Mill (no imported art). */
namespace BrokenMillPlaceholder
{
	/** Put the engine cube on Visual, scaled to Size (X, Z; thin in depth) and tinted Color. */
	UMBRELLAELLA_API void ApplyCube(UStaticMeshComponent* Visual, UObject* Outer, const FVector2D& Size, const FLinearColor& Color, float CubeSize, float DepthScale);
}
