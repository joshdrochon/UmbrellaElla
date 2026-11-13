#include "Feedback/Anim/KeeperPresenterSubsystem.h"
#include "Components/StaticMeshComponent.h"
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
	}
}

void UKeeperPresenterSubsystem::Deinitialize()
{
	if (UWorld* World = GetWorld())
	{
		World->RemoveOnActorSpawnedHandler(SpawnHandle);
	}
	Super::Deinitialize();
}

void UKeeperPresenterSubsystem::HandleActorSpawned(AActor* Actor)
{
	if (Cast<AKeeperOfTime>(Actor))
	{
		ShowStandIn(Actor);
	}
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
	++PresentedCount;
}
