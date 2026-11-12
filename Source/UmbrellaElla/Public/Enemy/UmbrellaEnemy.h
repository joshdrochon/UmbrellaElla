#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaEvent.h"
#include "Enemy/EnemyRules.h"
#include "Enemy/EnemyTuning.h"
#include "Core/UmbrellaTuning.h"
#include "GameFramework/Actor.h"
#include "Projectile/UmbrellaShotReceiver.h"
#include "UmbrellaEnemy.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

/**
 * One regular enemy (Roadwarden, Floodstrider or Sky Courier): patrols, stops, aims for a fixed time, fires one
 * committed shot of its placed colour, recovers. Takes damage from player blasts through IUmbrellaShotReceiver.
 * Lane enemies. Placeholder visual is an engine cube.
 */
UCLASS()
class UMBRELLAELLA_API AUmbrellaEnemy : public AActor, public IUmbrellaShotReceiver
{
	GENERATED_BODY()

public:
	AUmbrellaEnemy();

	/** Pick the type, the (cosmetic) gender and the placed shot colour; resets HP, brain and courier slots. */
	void Configure(EEnemyType NewType, EEnemyGender NewGender, EUmbrellaShotKind NewShotKind);

	/** Set the actor to aim at; when unset the first player pawn is used. */
	void SetTargetActor(AActor* NewTarget);

	/** Rebuild everything a retry needs: full HP, patrol start, all eight courier slots. */
	void ResetForRestart();

	virtual EUmbrellaShotResult ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation) override;

	virtual void Tick(float DeltaSeconds) override;

	/** Advance without the engine tick (tests). Returns the brain event. */
	EEnemyBrainEvent StepSeconds(float DeltaSeconds);

	EEnemyType GetEnemyType() const { return Type; }
	EEnemyGender GetGender() const { return Gender; }
	EUmbrellaShotKind GetShotKind() const { return ShotKind; }
	EEnemyState GetEnemyState() const { return Brain.State; }
	float GetHp() const { return Brain.Hp; }
	float GetMaxHp() const { return Profile.Hp; }
	int32 GetShotsFired() const { return ShotsFired; }
	int32 GetCourierSlotsRemaining() const { return Packets.GetRemaining(); }
	const FEnemyProfile& GetProfile() const { return Profile; }
	FVector GetMuzzleLocation() const;

protected:
	virtual void BeginPlay() override;

private:
	void ReleaseShot();
	void Defeat();
	void BroadcastEnemyEvent(EUmbrellaEventType EventType, FName Detail, float Value) const;
	bool CanResolveTarget(FVector& OutLocation) const;

	UPROPERTY(VisibleAnywhere, Category = "Enemy")
	TObjectPtr<UBoxComponent> Hitbox;

	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> Placeholder;

	UPROPERTY()
	TWeakObjectPtr<AActor> TargetActor;

	UPROPERTY(EditAnywhere, Category = "Enemy")
	EEnemyType Type = EEnemyType::Roadwarden;

	UPROPERTY(EditAnywhere, Category = "Enemy")
	EEnemyGender Gender = EEnemyGender::Male;

	UPROPERTY(EditAnywhere, Category = "Enemy")
	EUmbrellaShotKind ShotKind = EUmbrellaShotKind::EnemyRed;

	const FEnemyTuning& Tuning() const { return GetDefault<UUmbrellaTuning>()->Enemy; }
	FEnemyProfile Profile;
	FEnemyBrain Brain;
	FCourierPackets Packets;
	FVector HomeLocation = FVector::ZeroVector;
	FVector AimPoint = FVector::ZeroVector;
	int32 ShotsFired = 0;
};
