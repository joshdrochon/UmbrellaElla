#pragma once

#include "CoreMinimal.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "Subsystems/WorldSubsystem.h"
#include "ShotPresenterSubsystem.generated.h"

class AUmbrellaProjectile;
class UStaticMeshComponent;
class UTexture2D;
enum class EArtSlotDraw : uint8;

/**
 * Draws the shot art slots (shot:gold, shot:red, shot:yellow) on projectiles. The Projectile Service keeps its
 * placeholder sphere; this presenter swaps it for the picture once the sphere is set, keeps the same footprint, and
 * leaves the sphere when no asset exists. Visual only: no collision, never gameplay authority. Visuals lane.
 */
UCLASS()
class UMBRELLAELLA_API UShotPresenterSubsystem final : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void PostInitialize() override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** Art slot id for a shot kind, e.g. "shot:red". Pure. */
	static FString VisualIdFor(EUmbrellaShotKind Kind);

	/** Draw a picture on a shot (the slot load does this on tick; tests pass a transient texture). */
	EArtSlotDraw ShowArt(AUmbrellaProjectile* Shot, UTexture2D* Texture);

	/** Shots drawn with art so far. */
	int32 GetPresentedCount() const { return PresentedCount; }

private:
	void HandleActorSpawned(AActor* Actor);
	FDelegateHandle SpawnHandle;
	TArray<TWeakObjectPtr<AUmbrellaProjectile>> Shots;
	int32 PresentedCount = 0;
};
