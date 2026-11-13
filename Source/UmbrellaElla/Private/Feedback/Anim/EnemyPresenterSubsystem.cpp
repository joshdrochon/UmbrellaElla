#include "Feedback/Anim/EnemyPresenterSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Engine/Texture2D.h"
#include "Feedback/Art/ArtSlot.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Harness/UmbrellaFeatureFlags.h"

namespace
{
	const FName EnemyStandInName(TEXT("EnemyStandIn"));
}

FVector UEnemyPresenterSubsystem::StandInScaleFor(EEnemyState State, EEnemyGender Gender)
{
	FVector Scale = UmbrellaEnemyPresenterConst::StandInScale;
	if (State == EEnemyState::Aim)
	{
		Scale *= UmbrellaEnemyPresenterConst::AimMul;
	}
	else if (State == EEnemyState::Recovery)
	{
		Scale *= UmbrellaEnemyPresenterConst::RecoveryMul;
	}
	if (Gender == EEnemyGender::Female)
	{
		Scale.X *= UmbrellaEnemyPresenterConst::FemaleWidthMul;
	}
	return Scale;
}

bool UEnemyPresenterSubsystem::IsVisibleIn(EEnemyState State)
{
	return State != EEnemyState::Defeated && State != EEnemyState::Withdrawn;
}

FName UEnemyPresenterSubsystem::ArtKeyFor(EEnemyType Type, EEnemyGender Gender, EEnemyState State)
{
	return FName(*FString::Printf(TEXT("%s_%s_%s"),
		*StaticEnum<EEnemyType>()->GetNameStringByValue(static_cast<int64>(Type)),
		*StaticEnum<EEnemyGender>()->GetNameStringByValue(static_cast<int64>(Gender)),
		*StaticEnum<EEnemyState>()->GetNameStringByValue(static_cast<int64>(State))));
}

FString UEnemyPresenterSubsystem::VisualIdFor(EEnemyType Type, EEnemyGender Gender, ERoadwardenEquipment Equipment)
{
	const FString Family = Type == EEnemyType::Roadwarden
		? StaticEnum<ERoadwardenEquipment>()->GetNameStringByValue(static_cast<int64>(Equipment))
		: StaticEnum<EEnemyType>()->GetNameStringByValue(static_cast<int64>(Type));
	return FString::Printf(TEXT("enemy:%s:%s"), *Family,
		*StaticEnum<EEnemyGender>()->GetNameStringByValue(static_cast<int64>(Gender)));
}

ERoadwardenEquipment UEnemyPresenterSubsystem::GetEquipment(const AUmbrellaEnemy* Enemy) const
{
	const ERoadwardenEquipment* Found = EquipmentByEnemy.Find(Enemy);
	return Found ? *Found : ERoadwardenEquipment::SundialCaster;
}

FString UEnemyPresenterSubsystem::VisualIdOf(const AUmbrellaEnemy* Enemy) const
{
	return VisualIdFor(Enemy->GetEnemyType(), Enemy->GetGender(), GetEquipment(Enemy));
}

void UEnemyPresenterSubsystem::SetEquipment(AUmbrellaEnemy* Enemy, ERoadwardenEquipment Equipment)
{
	if (!IsValid(Enemy))
	{
		return;
	}
	EquipmentByEnemy.Add(Enemy, Equipment);
	UStaticMeshComponent* Mesh = FindStandIn(Enemy);
	const FArtSlotRow* Row = Mesh ? ArtSlot::Find(*VisualIdOf(Enemy)) : nullptr;
	if (Row && !ArtSlot::HasArt(Mesh))
	{
		ArtSlot::ApplyRow(Mesh, *Row, StandInScaleFor(Enemy->GetEnemyState(), Enemy->GetGender()));
	}
}

