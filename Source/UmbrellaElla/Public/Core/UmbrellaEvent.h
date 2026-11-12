#pragma once

#include "CoreMinimal.h"
#include "UmbrellaEvent.generated.h"

/** The manifest event vocabulary (docs/feature-manifest.json "events"). Append only; never reorder. */
UENUM()
enum class EUmbrellaEventType : uint8
{
	UmbrellaConfigChanged,
	LiftAvailabilityChanged,
	PlayerHealthChanged,
	ProjectileSpawned,
	ProjectileContact,
	CatchAttempt,
	CatchSucceeded,
	CatchFailed,
	BossTargetHit,
	BossAttackTelegraphed,
	WindEntered,
	WindExited,
	PlayerDefeated,
	EncounterCompleted,
	TestPresetLoaded,
	AnimationCue,
	BackgroundLooped,
	ModeSelected,
	PhaseStarted,
	CheckpointReached,
	CheckpointRetried,
	LifeLost,
	BossPartDestroyed,
	XPAwarded,
	LevelGained,
	RunCompleted,
	Count UMETA(Hidden)
};

/** One event. Fields follow the manifest event_fields; Value/Amount carry the payload number (health, damage, XP...). */
USTRUCT()
struct UMBRELLAELLA_API FUmbrellaEvent
{
	GENERATED_BODY()

	UPROPERTY()
	EUmbrellaEventType Type = EUmbrellaEventType::UmbrellaConfigChanged;

	UPROPERTY()
	int64 Frame = 0;

	UPROPERTY()
	FName SourceId;

	UPROPERTY()
	FName TargetId;

	UPROPERTY()
	FName RunConfigId;

	UPROPERTY()
	TArray<FName> FeatureIds;

	/** Event-specific label (attack name, part name, phase name...). */
	UPROPERTY()
	FName Detail;

	UPROPERTY()
	float Value = 0.0f;

	UPROPERTY()
	int32 Amount = 0;
};
