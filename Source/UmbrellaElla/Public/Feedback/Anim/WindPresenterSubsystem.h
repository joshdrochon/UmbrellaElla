#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "WindPresenterSubsystem.generated.h"

class AWindCurrent;
class UStaticMeshComponent;
class UTexture2D;
enum class EArtSlotDraw : uint8;

namespace UmbrellaWindPresenterConst
{
	/** Slot ids: the field picture, the streak lines over it, and the animated gust sheet over both. */
	static const TCHAR* const FieldVisual = TEXT("wind:current-field");
	static const TCHAR* const LinesVisual = TEXT("wind:decor-lines");
	static const TCHAR* const GustVisual = TEXT("vfx-sheet:VFX_Gust");
	/** Units each overlay sits in front of the field (toward the camera). */
	static constexpr float LinesLift = 5.0f;
	static constexpr float GustLift = 10.0f;
	/** Overlay thickness in the card's depth axis; the plane ignores it, the box scale just needs one. */
	static constexpr double OverlayDepth = 0.1;
	/** Gust sheet speed, frames per second. */
	static constexpr float GustFps = 12.0f;
}

/**
 * Draws the painted wind art on wind currents: the field slot replaces the colour card (the card stays when no asset
 * exists), and the streak lines and animated gust sheet are overlays that exist only when their asset does. Keeps the
 * art when the current refreshes its field. Visual only: no collision. Visuals lane.
 */
UCLASS()
class UMBRELLAELLA_API UWindPresenterSubsystem final : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void PostInitialize() override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** Draw a picture for a slot on a wind current (tests pass a transient texture). Field replaces the card; the others add an overlay. */
	EArtSlotDraw ShowArt(AWindCurrent* Wind, const FString& VisualId, UTexture2D* Texture);

	/** The overlay component for a slot id on a current, or null. */
	static UStaticMeshComponent* FindOverlay(const AWindCurrent* Wind, const FString& VisualId);

	/** Gust sheet frame after Seconds of game time. Pure. */
	static int32 GustFrameAt(float Seconds, int32 Frames);

private:
	void HandleActorSpawned(AActor* Actor);
	/** Re-assert the field art if a refresh replaced it. */
	void Follow(AWindCurrent* Wind);

	struct FWindEntry
	{
		TWeakObjectPtr<AWindCurrent> Wind;
		bool bLoaded = false;
		TWeakObjectPtr<UTexture2D> FieldTexture;
	};
	FDelegateHandle SpawnHandle;
	TArray<FWindEntry> Winds;
};
