#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Core/UmbrellaEvent.h"
#include "Health/HealthModel.h"
#include "Projectile/UmbrellaShotReceiver.h"
#include "UmbrellaHealthComponent.generated.h"

class UEnhancedInputComponent;

/** Did a hit change health? Blocked: protected, defeated, or reduced to nothing. */
UENUM()
enum class EHitResult : uint8
{
	Blocked,
	Landed
};

/**
 * Health/Condition: hits, lives, damage scale, healing; broadcasts PlayerDefeated. Lane c.
 * INV-1: Active health stays in 0..Capacity and Lives in 0..MaxLives.
 * INV-2: PlayerDefeated is broadcast once; after it no hit or heal changes anything (no revival).
 * INV-3: this component never moves Ella and never reloads anything.
 */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UUmbrellaHealthComponent : public UActorComponent, public IUmbrellaShotReceiver
{
	GENERATED_BODY()

public:
	UUmbrellaHealthComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);

	virtual EUmbrellaShotResult ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation) override;

	/** Take raw damage now (world clock for the post-hit window). Returns Landed when health changed. */
	EHitResult TakeHit(float RawDamage, FName SourceId);

	/** Same, with the clock given (tests). */
	EHitResult TakeHitAt(float RawDamage, FName SourceId, double NowSeconds);

	/** Heal one absorbed yellow at the current recovery rank. Returns what changed. */
	FHealthHealOutcome HealFromYellow(FName SourceId);

	/** Death or checkpoint retry: exactly the max lives and a full active life at the current capacity. No other state moves. */
	void ResetForRetry();

	/** Capacity and lives tracks (progression). Keeps the current state valid. */
	void SetCapacity(float NewCapacity, int32 NewMaxLives);

	void SetDefenseRank(int32 Rank);
	void SetRecoveryRank(int32 Rank);

	const FHealthState& GetState() const { return State; }
	float GetLiftMultiplier() const;
	int32 GetDefenseRank() const { return DefenseRank; }
	int32 GetRecoveryRank() const { return RecoveryRank; }

	/** Seconds of post-hit protection left at the given clock. */
	float GetProtectionRemaining(double NowSeconds) const;

protected:
	virtual void BeginPlay() override;

private:
	void Broadcast(EUmbrellaEventType Type, FName Source, FName Detail, float Value, int32 Amount) const;
	void BroadcastHealth(FName Source, FName Detail) const;

	FHealthState State;
	int32 DefenseRank = 0;
	int32 RecoveryRank = 0;
	double ProtectedUntil = -1.0;
};
