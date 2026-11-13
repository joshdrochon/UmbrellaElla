#include "Level/UmbrellaLevelDirector.h"
#include "Arena/UmbrellaArena.h"
#include "Camera/CameraComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Enemy/UmbrellaEnemy.h"
#include "EngineUtils.h"
#include "Field/WindCurrent.h"
#include "GameFramework/Pawn.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Kismet/GameplayStatics.h"
#include "Trap/UmbrellaTrap.h"

AUmbrellaLevelDirector::AUmbrellaLevelDirector()
{
	PrimaryActorTick.bCanEverTick = true;
	SetRootComponent(CreateDefaultSubobject<USceneComponent>(TEXT("Root")));
}

void AUmbrellaLevelDirector::ClearRoute()
{
	for (AActor* A : Spawned)
	{
		if (IsValid(A))
		{
			A->Destroy();
		}
	}
	Spawned.Reset();
	Plan.Reset();
	SlotsSpawned = 0;
	CheckpointReached = 0;
	bHandedOff = false;
}

AActor* AUmbrellaLevelDirector::SpawnBlock(const FLevelPlacement& P)
{
	AActor* Block = GetWorld()->SpawnActor<AActor>(AActor::StaticClass(), FTransform(P.Location));
	if (!Block)
	{
		return nullptr;
	}
	UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(Block, TEXT("Block"));
	Block->SetRootComponent(Mesh);
	Mesh->RegisterComponent();
	if (UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")))
	{
		Mesh->SetStaticMesh(Cube);
	}
	Mesh->SetWorldLocation(P.Location);
	Mesh->SetWorldScale3D(P.Size / LevelPlanConst::CubeSize);
	// Land blocks Ella; a checkpoint marker is only a sign she flies through.
	Mesh->SetCollisionEnabled(P.Kind == ELevelPlacementKind::Checkpoint ? ECollisionEnabled::NoCollision : ECollisionEnabled::QueryAndPhysics);
	return Block;
}

void AUmbrellaLevelDirector::SpawnMechanic(const FLevelPlacement& P)
{
	AActor* Made = nullptr;
	if (P.Kind == ELevelPlacementKind::Trap)
	{
		ETrapKind Kind = ETrapKind::AirMill;
		switch (P.Mechanic)
		{
		case EChunkMechanic::Shutter: Kind = ETrapKind::TimedShutter; break;
		case EChunkMechanic::Bellows: Kind = ETrapKind::HostileBellows; break;
		case EChunkMechanic::BridgeTooth: Kind = ETrapKind::RoofTeeth; break;
		default: break;
		}
		AUmbrellaTrap* Trap = GetWorld()->SpawnActor<AUmbrellaTrap>(AUmbrellaTrap::StaticClass(), FTransform(P.Location));
		if (Trap)
		{
			Trap->ConfigureKind(Kind);
			Made = Trap;
		}
	}
	else if (P.Kind == ELevelPlacementKind::Enemy)
	{
		EEnemyType Type = EEnemyType::Roadwarden;
		if (P.Mechanic == EChunkMechanic::Stilt)
		{
			Type = EEnemyType::Floodstrider;
		}
		else if (P.Mechanic == EChunkMechanic::Courier)
		{
			Type = EEnemyType::SkyCourier;
		}
		AUmbrellaEnemy* Enemy = GetWorld()->SpawnActor<AUmbrellaEnemy>(AUmbrellaEnemy::StaticClass(), FTransform(P.Location));
		if (Enemy)
		{
			Enemy->Configure(Type, (P.Slot % 2) ? EEnemyGender::Female : EEnemyGender::Male,
				P.bYellowShot ? EUmbrellaShotKind::EnemyYellow : EUmbrellaShotKind::EnemyRed);
			Made = Enemy;
		}
	}
	else if (P.Kind == ELevelPlacementKind::Wind)
	{
		AWindCurrent* Wind = GetWorld()->SpawnActor<AWindCurrent>(AWindCurrent::StaticClass(), FTransform(P.Location));
		if (Wind)
		{
			Wind->SetHalfExtent(0.5f * P.Size.X, 0.5f * P.Size.Z);
			Wind->SetCurrent(FVector(P.WindDirection.X, 0.0, P.WindDirection.Y), GetDefault<UUmbrellaTuning>()->Field.DefaultWindForce);
			Made = Wind;
		}
	}
	else
	{
		Made = SpawnBlock(P);
	}
	if (Made)
	{
		Spawned.Add(Made);
	}
}

int32 AUmbrellaLevelDirector::BuildRoute(int64 Seed)
{
	ClearRoute();
	if (!IsFeatureEnabled(EFeatureId::FLOW_24) || !IsFeatureEnabled(EFeatureId::HAZ_24) || !GetWorld())
	{
		return 0;
	}
	Route = LevelCatalogue::Generate(Seed);
	Plan = LevelPlan::Build(Route);
	for (const FLevelPlacement& P : Plan)
	{
		SpawnMechanic(P);
	}
	SlotsSpawned = Route.Slots.Num();
	return SlotsSpawned;
}

int32 AUmbrellaLevelDirector::PlaceAtCheckpoint(AActor* Actor, int32 Checkpoint) const
{
	if (!Actor || Checkpoint < 0 || Checkpoint > LevelPlanConst::MaxCheckpoint || !IsFeatureEnabled(EFeatureId::FLOW_28))
	{
		return 0;
	}
	Actor->SetActorLocation(LevelPlan::CheckpointStandLocation(Checkpoint));
	return Checkpoint;
}

void AUmbrellaLevelDirector::BroadcastRouteEvent(EUmbrellaEventType EventType, FName Detail, float Value) const
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EventType;
		Event.SourceId = GetFName();
		Event.Detail = Detail;
		Event.Value = Value;
		Bus->Broadcast(Event);
	}
}

