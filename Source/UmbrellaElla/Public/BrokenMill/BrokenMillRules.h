#pragma once

#include "CoreMinimal.h"
#include "BrokenMillRules.generated.h"

struct FBrokenMillTuning;

UENUM()
enum class EMillGuardState : uint8
{
	Idle,
	Warning,
	Recovery
};

UENUM()
enum class EMillGuardEvent : uint8
{
	None,
	WarningStarted,
	ShotReleased,
	WarningAborted,
	WarningCancelled
};

/** The 10 HP introduction, or the 20 HP comparison that changes nothing else. */
UENUM()
enum class EMillGuardProfile : uint8
{
	Introduction,
	Comparison
};

/** What the visible warning tell shows. */
UENUM()
enum class EMillTellPose : uint8
{
	Hidden,
	Raised,
	Lowered
};

UENUM()
enum class EMillWind : uint8
{
	None,
	UpperReset,
	LowerOnward
};

/** What the guard sees this step. */
struct UMBRELLAELLA_API FMillGuardInputs
{
	FVector Ella = FVector::ZeroVector;
	bool bPaused = false;
	bool bInActivationRegion = false;
	/** Range, no body/land muzzle occlusion, ahead-right, clear ray and a reachable descent all hold. */
	bool bEngagementValid = false;
	bool bPassedBehind = false;
	/** Reset, assist, underpass or exit: no new warning. */
	bool bInNoWarningPhase = false;
	bool bShotGone = false;
};

/** The stationary guard: one warning, one straight shot at the target captured at warning start, one shot per pass. */
struct UMBRELLAELLA_API FMillGuard
{
	EMillGuardState State = EMillGuardState::Idle;
	float Timer = 0.0f;
	FVector CapturedTarget = FVector::ZeroVector;
	bool bArmed = true;
	bool bEnabled = true;
	bool bShotLive = false;
	int32 ShotSerial = 0;

	/** Step the guard. Pause freezes every clock. */
	EMillGuardEvent Advance(const FBrokenMillTuning& Tuning, float DeltaTime, const FMillGuardInputs& Inputs);

	/** Disabling cancels a pending warning; a launched shot flies on. */
	void SetGuardEnabled(bool bNewEnabled);

	/** Retry: nothing stale survives. */
	void Reset();
};

/** One logged shot (prototype checks). */
struct UMBRELLAELLA_API FMillShotLogEntry
{
	int32 Serial = 0;
	float EmissionTime = 0.0f;
	FVector EmissionPosition = FVector::ZeroVector;
	FName FirstContact = NAME_None;
	float ImpactTime = -1.0f;
};

struct UMBRELLAELLA_API FMillShotLog
{
	TArray<FMillShotLogEntry> Entries;

	void RecordEmission(int32 Serial, float Time, const FVector& Position);
	void RecordFirstContact(int32 Serial, FName Contact, float Time);
};

/** What a candidate reuse of the room's setup must clear before it joins the catalogue pool. */
struct UMBRELLAELLA_API FMillPoolState
{
	bool bPendingWarning = false;
	bool bLiveShot = false;
	bool bDelayedImpact = false;
	int32 ActiveOwners = 0;
	int32 ActiveEnemyBullets = 0;
	bool bNewSimultaneousTiming = false;
	bool bMirrored = false;
};

/** Plain Broken Mill rule functions (tests call these). */
struct UMBRELLAELLA_API FBrokenMillRules
{
	static bool IsInActivationRegion(const FBrokenMillTuning& Tuning, const FVector& Ella);

	/** Room point to the room's own X/Z in a world transform's frame is the caller's job; these are room coordinates. */
	static bool IsRayClearOfRotor(const FBrokenMillTuning& Tuning, const FVector2D& From, const FVector2D& To);
	static bool IsRayClearOfIsland(const FBrokenMillTuning& Tuning, const FVector2D& From, const FVector2D& To);

	/** Muzzle ahead/right of Ella, in range, ray clear of rotor and island; descent reachability is the caller's. */
	static bool IsEngagementValid(const FBrokenMillTuning& Tuning, const FVector2D& Ella, bool bDescentReachable);

	/** Guard HP for a profile: the comparison changes HP only. */
	static float GetGuardHp(const FBrokenMillTuning& Tuning, EMillGuardProfile Profile);

