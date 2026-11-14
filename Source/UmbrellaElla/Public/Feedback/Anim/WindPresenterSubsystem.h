#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "WindPresenterSubsystem.generated.h"

class AWindCurrent;
class UStaticMesh;
class UStaticMeshComponent;

namespace UmbrellaWindPresenterConst
{
	/** Slot ids the current used to draw as picture cards (the framed field, the lines, the gust sheet). Not drawn. */
	static const TCHAR* const FieldVisual = TEXT("wind:current-field");
	static const TCHAR* const LinesVisual = TEXT("wind:decor-lines");
	static const TCHAR* const GustVisual = TEXT("vfx-sheet:VFX_Gust");
	/** Ribbon colour: ash blue #555e60 (art bible, wind role; measured on the Other Realm study ribbons). */
	static constexpr uint8 RibbonR = 0x55;
	static constexpr uint8 RibbonG = 0x5E;
	static constexpr uint8 RibbonB = 0x60;
	/** Strands in one current: one per this many units of its width, between Min and Max. */
	static constexpr float StrandSpacing = 70.0f;
	static constexpr int32 MinStrands = 2;
	static constexpr int32 MaxStrands = 5;
	/** Segments per strand: one per this many units of its length, between Min and Max. */
	static constexpr float SegmentLength = 45.0f;
	static constexpr int32 MinSegments = 8;
	static constexpr int32 MaxSegments = 28;
	/** Strand thickness at its middle, in world units (1 unit is about 1 pixel at 1920 wide); the ends taper to ThinEnd. */
	static constexpr float ThickMiddle = 4.0f;
	static constexpr float ThinEnd = 0.6f;
	/** Strands sit in the middle share of the current's width. */
	static constexpr float BandShare = 0.7f;
	/** Wave: one bend per Wavelength units of length, swing up to AmplitudeShare of the width (capped at MaxAmplitude). */
	static constexpr float Wavelength = 520.0f;
	static constexpr float AmplitudeShare = 0.14f;
	static constexpr float MaxAmplitude = 46.0f;
	/** Bends travel along the flow at this many radians per second. */
	static constexpr float WaveSpeed = 1.6f;
	/** Per-strand phase: Base + Step * strand, so strands differ without randomness (captures repeat). */
	static constexpr float StrandPhaseStep = 1.7f;
	static constexpr float StrandPhaseBase = 0.4f;
	/** A second, slower bend (DriftShare of the main swing, DriftRate of its frequency) so strands cross and part. */
	static constexpr float DriftShare = 0.45f;
	static constexpr float DriftRate = 0.5f;
	static constexpr float DriftStrandStep = 0.9f;
	/** Strand widths repeat every StrandScaleCycle strands: full, thin, middle. */
	static constexpr int32 StrandScaleCycle = 3;
	static constexpr float StrandThinScale = 0.55f;
	static constexpr float StrandMidScale = 0.8f;
	/** Ribbons sit this far in front of the current's (hidden) card, toward the camera. */
	static constexpr float RibbonLift = 2.0f;
	/** Plane edge of the engine plane, in units. */
	static constexpr float PlaneEdge = 100.0f;
}

/**
 * Draws wind currents as thin ash-blue ribbons in code (visualqa, Josh 16:05: wind is never a box, panel or card).
 * The current's colour card stays sized and coloured for the field rules, but is hidden in game; the ribbons follow
 * its box and flow direction and their bends drift with game time. Visual only: no collision.
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

	/** Strand count for a current Width units across. Pure. */
	static int32 StrandCount(float Width);

	/** Segment count for a strand Length units long. Pure. */
	static int32 SegmentCount(float Length);

	/**
	 * Point Index (0..Segments) of strand Strand of Strands, in the current's flow frame: X along the flow from
	 * -Length/2 to +Length/2, Y across the flow. Pure.
	 */
	static FVector2D StrandPoint(float Length, float Width, int32 Strand, int32 Strands, int32 Index, int32 Segments, float Seconds);

	/** Thickness of a strand at fraction T (0..1) of its length. Pure. */
	static float StrandThickness(int32 Strand, float T);

	/** The ribbon segments drawn on a current (empty before its first tick). */
	static TArray<UStaticMeshComponent*> RibbonsOf(const AWindCurrent* Wind);

	/** Build or move the ribbons of one current to game time Seconds (tests call it directly). */
	void DrawRibbons(AWindCurrent* Wind, float Seconds);

	/** How often the presenter loaded the plane mesh or searched a current's components (cached after the first). */
	int32 PlaneLoadCount() const { return PlaneLoads; }
	int32 RibbonSearchCount() const { return RibbonSearches; }

private:
	void HandleActorSpawned(AActor* Actor);
	UStaticMesh* GetPlane();
	/** The current's ribbons, from the cache; searched on the current's components only when the cache is stale. */
	TArray<UStaticMeshComponent*> CachedRibbons(AWindCurrent* Wind);

	UPROPERTY(Transient)
	TObjectPtr<UStaticMesh> Plane;
	TMap<TWeakObjectPtr<AWindCurrent>, TArray<TWeakObjectPtr<UStaticMeshComponent>>> RibbonCache;
	int32 PlaneLoads = 0;
	int32 RibbonSearches = 0;
	FDelegateHandle SpawnHandle;
	TArray<TWeakObjectPtr<AWindCurrent>> Winds;
};
