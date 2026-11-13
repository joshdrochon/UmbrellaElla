#include "Feedback/Anim/KeeperPresenterSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Feedback/Art/ArtSlot.h"
#include "GameFramework/Actor.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Owl/KeeperOfTime.h"

namespace
{
	/**
	 * Which Keeper stand-in cubes a drawn slot covers. The body sprite paints wings, clock and the three mechanisms at
	 * home; a part layer covers its own part. The exposed eye, chain head, talon tip, gust and telegraph are state cues
	 * with no slot art at their position, so their cubes stay.
	 */
	void KeeperCoverStandIns(AActor* Keeper, const FString& VisualId)
	{
		AKeeperOfTime* Owl = Cast<AKeeperOfTime>(Keeper);
		if (!Owl)
		{
			return;
		}
		TArray<EKeeperPart> Covered;
		if (VisualId == TEXT("keeper:body-hover-flap"))
		{
			Covered = {EKeeperPart::Wings, EKeeperPart::Clock, EKeeperPart::Front, EKeeperPart::Middle, EKeeperPart::Rear};
		}
		else if (VisualId == TEXT("keeper:wings-gust-wear"))
		{
			Covered = {EKeeperPart::Wings};
		}
		else if (VisualId == TEXT("keeper:clock-cover-glass-hands"))
		{
			Covered = {EKeeperPart::Clock};
		}
		else if (VisualId == TEXT("keeper:mechanism-front"))
		{
			Covered = {EKeeperPart::Front};
		}
		else if (VisualId == TEXT("keeper:mechanism-middle"))
		{
			Covered = {EKeeperPart::Middle};
		}
		else if (VisualId == TEXT("keeper:mechanism-rear"))
		{
			Covered = {EKeeperPart::Rear};
		}
		for (const EKeeperPart Part : Covered)
		{
			Owl->SetPartArtDrawn(Part, true);
		}
	}
}

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
	const EArtSlotDraw Result = ArtSlot::Apply(Mesh, Texture, *Row, UmbrellaKeeperPresenterConst::StandInScale);
	if (Result == EArtSlotDraw::Drawn)
	{
		KeeperCoverStandIns(Keeper, Row->Visual);
	}
	return Result;
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
<<<<<<< HEAD
	KeeperCoverStandIns(Keeper, VisualId);
	// State layers start hidden; Tick shows them while their state holds.
	Part->SetVisibility(VisualId != UmbrellaKeeperPresenterConst::MaskVisual && VisualId != UmbrellaKeeperPresenterConst::DepartureVisual);
=======
>>>>>>> parent of 2c293acc (Merge remote-tracking branch 'origin/area/artslots' into area/artkeeper)
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
		if (ArtSlot::ApplyRow(Mesh, *Row, UmbrellaKeeperPresenterConst::StandInScale) == EArtSlotDraw::Drawn)
		{
			KeeperCoverStandIns(Keeper, Row->Visual);
		}
	}
	Mesh->RegisterComponent();
	// Part slots (wings, mechanism, clock cover, talon) are layers over the body that exist only when their asset does.
	for (const UmbrellaKeeperPresenterConst::FKeeperPartLayer& Layer : UmbrellaKeeperPresenterConst::PartLayers)
	{
		ShowPartArt(Keeper, Layer.Visual, nullptr);
	}
	++PresentedCount;
}
