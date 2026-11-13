#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WindCurrent.generated.h"

namespace WindCurrentConst
{
	/** Engine cube edge length in units (the drawn field stand-in). */
	static constexpr float CubeSize = 100.0f;
}

class UBoxComponent;
class UStaticMeshComponent;

/**
 * A harmless wind current volume . On overlap with a pawn it broadcasts WindEntered / WindExited on the
 * event bus: SourceId = this current, TargetId = TargetIdFor(pawn) (the player id "Ella" for Ella), Value = force, Detail = direction label. The Motor applies
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

	/** Event target for a pawn: UmbrellaPlayerIds::Ella for Ella or a player-controlled pawn, else the actor name. */
	static FName TargetIdFor(const AActor* Other);

	/** What the current does for the player, from its direction: Transport (right), Descent, Lift (rescue) or Return (left). */
	static FName RoleLabel(const FVector& Direction);

	/** Stand-in colour of the drawn field for a role label (FieldTuning). */
	static FLinearColor FieldColourFor(FName Role);

	/** Width of the usable volume (what moves Ella) and of the drawn field (what the player sees), in units. */
	float GetUsableWidth() const;
	float GetDrawnWidth() const;
	UStaticMeshComponent* GetField() const { return Field; }

	/** Broadcast the enter/exit event for a pawn; separate so tests can call it without physics. */
	void BroadcastEntered(const AActor* Other) const;
	void BroadcastExited(const AActor* Other) const;

protected:
	virtual void BeginPlay() override;
	virtual void NotifyActorBeginOverlap(AActor* OtherActor) override;
	virtual void NotifyActorEndOverlap(AActor* OtherActor) override;

private:
	/** Size, place and colour the drawn field to match the usable volume. */
	void RefreshField();

	UPROPERTY(VisibleAnywhere, Category = "Wind")
	TObjectPtr<UBoxComponent> Volume;

	/** The drawn wind field: a visible, collision-free card the exact width and height of the volume, behind Ella. */
	UPROPERTY(VisibleAnywhere, Category = "Wind")
	TObjectPtr<UStaticMeshComponent> Field;

	UPROPERTY(EditAnywhere, Category = "Wind")
	FVector Direction = FVector(1.0, 0.0, 0.0);

	/** Negative = use tuning DefaultWindForce. */
	UPROPERTY(EditAnywhere, Category = "Wind")
	float Force = -1.0f;
};
