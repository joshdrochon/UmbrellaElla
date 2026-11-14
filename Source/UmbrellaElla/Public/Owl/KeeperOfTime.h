#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Encounter/KeeperFightModel.h"
#include "KeeperOfTime.generated.h"

class UKeeperPartComponent;
class UStaticMeshComponent;

/** Whether a part shows a state its static slot art cannot (broken, clock open): then its cube shows even under art. */
enum class EKeeperCubeState : uint8
{
	Default,
	StateCue,
};

/** One straight piece of a drawn gust ribbon: ends in world X/Z and its thickness in units (1 unit ~ 1 px at 1920). */
struct FKeeperGustStroke
{
	FVector2D A = FVector2D::ZeroVector;
	FVector2D B = FVector2D::ZeroVector;
	float Thick = 1.0f;
};

/**
 * Wing-gust cue (OWL-15 production cue: wing gather / load, then flap, readable direction and front; GDD line 375: the
 * gust's own animation and VFX). Presentation only: the cue reads the model's stage and timers and never changes them.
 */
namespace KeeperWingGustConst
{
	/** The owl clip strip (T_Keeper_WingGust_PH, one row): gather cells, then flap cells, then recover cells. */
	static constexpr int32 GatherCells = 7;
	static constexpr int32 FlapCells = 4;
	static constexpr int32 RecoverCells = 3;
	static constexpr int32 Cells = GatherCells + FlapCells + RecoverCells;
	/** Share of the warning spent gathering; the flap starts in the warning's last share and lands on the launch. */
	static constexpr float GatherShare = 0.7f;
	/** The flap's downstroke runs on this long into the gust's travel (s), then the wings recover over RecoverSeconds. */
	static constexpr float FlapAfterLaunchSeconds = 0.25f;
	static constexpr float RecoverSeconds = 0.45f;
	/** Ribbon colour: ash blue #555e60 (art bible wind role, the Other Realm study ribbons; same as the wind currents). */
	static constexpr uint8 RibbonR = 0x55;
	static constexpr uint8 RibbonG = 0x5E;
	static constexpr uint8 RibbonB = 0x60;
	/** Warning lane: thin edge strands at +-EdgeShare of the band, inner strands at +-InnerShare, an arrow head at the reach. */
	static constexpr float EdgeShare = 0.45f;
	static constexpr float InnerShare = 0.15f;
	static constexpr float EdgeThick = 3.0f;
	static constexpr float InnerThick = 5.0f;
	static constexpr float ArrowThick = 7.0f;
	/** Arrow head arms reach back this share of the band width. */
	static constexpr float ArrowBackShare = 0.35f;
	/** Travelling gust: a bowed front (apex ahead by FrontBulgeShare of the front thickness), trailing strands behind it. */
	static constexpr float FrontThick = 11.0f;
	static constexpr int32 FrontSegments = 8;
	static constexpr float FrontBulgeShare = 0.5f;
	static constexpr float TrailLength = 360.0f;
	static constexpr int32 TrailStrands = 4;
	static constexpr float TrailThickFront = 8.0f;
	static constexpr float TrailThickTail = 1.5f;
	/** Strand bends: amplitude (units), wavelength (units) and travel (rad/s, toward the gust's direction). */
	static constexpr float WaveAmplitude = 6.0f;
	static constexpr float Wavelength = 260.0f;
	static constexpr float WaveSpeed = 7.0f;
	static constexpr float SegmentLength = 45.0f;
	static constexpr int32 MaxSegments = 24;
	/** Ribbon pool on the Keeper (largest frame: 8 front + 4 x 24 trail + 2 x 24 lane ahead fits). */
	static constexpr int32 PoolSize = 160;
	/** Ribbons sit this far in front of the Keeper layer, toward the camera (+Y). */
	static constexpr float RibbonLift = 5.0f;
}

/**
 * The Keeper of Time boss actor: wings, three hanging mechanisms, clock and eye. Spawned by the Encounter Director.
 * It holds the hit regions and a placeholder look made from engine primitives; every rule lives in FKeeperFightModel.
 * The director calls Refresh each tick so hit regions, heads and telegraphs follow the model, never an animation.
 */
UCLASS()
class UMBRELLAELLA_API AKeeperOfTime : public AActor
{
	GENERATED_BODY()

public:
	AKeeperOfTime();

	virtual void BeginPlay() override;

	/** Make the hit regions and the placeholder look match the model. */
	void Refresh(const FKeeperFightModel& Model, float TimeSeconds);

	/** A physical move started its warning: show the locked lane or target. */
	void ShowTelegraph(const FKeeperCommand& Command);

	/** Remove the visible gust front and telegraph marker. */
	void ClearGusts();

