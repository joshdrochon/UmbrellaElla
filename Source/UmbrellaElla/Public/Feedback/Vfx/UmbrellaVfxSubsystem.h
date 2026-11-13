#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "UmbrellaVfxSubsystem.generated.h"

struct FUmbrellaEvent;
class AActor;
class UTexture2D;
enum class EArtSlotDraw : uint8;

namespace UmbrellaVfxConst
{
	/** Seconds a stand-in effect stays up (short, readable). */
	static constexpr float StandInLifeSeconds = 0.25f;
	/** Stand-in sphere scale. */
	static constexpr float StandInScale = 0.3f;
	/** Stand-in sizes per effect (multiples of StandInScale). */
	static constexpr float BurstScale = 0.45f;
	static constexpr float HitScale = 0.6f;
	static constexpr float TelegraphScale = 0.9f;
	static constexpr float BreakScale = 0.75f;
	static constexpr float LongLifeSeconds = 0.5f;
	/** An effect never lives shorter than this, so it can be read. */
	static constexpr float MinReadableSeconds = 0.12f;
	/** Longest an effect is held, even for a long telegraph. */
	static constexpr float MaxLifeSeconds = 2.0f;
	/** Most effects alive at once; beyond this new ones are dropped (performance). */
	static constexpr int32 MaxActiveEffects = 24;
	/** Flashing effects are at least this far apart (at most three flashes per second, photosensitivity guideline). */
	static constexpr float MinFlashGapSeconds = 0.34f;
	/** Reduced-flash mode shrinks a flashing effect to this fraction instead of removing it. */
	static constexpr float ReducedFlashScale = 0.4f;
	/** Stand-in light for effects that light nearby surfaces. */
	static constexpr float LightIntensity = 3000.0f;
	static constexpr float LightRadius = 250.0f;
}

/** One effect: its render layer (Y), size, whether it flashes, and whether it lights nearby lit surfaces. */
struct FVfxEffectSpec
{
	FName Name;
	float LayerY = 0.0f;
	float LifeSeconds = 0.25f;
	float Scale = 0.3f;
	bool bFlashing = false;
	bool bLit = false;
};

/**
 * Event-driven combat VFX (weapon, shared combat, Keeper). Synced to bus events, never to animation
 * clocks. Shows a short stand-in flash until Niagara/flipbook art exists. Never gameplay authority. Visuals lane.
 */
UCLASS()
class UMBRELLAELLA_API UUmbrellaVfxSubsystem final : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** Effect name an event maps to, or NAME_None. Pure. */
	static FName EffectForEvent(const FUmbrellaEvent& Event);

	/** Spawn the effect for an event (also what the bus handler does). Counts only when one was shown. */
	void PlayForEvent(const FUmbrellaEvent& Event);

	/** Draw the bolt-hit picture (art slot shot:red-impact) on a shown ShotImpact effect, keeping its size. */
	EArtSlotDraw ShowImpactArt(AActor* Effect, UTexture2D* Texture);

	/** Spec of a named effect (NAME_None Name if unknown). Pure. */
	static FVfxEffectSpec SpecForEffect(FName Effect);

	/** All effect names this subsystem can show. Pure. */
	static TArray<FName> AllEffects();

	/** Seconds an effect stays up for an event: spec life, or the telegraph time the event carries, clamped readable. Pure. */
	static float LifeFor(const FVfxEffectSpec& Spec, const FUmbrellaEvent& Event);

	/** True when a new effect must be dropped: too many alive, or a flash too soon after the last one. Pure. */
	static bool ShouldSuppress(int32 ActiveCount, bool bFlashing, float SecondsSinceLastFlash);

	/** Accessibility: shrink flashing effects. Called by whatever owns the setting (settings lane). */
	void SetReducedFlash(bool bReduced) { bReducedFlash = bReduced; }
	bool IsReducedFlash() const { return bReducedFlash; }

	/** Effects currently alive. */
	int32 GetActiveCount() const;
	/** Events dropped by the performance/flash limits. */
	int32 GetSuppressedCount() const { return SuppressedCount; }
	/** The last shown effect actor (test reads layer, light, collision). */
	AActor* GetLastActor() const { return LastActor.Get(); }
	/** Frame of the event that spawned the last effect (readability sync: effects follow events, not clocks). */
	int64 GetLastEventFrame() const { return LastEventFrame; }

	FName GetLastEffect() const { return LastEffect; }
	int32 GetEffectCount() const { return EffectCount; }

private:
	/** Bus handler: plays the event unless the effect director shows it. */
	void HandleBusEvent(const FUmbrellaEvent& Event);
	/** True when the flag that gates this event's effect family is on. */
	static bool IsEffectEnabled(const FUmbrellaEvent& Event);
	TArray<FDelegateHandle> Handles;
	FName LastEffect;
	int32 EffectCount = 0;
	int32 SuppressedCount = 0;
	int64 LastEventFrame = 0;
	bool bReducedFlash = false;
	double LastFlashTime = -1.0e9;
	TArray<TWeakObjectPtr<AActor>> Active;
	TWeakObjectPtr<AActor> LastActor;
};
