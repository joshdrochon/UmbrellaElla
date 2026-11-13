#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "WindCurrent.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

/** What a current is for, drawn differently (drawn width): carries along, pushes down, or restores the player. */
UENUM()
enum class EWindKind : uint8
{
	Transport,
	Descent,
	Rescue
};

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

	/** Optional local vertical field carried on WindEntered (Detail "Dir@gain,centreZ,compensation"):
	 * the Motor adds Vz = Gain * (CentreZ - RootZ) + Compensation while it rides this current. World z. */
	void SetLocalVerticalField(float Gain, float CentreZ, float Compensation);

	/** Kind from direction and local field: a local vertical field or an upward push is Rescue, downward is Descent. */
	/** Edge of the engine plane used to draw a field, in units at scale 1. */
	static constexpr float PlaneEdge = 100.0f;

	static EWindKind KindFor(const FVector& Direction, bool bHasLocalField);
	EWindKind GetKind() const { return KindFor(Direction, bHasLocalField); }

	/** Stand-in look per kind (colour, opacity) used until the vfx-gust art slot is painted. */
	static FLinearColor KindTint(EWindKind Kind);
	static float KindOpacity(EWindKind Kind);

	/** Width and height (X, Z) of the usable volume and of the drawn field, in world units. Drawn is 0 when nothing is drawn. */
	FVector2D GetUsableSize() const;
	FVector2D GetDrawnSize() const;
	bool IsDrawn() const { return bDrawn; }

	/** Broadcast the enter/exit event for a pawn; separate so tests can call it without physics. */
	void BroadcastEntered(const AActor* Other) const;
	void BroadcastExited(const AActor* Other) const;

protected:
	virtual void PostInitializeComponents() override;
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

	/** Rebuild the drawn field to cover the whole usable volume; called on every shape or kind change. */
	void RefreshDrawn();

	UPROPERTY(VisibleAnywhere, Category = "Wind")
	TObjectPtr<UStaticMeshComponent> Drawn;

	bool bDrawn = false;
	bool bHasLocalField = false;
	float LocalGain = 0.0f;
	float LocalCentreZ = 0.0f;
	float LocalCompensation = 0.0f;
};
