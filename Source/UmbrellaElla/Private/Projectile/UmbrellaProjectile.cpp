#include "Projectile/UmbrellaProjectile.h"
#include "Components/StaticMeshComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaCollision.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/OverlapResult.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Projectile/UmbrellaShotReceiver.h"

namespace
{
	/** Tag a non-Ella actor can carry to count as the player for shot routing. */
	const FName PlayerTag(TEXT("Player"));

	/** Engine mesh and material the placeholder borrows. */
	const TCHAR* SphereMeshPath = TEXT("/Engine/BasicShapes/Sphere.Sphere");
	const TCHAR* ShapeMaterialPath = TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
	const FName ColorParameter(TEXT("Color"));

	bool IsPlayerActor(const AActor* Target)
	{
		return Target && (Target->IsA<AEllaCharacter>() || Target->ActorHasTag(PlayerTag));
	}

	/** Receivers on the actor and its components, highest priority first. */
	TArray<IUmbrellaShotReceiver*> GatherReceivers(AActor* Target)
	{
		TArray<IUmbrellaShotReceiver*> Found;
		if (IUmbrellaShotReceiver* OnActor = Cast<IUmbrellaShotReceiver>(Target))
		{
			Found.Add(OnActor);
		}
		TInlineComponentArray<UActorComponent*> Components(Target);
		for (UActorComponent* Component : Components)
		{
			if (IUmbrellaShotReceiver* OnComponent = Cast<IUmbrellaShotReceiver>(Component))
			{
				Found.Add(OnComponent);
			}
		}
		Found.StableSort([](const IUmbrellaShotReceiver& A, const IUmbrellaShotReceiver& B)
		{
			return A.GetShotPriority() > B.GetShotPriority();
		});
		return Found;
	}
}

bool ProjectileRules::CanShotTouch(EUmbrellaShotKind Kind, const AActor* Target)
{
	if (!Target)
	{
		return false;
	}
	const bool bIsPlayer = IsPlayerActor(Target);
	return Kind == EUmbrellaShotKind::PlayerBlast ? !bIsPlayer : bIsPlayer;
}

ECollisionChannel ProjectileRules::ShotChannel(EUmbrellaShotKind Kind)
{
	return Kind == EUmbrellaShotKind::PlayerBlast ? UmbrellaCollision::PlayerShot : UmbrellaCollision::EnemyShot;
}

bool ProjectileRules::IsSolidStop(EUmbrellaShotKind Kind, const UPrimitiveComponent* Component, bool bHasReceivers)
{
	return Component && !bHasReceivers && Component->GetCollisionResponseToChannel(ShotChannel(Kind)) == ECR_Block;
}

FVector ProjectileRules::Advance(const FVector& Position, const FVector& Velocity, float Dt)
{
	return FVector(Position.X + Velocity.X * Dt, UmbrellaDrawOrder::ProjectileY, Position.Z + Velocity.Z * Dt);
}

AUmbrellaProjectile::AUmbrellaProjectile()
{
	PrimaryActorTick.bCanEverTick = true;
	Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
	Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Visual->SetGenerateOverlapEvents(false);
	SetRootComponent(Visual);
}

AUmbrellaProjectile* AUmbrellaProjectile::Fire(UWorld* World, const FUmbrellaShotSpec& Spec)
{
	if (!World)
	{
		return nullptr;
	}
	const FProjectileTuning& Tuning = GetDefault<UUmbrellaTuning>()->Projectile;
	FUmbrellaShotSpec Resolved = Spec;
	Resolved.Origin.Y = UmbrellaDrawOrder::ProjectileY;
	Resolved.Velocity.Y = 0.0;
	if (Resolved.Radius <= 0.0f)
	{
		Resolved.Radius = Tuning.DefaultRadius;
	}
	if (Resolved.LifetimeSeconds <= 0.0f)
	{
		Resolved.LifetimeSeconds = Tuning.DefaultLifetimeSeconds;
	}

	FActorSpawnParameters Params;
	Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
	AUmbrellaProjectile* Shot = World->SpawnActor<AUmbrellaProjectile>(AUmbrellaProjectile::StaticClass(), FTransform(Resolved.Origin), Params);
	if (!Shot)
	{
		return nullptr;
	}
	Shot->Spec = Resolved;
	Shot->LifetimeRemaining = Resolved.LifetimeSeconds;
	Shot->ApplyPlaceholderVisual();

	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::ProjectileSpawned;
		Event.SourceId = Resolved.SourceId;
		Event.Detail = StaticEnum<EUmbrellaShotKind>()->GetNameByValue(static_cast<int64>(Resolved.Kind));
		Event.Value = Resolved.Damage;
		Bus->Broadcast(Event);
	}
	Shot->ResolveContacts(Resolved.Origin, Resolved.Origin);
	return Shot;
}

