#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "KeeperPresenterSubsystem.generated.h"

class AActor;
class UStaticMeshComponent;
class UTexture2D;
enum class EArtSlotDraw : uint8;

namespace UmbrellaKeeperPresenterConst
{
	/** Stand-in box scale for the Keeper: wide body, flat card. */
	static const FVector StandInScale(6.0, 0.1, 6.0);
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
	};
}

/**
 * Shows a visible neutral stand-in on every spawned Keeper of Time until flipbook art exists. Reads nothing from
 * gameplay, adds no collision, and sits on the Keeper depth layer. Never gameplay authority. Visuals lane.
 */
UCLASS()
class UMBRELLAELLA_API UKeeperPresenterSubsystem final : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void PostInitialize() override;
	virtual void Deinitialize() override;

	/** Attach the stand-in to a Keeper (safe to call twice). The presented count tells whether one was added. */
	void ShowStandIn(AActor* Keeper);

	int32 GetPresentedCount() const { return PresentedCount; }

	/** Swap the stand-in on a Keeper for a picture (the slot load does this; tests pass a transient texture). */
	EArtSlotDraw ShowArt(AActor* Keeper, UTexture2D* Texture);

	/** Draw one part slot (a PartLayers visual) as a layer at the body's footprint (null = load its asset). Refuses a part already drawn. */
	EArtSlotDraw ShowPartArt(AActor* Keeper, const FString& VisualId, UTexture2D* Texture);

	/** The part layer component for a slot id on a Keeper, or null. */
	static UStaticMeshComponent* FindPart(const AActor* Keeper, const FString& VisualId);

private:
	void HandleActorSpawned(AActor* Actor);
	FDelegateHandle SpawnHandle;
	int32 PresentedCount = 0;
};