	/** Wing-gust strip cell to show now, or INDEX_NONE for the idle loop (set by Refresh; the presenter plays it). */
	int32 GetWingGustCell() const { return WingGustCell; }

	/**
	 * Wing-gust strip cell for a model state, or INDEX_NONE. Gather over the first GatherShare of the gust warning,
	 * flap over the rest of the warning and the first FlapAfterLaunchSeconds of the travel, then recover. Pure.
	 */
	static int32 WingGustCellFor(EKeeperPhysical Physical, EKeeperStage Stage, float StageRemaining, bool bWingsAlive, const FKeeperTuning& T);

	/**
	 * Gust ribbons for one frame (world X/Z). Warning (bTravelling false): the locked lane draws out from LaneStart
	 * toward -X over WarningProgress 0..1, thin edge and inner strands with an arrow head at the reach. Travel: a bowed
	 * front at FrontX, thick strands trailing behind it, thin edge lines over the lane still ahead. Pure.
	 */
	static void GustStrokes(const FVector2D& LaneStart, float LaneLength, float BandWidth, bool bTravelling, float WarningProgress,
		float FrontX, float FrontThickness, float Seconds, TArray<FKeeperGustStroke>& Out);

	/** Gust ribbon pieces drawn now (visible pool entries). Tests read it. */
	int32 GetVisibleGustRibbonCount() const;
	/** The gust ribbon pool (created on first use). Tests read it. */
	const TArray<TObjectPtr<UStaticMeshComponent>>& GetGustRibbons() const { return GustRibbons; }

	/** Presentation only: rise and fade away alive over Seconds. */
	void BeginDeparture(float Seconds);

	/** The hit region of a body part (nullptr for Count). Tests read it. */
	UKeeperPartComponent* GetPartComponent(EKeeperPart Part) const;

	/** The moving head of a mechanism cast. */
	UKeeperPartComponent* GetHeadComponent(EKeeperPart Part) const;

	bool IsDeparting() const { return DepartureRemaining > 0.0f; }

	/**
	 * Presentation only: slot art now draws this part (the body sprite or the part's own layer), so its stand-in cube
	 * hides while the part is in its default state. The art is static, so a broken wing or mechanism and an open clock
	 * still show their coloured cube as the state cue. Hit regions are unchanged.
	 */
	void MarkPartArtDrawn(EKeeperPart Part);
	void ClearPartArtDrawn(EKeeperPart Part);
	bool IsPartArtDrawn(EKeeperPart Part) const;

	/** The stand-in cube for a body part (nullptr for parts without one). Tests read it. */
	UStaticMeshComponent* GetStandInVisual(EKeeperPart Part) const;

	virtual void Tick(float DeltaSeconds) override;

private:
	UKeeperPartComponent* MakePart(FName Name, EKeeperPart Part, const FVector2D& Offset, const FVector2D& HalfExtent);
	UStaticMeshComponent* MakeVisual(FName Name);
	void PlaceVisual(UStaticMeshComponent* Visual, const FVector2D& Centre, const FVector2D& HalfExtent, const FLinearColor& Colour, EKeeperCubeState State = EKeeperCubeState::Default);
	void HideVisual(UStaticMeshComponent* Visual);
	FVector ToWorld(const FVector2D& Position) const;
	/** Draw Strokes with the ribbon pool (creating it on first use) and hide the rest. */
	void DrawGustRibbons(const TArray<FKeeperGustStroke>& Strokes);
	bool IsCoveredByArt(const UStaticMeshComponent* Visual) const;

	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> WingsPart;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> ClockPart;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> EyePart;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> FrontPart;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> MiddlePart;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> RearPart;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> FrontHead;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> MiddleHead;
	UPROPERTY()
	TObjectPtr<UKeeperPartComponent> RearHead;

	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> WingsVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> ClockVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> EyeVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> FrontVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> MiddleVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> RearVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> HeadVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> TalonVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> GustVisual;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> TelegraphVisual;

	UPROPERTY()
	TArray<TObjectPtr<UStaticMeshComponent>> GustRibbons;
	/** Gust lane start (front X at launch, band centre Z), stored by ShowTelegraph. */
	FVector2D GustLaneStart = FVector2D::ZeroVector;
	int32 WingGustCell = INDEX_NONE;

	FVector2D AnchorXZ = FVector2D::ZeroVector;
	FVector2D TelegraphFrom = FVector2D::ZeroVector;
	FVector2D TelegraphTo = FVector2D::ZeroVector;
	bool bTelegraphShown = false;
	/** One bit per EKeeperPart whose slot art draws. */
	uint8 ArtDrawnParts = 0;
	float DepartureRemaining = 0.0f;
	float DepartureTotal = 0.0f;
};
