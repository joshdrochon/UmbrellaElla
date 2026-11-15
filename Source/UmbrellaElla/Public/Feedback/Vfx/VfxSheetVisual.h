#pragma once

#include "CoreMinimal.h"

class AActor;
class UPointLightComponent;
class UStaticMeshComponent;
class UTexture2D;
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

	/** Turn Mesh into a plane showing Texture (one cell) with the VFX sheet material; HasArt(Mesh) tells whether it took (material or plane missing: unchanged). */
	UMBRELLAELLA_API void ShowTexture(UStaticMeshComponent* Mesh, UTexture2D* Texture);

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

	/**
	 * FacingCamera for an effect that travels along world X. Sheets are drawn travelling +X (front on the right): a
	 * negative TravelX turns the quad 180 degrees in the screen plane, so the front leads (lead order, Nov 13 21:49).
	 */
	UMBRELLAELLA_API FRotator FacingCameraToward(float TravelX);

	/**
	 * World X direction a sheet's art is drawn travelling: +1 (front on the right) for the wind gust sheets VFX_Gust and
	 * VFX_GustPuff, 0 for a sheet with no drawn direction (never turned). A new directional sheet adds its row here.
	 */
	UMBRELLAELLA_API float DrawnTravelX(const FString& Sheet);

	/**
	 * FacingCamera for a sheet drawn travelling DrawnX placed on an effect travelling TravelX: a 180 degree screen-plane
	 * turn only when both are set and opposed; otherwise the plain upright facing.
	 */
	UMBRELLAELLA_API FRotator FacingCameraForDrawn(float DrawnX, float TravelX);
}
