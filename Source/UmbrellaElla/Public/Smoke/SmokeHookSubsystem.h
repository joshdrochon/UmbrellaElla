#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "InputCoreTypes.h"
#include "Tickable.h"
#include "Smoke/PlaytestRun.h"
#include "SmokeHookSubsystem.generated.h"

enum class EEnemyType : uint8;

/**
 * The smoke hook (pipeline/unreal-rules.md "Smoke hook contract"). Exists only when the game is launched with
 * -SmokeQuitAfter=<s>. It presses Start Game through the Start screen's own path, logs SMOKE_EFFECTIVE at the first
 * gameplay frame and at the end, takes the -SmokeShot= screenshot, then logs SMOKE_OK and quits.
 */
UCLASS()
class UMBRELLAELLA_API USmokeHookSubsystem : public UGameInstanceSubsystem, public FTickableGameObject
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	virtual void Tick(float DeltaTime) override;
	virtual bool IsTickable() const override;
	virtual TStatId GetStatId() const override;

	/** The 1% low in frames per second from a list of frame times in seconds (plain rule function). */
	static float ComputeLowFps(const TArray<float>& FrameSeconds, float LowShare);

	/** The scripted input check: keyboard Shoot hold, then gamepad stick + trigger hold + A (dash). */
	enum class EInputStep : uint8
	{
		Idle,
		KeyHold,
		KeyGap,
		PadHold,
		PadDash,
		PadGap,
		Done
	};

	/**
	 * The input state machine's transitions (plain rule function). InStepSeconds is the time in Step, SinceStartSeconds
	 * the time since gameplay began. Idle waits ShotDelay + a gap, then goes to KeyHold (or Done on a map with no player).
	 */
	static EInputStep NextInputStep(EInputStep Step, double InStepSeconds, double SinceStartSeconds, float ShotDelaySeconds, bool bHasMotor, bool bHasController);

	/**
	 * -SmokeShot timing (plain rule function): true once the level is ready (gameplay running) AND FramesSinceReady
	 * frames have been counted. Wall clock plays no part: a busy machine can run at 0.1 fps and still gets a lit frame.
	 */
	static bool IsShotDue(bool bLevelReady, int32 FramesSinceReady, int32 RequiredFrames);

	/**
	 * Shot readiness (plain rule function): no shader compiles pending, no texture or asset still streaming or compiling,
	 * and Ella's pawn alive. Only frames counted while this holds count toward -SmokeShotFrames (a busy machine still
	 * shows "Preparing Textures" at a fixed frame count, so frames are counted only once everything has settled).
	 */
	static bool IsShotReady(int32 PendingShaderJobs, int32 StreamingResources, int32 PendingAssets, bool bPlayerAlive);

	/** -SmokeShot path: absolute paths stay, a relative one resolves against ProjectDir. */
	static FString ResolveShotPath(const FString& Path, const FString& ProjectDir);

	/** -SmokeEnemy=<family>: true for Roadwarden, Floodstrider or SkyCourier (case-insensitive), the family in OutType. False for anything else. */
	static bool HasEnemyFamilyName(const FString& Name, EEnemyType& OutType);

	/** The -SmokeShotFrames=N value: N when it is at least 1, else the default. */
	static int32 ResolveShotFrames(int32 Requested);

	/** SMOKE_VIEW (plain rule function): true when a projected point lies inside a ViewW x ViewH frame (projection succeeded). */
	static bool IsPixelInFrame(bool bProjected, const FVector2D& Pixel, const FVector2D& ViewSize);

	static constexpr int32 DefaultShotFrames = 60;
	/** The shot may take this long (seconds past -SmokeQuitAfter) before the run quits without it. */
	static constexpr double ShotMaxWaitSeconds = 1200.0;
	/** The -SmokeEnemy stand-in appears this far right of Ella (cm). */
	static constexpr double SmokeEnemyOffsetX = 700.0;

	static constexpr float MillisecondsPerSecond = 1000.0f;
	/** Seconds after the screenshot request before the hook checks the file exists (smoke fallback writes it itself). */
	static constexpr double ShotWriteWaitSeconds = 1.0;
	/** Alpha of the read-back window shot (the Slate read leaves it at zero). */
	static constexpr uint8 OpaqueAlpha = 255;

	/** Input check timeline, seconds after the screenshot moment. Each hold lasts HoldSeconds, then a settle gap. */
	static constexpr float InputHoldSeconds = 0.5f;
	static constexpr float InputGapSeconds = 0.3f;
	/** Past -SmokeQuitAfter the run waits at most this long for the input check to finish. */
	static constexpr float InputGraceSeconds = 6.0f;

private:
	enum class EStage : uint8
	{
		WaitingForStart,
		Running,
		Finished
	};

	FString BuildEffectiveLine(const TCHAR* At, const TCHAR* Outcome) const;
	void LogEnd(const TCHAR* Outcome);
	void SaveWindowShotDirect();
	/** At the shot: log what the camera sees (view target, Ella and arena centre in frame) as SMOKE_VIEW. */
	void LogShotView(class AUmbrellaPlayerController* Flow) const;
	/** -SmokeKeeper / -SmokeEnemy: set up the scene once, on the first gameplay frame (workbench builds only). */
	void ApplySceneSwitches();

	void TickInputCheck(class AUmbrellaPlayerController* Flow);
	bool CanSendKey(class APlayerController* Controller, const FKey& Key, EInputEvent Event, float Amount) const;
	bool HasMotor(FVector& OutVelocity) const;

	EInputStep InputStep = EInputStep::Idle;
	double InputStepStart = 0.0;
	bool bInputOk = false;
	bool bGamepadOk = false;
	float InputVz = 0.0f;
	float PadAttackVz = 0.0f;
	float PadPeakVx = 0.0f;

	/** -SmokePlaytest: the scripted measurement run (null otherwise). */
	TUniquePtr<FPlaytestRun> Playtest;
	bool bPlaytestStarted = false;

	EStage Stage = EStage::WaitingForStart;
	TArray<float> FrameSeconds;
	FString ShotPath;
	double InitTime = 0.0;
	double StartTime = 0.0;
	float QuitAfterSeconds = 0.0f;
	float LoadMs = 0.0f;
	bool bShotTaken = false;
	bool bShotChecked = false;
	double ShotRequestedAt = 0.0;
	bool bSelectedStart = false;
	int32 ShotFrames = DefaultShotFrames;
	int32 FramesSinceReady = 0;
	bool bSceneApplied = false;
	bool bShotReadyLogged = false;
};
