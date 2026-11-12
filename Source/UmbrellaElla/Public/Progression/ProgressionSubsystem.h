#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaPlayMode.h"
#include "Persistence/ProgressionSaveGame.h"
#include "Progression/ProgressionRules.h"
#include "Progression/ProgressionTypes.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Engine/World.h"
#include "ProgressionSubsystem.generated.h"

struct FProgressionTuning;

class UUmbrellaEventBus;
class UWorld;

DECLARE_MULTICAST_DELEGATE(FOnProgressionChanged);
DECLARE_MULTICAST_DELEGATE_OneParam(FOnProgressionLevelGained, int32);

/**
 * Director's Cut progression (GameInstance subsystem, so it survives map changes). It owns the earned profile, listens to
 * the event bus of the current game world and exposes getters the other areas read. Start Game never gains or shows
 * anything: every getter answers the baseline there.
 *
 * Bus contract (what this listens to, what it sends):
 *  - ModeSelected: Detail containing "Director" selects Director's Cut and begins a run; "Start" selects Start Game.
 *    (Flow may call SetPlayMode / BeginRun directly instead.)
 *  - BossPartDestroyed: XP for the label found in Detail, then TargetId, then SourceId (enemy family or Keeper part).
 *  - CheckpointReached: Detail containing "Phase", "Boss" or "Keeper" is a boss checkpoint, anything else a level checkpoint.
 *  - CheckpointRetried: death retry. RunCompleted or EncounterCompleted: a won run, counted once per run.
 *  - Sends XPAwarded (Amount = XP, Detail = label) and LevelGained (Amount = new level).
 */
UCLASS()
class UMBRELLAELLA_API UProgressionSubsystem final : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	UProgressionSubsystem();

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

	static UProgressionSubsystem* Get(const UObject* WorldContext);

	// ---- wiring
	void BindToBus(UUmbrellaEventBus* Bus);
	void UnbindFromBus();
	void HandleEvent(const FUmbrellaEvent& Event);
	/** Slot to save to; empty turns saving off (rule tests). Loads that slot as the new profile. */
	void UseSaveSlot(const FString& Slot);

	// ---- mode and run
	void SetPlayMode(EUmbrellaPlayMode Mode);
	EUmbrellaPlayMode GetPlayMode() const;
	/** Director's Cut run start: fixes this run's scaling (Final Hour when every stat is maxed) and takes the run-start checkpoint. */
	void BeginRun();
	void ReachCheckpoint(EProgressionCheckpointKind Kind);
	void RetryFromCheckpoint();
	void QuitAndReload();
	void CompleteRun();
	bool IsRunActive() const;
	bool IsFinalHourRun() const;
	FRunScaling GetRunScaling() const;

	// ---- XP
	/** Awards the kill XP for a label. Returns the XP given (0 outside Director's Cut or for a non-kill). */
	int32 AwardKill(FName Label);

	// ---- reads (Start Game answers the baseline)
	int32 GetLevel() const;
	FLevelProgress GetLevelProgress() const;
	int32 GetXp() const;
	int32 GetUnspentPoints() const;
	int32 GetCompletedRuns() const;
	int32 GetRank(EProgressionTrack Track) const;
	bool IsSpellUnlocked(EProgressionSpell Spell) const;
	TArray<EProgressionSpell> GetUnlockedSpells() const;
	int32 GetHitCapacity() const;
	int32 GetMaxLives() const;
	float GetHealPerYellow() const;
	float GetDamageReduction() const;
	float GetSuctionRange() const;
	float GetSuctionConeDegrees() const;
	float GetSpellDamageMultiplier(EProgressionSpell Spell) const;
	FProgressionProfile GetEffectiveProfile() const;
	EProgressionLoadStatus GetLoadStatus() const;
	bool IsBlocked() const;

	// ---- purchases
	void SetPurchaseContext(const FPurchaseContext& Context);
	FPurchaseContext GetPurchaseContext() const;
	bool CanPurchaseNow() const;
	bool CanReallocateNow() const;
	EProgressionCommit CommitRanks(const TArray<int32>& NewRanks);

	// ---- developer fixture: shadow progress, never written to the real profile
	void BeginShadowProgress(int32 Level);
	void EndShadowProgress();
	bool IsShadowActive() const;

	FOnProgressionChanged& OnChanged();
	FOnProgressionLevelGained& OnLevelGained();

	/** Tuning source. Core does not carry a Progression member yet (docs/build/requests/progression.md), so this is a default instance. */
	const FProgressionTuning& GetTuning() const;

private:
	void OnPostWorldInit(UWorld* World, const UWorld::InitializationValues Values);
	void OnWorldCleanup(UWorld* World, bool bSessionEnded, bool bCleanupResources);
	void Persist();
	void Broadcast(EUmbrellaEventType Type, FName Detail, int32 Amount);
	bool IsProgressing() const;

	FProgressionProfile Profile;
	FProgressionProfile RealProfileWhileShadow;
	FString SaveSlot;
	EUmbrellaPlayMode PlayMode = EUmbrellaPlayMode::StartGame;
	EProgressionLoadStatus LoadStatus = EProgressionLoadStatus::Fresh;
	FPurchaseContext PurchaseContext;
	FRunScaling RunScaling;
	bool bFinalHour = false;
	bool bRunActive = false;
	bool bShadowActive = false;

	TWeakObjectPtr<UUmbrellaEventBus> BoundBus;
	TArray<EUmbrellaEventType> BoundTypes;
	TArray<FDelegateHandle> BoundHandles;
	FDelegateHandle PostInitHandle;
	FDelegateHandle CleanupHandle;

	FOnProgressionChanged ChangedDelegate;
	FOnProgressionLevelGained LevelGainedDelegate;
};
