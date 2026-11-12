#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "InputCoreTypes.h"
#include "Tickable.h"
#include "SmokeHookSubsystem.generated.h"

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

	static constexpr float MillisecondsPerSecond = 1000.0f;

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

	void TickInputCheck(class AUmbrellaPlayerController* Flow);
	bool SendKey(class APlayerController* Controller, const FKey& Key, EInputEvent Event, float Amount) const;
	bool ReadMotor(FVector& OutVelocity) const;

	EInputStep InputStep = EInputStep::Idle;
	double InputStepStart = 0.0;
	bool bInputOk = false;
	bool bGamepadOk = false;
	float InputVz = 0.0f;
	float PadVx = 0.0f;
	float PadAttackVz = 0.0f;
	float PadPeakVx = 0.0f;

	EStage Stage = EStage::WaitingForStart;
	TArray<float> FrameSeconds;
	FString ShotPath;
	double InitTime = 0.0;
	double StartTime = 0.0;
	float QuitAfterSeconds = 0.0f;
	float LoadMs = 0.0f;
	bool bShotTaken = false;
	FDelegateHandle ShotHandle;
	bool bSelectedStart = false;
};
