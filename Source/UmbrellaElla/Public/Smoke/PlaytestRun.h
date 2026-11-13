#pragma once

#include "CoreMinimal.h"
#include "Delegates/IDelegateInstance.h"

class AEllaCharacter;
class ABrokenMillRoom;
class AUmbrellaLevelDirector;
class AWindCurrent;
class UWorld;
class UUmbrellaEventBus;

/** Edge a played path left a wind band by (room coordinates). */
enum class EPlaytestBandExit : uint8
{
	None,
	Right,
	Left,
	Top,
	Bottom
};

/** Where the real-time part of the run is. */
enum class EPlaytestPhase : uint8
{
	Idle,
	Haz,
	Flow28,
	Done
};

/**
 * The scripted playtest run behind -SmokePlaytest (lane playtest). It drives Ella through the measured scenarios with the
 * Motor, Health and Attack components of the live game and logs one PLAYTEST_* line per scenario for
 * tools/build/playtest_check.py, which compares them with fixed recorded calibration ranges (profile mill_lower_v1).
 * Ella is moved only by her own motor and the room's real wind volumes, except where a line says so (start placement,
 * the FLOW-28 route driver). Anything the run cannot measure is listed in that line's not_measured= field, never typed in
 * as a value. Plain rule functions below are the unit-testable part; UmbrellaElla.Smoke.World.PlaytestRunEmitsLines runs
 * the whole thing in a transient world.
 */
class UMBRELLAELLA_API FPlaytestRun
{
public:
	/** Calibration profile these paths are recorded under (tools/build/playtest_calibration.py). */
	static constexpr const TCHAR* CalibrationProfile = TEXT("mill_lower_v1");
	/** Hold time of the HAZ run in real seconds (Broken Mill room, natural attempts, no aids). */
	static constexpr float HazRunSeconds = 25.0f;
	/** Longest scripted route travel for FLOW-28 before it gives up, seconds. */
	static constexpr float FlowTravelMaxSeconds = 20.0f;
	/** Extra wait past the hook grace for the synchronous scenarios and the flow check, seconds. */
	static constexpr float PlaytestSetupGraceSeconds = 10.0f;
	/** Fake clock step between scripted hits, seconds (clears the post-hit window). */
	static constexpr double HitClockStep = 10.0;
	/** Health left after the scripted "minimum health" damage, health units. */
	static constexpr float MinHealthLeft = 0.1f;
	/** Spacing of the camera-lead and frame samples along the route, world units. */
	static constexpr float LeadSampleStep = 100.0f;
	/** Room X where the broken-mill run starts Ella, left of the firing column. */
	static constexpr float RoomStartX = 640.0f;
	/** Health damage taken before the carry-health measurement. */
	static constexpr float CarryDamage = 1.0f;
	/** The low-health run starts with this share of one life. */
	static constexpr float LowHealthShare = 0.5f;
	/** Fixed step of the synchronous scenarios, seconds. */
	static constexpr float StepSeconds = 1.0f / 60.0f;
	/** Longest played CAM path or transient phase, seconds. */
	static constexpr float CamSeconds = 3.0f;
	/** Momentum settle before each CAM profile: free fall far from every current, seconds. */
	static constexpr float SettleSeconds = 1.0f;
	/** Ella enters a band this far inside its left edge, room units. */
	static constexpr float PathEntryInset = 1.0f;
	/** Acceleration / reacquisition time is to this share of the current's speed. */
	static constexpr float CarryShare = 0.9f;
	/** Braking / decay time is to this share of the speed before the change. */
	static constexpr float DecayShare = 0.1f;
	/** After reopening, watch this long for a catch by a current, seconds. */
	static constexpr float CatchWatchSeconds = 1.0f;
	/** Park point for the momentum settle, room units (far left of the room, clear of every current). */
	static constexpr float ParkRoomX = -4000.0f;
	static constexpr float ParkRoomZ = 2000.0f;
	/** A run counts as boring (no useful action) when idle share of the HAZ run is above this. */
	static constexpr float BoringIdleShare = 0.5f;
	/** Drawn-width tolerance, world units. */
	static constexpr float DrawnWidthTolerance = 4.0f;
	/** World X of the scratch room: far left of the route start, so the level director never sees Ella past a checkpoint. */
	static constexpr double ScratchRoomX = -60000.0;
	/** A step longer than speed x time x this, plus PlaytestTeleportSlack, is a teleport. */
	static constexpr float PlaytestTeleportSpeedShare = 1.5f;
	static constexpr float PlaytestTeleportSlack = 2.0f;
	/** FLOW-28 route driver: scripted travel speed along the route, world units per second. */
	static constexpr float FlowTravelSpeed = 4000.0f;
	/** FLOW-28: how long after the handoff the camera is watched for settling, seconds. */
	static constexpr float FlowSettleSeconds = 0.5f;
	/** FLOW-28: camera X movement below this over the settle window counts as settled, world units. */
	static constexpr float FlowSettleTolerance = 1.0f;

	/** Level director seed of the FLOW-25 and FLOW-28 route. */
	static constexpr int64 RouteSeed = 1;
	/** Start of the fake clock used for scripted damage, seconds. */
	static constexpr double CarryClockStart = 1000.0;
	/** Share of the arena view height used as the vertical extent of a backdrop frame. */
	static constexpr float FrameHeightShare = 1.0f;

