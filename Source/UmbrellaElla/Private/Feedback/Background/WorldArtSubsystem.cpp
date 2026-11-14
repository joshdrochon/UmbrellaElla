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

	/** The component a piece's picture goes on. A trap's placeholder never collides, so it takes the picture itself. A land
	 *  block's mesh is its collision (UmbrellaLevelDirector::SpawnBlock): ArtSlot::Apply turns a mesh into a NoCollision
	 *  plane, which let Ella fly through every drawn solid once T_WorldSolids_PH was imported (main 991b3eb7; Level.World.
	 *  RealInputWalkerAtZ450StopsAt07ALowSolid). So a colliding mesh keeps its box and collision, is only hidden, and the
	 *  picture goes on a child plane at the same place and size. */
	UStaticMeshComponent* WorldArtPictureMesh(AActor* Piece, UStaticMeshComponent* Mesh)
	{
		if (!IsValid(Mesh) || Mesh->GetCollisionEnabled() == ECollisionEnabled::NoCollision)
		{
			return Mesh;
		}
		const FName PictureName(TEXT("BlockArt"));
		UStaticMeshComponent* Picture = FindObjectFast<UStaticMeshComponent>(Piece, PictureName);
		if (!Picture)
		{
			Picture = NewObject<UStaticMeshComponent>(Piece, PictureName);
			Picture->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Picture->SetGenerateOverlapEvents(false);
			Picture->SetupAttachment(Mesh);
			// The block's scale is its box size; the plane takes that size in world units, not on top of it.
			Picture->SetUsingAbsoluteScale(true);
			Picture->RegisterComponent();
		}
		return Picture;
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
	case ELevelPlacementKind::Floor:
		// The study has no ground, only floating eroded land: the route floor draws the island slab too (artscene request 4).
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

FString UWorldArtSubsystem::VisualFor(ELevelPlacementKind Kind, const FVector& Size)
{
	const bool bBlock = Kind == ELevelPlacementKind::Solid && Size.Z > 0.0f
		&& Size.X / Size.Z < UmbrellaWorldArtConst::BlockMaxAspect;
	return bBlock ? FString(TEXT("world:solids-block")) : VisualFor(Kind);
}

FString UWorldArtSubsystem::FallbackVisual(const FString& Visual)
{
	return Visual == TEXT("world:solids-block") ? FString(TEXT("world:solids")) : FString();
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
				Visual = VisualFor(Plan[Index].Kind, Plan[Index].Size);
			}
			const FArtSlotRow* Row = Visual.IsEmpty() ? nullptr : ArtSlot::Find(*Visual);
			UStaticMeshComponent* Mesh = Row ? WorldPieceMesh(Piece) : nullptr;
			if (!Mesh)
			{
				continue;
			}
			UTexture2D* Picture = Texture ? Texture : ArtSlot::LoadTexture(*Row);
			const FString Fallback = FallbackVisual(Visual);
			const FArtSlotRow* FallbackRow = !IsValid(Picture) && !Fallback.IsEmpty() ? ArtSlot::Find(*Fallback) : nullptr;
			if (FallbackRow)
			{
				// No block picture yet: the ledge picture beats a bare stand-in box until artscene imports one.
				Visual = Fallback;
				Row = FallbackRow;
				Picture = ArtSlot::LoadTexture(*Row);
			}
			if (!IsValid(Picture))
			{
				continue;
			}
			UStaticMeshComponent* Target = WorldArtPictureMesh(Piece, Mesh);
			if (ArtSlot::Apply(Target, Picture, *Row, Mesh->GetComponentScale()) == EArtSlotDraw::Drawn)
			{
				if (Target != Mesh)
				{
					// The box stays as the solid Ella meets; only its flat stand-in colour is no longer drawn.
					Mesh->SetVisibility(false);
				}
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
