#include "Feedback/Anim/ShotPresenterSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Feedback/Art/ArtSlot.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Projectile/UmbrellaProjectile.h"

FString UShotPresenterSubsystem::VisualIdFor(EUmbrellaShotKind Kind)
{
	switch (Kind)
	{
	case EUmbrellaShotKind::EnemyRed:
		return TEXT("shot:red");
	case EUmbrellaShotKind::EnemyYellow:
		return TEXT("shot:yellow");
	default:
		return TEXT("shot:gold");
	}
}

void UShotPresenterSubsystem::PostInitialize()
{
	Super::PostInitialize();
	if (UWorld* World = GetWorld())
	{
		SpawnHandle = World->AddOnActorSpawnedHandler(FOnActorSpawned::FDelegate::CreateUObject(this, &UShotPresenterSubsystem::HandleActorSpawned));
	}
}

void UShotPresenterSubsystem::Deinitialize()
{
	if (UWorld* World = GetWorld())
	{
		World->RemoveOnActorSpawnedHandler(SpawnHandle);
	}
	Super::Deinitialize();
}

void UShotPresenterSubsystem::HandleActorSpawned(AActor* Actor)
{
	if (AUmbrellaProjectile* Shot = Cast<AUmbrellaProjectile>(Actor))
	{
		Shots.Add(Shot);
	}
}

EArtSlotDraw UShotPresenterSubsystem::ShowArt(AUmbrellaProjectile* Shot, UTexture2D* Texture)
{
	UStaticMeshComponent* Mesh = IsValid(Shot) ? Cast<UStaticMeshComponent>(Shot->GetRootComponent()) : nullptr;
	const FArtSlotRow* Row = IsValid(Shot) ? ArtSlot::Find(*VisualIdFor(Shot->GetSpec().Kind)) : nullptr;
	if (!Mesh || !Row || !IsFeatureEnabled(EFeatureId::ANIM_05) || ArtSlot::HasArt(Mesh))
	{
		return EArtSlotDraw::NoTexture;
	}
	// The sphere's world scale is the shot's diameter / 100; the picture keeps that width and height.
	const EArtSlotDraw Result = ArtSlot::Apply(Mesh, Texture, *Row, Mesh->GetComponentScale());
	if (Result == EArtSlotDraw::Drawn)
	{
		++PresentedCount;
	}
	return Result;
}

void UShotPresenterSubsystem::Tick(float DeltaTime)
{
	// Fire() sets the sphere right after the spawn, so a shot is drawn on the first tick that finds its sphere.
	for (int32 Index = Shots.Num() - 1; Index >= 0; --Index)
	{
		AUmbrellaProjectile* Shot = Shots[Index].Get();
		const UStaticMeshComponent* Mesh = IsValid(Shot) ? Cast<UStaticMeshComponent>(Shot->GetRootComponent()) : nullptr;
		if (!Mesh)
		{
			Shots.RemoveAtSwap(Index);
		}
		else if (Mesh->GetStaticMesh())
		{
			if (const FArtSlotRow* Row = ArtSlot::Find(*VisualIdFor(Shot->GetSpec().Kind)))
			{
				ShowArt(Shot, ArtSlot::LoadTexture(*Row));
			}
			Shots.RemoveAtSwap(Index);
		}
	}
}

TStatId UShotPresenterSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UShotPresenterSubsystem, STATGROUP_Tickables);
}
