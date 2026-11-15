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
 * Wing-gust cue (the GDD's production cue: wing gather / load, then flap, readable direction and front; GDD line 375: the
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
	/** Clear margin around the gust puff sprite, as a share of its width: no ribbon piece is drawn within it (Josh, Nov 14). */
	static constexpr float PuffClearShare = 0.25f;
	/** Ribbon colour: ash blue #555e60 (art bible wind role, the Other Realm study ribbons; same as the wind currents). */
	static constexpr uint8 RibbonR = 0x55;
	static constexpr uint8 RibbonG = 0x5E;
	static constexpr uint8 RibbonB = 0x60;
	/**
	 * Ribbons in the study's look (visual_qa 22:15: straight ruled lines, an arrow glyph and an arc read as debug marks):
	 * wavy, tapered strands, thickest at the head that leads toward -X and thinning to a hair at the tail.
	 */
	static constexpr int32 WarningRibbons = 4;
	static constexpr int32 TravelRibbons = 5;
	/** Strand centres spread over this share of the band; bends swing up to WaveShare of the band (capped). */
	static constexpr float SpreadShare = 0.55f;
	static constexpr float WaveShare = 0.14f;
	static constexpr float MaxWave = 17.0f;
	static constexpr float Wavelength = 300.0f;
	/** Bends travel toward -X, the gust's direction (rad/s); a slower second bend lets strands cross and part. */
	static constexpr float WaveSpeed = 6.0f;
	static constexpr float DriftShare = 0.45f;
	static constexpr float DriftRate = 0.5f;
	/** Head thickness while the lane warns (the wings still gather) and while the gust travels. */
	static constexpr float WarningThick = 4.5f;
	static constexpr float TravelThick = 10.0f;
	static constexpr float TailThick = 0.8f;
	/** Heads stagger back from the front by this share of a ribbon's length (cycle of 3), so they never line up. */
	static constexpr float HeadStaggerShare = 0.07f;
	/** Travelling ribbon length (units) and the shortening per strand in the cycle of 3. */
	static constexpr float TravelLength = 420.0f;
	static constexpr float LengthStepShare = 0.2f;
	static constexpr float SegmentLength = 40.0f;
	static constexpr int32 MaxSegments = 24;
	static constexpr int32 MinSegments = 4;
	/** Per-strand phase Base + Step * strand and drift offset, so strands differ without randomness (captures repeat). */
	static constexpr float StrandPhaseStep = 1.7f;
	static constexpr float StrandPhaseBase = 0.4f;
	static constexpr float DriftStrandStep = 0.9f;
	/** Head profile: thickness rises from BluntTip of the head over the first 1/TipRise of the length, then tapers. */
	static constexpr float BluntTip = 0.45f;
	static constexpr float TipRise = 6.0f;
	/** Heads stagger and lengths step in a cycle of this many strands. */
	static constexpr int32 StaggerCycle = 3;
	/** Ribbon pool on the Keeper (largest frame: TravelRibbons x MaxSegments). */
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
	 * Gust ribbons for one frame (world X/Z), all inside the band (centre LaneStart.Y, BandWidth). Warning (bTravelling
	 * false): thin wavy strands draw out from LaneStart toward -X over WarningProgress 0..1, heads leading. Travel: thick
	 * strands whose heads sit at the front's leading edge (FrontX - FrontThickness/2), tails trailing toward +X. Pure.
	 */
	static void GustStrokes(const FVector2D& LaneStart, float LaneLength, float BandWidth, bool bTravelling, float WarningProgress,
		float FrontX, float FrontThickness, float Seconds, TArray<FKeeperGustStroke>& Out);

	/**
	 * Drops every stroke that reaches into the box at Centre with half-size Half (its thickness counted). The gust's white
	 * puff sprites (VFX_GustPuff / VFX_Gust, UmbrellaVfxDirectorSubsystem) sit on the gust front: no ribbon is drawn
	 * behind them (Josh 22:47: grey strokes behind the plume look tacky). Pure.
	 */
	static void ClipStrokesOutside(const FVector2D& Centre, const FVector2D& Half, TArray<FKeeperGustStroke>& Strokes);

	/** Half-size of the box around the gust front where no ribbon is drawn: the puff sprite's half-size plus PuffClearShare of its width. Pure. */
	static FVector2D PuffClearHalf();

	/** World X/Z box no ribbon may reach into around a drawn puff: its bounds grown by PuffClearShare of its width on every side (invalid for invalid bounds). Pure. */
	static FBox2D PuffClearBox(const FBox& PuffBounds);

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
	/** Drops every stroke within PuffClearBox of a live gust puff sprite (the effect director's GustWarning/Release/Travel/Expiry). */
	void ClipStrokesAroundLivePuffs(TArray<FKeeperGustStroke>& Strokes) const;
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
	/** The warning mark shows the painted streak (PaintedWarningArt); false: the flat-line fallback (no VFX material). */
	bool bTelegraphPainted = false;
	/** One bit per EKeeperPart whose slot art draws. */
	uint8 ArtDrawnParts = 0;
	float DepartureRemaining = 0.0f;
	float DepartureTotal = 0.0f;
};
