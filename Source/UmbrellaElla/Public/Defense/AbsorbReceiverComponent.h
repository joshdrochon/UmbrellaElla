#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "Core/UmbrellaEvent.h"
#include "Projectile/UmbrellaShotReceiver.h"
#include "AbsorbReceiverComponent.generated.h"

class UEnhancedInputComponent;

/** Whether Ella is in absorb-fall. One state, one setter. */
UENUM()
enum class EAbsorbPose : uint8
{
	Closed,
	AbsorbFall
};

/**
 * Defense Receiver: absorbs yellow shots during absorb-fall. Lane c.
 * INV-1: only a yellow shot during absorb-fall is absorbed; red is never absorbed; outside absorb-fall nothing is.
 * The pose comes from SetPose (the umbrella state lane calls it) or from an UmbrellaConfigChanged event with Detail
 * "AbsorbFall" and Amount 1 (on) or 0 (off).
 */
UCLASS(ClassGroup = (UmbrellaElla), meta = (BlueprintSpawnableComponent))
class UMBRELLAELLA_API UAbsorbReceiverComponent : public UActorComponent, public IUmbrellaShotReceiver
{
	GENERATED_BODY()

public:
	UAbsorbReceiverComponent();

	/** Called once by AEllaCharacter::SetupPlayerInputComponent. Bind this module's actions here (or do nothing). */
	void BindInput(UEnhancedInputComponent* Input);

	virtual EUmbrellaShotResult ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation) override;
	virtual int32 GetShotPriority() const override;

	void SetPose(EAbsorbPose NewPose);
	EAbsorbPose GetPose() const { return Pose; }

protected:
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type Reason) override;

private:
	void OnConfigChanged(const FUmbrellaEvent& Event);
	void Broadcast(EUmbrellaEventType Type, FName Source, FName Detail, float Value) const;

	EAbsorbPose Pose = EAbsorbPose::Closed;
	FDelegateHandle ConfigHandle;
};
