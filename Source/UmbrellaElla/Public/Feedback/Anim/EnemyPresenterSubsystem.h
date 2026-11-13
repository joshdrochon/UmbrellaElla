#pragma once

#include "CoreMinimal.h"
#include "Enemy/EnemyTypes.h"
#include "Subsystems/WorldSubsystem.h"
#include "EnemyPresenterSubsystem.generated.h"

class AUmbrellaEnemy;
class UStaticMeshComponent;
class UTexture2D;
enum class EArtSlotDraw : uint8;

namespace UmbrellaEnemyPresenterConst
{
	/** Stand-in card scale for an enemy (slim figure, flat). */
	static const FVector StandInScale(0.8, 0.1, 1.2);
	/** Per-state shape multipliers (X, Y, Z): aim leans forward, recovery slumps. */
	static const FVector AimMul(1.3, 1.0, 1.0);
	static const FVector RecoveryMul(1.0, 1.0, 0.8);
	/** Female variant is a presentation difference only: slightly narrower card. Never changes collision or tuning. */
	static constexpr float FemaleWidthMul = 0.9f;
}

/**
 * Shows a neutral stand-in on every spawned enemy and follows its state (patrol, aim, recovery, defeated, withdrawn)
 * through public getters only. Art keys name the flipbook each (type, gender, state) will use. No collision.
 * Never gameplay authority. Visuals lane.
 */
UCLASS()
class UMBRELLAELLA_API UEnemyPresenterSubsystem final : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void PostInitialize() override;
	virtual void Deinitialize() override;
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;

	/** Attach the stand-in to an enemy (safe to call twice). */
	void ShowStandIn(AUmbrellaEnemy* Enemy);

	/** Swap the stand-in for a picture (the slot load does this at spawn; tests pass a transient texture). */
	EArtSlotDraw ShowArt(AUmbrellaEnemy* Enemy, UTexture2D* Texture);

	/** Art slot id for a type, gender and Roadwarden equipment, e.g. "enemy:ArmillaryLauncher:Female". Equipment is ignored for other types. Pure. */
	static FString VisualIdFor(EEnemyType Type, EEnemyGender Gender, ERoadwardenEquipment Equipment = ERoadwardenEquipment::SundialCaster);

	/** Set a Roadwarden's equipment variant (the enemy does not store it yet: request artslots 2). Redraws the art slot if it is not yet drawn. */
	void SetEquipment(AUmbrellaEnemy* Enemy, ERoadwardenEquipment Equipment);
	ERoadwardenEquipment GetEquipment(const AUmbrellaEnemy* Enemy) const;
	/** Slot id for this enemy, using its stored equipment. */
	FString VisualIdOf(const AUmbrellaEnemy* Enemy) const;

	/** Apply the enemy's current state to its stand-in. */
	void Refresh(AUmbrellaEnemy* Enemy);

	int32 GetPresentedCount() const { return PresentedCount; }

	/** Stand-in shape for a state and gender. Pure. */
	static FVector StandInScaleFor(EEnemyState State, EEnemyGender Gender);
	/** Defeated and withdrawn enemies are not drawn. Pure. */
	static bool IsVisibleIn(EEnemyState State);
	/** Flipbook key an art swap uses, e.g. "Roadwarden_Female_Aim". Pure. */
	static FName ArtKeyFor(EEnemyType Type, EEnemyGender Gender, EEnemyState State);

private:
	void HandleActorSpawned(AActor* Actor);
	static UStaticMeshComponent* FindStandIn(const AActor* Enemy);
	FDelegateHandle SpawnHandle;
	TArray<TWeakObjectPtr<AUmbrellaEnemy>> Enemies;
	TMap<TWeakObjectPtr<const AUmbrellaEnemy>, ERoadwardenEquipment> EquipmentByEnemy;
	int32 PresentedCount = 0;
};
