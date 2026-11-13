#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "Tickable.h"
#include "Smoke/AgentPlayRules.h"
#include "AgentPlayHookSubsystem.generated.h"

class AEllaCharacter;
class ABrokenMillRoom;

/**
 * Agent play hook (decision D-new-haz16-agent-playtest). Workbench builds only, and only when the game starts with
 * -AgentPlay=<dir>. An outside player (tools/build/agent_play.py) plays the Broken Mill room from the rendered screen:
 *  - the hook writes the window to <dir>/frames/fNNNNNN.jpg about every 150 ms while the game runs, and once more when
 *    a turn ends;
 *  - the player writes <dir>/turn_NNNN.txt (a key-press script, see AgentPlayRules::ParseTurn); the hook runs it through
 *    APlayerController::InputKey, the same path as the keyboard, then pauses until the next turn file;
 *  - <dir>/status.json says where the run is (waiting, ready, running, paused, ended) and <dir>/result.json holds the
 *    measured numbers at the end. The player never sees these two files.
 * There is no way to move, aim, heal or skip a wait from here; pausing between turns only stops the clock while the
 * player thinks, so a slow player does not cost game time.
 * Options: -AgentPlayLow (start at half a life), -AgentPlayMaxSeconds=<s> (game seconds before the attempt is cut),
 * -AgentPlayIdleTimeout=<s> (real seconds to wait for a turn file); -MillGuardComparison picks the 20 HP guard.
 */
UCLASS()
class UMBRELLAELLA_API UAgentPlayHookSubsystem : public UGameInstanceSubsystem, public FTickableGameObject
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	virtual void Tick(float DeltaTime) override;
	virtual bool IsTickable() const override;
	virtual bool IsTickableWhenPaused() const override { return true; }
	virtual TStatId GetStatId() const override;

	/** Real seconds between frames while the game runs. */
	static constexpr double FrameIntervalSeconds = 0.15;
	/** While paused the picture refreshes this many frame intervals apart. */
	static constexpr double PausedFrameFactor = 4.0;
	static constexpr double MillisPerSecond = 1000.0;
	static constexpr uint8 OpaqueAlpha = 255;
	/** A window pixel at or below this in every channel counts as empty (the scene shows through). */
	static constexpr uint8 EmptyPixelMax = 2;
	/** The test light: shines toward -Y (into the screen), at this brightness in lux. */
	static constexpr float AgentPlayLightPitch = 0.0f;
	static constexpr float AgentPlayLightYaw = -90.0f;
	static constexpr float AgentPlayLightLux = 6.0f;
	/** Default game seconds an attempt may last, and real seconds the hook waits for a turn file. */
	static constexpr float DefaultMaxGameSeconds = 90.0f;
	static constexpr float DefaultIdleTimeoutSeconds = 600.0f;
	/** Real seconds the hook waits after the result is written before it exits. */
	static constexpr double ExitDelaySeconds = 2.0;
	/** The low-health attempt starts with this share of one life (same share as the scripted playtest). */
	static constexpr float LowHealthShare = 0.5f;
	/** Fake clock step for the one scripted starting hit of a low-health attempt (clears the post-hit window). */
	static constexpr double LowHealthClockStart = 1000.0;
	/** Room X Ella starts at, left of the firing column (the same start as the scripted run). */
	static constexpr float RoomStartX = 640.0f;
	/** A step longer than speed x time x this, plus the slack, counts as a teleport (same measure as the scripted run). */
	static constexpr float TeleportSlack = 2.0f;
	static constexpr float TeleportSpeedShare = 2.5f;

private:
	enum class EState : uint8
	{
		WaitingForStart,
		Setup,
		Paused,
		Running,
		Ended
	};

	void TickSetup();
	void TickPaused();
	void TickRunning(float DeltaTime);
	void BeginTurn(const AgentPlayRules::FTurn& Turn, int32 TurnNumber);
	void EndTurn();
	void Finish(const TCHAR* Outcome);

	void PressKey(const FName& KeyName);
	void ReleaseKey(const FName& KeyName);
	void SendKey(const FName& KeyName, EInputEvent Event);
	void ReleaseAllKeys();
	void WriteFrame();
	void WriteStatus(const TCHAR* Word) const;
	void WriteResult(const TCHAR* Outcome) const;
	void WriteTextAtomic(const FString& Path, const FString& Text) const;
	void SetPaused(bool bPaused);
	FString FilePath(const FString& Name) const;

	EState State = EState::WaitingForStart;
	FString Dir;
	float MaxGameSeconds = DefaultMaxGameSeconds;
	float IdleTimeoutSeconds = DefaultIdleTimeoutSeconds;
	bool bLow = false;
	bool bSelectedStart = false;
	bool bLitByHook = false;

	TWeakObjectPtr<AEllaCharacter> Ella;
	TWeakObjectPtr<ABrokenMillRoom> Room;

	int32 FrameNumber = 0;
	int32 TurnNumber = 0;
	double LastFrameReal = 0.0;
	double WaitingSince = 0.0;
	double EndedAt = 0.0;

	AgentPlayRules::FTurn Active;
	double TurnMillisElapsed = 0.0;
	int32 NextEvent = 0;
	TSet<FName> Held;

	// Measured, never given to the player.
	float HealthAtStart = 0.0f;
	float StartGuardHp = 0.0f;
	int32 ShotsAtStart = 0;
	float GameSeconds = 0.0f;
	float OffLineSeconds = 0.0f;
	float IdleSeconds = 0.0f;
	int32 TeleportSteps = 0;
	int32 Turns = 0;
	int32 WarningsSeen = 0;
	FVector LastLocation = FVector::ZeroVector;
	float LastSpeed = 0.0f;
	TArray<FString> EventLog;
};
