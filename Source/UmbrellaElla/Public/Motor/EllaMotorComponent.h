#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Motor/MotorModel.h"
#include "Umbrella/UmbrellaAction.h"
#include "EllaMotorComponent.generated.h"

class UEnhancedInputComponent;
class UUmbrellaStateComponent;
class UUmbrellaEventBus;
struct FUmbrellaEvent;

/**
 * Player Motor: the only writer of Ella's velocity and position. Reads the action from the Umbrella State, requests
 * from the Input Adapter, and WindEntered / WindExited / PlayerHealthChanged from the event bus. Lane a.
 */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UEllaMotorComponent : public UActorComponent
{
	GENERATED_BODY()

public:
	UEllaMotorComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);

	/** Hop button: overhead = hop, falling = dash toward the input side (left = back). */
	void RequestHop();
	void RequestDash(EUmbrellaDashDirection Direction);

	/** Vertical trim, -1 (down) to 1 (up). */
	void SetTrimAxis(float Axis);

	/** Horizontal input, -1 to 1. Chooses hop/dash direction only; direct steering is off. */
	void SetMoveAxis(float Axis);

	/** Keep Ella inside this box (X = world X, Y = world Z). */
	void SetPlayBounds(const FBox2D& Bounds);
	void ClearPlayBounds();

	/** X = horizontal, Y = 0, Z = vertical, units/s. */
	FVector GetVelocity() const;
	bool IsHopProtected() const;
	bool IsRiding() const;
	float GetLiftMultiplier() const { return LiftMultiplier; }

	/** Test seam: advance the motor by a fixed delta without a world tick. */
	void StepMotor(float DeltaSeconds);

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

private:
	void OnWindEntered(const FUmbrellaEvent& Event);
	void OnWindExited(const FUmbrellaEvent& Event);
	void OnHealthChanged(const FUmbrellaEvent& Event);
	bool IsEventForElla(const FUmbrellaEvent& Event) const;
	FVector2D SumCurrents() const;
	FVector2D SumForcedPushes() const;

	UPROPERTY(Transient)
	TObjectPtr<UUmbrellaStateComponent> UmbrellaState;

	FMotorModelState Model;
	TMap<FName, FVector2D> ActiveCurrents;
	/** Local vertical fields of currents Ella is in: x gain, y centre z, z compensation. */
	TMap<FName, FVector> ActiveLocalFields;
	/** Hostile sources (GUST_Band) by SourceId; they bypass the voluntary ride path. */
	TMap<FName, FVector2D> ForcedPushes;
	FBox2D PlayBounds = FBox2D(ForceInit);
	float TrimAxis = 0.0f;
	float MoveAxis = 0.0f;
	float LiftMultiplier = 1.0f;
	FDelegateHandle WindEnteredHandle;
	FDelegateHandle WindExitedHandle;
	FDelegateHandle HealthHandle;
};