	/** -PlaytestWindRelay: diagnosis run that re-sends wind events with the contract player id. Its lines carry relay=1. */
	static bool IsWindRelayRun();

	/** Which edge of Band (room X/Z) Root has left by, or None while inside. Right and Left win over Top and Bottom. */
	static EPlaytestBandExit BandExit(const FVector2D& Root, const FBox2D& Band);

	/** Log word for a band exit. */
	static const TCHAR* BandExitName(EPlaytestBandExit Exit);

	/** Share of Seconds spent with no useful action. 1 when Seconds is not positive. */
	static float IdleShare(float IdleSeconds, float Seconds);

	/** Format the key=value tail of a line: PLAYTEST_<Key> then the pairs. */
	static FString FormatLine(const TCHAR* Key, const TArray<TPair<FString, FString>>& Pairs);

	/** The frame (X, Z box) is covered when the X spans of the layers whose Z range holds the frame's whole height cover its width. */
	static bool IsFrameCovered(const FBox2D& Frame, const TArray<FBox2D>& Layers);

	/** A tick moved Ella farther than her own speed allows (the faster of before/after, times the share, plus slack). */
	static bool IsTeleportStep(float StepDistance, float SpeedBefore, float SpeedAfter, float DeltaSeconds);

	/** A required current is live: present, shown, force above zero and its volume still generating overlaps. */
	static bool IsCurrentLive(const AWindCurrent* Current);

	~FPlaytestRun();

	/** Run the synchronous scenarios (CAM-04, CAM-07 falls, FLOW-25) and start the broken-mill run. Ella defaults to player 0's pawn. */
	void Start(UWorld* World, AEllaCharacter* EllaOverride = nullptr);

	/** Measure FLOW-28 on this director instead of the game mode's (world tests have no game mode). */
	void UseDirector(AUmbrellaLevelDirector* Director);

	/** Advance the real-time part (HAZ run, then the FLOW-28 route). Check IsDone for the end. */
	void Advance(float DeltaSeconds);

	bool IsDone() const { return Phase == EPlaytestPhase::Done; }

	/** Every PLAYTEST_* line this run wrote, in order. */
	const TArray<FString>& GetLines() const { return Lines; }

private:
	void Emit(const TCHAR* Key, const TArray<TPair<FString, FString>>& Pairs);
	void MeasureCam04(AEllaCharacter* Ella);
	void MeasureCam04Path(AEllaCharacter* Ella, const TCHAR* Path, bool bMinHealth, float Trim);
	void MeasureCam04Transients(AEllaCharacter* Ella);
	void MeasureCam07(AEllaCharacter* Ella);
	void MeasureCam07Case(AEllaCharacter* Ella, const TCHAR* Case, float ReopenRootZ);
	void PlaytestSettle(AEllaCharacter* Ella);
	void PlaytestPlace(AEllaCharacter* Ella, const FVector2D& RoomPoint) const;
	void MeasureFlow25();
	void AdvanceHaz(float DeltaSeconds);
	void FinishHaz();
	void StartFlow28();
	void AdvanceFlow28(float DeltaSeconds);
	void FinishFlow28(const TCHAR* NotMeasured);
	void Finish();
	void StartWindRelay(AEllaCharacter* Ella);
	void StopWindRelay();

	TWeakObjectPtr<UWorld> WorldPtr;
	TWeakObjectPtr<AEllaCharacter> EllaPtr;
	TWeakObjectPtr<ABrokenMillRoom> Room;
	TWeakObjectPtr<AUmbrellaLevelDirector> DirectorOverride;
	TWeakObjectPtr<AUmbrellaLevelDirector> FlowDirector;
	TArray<FString> Lines;
	TWeakObjectPtr<UUmbrellaEventBus> RelayBus;
	FDelegateHandle RelayEnteredHandle;
	FDelegateHandle RelayExitedHandle;
	EPlaytestPhase Phase = EPlaytestPhase::Idle;

	// HAZ run.
	float HazElapsed = 0.0f;
	float IdleSeconds = 0.0f;
	float HealthAtStart = 0.0f;
	float StartGuardHp = 0.0f;
	int32 ShotsAtStart = 0;
	int32 TeleportSteps = 0;
	float ProtectedSeconds = 0.0f;
	FVector LastEllaLocation = FVector::ZeroVector;
	float LastEllaSpeed = 0.0f;

	// CAM-07 persistence: required currents sampled every HAZ tick while the guard lives.
	int32 CurrentSamples = 0;
	int32 CurrentSamplesLive = 0;
	bool bGuardDiedWhileSampling = false;

	// FLOW-28 route.
	float FlowElapsed = 0.0f;
	float FlowTravelX = 0.0f;
	int32 FlowHealthBefore = 0;
	int32 FlowThreatsAtHandoff = -1;
	int32 FlowHealthAtHandoff = 0;
	float FlowCameraAtHandoff = 0.0f;
	float FlowHandoffAt = -1.0f;
	int32 FlowCheckpointsPassed = 0;

	/** Fake clock for scripted hits; only grows, so no hit lands inside an earlier hit's post-hit window. */
	double ScriptClock = 0.0;
	/** Where Ella stood before the run; she goes back there when it ends. */
	FVector EllaHome = FVector::ZeroVector;
};
