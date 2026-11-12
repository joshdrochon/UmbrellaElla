#pragma once

#include "CoreMinimal.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "Owl/KeeperTuning.h"
#include "Encounter/EncounterTuning.h"

/** The three acts of the Keeper fight. */
enum class EKeeperPhase : uint8
{
	Wings,
	Mechanisms,
	Clock
};

/** Every hittable part. Eye has no HP. */
enum class EKeeperPart : uint8
{
	Wings,
	Front,
	Middle,
	Rear,
	Clock,
	Eye,
	Count
};

/** What the Projectile Service should do with a player shot that touched a part. */
enum class EKeeperHitOutcome : uint8
{
	PassThrough,
	Blocked,
	Damaged
};

/** The one physical attack that can run at a time. */
enum class EKeeperPhysical : uint8
{
	None,
	Gust,
	Talon,
	FrontCast,
	MiddleCurve,
	RearTwoStage
};

/** Physical move stages: warning, strokes, recovery. Harmless stages are Return and Recovery. */
enum class EKeeperStage : uint8
{
	Idle,
	Warning,
	Stroke,
	Pause,
	SecondStroke,
	Recovery
};

/** What the model asks the actor/director to do. The model never touches the world. */
enum class EKeeperCommandType : uint8
{
	FireShot,
	PhysicalWarning,
	PhysicalStrike,
	PhysicalRecovery,
	PhysicalCancelled,
	DamagePlayer,
	PushPlayer,
	ClearProjectiles,
	ClearGusts,
	PartBroken,
	PhaseStarted,
	TransitionEnded,
	ClockOpened,
	ClockClosed,
	SlowStarted,
	SlowEnded,
	EyeShown,
	EyeHidden,
	BlackoutStarted,
	BlackoutEnded,
	StunStarted,
	StunEnded,
	FightWon
};

/** One request from the model. Unused fields stay zero. */
struct UMBRELLAELLA_API FKeeperCommand
{
	EKeeperCommandType Type = EKeeperCommandType::FireShot;
	EKeeperPhysical Physical = EKeeperPhysical::None;
	EKeeperPart Part = EKeeperPart::Count;
	EKeeperPhase Phase = EKeeperPhase::Wings;
	EUmbrellaShotKind ShotKind = EUmbrellaShotKind::EnemyRed;
	FName Name;
	/** Shot origin, locked target or head position (X, Z). */
	FVector2D A = FVector2D::ZeroVector;
	/** Shot velocity or second point (X, Z). */
	FVector2D B = FVector2D::ZeroVector;
	/** Shot radius, damage, push speed or a duration, by Type. */
	float Value = 0.0f;
	float Damage = 0.0f;
	int32 Serial = 0;
};

/** Which parts of the fight are built (each is a manifest feature flag, set by the director). */
struct UMBRELLAELLA_API FKeeperRuleSwitches
{
	bool bRed = true;
	bool bYellow = true;
	bool bGust = true;
	bool bTalon = true;
	bool bFrontCast = true;
	bool bMiddleCast = true;
	bool bRearCast = true;
	bool bDoubleBeat = true;
	bool bBreakStun = true;
	bool bClockProtection = true;
	bool bSlow = true;
	bool bEye = true;
};

/** What the world tells the model each tick. */
struct UMBRELLAELLA_API FKeeperTickInput
{
	FVector2D PlayerPos = FVector2D::ZeroVector;
	float PlayerRadius = 0.0f;
};

/** Result of one player shot on a part. */
struct UMBRELLAELLA_API FKeeperHitResult
{
	EKeeperHitOutcome Outcome = EKeeperHitOutcome::PassThrough;
	bool bBroke = false;
	bool bPhaseAdvanced = false;
	bool bFightWon = false;
	bool bClockHpReduced = false;
	float HpAfter = 0.0f;
};

/**
 * The Keeper fight as plain rules: phases, HP, eligibility, the attack scheduler, clock protection, slow, eye and
 * stun. No world, no UObject, no wall clock: tests call Tick with fixed deltas and read the commands.
 * Time domains: Tick takes unscaled active-gameplay seconds. Slow, fire pause, stun and blackout scale or freeze the
 * world timers (cooldowns, warnings, strokes, queued shots); the clock, stun, slow, eye and exposure timers stay unscaled.
 */