void AUmbrellaLevelDirector::StepFollow(float EllaX, int32 TravelDirection)
{
	if (!Arena && GetWorld())
	{
		TActorIterator<AUmbrellaArena> It(GetWorld());
		if (It)
		{
			Arena = *It;
		}
	}
	if (Arena)
	{
		Arena->FollowEllaX(EllaX, TravelDirection);
		if (Arena->GetPlayCamera())
		{
			LastCameraX = Arena->GetPlayCamera()->GetComponentLocation().X;
		}
	}
	const int32 Reached = LevelPlan::CheckpointReachedAt(EllaX);
	if (Reached > CheckpointReached)
	{
		CheckpointReached = Reached;
		BroadcastRouteEvent(EUmbrellaEventType::CheckpointReached, FName(*FString::Printf(TEXT("CP%d"), Reached)), static_cast<float>(Reached));
	}
	if (!bHandedOff && SlotsSpawned > 0 && EllaX >= LevelPlan::KeeperHandoffX())
	{
		bHandedOff = true;
		// FLOW-28: the route's enemies and traps are gone once the Keeper fight begins.
		for (int32 Index = Spawned.Num() - 1; Index >= 0; --Index)
		{
			AActor* A = Spawned[Index];
			if (IsValid(A) && (A->IsA<AUmbrellaEnemy>() || A->IsA<AUmbrellaTrap>()))
			{
				A->Destroy();
				Spawned.RemoveAtSwap(Index);
			}
		}
		if (UEncounterDirectorSubsystem* Encounter = GetWorld() ? GetWorld()->GetSubsystem<UEncounterDirectorSubsystem>() : nullptr)
		{
			Encounter->BeginKeeperFight();
		}
	}
}

void AUmbrellaLevelDirector::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (SlotsSpawned == 0)
	{
		return;
	}
	if (const APawn* Pawn = UGameplayStatics::GetPlayerPawn(this, 0))
	{
		StepFollow(Pawn->GetActorLocation().X, FMath::Sign(Pawn->GetVelocity().X));
	}
}
