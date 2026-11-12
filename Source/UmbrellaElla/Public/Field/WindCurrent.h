#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WindCurrent.generated.h"

class UBoxComponent;

/**
 * A harmless wind current volume . On overlap with a pawn it broadcasts WindEntered / WindExited on the
 * event bus: SourceId = this current, TargetId = the pawn, Value = force, Detail = direction label. The Motor applies
 * the motion; this actor never writes velocity and never damages. Lane e.
 */
UCLASS()
class UMBRELLAELLA_API AWindCurrent : public AActor
{
	GENERATED_BODY()

public:
	AWindCurrent();

	/** Direction label for a unit-ish direction in X/Z: Left, Right, Up or Down by the dominant axis. */
	static FName DirectionLabel(const FVector& Direction);

	/** Force of this current in units per second; negative tuning is clamped to 0. */
	float GetForce() const;

	FVector GetDirection() const { return Direction; }

	/** Half-extent of the volume in X/Z (Y keeps a thin depth). */
	void SetHalfExtent(float HalfX, float HalfZ);

	void SetCurrent(const FVector& NewDirection, float NewForce);

	/** Broadcast the enter/exit event for a pawn; separate so tests can call it without physics. */
	void BroadcastEntered(const AActor* Other) const;
	void BroadcastExited(const AActor* Other) const;

protected:
	virtual void NotifyActorBeginOverlap(AActor* OtherActor) override;
	virtual void NotifyActorEndOverlap(AActor* OtherActor) override;

private:
	UPROPERTY(VisibleAnywhere, Category = "Wind")
	TObjectPtr<UBoxComponent> Volume;

	UPROPERTY(EditAnywhere, Category = "Wind")
	FVector Direction = FVector(1.0, 0.0, 0.0);

	/** Negative = use tuning DefaultWindForce. */
	UPROPERTY(EditAnywhere, Category = "Wind")
	float Force = -1.0f;
};
