#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaEvent.h"
#include "Subsystems/WorldSubsystem.h"
#include "Encounter/KeeperFightModel.h"
#include "EncounterDirectorSubsystem.generated.h"

class AKeeperOfTime;
class AUmbrellaArena;

DECLARE_MULTICAST_DELEGATE_TwoParams(FOnKeeperDamageDelivered, FName /*Source attack*/, float /*Health damage*/);

/** Encounter state: READY -> ACTIVE -> ENDING_SUCCESS or ENDING_FAILURE -> RESTARTING -> READY, plus PAUSED. */
UENUM()
enum class EEncounterState : uint8
{
	Ready,
	Active,
	EndingSuccess,
	EndingFailure,
	Restarting,
	Paused
};

/** Encounter Director: owns the encounter state, phases, checkpoints, retry and the win. Lane b. */
UCLASS()
class UMBRELLAELLA_API UEncounterDirectorSubsystem : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** Flow (lane d) calls this when a mode reaches the Keeper. Spawns the Keeper at the arena anchor. */
	void BeginKeeperFight();

	/** Workbench and tests: start a fresh fight at a later phase (parts of earlier phases already depleted). */
	void BeginKeeperFightAtPhase(EKeeperPhase Phase);

	/** Fired when a Keeper physical attack (gust, talon, chain) damages Ella, after the damage was delivered. */
	FOnKeeperDamageDelivered& OnDamageDelivered() { return DamageDelivered; }

	/** Clears every projectile, timer and module state and returns to READY. Re-enters the checkpoint phase after a defeat. */
	void ResetForRestart();

	/** Flow (lane d): the pause menu. PAUSED freezes the schedule and every projectile. */
	void SetPaused(bool bPaused);

	/** Run the fight forward by DeltaSeconds of unscaled active gameplay time. Tick calls it; tests call it directly. */
	void AdvanceFight(float DeltaSeconds);

	/** The Keeper part components call this. Returns what the shot should do. */
	EKeeperHitOutcome HandlePlayerShot(EKeeperPart Part, float Damage);

	/** Tests and workbench: stop the engine tick from advancing the fight, so AdvanceFight is the only clock. */
	void SetManualStepping(bool bManual);

	/** Tests: use this actor as Ella (position and damage target) when the player pawn is absent. */
	void SetPlayerActor(AActor* Actor);

	EEncounterState GetState() const { return State; }
	const FKeeperFightModel& GetModel() const { return Model; }
	AKeeperOfTime* GetKeeper() const { return Keeper.Get(); }
	EKeeperPhase GetPhase() const { return Model.GetPhase(); }
	FKeeperRuleSwitches BuildSwitches() const;

	/** How the same-frame tie resolves: defeat wins. */
	static EEncounterState ResolveEnding(bool bPlayerDefeated, bool bFightWon);

	static FName PhaseName(EKeeperPhase Phase);

protected:
	virtual bool DoesSupportWorldType(EWorldType::Type WorldType) const override;

private:
	void HandleDefeated(const FUmbrellaEvent& Event);
	void HandleLifeLost(const FUmbrellaEvent& Event);
	void ProcessCommands(TArray<FKeeperCommand>& Commands);
	void Broadcast(EUmbrellaEventType Type, FName Detail, FName Target, float Value, int32 Amount) const;
	void SpawnKeeper();
	void DestroyKeeper();
	void ClearEnemyProjectiles() const;
	void FreezeProjectiles() const;
	void ThawProjectiles() const;
	void SetProjectileTicks(bool bEnabled) const;
	void FinalizeEnding();
	void EnterFailure();
	void DeliverDamage(FName Source, float Amount) const;
	FVector2D PlayerPosition() const;
	float PlayerRadius() const;
	FVector FindAnchor();
	AActor* GetPlayerActor() const;

	UPROPERTY()
	EEncounterState State = EEncounterState::Ready;
	UPROPERTY()
	TObjectPtr<AKeeperOfTime> Keeper;
	UPROPERTY()
	TObjectPtr<AUmbrellaArena> Arena;
	UPROPERTY()
	TObjectPtr<AActor> PlayerOverride;
	UPROPERTY()
	EEncounterState StateBeforePause = EEncounterState::Active;

	FKeeperFightModel Model;
	FOnKeeperDamageDelivered DamageDelivered;
	FDelegateHandle DefeatedHandle;
	FDelegateHandle LifeLostHandle;
	bool bManualStepping = false;
	bool bModelReady = false;
	bool bResumePending = false;
	bool bWinPending = false;
	bool bDefeatInWinFrame = false;
	int64 WinFrame = 0;
	float LastDelta = 0.0f;
	float ElapsedSeconds = 0.0f;
	int32 LivesLostThisPhase = 0;
};
