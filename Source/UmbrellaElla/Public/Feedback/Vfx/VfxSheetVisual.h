#pragma once

#include "CoreMinimal.h"

class AActor;
class UPointLightComponent;
class UStaticMeshComponent;
struct FVfxArtRow;
struct FVfxLightPlan;

/**
 * Builds what an effect looks like: a camera-facing quad showing the effect's sheet (one row of frames, stepped by
 * a material parameter), or a plain stand-in shape while the sheet is not imported. No collision, ever.
 */
namespace VfxSheetVisual
{
	/** The engine plane and sphere are this many units across. */
	static constexpr float ShapeEdge = 100.0f;
	/** A stand-in is this fraction of the effect size, so it never looks bigger than the art will. */
	static constexpr float StandInFraction = 0.5f;

	/** Make the effect's visual the root of Owner. Size is the quad's world width and height. */
	UMBRELLAELLA_API UStaticMeshComponent* Build(AActor* Owner, const FVfxArtRow& Row, const FVector2D& Size);

	/** Resize a built visual (beam length, umbra width). */
	UMBRELLAELLA_API void Resize(UStaticMeshComponent* Visual, const FVector2D& Size);

	/** True when the visual shows the imported sheet, false for the stand-in. */
	UMBRELLAELLA_API bool HasArt(const UStaticMeshComponent* Visual);

	UMBRELLAELLA_API void SetFrame(UStaticMeshComponent* Visual, int32 Frame);
	UMBRELLAELLA_API void SetOpacity(UStaticMeshComponent* Visual, float Opacity);

	/** The effect's point light, or nullptr when the plan has none. */
	UMBRELLAELLA_API UPointLightComponent* AddLight(AActor* Owner, const FVfxLightPlan& Plan);

	/** The effect's additive light overlay, or nullptr when the plan has none or its material is not imported. */
	UMBRELLAELLA_API UStaticMeshComponent* AddSpill(AActor* Owner, const FVfxLightPlan& Plan);

	/** Rotation that turns the engine plane to face the play camera with the sheet upright. */
	UMBRELLAELLA_API FRotator FacingCamera();
}
