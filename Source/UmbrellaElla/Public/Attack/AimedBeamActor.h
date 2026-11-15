#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "AimedBeamActor.generated.h"

class UStaticMeshComponent;
class UTexture2D;
struct FUmbrellaShotSpec;

/** Looks of the aimed beam's painted ribbon (presentation only; the hitbox is the tuning's length and width). */
namespace AimedRibbonLook
{
	/** Ragged edge: half-thickness base, slow wander (amount, frequency, seed), fine bite (amount, frequency, seed). */
	static constexpr float EdgeBase = 0.86f;
	static constexpr float EdgeWander = 0.14f;
	static constexpr float EdgeWanderFreq = 18.0f;
	static constexpr int32 EdgeWanderSeed = 7;
	static constexpr float EdgeBite = 0.06f;
	static constexpr float EdgeBiteFreq = 61.0f;
	static constexpr int32 EdgeBiteSeed = 11;
	static constexpr float EdgeMin = 0.2f;
	/** Alpha falls from 1 to 0 between these shares of the half-thickness. */
	static constexpr float AlphaSoftFrom = 0.35f;
	/** Ivory core to brass up to this share across, then brass to ash. */
	static constexpr float CoreShare = 0.45f;
	/** Painted streaks: rows per streak, slow grain (base, amount, frequency, row phase, seed), fine strokes (amount, frequency, seed). */
	static constexpr int32 StreakRows = 3;
	static constexpr float GrainBase = 0.88f;
	static constexpr float GrainAmount = 0.24f;
	static constexpr float GrainFreq = 9.0f;
	static constexpr float GrainRowPhase = 3.1f;
	static constexpr int32 GrainSeed = 23;
	static constexpr float StrokeAmount = 0.08f;
	static constexpr float StrokeFreq = 140.0f;
	static constexpr int32 StrokeSeed = 31;
	/** Hairline share of the full width the beam thins to at the end of its life. */
	static constexpr float EndThickness = 0.15f;
}

/**
 * Aimed shot beam (D-new-aimed-shot, Josh 14 Nov): one long beam to the right that the Attack Emitter fires after
 * Shoot is held for AimedChargeSeconds. Damage lands once, on every receiver along the box, when it fires; then the
 * beam stays on screen for AimedBeamSeconds, thinning out. Looks: a painted, soft-edged ribbon in warm ivory, brass
 * and ash (Ricky's Other Realm study palette, no neon), drawn from a generated grain texture on the soft-edged slot
 * material, never a flat box. The box is the hitbox; art never changes damage.
 */
UCLASS()
class UMBRELLAELLA_API AAimedBeamActor : public AActor
{
	GENERATED_BODY()

public:
	AAimedBeamActor();

	/** Ribbon texture size (pixels): long axis along the beam. */
	static constexpr int32 RibbonWidth = 512;
	static constexpr int32 RibbonHeight = 64;
	/** Soft fade-out share at the far end of the ribbon (FadeRight on the soft-edged material) and at the muzzle. */
	static constexpr float FarFade = 0.22f;
	static constexpr float NearFade = 0.04f;
	/** The painted ribbon is drawn this many times the hitbox width: its soft edges fade out, so the bright core matches the box. */
	static constexpr float VisualWidthScale = 1.6f;
	/** Share of the beam's life drawn at full width before it thins out. */
	static constexpr float FullWidthShare = 0.75f;

	/**
	 * Depth (Y) the beam's hitbox spans: from the Keeper's parts (KeeperY - PartDepth = -70) to the shot plane
	 * (ProjectileY + StreamDepthHalfExtent = 37), so it reaches the Keeper as well as enemies on Ella's plane. Pure.
	 */
	static void HitDepth(float& OutCenterY, float& OutHalfDepth);

	/** Place the beam from Muzzle (clipped by solid blockers) and draw it at full width. */
	void Place(const FVector& Muzzle, float Length, float Width);

	/** Hit every receiver along the beam once with Shot. Returns how many actors were hit. */
	int32 Fire(const FUmbrellaShotSpec& Shot);

	/** Move with Ella (the muzzle follows her as she falls) and thin out over the beam's life (Age01 0..1). */
	void Follow(const FVector& Muzzle, float Age01);

	float GetEffectiveLength() const { return EffectiveLength; }
	float GetWidth() const { return BeamWidth; }
	FVector GetMuzzle() const { return BeamMuzzle; }
	UStaticMeshComponent* GetVisual() const { return Visual; }
	UTexture2D* GetRibbon() const { return Ribbon; }

	/** One RGBA texel of the ribbon (U along the beam 0..1, V across it 0..1): warm ivory core, brass, ash edges, a
	 *  painted streak grain and a ragged soft alpha edge. Pure; the texture and the tests both read it. */
	static FColor RibbonTexel(int32 X, int32 Y);

	/** A new generated ribbon texture owned by Outer. */
	static UTexture2D* MakeRibbonTexture(UObject* Outer);

private:
	void DrawRibbon(float Thickness);

	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> Visual;

	UPROPERTY(Transient)
	TObjectPtr<UTexture2D> Ribbon;

	FVector BeamMuzzle = FVector::ZeroVector;
	float EffectiveLength = 0.0f;
	float BeamWidth = 0.0f;
};
