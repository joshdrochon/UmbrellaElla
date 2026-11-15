#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "StreamBeamActor.generated.h"

class UStaticMeshComponent;
struct FUmbrellaShotSpec;

/**
 * Streamed Blast beam: one actor that grows forward from the muzzle while the spell is held, deals damage in
 * discrete ticks to every receiver inside its box, and stops at a solid blocker. The Attack Emitter owns it, sets its
 * length each step and calls ApplyTick on the tick cadence. Art never changes damage: the box is the hitbox. Lane a.
 */
UCLASS()
class UMBRELLAELLA_API AStreamBeamActor : public AActor
{
	GENERATED_BODY()

public:
	/** The engine cube is this many units on a side; the visual scales it to the box. */
	static constexpr float CubeSize = 100.0f;
	/** The placeholder is this fraction as deep as it is thick (looks, not collision). */
	static constexpr float VisualDepthFraction = 0.25f;
	/** Smallest visual length, so a zero-length beam never scales to zero. */
	static constexpr float MinVisualLength = 0.01f;

	AStreamBeamActor();

	/** Place the beam: Muzzle is the fixed anchor, Length the grown length (before blockers), Width the full thickness. */
	void SetBeam(const FVector& Muzzle, float Length, float Width);

	/** Length after clipping by a solid blocker (what the box and the visual cover). */
	float GetEffectiveLength() const { return EffectiveLength; }
	float GetWidth() const { return BeamWidth; }
	FVector GetMuzzle() const { return BeamMuzzle; }

	/** Stand-in strands (two segments each: canopy to body edge, then along the edge). Looks only, no collision. */
	const TArray<TObjectPtr<UStaticMeshComponent>>& GetStrandParts() const { return StrandParts; }

	/** The dark beam body (sized to the hitbox) and the color it is drawn in. */
	UStaticMeshComponent* GetBody() const { return Visual; }
	FLinearColor GetBodyColor() const { return BodyColor; }
	FLinearColor GetStrandColor() const { return StrandColor; }

	/** One damage tick: hand Tick (damage, source) to every receiver in the box. Returns how many actors were hit. */
	int32 ApplyTick(const FUmbrellaShotSpec& Tick);

	/** Length of a beam box from Muzzle after a solid blocker (blocks the player shot channel, no receiver) ends it. Shared with the aimed beam. */
	static float ClipToBlockers(UWorld* World, const AActor* Ignore, const FVector& Muzzle, float Length, float Width, float HalfDepth);

	/** Hand Tick to every receiver inside the box from Muzzle (Length x HalfDepth x Width). Returns how many actors were hit. Shared with the aimed beam. */
	static int32 HitBox(UWorld* World, const AActor* Ignore, const FVector& Muzzle, float Length, float Width, float HalfDepth, const FUmbrellaShotSpec& Tick);

private:
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> Visual;

	void PlaceStrands();
	UStaticMeshComponent* MakePart(const FName& Name, const FLinearColor& Color);

	UPROPERTY()
	TArray<TObjectPtr<UStaticMeshComponent>> StrandParts;

	FLinearColor BodyColor = FLinearColor::Black;
	FLinearColor StrandColor = FLinearColor::White;
	FVector BeamMuzzle = FVector::ZeroVector;
	float RequestedLength = 0.0f;
	float EffectiveLength = 0.0f;
	float BeamWidth = 0.0f;
};