	/** Raised for the whole warning, lowered for the quiet recovery after an aborted release, else hidden. */
	static EMillTellPose GetTellPose(EMillGuardState State, bool bLastReleaseAborted, bool bGuardAlive);

	/** Lifetime of the guard shot: range / speed (at most 4.167 s by default). */
	static float GetGuardShotLifetime(const FBrokenMillTuning& Tuning);

	/** Local wind choice from Ella's height: the two bands never overlap, so neither steals the other. */
	static EMillWind SelectWind(const FBrokenMillTuning& Tuning, float EllaZ);

	/**
	 * Local eligibility: the one mill wind Ella's ROOT may ride, by height (SelectWind) and only inside the firing
	 * column. The room enables only this band's volume, so a tall collision body in the gap cannot touch both.
	 */
	static EMillWind GetEligibleWind(const FBrokenMillTuning& Tuning, const FVector2D& Ella);

	static bool IsInMissedCurrentAssist(const FBrokenMillTuning& Tuning, const FVector2D& Ella);

	/** Underpass clearances for a root height. */
	static float GetUndersideClearance(const FBrokenMillTuning& Tuning, float Root);
	static float GetFloorClearance(const FBrokenMillTuning& Tuning, float Root);

	/** Gap between the highest useful friendly shot and the rotor bottom. */
	static float GetRotorClearanceAboveShots(const FBrokenMillTuning& Tuning, float HighestShotCentre);

	/** Margin between the protected core plus Ella half width plus bullet radius and where the leftmost ray ends. */
	static float GetReturnMargin(const FBrokenMillTuning& Tuning);

	/** Guard feet (GuardFeetX, bottom of the target box). */
	static FVector2D GetGuardFeet(const FBrokenMillTuning& Tuning);
	/** Lowered underpass step root envelope: LoweredStepEnvelope (185-285). */
	static FVector2D GetLoweredStepEnvelope(const FBrokenMillTuning& Tuning);
	/** The ascent toward the exit has started: Ella is right of AscentStartX. */
	static bool IsInAscent(const FBrokenMillTuning& Tuning, const FVector2D& Ella);
	/** AscentStartX leaves the island edge, Ella's half width and the margin behind it. */
	static bool IsAscentStartClear(const FBrokenMillTuning& Tuning);
	/** Inside the protected root core box (ProtectedCoreX x ProtectedCoreZ). */
	static bool IsInProtectedCore(const FBrokenMillTuning& Tuning, const FVector2D& Root);
	/** Inside the vertical lift: |x - end x| <= half-width and z at or below the end z. */
	static bool IsInVerticalLift(const FBrokenMillTuning& Tuning, const FVector2D& Root);
	/** The root has dropped to the reopen height, so the decision to reopen is now. */
	static bool IsRootAtReopen(const FBrokenMillTuning& Tuning, float RootZ);

	/** Ella root range [min, max] that lets a shot hit the target, with the island blocking low lines. */
	static FVector2D GetFiringWindowRoot(const FBrokenMillTuning& Tuning);

	/** The same window for a plain comparison target of the given height (no island). */
	static FVector2D GetComparisonWindowRoot(const FBrokenMillTuning& Tuning, float TargetHeight);

	static float GetWindowSeconds(const FVector2D& Window, float FallSpeed);

	/** (floor, ceil) of the emissions a window of the given length holds at an arbitrary cadence phase. */
	static FIntPoint GetEmissionCountRange(float WindowSeconds, float PeriodSeconds);

	/** Time from the muzzle to first contact with the target's left face. */
	static float GetFirstContactSeconds(const FBrokenMillTuning& Tuning, float RootX, float HeroSize);

	/** Shadow-fixture muzzle offset (X, Z) for a HeroSize. */
	static FVector2D GetMuzzleOffset(const FBrokenMillTuning& Tuning, float HeroSize);

	/** Shadow tests never write earned progression. */
	static bool IsProgressionWriteAllowed();

	/** Empty = the candidate may join the pool; each entry names a failed check. */
	static TArray<FName> GetPoolGateFailures(const FBrokenMillTuning& Tuning, const FMillPoolState& State);
};
