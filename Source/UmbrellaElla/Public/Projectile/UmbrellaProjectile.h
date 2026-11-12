#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "UmbrellaProjectile.generated.h"

class UStaticMeshComponent;
class UPrimitiveComponent;

/** Where a shot may land: player shots skip Ella, enemy shots only touch Ella (never the Keeper). Plain rule, tests call it. */
namespace ProjectileRules
{
	/** True when a shot of this kind may touch this actor. */
	UMBRELLAELLA_API bool CanShotTouch(EUmbrellaShotKind Kind, const AActor* Target);

	/** Collision channel a shot of this kind is traced as (PlayerShot or EnemyShot). */
	UMBRELLAELLA_API ECollisionChannel ShotChannel(EUmbrellaShotKind Kind);

	/** True when this component is a solid stop for the shot: it blocks the shot channel and its actor has no shot receiver. */
	UMBRELLAELLA_API bool IsSolidStop(EUmbrellaShotKind Kind, const UPrimitiveComponent* Component, bool bHasReceivers);

	/** Position after Dt seconds. Motion is in X/Z; Y stays on the projectile depth. */
	UMBRELLAELLA_API FVector Advance(const FVector& Position, const FVector& Velocity, float Dt);
}

/** Projectile Service actor (lane c): spawn, motion, collision report, lifetime. */
UCLASS()
class UMBRELLAELLA_API AUmbrellaProjectile : public AActor
{
	GENERATED_BODY()

public:
	AUmbrellaProjectile();

	/** The one way to fire a shot. Returns nullptr when the world refuses the spawn. */
	static AUmbrellaProjectile* Fire(UWorld* World, const FUmbrellaShotSpec& Spec);

	const FUmbrellaShotSpec& GetSpec() const { return Spec; }

	/** Seconds of life left. */
	float GetLifetimeRemaining() const { return LifetimeRemaining; }

	/** One step: move, resolve contacts, count down the lifetime. Tick calls it; tests call it with a fixed Dt. */
	void AdvanceShot(float Dt);

	virtual void Tick(float DeltaSeconds) override;

private:
	/** Find what the shot overlaps along From..To and hand the shot to the receivers. Destroys the shot when consumed. */
	void ResolveContacts(const FVector& From, const FVector& To);

	void ApplyPlaceholderVisual();

	UPROPERTY()
	FUmbrellaShotSpec Spec;

	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> Visual;

	float LifetimeRemaining = 0.0f;
};