class UMBRELLAELLA_API FKeeperFightModel
{
public:
	void Init(const FKeeperTuning& InTuning, const FEncounterTuning& InEncounter, const FKeeperRuleSwitches& InSwitches);

	/** Full reset to the start of StartPhase from the checkpoint (or a fresh fight for Wings). Clears every timer. */
	void BeginPhase(EKeeperPhase StartPhase, TArray<FKeeperCommand>& Out);

	/** Retry: restore the saved phase-start checkpoint (parts at their checkpoint HP) and begin that phase again. */
	void RetryCheckpoint(TArray<FKeeperCommand>& Out);

	void SetAnchor(const FVector2D& InAnchor) { Anchor = InAnchor; }

	void Step(float UnscaledDeltaSeconds, const FKeeperTickInput& Input, TArray<FKeeperCommand>& Out);

	FKeeperHitResult ApplyPlayerHit(EKeeperPart Part, float Damage, TArray<FKeeperCommand>& Out);

	/** A terminal lock (player defeated, success): stop everything. */
	void Halt(TArray<FKeeperCommand>& Out);

	// ---- Readers ----
	EKeeperPhase GetPhase() const { return Phase; }
	bool IsTransitioning() const { return TransitionRemaining > 0.0f; }
	bool IsEnded() const { return bEnded; }
	float GetPartHp(EKeeperPart Part) const;
	bool IsPartBroken(EKeeperPart Part) const;
	/** True when a shot on this part would do damage right now. */
	bool IsPartEligible(EKeeperPart Part) const;
	bool IsClockOpen() const { return ClockOpenRemaining > 0.0f; }
	bool IsEyeExposed() const { return EyeWindowRemaining > 0.0f; }
	bool IsSlowed() const { return SlowRemaining > 0.0f; }
	bool IsStunned() const { return StunRemaining > 0.0f; }
	bool IsBlackedOut() const { return BlackoutRemaining > 0.0f; }
	bool IsFirePaused() const { return FirePauseRemaining > 0.0f; }
	float GetWorldScale() const;
	EKeeperPhysical GetPhysical() const { return Physical; }
	EKeeperStage GetStage() const { return Stage; }
	int32 GetCastSerial() const { return CastSerial; }
	int32 GetPendingShotCount() const { return Pending.Num(); }
	/** Head of the running cast, or the claw tip of the talon (X, Z). */
	FVector2D GetHeadPosition() const { return HeadPos; }
	bool IsHeadHurting() const;
	FVector2D GetGustFront() const { return GustFront; }
	float GetGustBandZ() const { return GustBandZ; }
	bool IsGustTravelling() const { return Physical == EKeeperPhysical::Gust && Stage == EKeeperStage::Stroke; }
	bool IsPhysicalThreatening() const;
	float GetPhysicalCountdown() const { return PhysicalCountdown; }
	float GetRedCountdown() const { return RedCountdown; }
	float GetYellowCountdown() const { return YellowCountdown; }
	bool IsTalonArmed() const { return bTalonArmed; }
	float GetTalonCooldown() const { return TalonCooldown; }
	FVector2D GetMechanismHome(EKeeperPart Part) const;
	FVector2D GetMuzzle() const { return Anchor + FVector2D(Tuning.MuzzleOffset); }
	FVector2D GetClaw() const { return Anchor + FVector2D(Tuning.ClawOffset); }
	float GetStageRemaining() const { return StageRemaining; }

	/** The shared rule for parity: the sign of the middle curve for a global physical-attack serial. */
	static float MiddleSignForSerial(int32 Serial);
	/** Fan angle (degrees) of shot Index of Count across Spread degrees around Center. */
	static float FanAngleDeg(float CenterDeg, float SpreadDeg, int32 Index, int32 Count);
	/** Which of two same-frame outcomes wins: a fatal player hit beats the final clock hit. */
	static bool ShouldDefeatWin(bool bPlayerDefeated, bool bFightWon);

private:
	struct FPendingShot
	{
		float DelayRemaining = 0.0f;
		FKeeperCommand Command;
	};

