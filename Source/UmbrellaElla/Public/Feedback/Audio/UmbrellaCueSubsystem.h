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
class UAudioComponent;
class USoundBase;

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

	/** Cues that are music (looped, one at a time), not one-shots. */
	static bool IsMusicCue(FName Cue);

	/** Stops the current music component, then starts Sound on the one persistent component (null Sound = stop only). */
	void RestartMusic(USoundBase* Sound);
	void StopMusic();

	UAudioComponent* GetMusicComponent() const { return MusicComponent; }
	/** How many times music was started; a mode change adds one, the component is reused. */
	int32 GetMusicStartCount() const { return MusicStartCount; }

private:
	void HandleEvent(const FUmbrellaEvent& Event);

	TArray<FDelegateHandle> Handles;
	FName LastCue;
	int32 CueCount = 0;

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> MusicComponent;
	int32 MusicStartCount = 0;
};
