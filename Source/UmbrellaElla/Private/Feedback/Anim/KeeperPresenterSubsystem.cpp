#include "Feedback/Anim/KeeperPresenterSubsystem.h"
#include "Arena/UmbrellaArena.h"
#include "EngineUtils.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
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
	TArray<EKeeperPart> KeeperPartsCoveredBy(const FString& VisualId)
	{
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
		return Covered;
	}

	void KeeperCoverStandIns(AActor* Keeper, const FString& VisualId)
	{
		if (AKeeperOfTime* Owl = Cast<AKeeperOfTime>(Keeper))
		{
			for (const EKeeperPart Part : KeeperPartsCoveredBy(VisualId))
			{
				Owl->MarkPartArtDrawn(Part);
			}
		}
	}
}

void UKeeperPresenterSubsystem::PostInitialize()
{
	Super::PostInitialize();
	if (UWorld* World = GetWorld())
	{
		SpawnHandle = World->AddOnActorSpawnedHandler(FOnActorSpawned::FDelegate::CreateUObject(this, &UKeeperPresenterSubsystem::HandleActorSpawned));
		DestroyHandle = World->AddOnActorDestroyedHandler(FOnActorDestroyed::FDelegate::CreateUObject(this, &UKeeperPresenterSubsystem::HandleActorDestroyed));
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
		World->RemoveOnActorDestroyedHandler(DestroyHandle);
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
	else if (AUmbrellaArena* Arena = Cast<AUmbrellaArena>(Actor))
	{
		Arena->SetKeeperArtShown(bArenaArtShown);
	}
}

void UKeeperPresenterSubsystem::HandleActorDestroyed(AActor* Actor)
{
	if (Cast<AKeeperOfTime>(Actor))
	{
		Keepers.Remove(TWeakObjectPtr<AActor>(Actor));
		SyncArenaStandIn();
	}
}

void UKeeperPresenterSubsystem::SyncPartCover(AKeeperOfTime* Owl)
{
	if (!Owl)
	{
		return;
	}
	// What the art draws now: the body picture and every part layer that still exists.
	uint8 Covered = 0;
	auto Add = [&Covered](const FString& VisualId)
	{
		for (const EKeeperPart Part : KeeperPartsCoveredBy(VisualId))
		{
			Covered |= static_cast<uint8>(1u << static_cast<uint8>(Part));
		}
	};
	static const FName StandInName(TEXT("KeeperStandIn"));
	const UStaticMeshComponent* Body = FindObjectFast<UStaticMeshComponent>(Owl, StandInName);
	if (Body && ArtSlot::HasArt(Body))
	{
		Add(TEXT("keeper:body-hover-flap"));
	}
	for (const UmbrellaKeeperPresenterConst::FKeeperPartLayer& Layer : UmbrellaKeeperPresenterConst::PartLayers)
	{
		if (FindPart(Owl, Layer.Visual))
		{
			Add(Layer.Visual);
		}
	}
	for (uint8 Index = 0; Index < static_cast<uint8>(EKeeperPart::Count); ++Index)
	{
		const EKeeperPart Part = static_cast<EKeeperPart>(Index);
		const bool bCovered = (Covered & (1u << Index)) != 0;
		if (bCovered && !Owl->IsPartArtDrawn(Part))
		{
			Owl->MarkPartArtDrawn(Part);
		}
		else if (!bCovered && Owl->IsPartArtDrawn(Part))
		{
			Owl->ClearPartArtDrawn(Part);
		}
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

bool UKeeperPresenterSubsystem::HasKeeperArt(const AActor* Keeper)
{
	if (!IsValid(Keeper))
	{
		return false;
	}
	static const FName StandInName(TEXT("KeeperStandIn"));
	const UStaticMeshComponent* Body = FindObjectFast<UStaticMeshComponent>(const_cast<AActor*>(Keeper), StandInName);
	if (Body && ArtSlot::HasArt(Body))
	{
		return true;
	}
	for (const UmbrellaKeeperPresenterConst::FKeeperPartLayer& Layer : UmbrellaKeeperPresenterConst::PartLayers)
	{
		if (FindPart(Keeper, Layer.Visual))
		{
			return true;
		}
	}
	return false;
}

bool UKeeperPresenterSubsystem::HasAnyKeeperArt() const
{
	for (const TWeakObjectPtr<AActor>& Keeper : Keepers)
	{
		if (HasKeeperArt(Keeper.Get()))
		{
			return true;
		}
	}
	return false;
}

void UKeeperPresenterSubsystem::SyncArenaStandIn()
{
	const bool bArt = HasAnyKeeperArt();
	bArenaArtShown = bArt;
	if (UWorld* World = GetWorld())
	{
		for (TActorIterator<AUmbrellaArena> It(World); It; ++It)
		{
			if (It->IsKeeperArtShown() != bArt)
			{
				It->SetKeeperArtShown(bArt);
			}
		}
	}
}

void UKeeperPresenterSubsystem::Tick(float DeltaTime)
{
	bool bKeeperGone = false;
	for (int32 Index = Keepers.Num() - 1; Index >= 0; --Index)
	{
		AActor* Keeper = Keepers[Index].Get();
		AKeeperOfTime* Owl = Cast<AKeeperOfTime>(Keeper);
		if (!Owl)
		{
			Keepers.RemoveAtSwap(Index);
			bKeeperGone = true;
			continue;
		}
		SyncPartCover(Owl);
		PlayIdle(Owl);
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
	// The arena square changes only when a Keeper goes or its art does; no world search otherwise.
	if (bKeeperGone || HasAnyKeeperArt() != bArenaArtShown)
	{
		SyncArenaStandIn();
	}
}

FVector UKeeperPresenterSubsystem::BodyArtScaleFor(const UTexture2D* Texture, const FArtSlotRow& Row)
{
	// Keep the body width; the height follows one sheet cell's aspect, so the picture is never squashed into the square box.
	const double Width = UmbrellaKeeperPresenterConst::StandInScale.X;
	float Aspect = ArtSlot::CellAspect(Texture, Row);
#if WITH_EDITORONLY_DATA
	// An uncooked run reads the texture while it still compiles: GetSizeX/Y give the placeholder's size (square), which
	// drew the body 600 x 900 (VQDUMP). The source keeps the picture's real size.
	// UE 5.8.4 Engine/Classes/Engine/Texture.h: UTexture::Source (FTextureSource, line 1272, editor-only data);
	// FTextureSource::IsValid() (line 372), GetSizeX()/GetSizeY() (lines 417-418, int64).
	if (IsValid(Texture) && Texture->Source.IsValid() && Texture->Source.GetSizeY() > 0)
	{
		Aspect = (static_cast<float>(Texture->Source.GetSizeX()) / FMath::Max(1, Row.Cols)) / (static_cast<float>(Texture->Source.GetSizeY()) / FMath::Max(1, Row.Rows));
	}
#endif
	return FVector(Width, UmbrellaKeeperPresenterConst::StandInScale.Y, Width / FMath::Max(UmbrellaKeeperPresenterConst::MinBodyAspect, Aspect));
}

int32 UKeeperPresenterSubsystem::IdleFrameAt(double Seconds, float Fps, int32 Cols, int32 Rows, EKeeperGridPlayback Playback)
{
	const int32 SafeCols = FMath::Max(1, Cols);
	const int64 Step = FMath::Max<int64>(0, FMath::FloorToInt64(FMath::Max(0.0, Seconds) * FMath::Max(0.0f, Fps)));
	if (Playback == EKeeperGridPlayback::AllCells)
	{
		return static_cast<int32>(Step % (SafeCols * FMath::Max(1, Rows)));
	}
	if (SafeCols == 1)
	{
		return 0;
	}
	const int64 Period = 2 * SafeCols - 2;
	const int32 Index = static_cast<int32>(Step % Period);
	return Index < SafeCols ? Index : static_cast<int32>(Period) - Index;
}

void UKeeperPresenterSubsystem::PlayIdle(AActor* Keeper) const
{
	static const FName StandInName(TEXT("KeeperStandIn"));
	UStaticMeshComponent* Mesh = IsValid(Keeper) ? FindObjectFast<UStaticMeshComponent>(Keeper, StandInName) : nullptr;
	const FArtSlotRow* Row = ArtSlot::Find(TEXT("keeper:body-hover-flap"));
	if (!Mesh || !Row || !ArtSlot::HasArt(Mesh) || Row->Cols * Row->Rows <= 1 || !GetWorld())
	{
		return;
	}
	ArtSlot::SetFrame(Mesh, IdleFrameAt(GetWorld()->GetTimeSeconds(), UmbrellaKeeperPresenterConst::IdleFps, Row->Cols, Row->Rows,
		UmbrellaKeeperPresenterConst::IdlePlayback));
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
	const EArtSlotDraw Result = ArtSlot::Apply(Mesh, Texture, *Row, BodyArtScaleFor(Texture, *Row));
	if (Result == EArtSlotDraw::Drawn)
	{
		KeeperCoverStandIns(Keeper, Row->Visual);
		SyncArenaStandIn();
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

bool UKeeperPresenterSubsystem::ShouldPartPictureYieldToBody(const UTexture2D* Picture, const AActor* Keeper)
{
	static const FName StandInName(TEXT("KeeperStandIn"));
	const UStaticMeshComponent* Body = IsValid(Keeper) ? FindObjectFast<UStaticMeshComponent>(const_cast<AActor*>(Keeper), StandInName) : nullptr;
	// Part stand-ins were cut for an older body; layered over the body art they hide it. A passed part still draws.
	return IsValid(Picture) && ArtSlot::HasArt(Body) && Picture->GetName().EndsWith(UmbrellaArtSlotConst::PlaceholderSuffix);
}

UStaticMeshComponent* UKeeperPresenterSubsystem::FindPart(const AActor* Keeper, const FString& VisualId)
{
	UStaticMeshComponent* Part = IsValid(Keeper) ? FindObjectFast<UStaticMeshComponent>(const_cast<AActor*>(Keeper), KeeperPartName(VisualId)) : nullptr;
	// A destroyed layer waits for garbage collection under the same name; it no longer draws.
	return IsValid(Part) ? Part : nullptr;
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
	if (!Picture || ShouldPartPictureYieldToBody(Picture, Keeper))
	{
		return EArtSlotDraw::NoTexture;
	}
	if (UStaticMeshComponent* Stale = FindObjectFast<UStaticMeshComponent>(Keeper, KeeperPartName(VisualId)))
	{
		// A destroyed layer still holds the name until garbage collection; move it aside so the new layer can take it.
		Stale->Rename(nullptr, GetTransientPackage(), REN_DontCreateRedirectors);
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
	KeeperCoverStandIns(Keeper, VisualId);
	SyncArenaStandIn();
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
		UTexture2D* Body = ArtSlot::LoadTexture(*Row);
		if (ArtSlot::Apply(Mesh, Body, *Row, BodyArtScaleFor(Body, *Row)) == EArtSlotDraw::Drawn)
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
	SyncArenaStandIn();
}
