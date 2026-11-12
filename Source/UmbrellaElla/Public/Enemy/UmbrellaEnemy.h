#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "Enemy/EnemyModel.h"
#include "Projectile/UmbrellaShotReceiver.h"
#include "UmbrellaEnemy.generated.h"

class UBoxComponent;
class UStaticMeshComponent;

/**
 * A standard enemy in the world: Roadwarden (three equipment variants), Floodstrider or Sky Courier. All rules live in
 * FEnemyModel; this actor holds the hit box, a placeholder look, fires through the Projectile Service and tells the
 * art lane its state through AnimationCue events. Contact damage is off.
 */
UCLASS()
class UMBRELLAELLA_API AUmbrellaEnemy : public AActor, public IUmbrellaShotReceiver
{
	GENERATED_BODY()

public:
	AUmbrellaEnemy();

	/** Spawn and configure one enemy. Support bounds keep a grounded patrol on its surface. Returns nullptr if its feature is off. */
	static AUmbrellaEnemy* SpawnEnemy(UWorld* World, EEnemyType Type, EEnemyVariant Variant, EUmbrellaShotKind Color, const FVector& Location,
		float SupportMinX, float SupportMaxX);

	virtual void BeginPlay() override;
	virtual void Tick(float DeltaSeconds) override;
	virtual EUmbrellaShotResult ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation) override;

	/** Retry: full HP, full emission slots, back home, visible again. */
	void ResetForRestart();

	const FEnemyModel& GetModel() const { return Model; }
	EEnemyVariant GetVariant() const { return Variant; }

	/** Tests: advance the enemy by hand against a player position, bypassing the actor tick. */
	void StepBy(float DeltaSeconds, const FVector2D& PlayerPos);

private:
	void Configure(EEnemyType InType, EEnemyVariant InVariant, EUmbrellaShotKind InColor, const FVector& Location, float SupportMinX, float SupportMaxX);
	void Process(TArray<FEnemyCommand>& Commands);
	void Broadcast(EEnemyState State) const;
	void ApplyLook();

	UPROPERTY()
	TObjectPtr<UBoxComponent> HitBox;
	UPROPERTY()
	TObjectPtr<UStaticMeshComponent> Visual;

	FEnemyModel Model;
	EEnemyVariant Variant = EEnemyVariant::Male;
	bool bManualStepping = false;
};