void AUmbrellaProjectile::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	AdvanceShot(DeltaSeconds);
}

void AUmbrellaProjectile::AdvanceShot(float Dt)
{
	const FVector From = GetActorLocation();
	const FVector To = ProjectileRules::Advance(From, Spec.Velocity, Dt);
	SetActorLocation(To);
	LifetimeRemaining -= Dt;
	ResolveContacts(From, To);
	if (!IsActorBeingDestroyed() && LifetimeRemaining <= 0.0f)
	{
		Destroy();
	}
}

void AUmbrellaProjectile::ResolveContacts(const FVector& From, const FVector& To)
{
	UWorld* World = GetWorld();
	if (!World || IsActorBeingDestroyed())
	{
		return;
	}
	const FCollisionShape Shape = FCollisionShape::MakeSphere(Spec.Radius);
	FCollisionQueryParams QueryParams(SCENE_QUERY_STAT(UmbrellaShot), false, this);
	const FCollisionObjectQueryParams AllObjects(FCollisionObjectQueryParams::AllObjects);

	struct FContact
	{
		AActor* Actor = nullptr;
		UPrimitiveComponent* Component = nullptr;
		FVector Location = FVector::ZeroVector;
	};
	TArray<FContact> Contacts;
	if (From.Equals(To, UE_KINDA_SMALL_NUMBER))
	{
		TArray<FOverlapResult> Overlaps;
		World->OverlapMultiByObjectType(Overlaps, To, FQuat::Identity, AllObjects, Shape, QueryParams);
		for (const FOverlapResult& Overlap : Overlaps)
		{
			Contacts.Add({Overlap.GetActor(), Overlap.GetComponent(), To});
		}
	}
	else
	{
		TArray<FHitResult> Hits;
		World->SweepMultiByObjectType(Hits, From, To, FQuat::Identity, AllObjects, Shape, QueryParams);
		for (const FHitResult& Hit : Hits)
		{
			Contacts.Add({Hit.GetActor(), Hit.GetComponent(), Hit.bStartPenetrating ? To : FVector(Hit.ImpactPoint)});
		}
	}

	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World);
	TSet<AActor*> Routed;
	for (const FContact& Contact : Contacts)
	{
		AActor* Target = Contact.Actor;
		if (!Target)
		{
			continue;
		}
		// A solid wall or ceiling that blocks this shot channel ends the shot (Ella is never a wall).
		const TArray<IUmbrellaShotReceiver*> Receivers = GatherReceivers(Target);
		if (!IsPlayerActor(Target) && ProjectileRules::IsSolidStop(Spec.Kind, Contact.Component, Receivers.Num() > 0))
		{
			Destroy();
			return;
		}
		if (!ProjectileRules::CanShotTouch(Spec.Kind, Target) || Routed.Contains(Target))
		{
			continue;
		}
		Routed.Add(Target);
		const FVector Location = Contact.Location;
		bool bConsumed = false;
		for (IUmbrellaShotReceiver* Receiver : Receivers)
		{
			if (Receiver->ReceiveShot(Spec, Location) == EUmbrellaShotResult::Consumed)
			{
				bConsumed = true;
				break;
			}
		}
		if (Bus)
		{
			FUmbrellaEvent Event;
			Event.Type = EUmbrellaEventType::ProjectileContact;
			Event.SourceId = Spec.SourceId;
			Event.TargetId = Target->GetFName();
			Event.Detail = bConsumed ? FName(TEXT("Consumed")) : FName(TEXT("Passed"));
			Event.Value = Spec.Damage;
			Bus->Broadcast(Event);
		}
		if (bConsumed)
		{
			Destroy();
			return;
		}
	}
}

void AUmbrellaProjectile::ApplyPlaceholderVisual()
{
	const FProjectileTuning& Tuning = GetDefault<UUmbrellaTuning>()->Projectile;
	UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, SphereMeshPath, nullptr, LOAD_NoWarn | LOAD_Quiet);
	if (!Mesh || !Visual)
	{
		return;
	}
	Visual->SetStaticMesh(Mesh);
	Visual->SetWorldScale3D(FVector(Spec.Radius / Tuning.PlaceholderMeshRadius));
	UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, ShapeMaterialPath, nullptr, LOAD_NoWarn | LOAD_Quiet);
	if (!Base)
	{
		return;
	}
	FLinearColor Tint = Tuning.PlayerColor;
	if (Spec.Kind == EUmbrellaShotKind::EnemyRed)
	{
		Tint = Tuning.RedColor;
	}
	else if (Spec.Kind == EUmbrellaShotKind::EnemyYellow)
	{
		Tint = Tuning.YellowColor;
	}
	UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(Base, this);
	Material->SetVectorParameterValue(ColorParameter, Tint);
	Visual->SetMaterial(0, Material);
}