	int32 PartIndex(EKeeperPart Part) const { return static_cast<int32>(Part); }
	float PartMaxHp(EKeeperPart Part) const;
	void StartTransition(EKeeperPhase NewPhase, TArray<FKeeperCommand>& Out);
	void FinishTransition(TArray<FKeeperCommand>& Out);
	void ClearDynamicState();
	void TickUnscaled(float Dt, TArray<FKeeperCommand>& Out);
	void TickPending(float WorldDt, TArray<FKeeperCommand>& Out);
	void TickAttacks(float WorldDt, const FKeeperTickInput& Input, TArray<FKeeperCommand>& Out);
	void TickPhysical(float WorldDt, const FKeeperTickInput& Input, TArray<FKeeperCommand>& Out);
	void StartRedVolley(const FKeeperTickInput& Input);
	void StartDoubleBeat(const FKeeperTickInput& Input);
	void StartYellow(const FKeeperTickInput& Input);
	void QueueShot(float Delay, EUmbrellaShotKind Kind, FName Name, const FVector2D& Origin, float AngleDeg, float Speed, float Radius);
	void StartPhysical(EKeeperPhysical Kind, const FKeeperTickInput& Input, TArray<FKeeperCommand>& Out);
	void EnterStage(EKeeperStage NewStage, float Duration, TArray<FKeeperCommand>& Out);
	void CancelPhysical(TArray<FKeeperCommand>& Out);
	void EnterRecovery(float Duration, TArray<FKeeperCommand>& Out);
	void UpdateHead();
	bool IsCastPhysical(EKeeperPhysical Kind) const;
	EKeeperPart CastPart(EKeeperPhysical Kind) const;
	EKeeperPhysical PickScheduled() const;
	bool IsKindEnabled(EKeeperPhysical Kind) const;
	void OpenClock(TArray<FKeeperCommand>& Out, bool bFinalCycle);
	void CloseClock(TArray<FKeeperCommand>& Out);
	void StartEyeBlackout(TArray<FKeeperCommand>& Out);
	void EndEffects(TArray<FKeeperCommand>& Out);
	void BreakPart(EKeeperPart Part, TArray<FKeeperCommand>& Out, FKeeperHitResult& Result);
	void EmitDamage(FName Source, float Amount, TArray<FKeeperCommand>& Out);
	float RedSpeed() const;
	float RedSpread() const;
	float RedSize() const;
	float YellowSpeed() const;
	float SegmentDistance(const FVector2D& P, const FVector2D& A, const FVector2D& B) const;

	FKeeperTuning Tuning;
	FEncounterTuning EncounterTuning;
	FKeeperRuleSwitches Switches;
	FVector2D Anchor = FVector2D::ZeroVector;

	EKeeperPhase Phase = EKeeperPhase::Wings;
	bool bEnded = false;
	TArray<float> PartHp;
	TArray<float> CheckpointHp;
	EKeeperPhase CheckpointPhase = EKeeperPhase::Wings;
	bool bHasCheckpoint = false;

	float TransitionRemaining = 0.0f;
	float PhaseTime = 0.0f;

	// Unscaled timers
	float StunRemaining = 0.0f;
	float BlackoutRemaining = 0.0f;
	float FirePauseRemaining = 0.0f;
	float ClockOpenRemaining = 0.0f;
	float ClockProtectRemaining = 0.0f;
	float FinalCycleTime = 0.0f;
	float SlowRemaining = 0.0f;
	float SlowCooldownRemaining = 0.0f;
	float EyeWindowRemaining = 0.0f;
	float EyeCooldownRemaining = 0.0f;
	bool bSlowUsedThisOpening = false;
	bool bEyeUsedThisOpening = false;

	// World timers
	float RedCountdown = 0.0f;
	float YellowCountdown = 0.0f;
	float PhysicalCountdown = 0.0f;
	float TalonCooldown = 0.0f;
	bool bTalonArmed = true;
	TArray<FPendingShot> Pending;
	int32 NextCastIndex = 0;

	// Physical move
	EKeeperPhysical Physical = EKeeperPhysical::None;
	EKeeperStage Stage = EKeeperStage::Idle;
	float StageRemaining = 0.0f;
	float StageDuration = 0.0f;
	int32 CastSerial = 0;
	bool bDamagedThisCast = false;
	FVector2D LockStart = FVector2D::ZeroVector;
	FVector2D LockEnd = FVector2D::ZeroVector;
	FVector2D HeadPos = FVector2D::ZeroVector;
	FVector2D PrevHeadPos = FVector2D::ZeroVector;
	FVector2D GustFront = FVector2D::ZeroVector;
	float GustBandZ = 0.0f;
	float GustTravelled = 0.0f;
	float MiddleSign = 1.0f;
};
