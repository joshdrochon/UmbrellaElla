#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "KeeperPresenterSubsystem.generated.h"

class AActor;
class UTexture2D;
enum class EArtSlotDraw : uint8;

namespace UmbrellaKeeperPresenterConst
{
	/** Stand-in box scale for the Keeper: wide body, flat card. */
	static const FVector StandInScale(6.0, 0.1, 6.0);
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

private:
	void HandleActorSpawned(AActor* Actor);
	FDelegateHandle SpawnHandle;
	int32 PresentedCount = 0;
};
