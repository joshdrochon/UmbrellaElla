#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "AttackEmitterComponent.generated.h"

class UEnhancedInputComponent;
class UUmbrellaStateComponent;

/**
 * Attack Emitter: Small Blasts, unlimited, fixed right, only while dropping (shoot-fall). Fires through
 * AUmbrellaProjectile::Fire. No ammunition, no stored energy. Lane a.
 */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UAttackEmitterComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UAttackEmitterComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);

	/** Test seam: advance the emitter by a fixed delta without a world tick. */
	void StepEmitter(float DeltaSeconds);

	int32 GetShotsFired() const { return ShotsFired; }
	const FUmbrellaShotSpec& GetLastShot() const { return LastShot; }

protected:
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	void FireSmallBlast();

	UPROPERTY(Transient)
	TObjectPtr<UUmbrellaStateComponent> UmbrellaState;

	FUmbrellaShotSpec LastShot;
	float Countdown = 0.0f;
	int32 ShotsFired = 0;
};
