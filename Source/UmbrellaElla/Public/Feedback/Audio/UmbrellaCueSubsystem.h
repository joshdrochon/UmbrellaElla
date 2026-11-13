#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "Core/UmbrellaEvent.h"
#include "UmbrellaCueSubsystem.generated.h"

/**
 * Plays placeholder sound cues from event-bus events (ProjectileSpawned, ProjectileContact, CatchSucceeded,
 * BossTargetHit, BossAttackTelegraphed, ...). Never gameplay authority: a missing sound asset only records the cue.
 * Lane e.
 */
struct FUmbrellaSoundCue;
class UAudioComponent;
class USoundBase;
class FUmbrellaSoundLabelBoard;
class FUmbrellaSoundLabelHud;

namespace UmbrellaCueConst
{
	inline constexpr int32 RandomSeed = 7;
}

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

	/**
	 * Plays one sound-list row by id (the rows with no bus event yet, and the lanes that own their own trigger).
	 * Silent when the id is not a live row or no take of it is imported (CanPlaySound says which).
	 */
	void PlaySoundById(FName Id);
	bool CanPlaySound(FName Id) const;
	/** Stops every running loop of a group ("move", "wind"). */
	void StopLoopGroup(const FString& Group);
	int32 GetSoundCueCount() const { return SoundCueCount; }
	FName GetLastSoundId() const { return LastSoundId; }

#if UMBRELLAELLA_WORKBENCH
	/** Dev-only sound labels: every sound that starts, music included. Null in a world without the board. */
	TSharedPtr<FUmbrellaSoundLabelBoard> GetSoundLabelBoard() const { return SoundLabels; }
	/** Test seam: the same call both play paths make. */
	void NoteSoundLabel(FName Id, int32 Take);
#endif

	UAudioComponent* GetMusicComponent() const { return MusicComponent; }
	/** How many times music was started; a mode change adds one, the component is reused. */
	int32 GetMusicStartCount() const { return MusicStartCount; }

private:
	void HandleEvent(const FUmbrellaEvent& Event);

	/** bOutPlayed: a take was found and started. */
	void PlayRow(const FUmbrellaSoundCue& Cue, bool& bOutPlayed);
	bool HasTakes(const FUmbrellaSoundCue& Cue) const;

	TArray<TPair<EUmbrellaEventType, FDelegateHandle>> Handles;
	TMap<EUmbrellaEventType, FName> PrevDetails;
	FName LastSoundId;
	int32 SoundCueCount = 0;
	/** Cosmetic take choice and pitch jitter; seeded so a run repeats (GDD QA-08). */
	FRandomStream CueRandom{UmbrellaCueConst::RandomSeed};

	UPROPERTY(Transient)
	TMap<FName, TObjectPtr<UAudioComponent>> ActiveLoops;

	FName LastCue;
	int32 CueCount = 0;

	UPROPERTY(Transient)
	TObjectPtr<UAudioComponent> MusicComponent;
	int32 MusicStartCount = 0;

#if UMBRELLAELLA_WORKBENCH
	TSharedPtr<FUmbrellaSoundLabelBoard> SoundLabels;
	TSharedPtr<FUmbrellaSoundLabelHud> SoundLabelHud;
	/** The bus event being handled, for the label; "Direct" for a play by id. */
	FString LabelEvent;
#endif
};
