#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Trap/TrapRules.h"
#include "Trap/TrapTuning.h"
#include "UmbrellaTrap.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

/**
 * One trap: air mill, timed shutter, hostile bellows or roof teeth. Hurts a pawn that overlaps its Hazard box while
 * the trap is in a damaging phase; each victim gets post-hit protection so damage is never per frame. Lane enemies.
 */
UCLASS()
class UMBRELLAELLA_API AUmbrellaTrap : public AActor
{
	GENERATED_BODY()

public:
	AUmbrellaTrap();

	/** Pick the kind and size the hazard box around the actor. */
	void ConfigureKind(ETrapKind NewKind);

	/** Advance the cycle and the protection timers; hurts every pawn currently overlapping. */
	void StepSeconds(float DeltaSeconds);

	/** Hurt Victim now if the trap is damaging and the victim is unprotected. Returns the damage dealt. */
	float ApplyContact(AActor* Victim);

	virtual void Tick(float DeltaSeconds) override;

	ETrapKind GetKind() const { return Kind; }
	ETrapPhase GetPhase() const;
	float GetCycleTime() const { return CycleTime; }

protected:
	virtual void BeginPlay() override;

private:
	UPROPERTY(VisibleAnywhere, Category = "Trap")
	TObjectPtr<UBoxComponent> Hazard;

	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> Placeholder;

	UPROPERTY(EditAnywhere, Category = "Trap")
	ETrapKind Kind = ETrapKind::AirMill;

	FTrapTuning Tuning;
	FTrapCycle Cycle;
	FContactGate Gate;
	float CycleTime = 0.0f;
};
