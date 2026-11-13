#include "Feedback/Background/WorldArtSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "Feedback/Art/ArtSlot.h"
#include "GameFramework/Actor.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Level/UmbrellaLevelDirector.h"
#include "Trap/UmbrellaTrap.h"

namespace
{
	/** The stand-in box component a piece draws on: the trap's placeholder, or the level block. */
	UStaticMeshComponent* WorldPieceMesh(AActor* Piece)
	{
		const FName Name = Cast<AUmbrellaTrap>(Piece) ? FName(TEXT("Placeholder")) : FName(TEXT("Block"));
		return FindObjectFast<UStaticMeshComponent>(Piece, Name);
	}
}

bool UWorldArtSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->IsGameWorld() && Super::ShouldCreateSubsystem(Outer);
}

FString UWorldArtSubsystem::VisualFor(ELevelPlacementKind Kind)
{
	switch (Kind)
	{
	case ELevelPlacementKind::Solid:
		return TEXT("world:solids");
	case ELevelPlacementKind::Refuge:
	case ELevelPlacementKind::Checkpoint:
		return TEXT("world:refuge-and-yellow-bay");
	case ELevelPlacementKind::Trap:
		return TEXT("world:mill-and-traps");
	default:
		return FString();
	}
}

int32 UWorldArtSubsystem::DrawnCount(const FString& Visual) const
{
	const int32* Count = Counts.Find(Visual);
	return Count ? *Count : 0;
}

int32 UWorldArtSubsystem::Refresh(UTexture2D* Texture)
{
	UWorld* World = GetWorld();
	if (!IsValid(World) || !IsFeatureEnabled(EFeatureId::ANIM_08))
	{
		return 0;
	}
	int32 Drawn = 0;
	for (TActorIterator<AUmbrellaLevelDirector> It(World); It; ++It)
	{
		const TArray<FLevelPlacement>& Plan = It->GetPlan();
		const TArray<TObjectPtr<AActor>>& Spawned = It->GetSpawned();
		// Spawned lines up with Plan one to one unless a mechanic failed to spawn; traps are known by class either way.
		const bool bAligned = Plan.Num() == Spawned.Num();
		for (int32 Index = 0; Index < Spawned.Num(); ++Index)
		{
			AActor* Piece = Spawned[Index];
			if (!IsValid(Piece) || Done.Contains(Piece))
			{
				continue;
			}
			FString Visual;
			if (Cast<AUmbrellaTrap>(Piece))
			{
				Visual = VisualFor(ELevelPlacementKind::Trap);
			}
			else if (bAligned)
			{
				Visual = VisualFor(Plan[Index].Kind);
			}
			const FArtSlotRow* Row = Visual.IsEmpty() ? nullptr : ArtSlot::Find(*Visual);
			UStaticMeshComponent* Mesh = Row ? WorldPieceMesh(Piece) : nullptr;
			if (!Mesh)
			{
				continue;
			}
			UTexture2D* Picture = Texture ? Texture : ArtSlot::LoadTexture(*Row);
			if (!IsValid(Picture))
			{
				continue;
			}
			if (ArtSlot::Apply(Mesh, Picture, *Row, Mesh->GetRelativeScale3D()) == EArtSlotDraw::Drawn)
			{
				Done.Add(Piece);
				++Counts.FindOrAdd(Visual);
				++Drawn;
			}
		}
	}
	return Drawn;
}

void UWorldArtSubsystem::Tick(float DeltaTime)
{
	// New pieces appear when a route is built; look a few times a second, not every frame.
	Since += DeltaTime;
	if (Since >= UmbrellaWorldArtConst::RefreshSeconds)
	{
		Since = 0.0f;
		Refresh(nullptr);
	}
}

TStatId UWorldArtSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UWorldArtSubsystem, STATGROUP_Tickables);
}
