#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
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
	/** Seconds after the screenshot request before the hook checks the file exists (smoke fallback writes it itself). */
	static constexpr double ShotWriteWaitSeconds = 1.0;

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
};
