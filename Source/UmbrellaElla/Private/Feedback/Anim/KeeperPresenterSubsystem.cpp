#include "Feedback/Anim/KeeperPresenterSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Feedback/Art/ArtSlot.h"
#include "GameFramework/Actor.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Owl/KeeperOfTime.h"

void UKeeperPresenterSubsystem::PostInitialize()
{
	Super::PostInitialize();
	if (UWorld* World = GetWorld())
	{
		SpawnHandle = World->AddOnActorSpawnedHandler(FOnActorSpawned::FDelegate::CreateUObject(this, &UKeeperPresenterSubsystem::HandleActorSpawned));
		if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World))
		{
			PartHandle = Bus->On(EUmbrellaEventType::BossPartDestroyed).AddUObject(this, &UKeeperPresenterSubsystem::HandlePartDestroyed);
			RestartHandle = Bus->On(EUmbrellaEventType::CheckpointRetried).AddUObject(this, &UKeeperPresenterSubsystem::HandleRestart);
		}
	}
}

void UKeeperPresenterSubsystem::Deinitialize()
{
	if (UWorld* World = GetWorld())
	{
		World->RemoveOnActorSpawnedHandler(SpawnHandle);
		if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World))
		{
			Bus->On(EUmbrellaEventType::BossPartDestroyed).Remove(PartHandle);
			Bus->On(EUmbrellaEventType::CheckpointRetried).Remove(RestartHandle);
		}
	}
	Super::Deinitialize();
}

void UKeeperPresenterSubsystem::HandleActorSpawned(AActor* Actor)
{
	if (Cast<AKeeperOfTime>(Actor))
	{
		bMasksShown = false;
		PartsDestroyed = 0;
		Keepers.Add(Actor);
		ShowStandIn(Actor);
	}
}

void UKeeperPresenterSubsystem::HandlePartDestroyed(const FUmbrellaEvent&)
{
	++PartsDestroyed;
	bMasksShown = true;
}

void UKeeperPresenterSubsystem::HandleRestart(const FUmbrellaEvent&)
{
	PartsDestroyed = 0;
	bMasksShown = false;
}

void UKeeperPresenterSubsystem::ShowStateLayer(AActor* Keeper, const FString& VisualId)
{
	if (UStaticMeshComponent* Layer = FindPart(Keeper, VisualId))
	{
		Layer->SetVisibility(true);
	}
}

void UKeeperPresenterSubsystem::HideStateLayer(AActor* Keeper, const FString& VisualId)
{
	if (UStaticMeshComponent* Layer = FindPart(Keeper, VisualId))
	{
		Layer->SetVisibility(false);
	}
}

void UKeeperPresenterSubsystem::Tick(float DeltaTime)
{
	for (int32 Index = Keepers.Num() - 1; Index >= 0; --Index)
	{
		AActor* Keeper = Keepers[Index].Get();
		const AKeeperOfTime* Owl = Cast<AKeeperOfTime>(Keeper);
		if (!Owl)
		{
			Keepers.RemoveAtSwap(Index);
			continue;
		}
		if (bMasksShown)
		{
			ShowStateLayer(Keeper, UmbrellaKeeperPresenterConst::MaskVisual);
		}
		else
		{
			HideStateLayer(Keeper, UmbrellaKeeperPresenterConst::MaskVisual);
		}
		if (Owl->IsDeparting())
		{
			ShowStateLayer(Keeper, UmbrellaKeeperPresenterConst::DepartureVisual);
		}
		else
		{
			HideStateLayer(Keeper, UmbrellaKeeperPresenterConst::DepartureVisual);
		}
	}
}

TStatId UKeeperPresenterSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UKeeperPresenterSubsystem, STATGROUP_Tickables);
}

EArtSlotDraw UKeeperPresenterSubsystem::ShowArt(AActor* Keeper, UTexture2D* Texture)
{
	static const FName StandInName(TEXT("KeeperStandIn"));
	UStaticMeshComponent* Mesh = IsValid(Keeper) ? FindObjectFast<UStaticMeshComponent>(Keeper, StandInName) : nullptr;
	const FArtSlotRow* Row = ArtSlot::Find(TEXT("keeper:body-hover-flap"));
	if (!Mesh || !Row || ArtSlot::HasArt(Mesh))
	{
		return EArtSlotDraw::NoTexture;
	}
	return ArtSlot::Apply(Mesh, Texture, *Row, UmbrellaKeeperPresenterConst::StandInScale);
}

