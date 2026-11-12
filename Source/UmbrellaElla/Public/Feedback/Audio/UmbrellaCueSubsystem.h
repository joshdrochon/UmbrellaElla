#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "UmbrellaCueSubsystem.generated.h"

/**
 * Plays placeholder sound cues from event-bus events (ProjectileSpawned, ProjectileContact, CatchSucceeded,
 * BossTargetHit, BossAttackTelegraphed, ...). Never gameplay authority: a missing sound asset only records the cue.
 * Lane e.
 */
struct FUmbrellaEvent;

UCLASS()
class UMBRELLAELLA_API UUmbrellaCueSubsystem final : public UWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	/** The cue name an event maps to, or NAME_None when it has no sound. */
	static FName CueForEvent(const FUmbrellaEvent& Event);

	FName GetLastCue() const { return LastCue; }
	int32 GetCueCount() const { return CueCount; }

private:
	void HandleEvent(const FUmbrellaEvent& Event);

	TArray<FDelegateHandle> Handles;
	FName LastCue;
	int32 CueCount = 0;
};
