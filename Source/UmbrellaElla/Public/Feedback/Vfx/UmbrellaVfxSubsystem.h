#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "UmbrellaVfxSubsystem.generated.h"

struct FUmbrellaEvent;

namespace UmbrellaVfxConst
{
	/** Seconds a stand-in effect stays up (short, readable). */
	static constexpr float StandInLifeSeconds = 0.25f;
	/** Stand-in sphere scale. */
	static constexpr float StandInScale = 0.3f;
}

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

	FName GetLastEffect() const { return LastEffect; }
	int32 GetEffectCount() const { return EffectCount; }

private:
	/** True when the flag that gates this event's effect family is on. */
	static bool IsEffectEnabled(const FUmbrellaEvent& Event);
	TArray<FDelegateHandle> Handles;
	FName LastEffect;
	int32 EffectCount = 0;
};