EArtSlotDraw UEnemyPresenterSubsystem::ShowArt(AUmbrellaEnemy* Enemy, UTexture2D* Texture)
{
	UStaticMeshComponent* Mesh = IsValid(Enemy) ? FindStandIn(Enemy) : nullptr;
	const FArtSlotRow* Row = IsValid(Enemy) ? ArtSlot::Find(*VisualIdOf(Enemy)) : nullptr;
	if (!Mesh || !Row || ArtSlot::HasArt(Mesh))
	{
		return EArtSlotDraw::NoTexture;
	}
	const EArtSlotDraw Result = ArtSlot::Apply(Mesh, Texture, *Row, StandInScaleFor(Enemy->GetEnemyState(), Enemy->GetGender()));
	if (Result == EArtSlotDraw::Drawn)
	{
		Refresh(Enemy);
	}
	return Result;
}

void UEnemyPresenterSubsystem::PostInitialize()
{
	Super::PostInitialize();
	if (UWorld* World = GetWorld())
	{
		SpawnHandle = World->AddOnActorSpawnedHandler(FOnActorSpawned::FDelegate::CreateUObject(this, &UEnemyPresenterSubsystem::HandleActorSpawned));
	}
}

void UEnemyPresenterSubsystem::Deinitialize()
{
	if (UWorld* World = GetWorld())
	{
		World->RemoveOnActorSpawnedHandler(SpawnHandle);
	}
	Super::Deinitialize();
}

void UEnemyPresenterSubsystem::HandleActorSpawned(AActor* Actor)
{
	if (AUmbrellaEnemy* Enemy = Cast<AUmbrellaEnemy>(Actor))
	{
		ShowStandIn(Enemy);
	}
}

UStaticMeshComponent* UEnemyPresenterSubsystem::FindStandIn(const AActor* Enemy)
{
	TInlineComponentArray<UStaticMeshComponent*> Meshes(Enemy);
	for (UStaticMeshComponent* Mesh : Meshes)
	{
		if (Mesh->GetFName() == EnemyStandInName)
		{
			return Mesh;
		}
	}
	return nullptr;
}

void UEnemyPresenterSubsystem::ShowStandIn(AUmbrellaEnemy* Enemy)
{
	if (!IsValid(Enemy) || !IsFeatureEnabled(EFeatureId::ANIM_08) || !IsValid(Enemy->GetRootComponent()) || FindStandIn(Enemy))
	{
		return;
	}
	UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(Enemy, EnemyStandInName);
	if (UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")))
	{
		Mesh->SetStaticMesh(Shape);
	}
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetGenerateOverlapEvents(false);
	Mesh->SetupAttachment(Enemy->GetRootComponent());
	// Art slot enemy:<Family>:<Gender>; the cube stays when no asset exists.
	if (const FArtSlotRow* Row = ArtSlot::Find(*VisualIdOf(Enemy)))
	{
		ArtSlot::ApplyRow(Mesh, *Row, StandInScaleFor(Enemy->GetEnemyState(), Enemy->GetGender()));
	}
	Mesh->RegisterComponent();
	Enemies.Add(Enemy);
	++PresentedCount;
	Refresh(Enemy);
}

void UEnemyPresenterSubsystem::Refresh(AUmbrellaEnemy* Enemy)
{
	UStaticMeshComponent* Mesh = IsValid(Enemy) ? FindStandIn(Enemy) : nullptr;
	if (!Mesh)
	{
		return;
	}
	const EEnemyState State = Enemy->GetEnemyState();
	ArtSlot::SetWorldBoxScale(Mesh, StandInScaleFor(State, Enemy->GetGender()));
	Mesh->SetVisibility(IsVisibleIn(State));
	// Dual-colour art comes from the art swap; the shot kind is already on the enemy.
	FVector Location = Mesh->GetComponentLocation();
	Location.Y = UmbrellaDrawOrder::KeeperY;
	Mesh->SetWorldLocation(Location);
}

void UEnemyPresenterSubsystem::Tick(float DeltaTime)
{
	Enemies.RemoveAll([](const TWeakObjectPtr<AUmbrellaEnemy>& Entry) { return !Entry.IsValid(); });
	for (const TWeakObjectPtr<AUmbrellaEnemy>& Enemy : Enemies)
	{
		Refresh(Enemy.Get());
	}
}

TStatId UEnemyPresenterSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UEnemyPresenterSubsystem, STATGROUP_Tickables);
}
