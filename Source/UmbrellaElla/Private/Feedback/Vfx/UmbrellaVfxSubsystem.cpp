#include "Feedback/Vfx/UmbrellaVfxSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "Harness/UmbrellaFeatureFlags.h"

namespace
{
	const EUmbrellaEventType VfxEvents[] = {
		EUmbrellaEventType::ProjectileSpawned,
		EUmbrellaEventType::ProjectileContact,
		EUmbrellaEventType::CatchSucceeded,
		EUmbrellaEventType::CatchFailed,
		EUmbrellaEventType::BossTargetHit,
		EUmbrellaEventType::BossAttackTelegraphed,
		EUmbrellaEventType::BossPartDestroyed,
	};
}

void UUmbrellaVfxSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Collection.InitializeDependency<UUmbrellaEventBus>();
	Super::Initialize(Collection);
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		for (const EUmbrellaEventType Type : VfxEvents)
		{
			Handles.Add(Bus->On(Type).AddUObject(this, &UUmbrellaVfxSubsystem::PlayForEvent));
		}
	}
}

void UUmbrellaVfxSubsystem::Deinitialize()
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		for (int32 Index = 0; Index < Handles.Num(); ++Index)
		{
			Bus->On(VfxEvents[Index]).Remove(Handles[Index]);
		}
	}
	Handles.Reset();
	Super::Deinitialize();
}

FName UUmbrellaVfxSubsystem::EffectForEvent(const FUmbrellaEvent& Event)
{
	switch (Event.Type)
	{
	case EUmbrellaEventType::ProjectileSpawned:
		return TEXT("ShotMuzzle");
	case EUmbrellaEventType::ProjectileContact:
		return TEXT("ShotImpact");
	case EUmbrellaEventType::CatchSucceeded:
		return TEXT("AbsorbBurst");
	case EUmbrellaEventType::CatchFailed:
		return TEXT("AbsorbFizzle");
	case EUmbrellaEventType::BossTargetHit:
		return TEXT("KeeperHitFlash");
	case EUmbrellaEventType::BossAttackTelegraphed:
		return TEXT("KeeperTelegraph");
	case EUmbrellaEventType::BossPartDestroyed:
		return TEXT("KeeperPartBreak");
	default:
		return NAME_None;
	}
}

bool UUmbrellaVfxSubsystem::IsEffectEnabled(const FUmbrellaEvent& Event)
{
	switch (Event.Type)
	{
	case EUmbrellaEventType::ProjectileSpawned:
		return IsFeatureEnabled(EFeatureId::VFX_03);
	case EUmbrellaEventType::BossTargetHit:
	case EUmbrellaEventType::BossAttackTelegraphed:
	case EUmbrellaEventType::BossPartDestroyed:
		return IsFeatureEnabled(EFeatureId::VFX_05);
	default:
		return IsFeatureEnabled(EFeatureId::VFX_04);
	}
}

void UUmbrellaVfxSubsystem::PlayForEvent(const FUmbrellaEvent& Event)
{
	const FName Effect = EffectForEvent(Event);
	UWorld* World = GetWorld();
	if (Effect.IsNone() || !IsValid(World) || !IsEffectEnabled(Event))
	{
		return;
	}
	LastEffect = Effect;
	++EffectCount;

	// Place at the source actor when it exists; depth is always the VFX layer.
	FVector Location(0.0, UmbrellaDrawOrder::VfxY, 0.0);
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (It->GetFName() == Event.SourceId)
		{
			Location.X = It->GetActorLocation().X;
			Location.Z = It->GetActorLocation().Z;
			break;
		}
	}
	AActor* Flash = World->SpawnActor<AActor>(Location, FRotator::ZeroRotator);
	if (!IsValid(Flash))
	{
		return;
	}
	UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(Flash, TEXT("VfxStandIn"));
	if (UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere")))
	{
		Mesh->SetStaticMesh(Shape);
	}
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetRelativeScale3D(FVector(UmbrellaVfxConst::StandInScale));
	Flash->SetRootComponent(Mesh);
	Mesh->RegisterComponent();
	Flash->SetActorLocation(Location);
	Flash->SetLifeSpan(UmbrellaVfxConst::StandInLifeSeconds);
}
