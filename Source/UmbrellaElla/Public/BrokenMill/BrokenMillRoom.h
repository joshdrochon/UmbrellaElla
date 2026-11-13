#pragma once

#include "CoreMinimal.h"
#include "BrokenMill/BrokenMillRules.h"
#include "Core/UmbrellaTuning.h"
#include "GameFramework/Actor.h"
#include "Projectile/UmbrellaShotReceiver.h"
#include "BrokenMillRoom.generated.h"

struct FBrokenMillTuning;

class ABrokenMillIsland;
class AUmbrellaProjectile;
class AUmbrellaTrap;
class AWindCurrent;
class UBoxComponent;
class USceneComponent;
class UStaticMeshComponent;

/**
 * The Broken Mill Crossing one-room test: a stationary Roadwarden guard on an island, an air-mill rotor, one
 * warning and one straight shot per pass. Spawn it from code anywhere; the actor origin is the room's bottom-left.
 * Lane enemies. Placeholder visuals are engine cubes; no art is imported.
 */
UCLASS()
class UMBRELLAELLA_API ABrokenMillRoom : public AActor, public IUmbrellaShotReceiver
{
	GENERATED_BODY()

public:
	ABrokenMillRoom();

	/** Spawn the island, the target box and the rotor trap. Safe to call once, after the actor is in a world. */
	void BuildRoom();

	void SetTargetActor(AActor* NewTarget);

	/** Spawn the upper reset (left) and lower onward (right) currents over the firing column. Once, after BuildRoom. */
	void BuildWinds();

	/** Freeze the guard like a game pause (tests; the real pause is read from the world). */
	void SetSimulationPaused(bool bPaused) { bSimulationPaused = bPaused; }

	/** Cancel a pending warning and stop new fire; a launched shot continues. */
	void DisableGuard();

	/** Retry: full guard HP, idle guard, empty log. */
	void ResetForRestart();

	/**
	 * Pick the 10 HP introduction or the 20 HP comparison (ONE changed variable). Takes effect now and on
	 * every retry. BuildRoom picks Comparison when the command line has -MillGuardComparison.
	 */
	void SetGuardProfile(EMillGuardProfile NewProfile);
	EMillGuardProfile GetGuardProfile() const { return Profile; }

	virtual EUmbrellaShotResult ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation) override;

	virtual void Tick(float DeltaSeconds) override;

	/** Advance the guard one step with explicit time (tests). Returns the guard event. */
	EMillGuardEvent StepSeconds(float DeltaSeconds);

	FVector RoomToWorld(const FVector2D& RoomPoint) const;
	FVector2D WorldToRoom(const FVector& WorldPoint) const;

	float GetGuardHp() const { return GuardHp; }
	const FMillGuard& GetGuard() const { return Guard; }
	const FMillShotLog& GetShotLog() const { return ShotLog; }
	const FBrokenMillTuning& GetMillTuning() const { return Tuning(); }
	AUmbrellaTrap* GetRotor() const { return Rotor; }
	ABrokenMillIsland* GetIsland() const { return Island; }
	UStaticMeshComponent* GetTellVisual() const { return TellVisual; }
	UStaticMeshComponent* GetGuardVisual() const { return GuardVisual; }
	EMillTellPose GetTellPose() const;
	int32 GetShotsFired() const { return ShotsFired; }
	AWindCurrent* GetUpperWind() const { return UpperWind; }
	AWindCurrent* GetLowerWind() const { return LowerWind; }

	/** How many times the guard reported this event since the last restart (world ticks discard the return value). */
	int32 GetEventCount(EMillGuardEvent Event) const { return EventCounts.FindRef(Event); }

private:
	void ReleaseShot();

	/** Show, hide or lower the warning tell and hide the guard body once it is down. */
	void UpdateVisuals();

	/** Enable only the wind band Ella's root is eligible for (no target known: both stay on). */
	void ApplyWindEligibility(EMillWind Eligible);

	UPROPERTY(VisibleAnywhere, Category = "BrokenMill")
	TObjectPtr<USceneComponent> Root;

	UPROPERTY()
	TObjectPtr<ABrokenMillIsland> Island;

	UPROPERTY(VisibleAnywhere, Category = "BrokenMill")
	TObjectPtr<UStaticMeshComponent> GuardVisual;

	UPROPERTY(VisibleAnywhere, Category = "BrokenMill")
	TObjectPtr<UStaticMeshComponent> TellVisual;

	UPROPERTY(VisibleAnywhere, Category = "BrokenMill")
	TObjectPtr<UBoxComponent> TargetBox;

	UPROPERTY()
	TObjectPtr<AUmbrellaTrap> Rotor;

	UPROPERTY()
	TObjectPtr<AWindCurrent> UpperWind;

	UPROPERTY()
	TObjectPtr<AWindCurrent> LowerWind;

	/** The two wind volumes, found once in BuildWinds (ApplyWindEligibility runs every tick). */
	UPROPERTY()
	TObjectPtr<UBoxComponent> UpperVolume;

	UPROPERTY()
	TObjectPtr<UBoxComponent> LowerVolume;

	UPROPERTY()
	TWeakObjectPtr<AActor> TargetActor;

	UPROPERTY()
	TWeakObjectPtr<AUmbrellaProjectile> ActiveShot;

	const FBrokenMillTuning& Tuning() const { return GetDefault<UUmbrellaTuning>()->BrokenMill; }
	FMillGuard Guard;
	FMillShotLog ShotLog;
	float GuardHp = 0.0f;
	float Clock = 0.0f;
	int32 ShotsFired = 0;
	bool bSimulationPaused = false;
	bool bLastReleaseAborted = false;
	EMillGuardProfile Profile = EMillGuardProfile::Introduction;
	TMap<EMillGuardEvent, int32> EventCounts;
};