namespace
{
	FName KeeperPartName(const FString& VisualId)
	{
		FString Name = VisualId;
		Name.ReplaceInline(TEXT(":"), TEXT("_"));
		return FName(*(FString(TEXT("KeeperPart_")) + Name));
	}
}

UStaticMeshComponent* UKeeperPresenterSubsystem::FindPart(const AActor* Keeper, const FString& VisualId)
{
	return IsValid(Keeper) ? FindObjectFast<UStaticMeshComponent>(const_cast<AActor*>(Keeper), KeeperPartName(VisualId)) : nullptr;
}

EArtSlotDraw UKeeperPresenterSubsystem::ShowPartArt(AActor* Keeper, const FString& VisualId, UTexture2D* Texture)
{
	const FArtSlotRow* Row = ArtSlot::Find(*VisualId);
	const UmbrellaKeeperPresenterConst::FKeeperPartLayer* Layer = nullptr;
	for (const UmbrellaKeeperPresenterConst::FKeeperPartLayer& Candidate : UmbrellaKeeperPresenterConst::PartLayers)
	{
		Layer = VisualId == Candidate.Visual ? &Candidate : Layer;
	}
	if (!IsValid(Keeper) || !Row || !Layer || !IsFeatureEnabled(EFeatureId::ANIM_06) || !Keeper->GetRootComponent() || FindPart(Keeper, VisualId))
	{
		return EArtSlotDraw::NoTexture;
	}
	UTexture2D* Picture = Texture ? Texture : ArtSlot::LoadTexture(*Row);
	if (!Picture)
	{
		return EArtSlotDraw::NoTexture;
	}
	UStaticMeshComponent* Part = NewObject<UStaticMeshComponent>(Keeper, KeeperPartName(VisualId));
	Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Part->SetGenerateOverlapEvents(false);
	Part->SetupAttachment(Keeper->GetRootComponent());
	const EArtSlotDraw Result = ArtSlot::Apply(Part, Picture, *Row, UmbrellaKeeperPresenterConst::StandInScale);
	if (Result != EArtSlotDraw::Drawn)
	{
		Part->DestroyComponent();
		return Result;
	}
	Part->RegisterComponent();
	ArtSlot::SetWorldBoxScale(Part, UmbrellaKeeperPresenterConst::StandInScale);
	Part->SetWorldLocation(Keeper->GetActorLocation() + FVector(0.0, Layer->DepthOffset, 0.0));
	// State layers start hidden; Tick shows them while their state holds.
	Part->SetVisibility(VisualId != UmbrellaKeeperPresenterConst::MaskVisual && VisualId != UmbrellaKeeperPresenterConst::DepartureVisual);
	return Result;
}

void UKeeperPresenterSubsystem::ShowStandIn(AActor* Keeper)
{
	if (!IsValid(Keeper) || !IsFeatureEnabled(EFeatureId::ANIM_06))
	{
		return;
	}
	static const FName StandInName(TEXT("KeeperStandIn"));
	if (FindObjectFast<UStaticMeshComponent>(Keeper, StandInName))
	{
		return;
	}
	UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(Keeper, StandInName);
	if (UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")))
	{
		Mesh->SetStaticMesh(Shape);
	}
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetGenerateOverlapEvents(false);
	Mesh->SetRelativeScale3D(UmbrellaKeeperPresenterConst::StandInScale);
	ArtSlot::SetFlatUnlit(Mesh, Keeper, UmbrellaArtSlotConst::StandInKeeperColor);
	if (!Keeper->GetRootComponent())
	{
		Keeper->SetRootComponent(Mesh);
	}
	else
	{
		Mesh->SetupAttachment(Keeper->GetRootComponent());
	}
	// Art slot keeper:body-hover-flap; the cube stays when no asset exists.
	if (const FArtSlotRow* Row = ArtSlot::Find(TEXT("keeper:body-hover-flap")))
	{
		ArtSlot::ApplyRow(Mesh, *Row, UmbrellaKeeperPresenterConst::StandInScale);
	}
	Mesh->RegisterComponent();
	// Part slots (wings, mechanism, clock cover, talon) are layers over the body that exist only when their asset does.
	for (const UmbrellaKeeperPresenterConst::FKeeperPartLayer& Layer : UmbrellaKeeperPresenterConst::PartLayers)
	{
		ShowPartArt(Keeper, Layer.Visual, nullptr);
	}
	++PresentedCount;
}
