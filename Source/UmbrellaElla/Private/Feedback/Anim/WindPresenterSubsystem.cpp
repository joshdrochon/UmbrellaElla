#include "Feedback/Anim/WindPresenterSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Feedback/Art/ArtSlot.h"
#include "Field/WindCurrent.h"
#include "Harness/UmbrellaFeatureFlags.h"

namespace
{
	FName WindOverlayName(const FString& VisualId)
	{
		FString Name = VisualId;
		Name.ReplaceInline(TEXT(":"), TEXT("_"));
		return FName(*(FString(TEXT("WindArt_")) + Name));
	}

	/** Width/height/depth box scale of the card the current draws, whether it shows the colour card or its picture. */
	FVector WindCardBox(const UStaticMeshComponent* Field)
	{
		const FVector Scale = Field->GetRelativeScale3D();
		return ArtSlot::IsDrawingArt(Field) ? FVector(Scale.X, UmbrellaWindPresenterConst::OverlayDepth, Scale.Y) : Scale;
	}
}

int32 UWindPresenterSubsystem::GustFrameAt(float Seconds, int32 Frames)
{
	return Frames > 1 ? FMath::FloorToInt32(FMath::Max(Seconds, 0.0f) * UmbrellaWindPresenterConst::GustFps) % Frames : 0;
}

UStaticMeshComponent* UWindPresenterSubsystem::FindOverlay(const AWindCurrent* Wind, const FString& VisualId)
{
	TInlineComponentArray<UStaticMeshComponent*> Meshes(Wind);
	for (UStaticMeshComponent* Mesh : Meshes)
	{
		if (Mesh->GetFName() == WindOverlayName(VisualId))
		{
			return Mesh;
		}
	}
	return nullptr;
}

void UWindPresenterSubsystem::PostInitialize()
{
	Super::PostInitialize();
	if (UWorld* World = GetWorld())
	{
		SpawnHandle = World->AddOnActorSpawnedHandler(FOnActorSpawned::FDelegate::CreateUObject(this, &UWindPresenterSubsystem::HandleActorSpawned));
	}
}

void UWindPresenterSubsystem::Deinitialize()
{
	if (UWorld* World = GetWorld())
	{
		World->RemoveOnActorSpawnedHandler(SpawnHandle);
	}
	Super::Deinitialize();
}

void UWindPresenterSubsystem::HandleActorSpawned(AActor* Actor)
{
	if (AWindCurrent* Wind = Cast<AWindCurrent>(Actor))
	{
		FWindEntry& Entry = Winds.AddDefaulted_GetRef();
		Entry.Wind = Wind;
	}
}

EArtSlotDraw UWindPresenterSubsystem::ShowArt(AWindCurrent* Wind, const FString& VisualId, UTexture2D* Texture)
{
	UStaticMeshComponent* Field = IsValid(Wind) ? Wind->GetField() : nullptr;
	const FArtSlotRow* Row = ArtSlot::Find(*VisualId);
	if (!Field || !Field->GetStaticMesh() || !Row || !IsFeatureEnabled(EFeatureId::FLOW_25))
	{
		return EArtSlotDraw::NoTexture;
	}
	if (VisualId == UmbrellaWindPresenterConst::FieldVisual)
	{
		if (ArtSlot::IsDrawingArt(Field))
		{
			return EArtSlotDraw::NoTexture;
		}
		const EArtSlotDraw Result = ArtSlot::Apply(Field, Texture, *Row, Field->GetRelativeScale3D());
		for (FWindEntry& Entry : Winds)
		{
			if (Entry.Wind == Wind && Result == EArtSlotDraw::Drawn)
			{
				Entry.FieldTexture = Texture;
			}
		}
		return Result;
	}
	if (FindOverlay(Wind, VisualId) || !IsValid(Texture))
	{
		return EArtSlotDraw::NoTexture;
	}
	UStaticMeshComponent* Overlay = NewObject<UStaticMeshComponent>(Wind, WindOverlayName(VisualId));
	Overlay->SetupAttachment(Wind->GetRootComponent());
	const EArtSlotDraw Result = ArtSlot::Apply(Overlay, Texture, *Row, WindCardBox(Field));
	if (Result != EArtSlotDraw::Drawn)
	{
		Overlay->DestroyComponent();
		return Result;
	}
	const bool bGust = VisualId == UmbrellaWindPresenterConst::GustVisual;
	Overlay->SetRelativeLocation(Field->GetRelativeLocation() + FVector(0.0, bGust ? UmbrellaWindPresenterConst::GustLift : UmbrellaWindPresenterConst::LinesLift, 0.0));
	Overlay->RegisterComponent();
	return Result;
}

void UWindPresenterSubsystem::Follow(AWindCurrent* Wind)
{
	UStaticMeshComponent* Field = Wind->GetField();
	if (!Field || !Field->GetStaticMesh() || !Field->IsVisible())
	{
		return;
	}
	FWindEntry* Found = Winds.FindByPredicate([Wind](const FWindEntry& Entry) { return Entry.Wind == Wind; });
	if (!Found)
	{
		return;
	}
	// A refresh of the current puts its colour card back; draw the picture again, from the texture already loaded.
	if (!ArtSlot::IsDrawingArt(Field))
	{
		UTexture2D* Texture = Found->FieldTexture.Get();
		if (!Texture && !Found->bLoaded)
		{
			if (const FArtSlotRow* Row = ArtSlot::Find(UmbrellaWindPresenterConst::FieldVisual))
			{
				Texture = ArtSlot::LoadTexture(*Row);
			}
		}
		if (Texture)
		{
			ShowArt(Wind, UmbrellaWindPresenterConst::FieldVisual, Texture);
		}
	}
	if (!Found->bLoaded)
	{
		Found->bLoaded = true;
		for (const TCHAR* Visual : { UmbrellaWindPresenterConst::LinesVisual, UmbrellaWindPresenterConst::GustVisual })
		{
			if (const FArtSlotRow* Row = ArtSlot::Find(Visual))
			{
				if (UTexture2D* Texture = ArtSlot::LoadTexture(*Row))
				{
					ShowArt(Wind, Visual, Texture);
				}
			}
		}
	}
	const float Seconds = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
	for (const TCHAR* Visual : { UmbrellaWindPresenterConst::LinesVisual, UmbrellaWindPresenterConst::GustVisual })
	{
		if (UStaticMeshComponent* Overlay = FindOverlay(Wind, Visual))
		{
			ArtSlot::SetBoxScale(Overlay, WindCardBox(Field));
			if (const FArtSlotRow* Row = ArtSlot::Find(Visual))
			{
				ArtSlot::SetFrame(Overlay, GustFrameAt(Seconds, Row->Cols));
			}
		}
	}
}

void UWindPresenterSubsystem::Tick(float DeltaTime)
{
	Winds.RemoveAll([](const FWindEntry& Entry) { return !Entry.Wind.IsValid(); });
	for (const FWindEntry& Entry : Winds)
	{
		if (AWindCurrent* Wind = Entry.Wind.Get())
		{
			Follow(Wind);
		}
	}
}

TStatId UWindPresenterSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UWindPresenterSubsystem, STATGROUP_Tickables);
}
