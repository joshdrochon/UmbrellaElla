#pragma once

#include "CoreMinimal.h"
#include "Feedback/Art/FigureScale.h"
#include "Subsystems/WorldSubsystem.h"
#include "KeeperPresenterSubsystem.generated.h"

class AActor;
struct FUmbrellaEvent;
class AKeeperOfTime;
class UStaticMeshComponent;
class UTexture2D;
struct FArtSlotRow;
enum class EArtSlotDraw : uint8;

/** How a grid sheet on the Keeper body plays. */
enum class EKeeperGridPlayback : uint8
{
	/** The art-slot material samples only the top row: play row 0 forward and back so the loop never jumps. */
	TopRowPingPong,
	/** Every cell, row by row, as a loop (needs the material's row offset). */
	AllCells
};

namespace UmbrellaKeeperPresenterConst
{
	/** Stand-in box scale for the Keeper: wide body, flat card. */
	static const FVector StandInScale(6.0 * UmbrellaFigureScale::Keeper, 0.1, 6.0 * UmbrellaFigureScale::Keeper);   // D-new-character-scale
	/** Part slots that draw as layers over the body, back to front, with their depth offset (Y units from the body; negative = behind). */
	struct FKeeperPartLayer
	{
		const TCHAR* Visual;
		float DepthOffset;
	};
	static constexpr float PartStep = 1.0f;
	static const FKeeperPartLayer PartLayers[] = {
		{ TEXT("keeper:wings-gust-wear"), -3.0f * PartStep },
		{ TEXT("keeper:mechanism-rear"), -2.0f * PartStep },
		{ TEXT("keeper:mechanism-middle"), -1.0f * PartStep },
		{ TEXT("keeper:mechanism-front"), 1.0f * PartStep },
		{ TEXT("keeper:clock-cover-glass-hands"), 2.0f * PartStep },
		{ TEXT("keeper:talon-empty-and-closed"), 3.0f * PartStep },
		{ TEXT("keeper:part-masks-7-6-4-0"), 4.0f * PartStep },
		{ TEXT("keeper:living-departure"), 5.0f * PartStep },
	};
	/** Body idle grid playback rate: the cut's sidecar fps (pipeline/art/proof/artkeeper/keeper-idle/fixed/Keeper_idle_N24_grid.sprite.json). */
	static constexpr float IdleFps = 6.4f;
	// Smallest cell aspect the body scale divides by (guards a zero-size texture).
	static constexpr float MinBodyAspect = 0.01f;
	/** M_ArtSlot draws only the top row of a grid today (docs/build/requests/artkeeper.md Update 5); AllCells once it offsets rows. */
	static constexpr EKeeperGridPlayback IdlePlayback = EKeeperGridPlayback::TopRowPingPong;
	/** State layers: hidden until their state starts (a part is destroyed; the Keeper departs). */
	static const TCHAR* const MaskVisual = TEXT("keeper:part-masks-7-6-4-0");
	static const TCHAR* const DepartureVisual = TEXT("keeper:living-departure");
}

/**
 * Shows a visible neutral stand-in on every spawned Keeper of Time until flipbook art exists. Reads nothing from
 * gameplay, adds no collision, and sits on the Keeper depth layer. Never gameplay authority. Visuals lane.
 */
UCLASS()
class UMBRELLAELLA_API UKeeperPresenterSubsystem final : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void PostInitialize() override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual bool IsTickableInEditor() const override { return false; }

	/** Show or hide a state layer on every Keeper: the damage masks once a part is destroyed, the departure while it leaves. */
	void ShowStateLayer(AActor* Keeper, const FString& VisualId);
	void HideStateLayer(AActor* Keeper, const FString& VisualId);
	bool IsShowingMasks() const { return bMasksShown; }

	/** Attach the stand-in to a Keeper (safe to call twice). The presented count tells whether one was added. */
	void ShowStandIn(AActor* Keeper);

	int32 GetPresentedCount() const { return PresentedCount; }

	/** Swap the stand-in on a Keeper for a picture (the slot load does this; tests pass a transient texture). */
	EArtSlotDraw ShowArt(AActor* Keeper, UTexture2D* Texture);

	/** Draw one part slot (a PartLayers visual) as a layer at the body's footprint (null = load its asset). Refuses a part already drawn. */
	EArtSlotDraw ShowPartArt(AActor* Keeper, const FString& VisualId, UTexture2D* Texture);

	/** True when a part picture is an unpassed _PH stand-in and the Keeper body already draws art: the part layer is skipped. Pure read. */
	static bool ShouldPartPictureYieldToBody(const UTexture2D* Picture, const AActor* Keeper);

	/** The part layer component for a slot id on a Keeper, or null. */
	static UStaticMeshComponent* FindPart(const AActor* Keeper, const FString& VisualId);

	/** True when any Keeper slot draws on this Keeper: the body picture or any part layer. Pure read. */
	static bool HasKeeperArt(const AActor* Keeper);

	/**
	 * The arena's graybox Keeper square hides while any tracked Keeper draws slot art and shows when none does.
	 * Runs on a Keeper spawn, draw or destroy, and in Tick only when a part layer's loss changed the answer.
	 */
	void SyncArenaStandIn();

	/** Box scale for the body picture: StandInScale's width, height from one sheet cell's aspect (no squash). Pure. */
	static FVector BodyArtScaleFor(const UTexture2D* Texture, const FArtSlotRow& Row);

	/** Sheet cell shown at Seconds for a Cols x Rows body grid played at Fps. Pure. */
	static int32 IdleFrameAt(double Seconds, float Fps, int32 Cols, int32 Rows, EKeeperGridPlayback Playback);

	/** True when any tracked Keeper draws slot art. Pure read. */
	bool HasAnyKeeperArt() const;

private:
	void HandleActorSpawned(AActor* Actor);
	FDelegateHandle SpawnHandle;
	void HandleActorDestroyed(AActor* Actor);
	FDelegateHandle DestroyHandle;
	/** Set each part's art cover to what draws now (body picture, live part layers); a part whose art is gone shows its cube again. */
	void SyncPartCover(AKeeperOfTime* Owl);
	/** Step the body grid's frame from world time (no gameplay read). */
	void PlayIdle(AActor* Keeper) const;
	/** Last value written to the arenas by SyncArenaStandIn. */
	bool bArenaArtShown = false;
	void HandlePartDestroyed(const FUmbrellaEvent& Event);
	FDelegateHandle PartHandle;
	void HandleRestart(const FUmbrellaEvent& Event);
	FDelegateHandle RestartHandle;
	/** Single mask layer: shown while any part is destroyed since the last spawn or retry (an approximation of the 7/6/4/0 steps). */
	int32 PartsDestroyed = 0;
	TArray<TWeakObjectPtr<AActor>> Keepers;
	bool bMasksShown = false;
	int32 PresentedCount = 0;
};
