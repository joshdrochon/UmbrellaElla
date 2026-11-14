#include "Feedback/Art/FrameCompositionSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "EngineUtils.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Arena/UmbrellaArena.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Core/UmbrellaTuning.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Feedback/Art/ArtSlot.h"
#include "GameFramework/Character.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Actor.h"
#include "Misc/CommandLine.h"
#include "Misc/Parse.h"
#include "Flow/UmbrellaPlayerController.h"

DEFINE_LOG_CATEGORY_STATIC(LogUmbrellaFrame, Log, All);

namespace
{
	bool FrameIsBrighter(const FLinearColor& A, const FLinearColor& B)
	{
		return A.R + A.G + A.B > B.R + B.G + B.B + UmbrellaFrameConst::AppliedTolerance;
	}
}

EFrameTreatment UFrameCompositionSubsystem::TreatmentFor(const FFrameMeshFacts& F)
{
	if (!F.bSlotMaterial)
	{
		return EFrameTreatment::Keep;
	}
	const bool bKeeperStandIn = !F.bDrawsArt && (F.ComponentName == FName(UmbrellaFrameConst::KeeperStandInName)
		|| F.Tint.Equals(UmbrellaArtSlotConst::StandInKeeperColor, UmbrellaFrameConst::RoleTolerance));
	if (bKeeperStandIn)
	{
		// The arena's lilac square is never drawn (the Keeper actor is the Keeper; on the route it was a grey box). The
		// Keeper actor's own stand-ins are always seen.
		return F.bArenaOwned ? EFrameTreatment::Hide : EFrameTreatment::TintKeeper;
	}
	if (!F.bDrawsArt && (F.ComponentName == FName(UmbrellaFrameConst::EllaStandInName)
		|| F.Tint.Equals(UmbrellaArtSlotConst::StandInEllaColor, UmbrellaFrameConst::RoleTolerance)))
	{
		return EFrameTreatment::TintElla;
	}
	if (F.WorldY < UmbrellaFrameConst::BehindPlayY)
	{
		if (F.bDrawsArt)
		{
			return F.Tint.Equals(UmbrellaFrameConst::BackdropDim, UmbrellaFrameConst::AppliedTolerance) ? EFrameTreatment::Keep : EFrameTreatment::DimBackdropArt;
		}
		return FrameIsBrighter(F.Tint, UmbrellaFrameConst::BackdropFlat) ? EFrameTreatment::DarkenBackdropPanel : EFrameTreatment::Keep;
	}
	if (!F.bDrawsArt && F.Tint.Equals(UmbrellaArtSlotConst::StandInDefaultColor, UmbrellaFrameConst::RoleTolerance))
	{
		return EFrameTreatment::TintIsland;
	}
	if (!F.bDrawsArt && F.Tint.Equals(UmbrellaArtSlotConst::StandInEnemyColor, UmbrellaFrameConst::RoleTolerance))
	{
		return EFrameTreatment::TintEnemy;
	}
	return EFrameTreatment::Keep;
}

FLinearColor UFrameCompositionSubsystem::TintFor(EFrameTreatment Treatment)
{
	switch (Treatment)
	{
	case EFrameTreatment::DimBackdropArt: return UmbrellaFrameConst::BackdropDim;
	case EFrameTreatment::DarkenBackdropPanel: return UmbrellaFrameConst::BackdropFlat;
	case EFrameTreatment::TintIsland: return UmbrellaFrameConst::IslandUmber;
	case EFrameTreatment::TintEnemy: return UmbrellaFrameConst::EnemyShadow;
	case EFrameTreatment::TintKeeper: return UmbrellaFrameConst::KeeperMetal;
	case EFrameTreatment::TintElla: return UmbrellaFrameConst::EllaInk;
	default: return FLinearColor::White;
	}
}

bool UFrameCompositionSubsystem::DoesSupportWorldType(const EWorldType::Type WorldType) const
{
	// Gameplay worlds only: never the editor, previews or inactive worlds.
	return WorldType == EWorldType::Game || WorldType == EWorldType::PIE;
}

void UFrameCompositionSubsystem::PostInitialize()
{
	Super::PostInitialize();
	if (UWorld* World = GetWorld())
	{
		SpawnHandle = World->AddOnActorSpawnedHandler(FOnActorSpawned::FDelegate::CreateUObject(this, &UFrameCompositionSubsystem::HandleActorSpawned));
	}
}

void UFrameCompositionSubsystem::Deinitialize()
{
	if (UWorld* World = GetWorld())
	{
		World->RemoveOnActorSpawnedHandler(SpawnHandle);
	}
	RestoreAll();
	Super::Deinitialize();
}

void UFrameCompositionSubsystem::HandleActorSpawned(AActor* Actor)
{
	if (IsValid(Actor))
	{
		NewActors.Add(Actor, UmbrellaFrameConst::NewActorPasses);
	}
}

AUmbrellaArena* UFrameCompositionSubsystem::FindArena()
{
	UWorld* World = GetWorld();
	if (!CachedArena.IsValid() && World)
	{
		TActorIterator<AUmbrellaArena> It(World);
		CachedArena = It ? *It : nullptr;
	}
	return CachedArena.Get();
}

int32 UFrameCompositionSubsystem::ComposeMesh(UStaticMeshComponent* Mesh)
{
	if (!IsValid(Mesh))
	{
		return 0;
	}
	FFrameOriginal* Original = Touched.Find(Mesh);
	if (!Original && (Mesh->bHiddenInGame || !ArtSlot::IsUnlit(Mesh)))
	{
		return 0;
	}
	const bool bArt = ArtSlot::IsDrawingArt(Mesh);
	if (Original && Original->bDrawsArt != bArt)
	{
		// The mesh started (or stopped) drawing a picture: its material is new, so take its own state again.
		if (Mesh->bHiddenInGame != Original->bHiddenInGame)
		{
			Mesh->SetHiddenInGame(Original->bHiddenInGame);
		}
		Touched.Remove(Mesh);
		Original = nullptr;
		if (Mesh->bHiddenInGame || !ArtSlot::IsUnlit(Mesh))
		{
			return 1;
		}
	}
	FFrameMeshFacts Facts;
	Facts.ComponentName = Mesh->GetFName();
	Facts.WorldY = static_cast<float>(Mesh->GetComponentLocation().Y);
	Facts.bDrawsArt = bArt;
	Facts.Tint = Original ? Original->Tint : ArtSlot::GetTint(Mesh);
	Facts.bArenaOwned = Cast<AUmbrellaArena>(Mesh->GetOwner()) != nullptr;
	const FLinearColor Current = ArtSlot::GetTint(Mesh);
	if (Original && !Current.Equals(Original->Applied, UmbrellaFrameConst::AppliedTolerance))
	{
		// Its owner set a colour of its own since our pass (a stand-in refresh, a flash): that is its own tint now.
		Original->Tint = Current;
		Facts.Tint = Current;
	}
	const EFrameTreatment Treatment = TreatmentFor(Facts);
	if (Treatment == EFrameTreatment::Keep)
	{
		if (!Original)
		{
			return 0;
		}
		// No longer a stand-in to change (a Keeper arrived, art draws): put the mesh back as its owner made it.
		ArtSlot::SetTint(Mesh, Original->Tint);
		Mesh->SetHiddenInGame(Original->bHiddenInGame);
		Touched.Remove(Mesh);
		return 1;
	}
	if (!Original)
	{
		Original = &Touched.Add(Mesh, FFrameOriginal{Facts.Tint, Current, Mesh->bHiddenInGame, bArt});
	}
	const bool bHide = Treatment == EFrameTreatment::Hide;
	const FLinearColor Want = bHide ? Original->Tint : TintFor(Treatment);
	int32 Changed = 0;
	if (Mesh->bHiddenInGame != (bHide || Original->bHiddenInGame))
	{
		Mesh->SetHiddenInGame(bHide || Original->bHiddenInGame);
		Changed = 1;
	}
	if (!Current.Equals(Want, UmbrellaFrameConst::AppliedTolerance))
	{
		ArtSlot::SetTint(Mesh, Want);
		Changed = 1;
	}
	Original->Applied = Want;
	return Changed;
}

int32 UFrameCompositionSubsystem::ComposePass(bool bFull)
{
	UWorld* World = GetWorld();
	if (!World)
	{
		return 0;
	}
	int32 Changed = 0;
	LastActorCount = 0;
	TSet<UStaticMeshComponent*> Seen;
	auto Visit = [&](AActor* Actor)
	{
		++LastActorCount;
		TInlineComponentArray<UStaticMeshComponent*> Meshes(Actor);
		for (UStaticMeshComponent* Mesh : Meshes)
		{
			Seen.Add(Mesh);
			Changed += ComposeMesh(Mesh);
		}
	};
	if (bFull)
	{
		NewActors.Reset();
		for (TActorIterator<AActor> It(World); It; ++It)
		{
			Visit(*It);
		}
	}
	else
	{
		for (auto It = NewActors.CreateIterator(); It; ++It)
		{
			if (AActor* Actor = It.Key().Get())
			{
				Visit(Actor);
			}
			if (!It.Key().IsValid() || --It.Value() <= 0)
			{
				It.RemoveCurrent();
			}
		}
	}
	// Meshes changed earlier are looked at every pass: a Keeper arriving or art landing restores them.
	TArray<TWeakObjectPtr<UStaticMeshComponent>> Earlier;
	Touched.GetKeys(Earlier);
	for (const TWeakObjectPtr<UStaticMeshComponent>& Weak : Earlier)
	{
		UStaticMeshComponent* Mesh = Weak.Get();
		if (!Mesh)
		{
			Touched.Remove(Weak);
		}
		else if (!Seen.Contains(Mesh))
		{
			Changed += ComposeMesh(Mesh);
		}
	}
	return Changed;
}

int32 UFrameCompositionSubsystem::ComposeNow()
{
	return ComposePass(true);
}

int32 UFrameCompositionSubsystem::RestoreAll()
{
	int32 Restored = 0;
	for (const TPair<TWeakObjectPtr<UStaticMeshComponent>, FFrameOriginal>& Pair : Touched)
	{
		if (UStaticMeshComponent* Mesh = Pair.Key.Get())
		{
			ArtSlot::SetTint(Mesh, Pair.Value.Tint);
			Mesh->SetHiddenInGame(Pair.Value.bHiddenInGame);
			++Restored;
		}
	}
	Touched.Reset();
	return Restored;
}

int32 UFrameCompositionSubsystem::DumpVisibleMeshes() const
{
	int32 Count = 0;
	UWorld* World = GetWorld();
	if (!World)
	{
		return 0;
	}
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		TInlineComponentArray<UStaticMeshComponent*> Meshes(*It);
		for (const UStaticMeshComponent* Mesh : Meshes)
		{
			if (!IsValid(Mesh) || !Mesh->IsVisible() || !Mesh->bRenderInMainPass || !Mesh->IsRegistered())
			{
				continue;
			}
			const FBoxSphereBounds& B = Mesh->Bounds;
			const FLinearColor Tint = ArtSlot::GetTint(Mesh);
			UE_LOG(LogUmbrellaFrame, Display, TEXT("VQDUMP owner=%s class=%s comp=%s mesh=%s at=(%.0f,%.0f,%.0f) half=(%.0f,%.0f,%.0f) art=%d unlit=%d tint=(%.3f,%.3f,%.3f)"),
				*It->GetName(), *It->GetClass()->GetName(), *Mesh->GetName(), Mesh->GetStaticMesh() ? *Mesh->GetStaticMesh()->GetName() : TEXT("-"),
				B.Origin.X, B.Origin.Y, B.Origin.Z, B.BoxExtent.X, B.BoxExtent.Y, B.BoxExtent.Z,
				ArtSlot::IsDrawingArt(Mesh) ? 1 : 0, ArtSlot::IsUnlit(Mesh) ? 1 : 0, Tint.R, Tint.G, Tint.B);
			++Count;
		}
	}
	return Count;
}

float UFrameCompositionSubsystem::SpriteHalfHeight(float ActorScaleZ)
{
	return static_cast<float>(UmbrellaPresenterConst::ArtCellHeight) * UmbrellaFrameConst::UnitBoxSize * 0.5f * ActorScaleZ;
}

float UFrameCompositionSubsystem::MarginOrthoWidth(float ArenaHeight, float AspectRatio, float SpriteHalf, float CapsuleHalf, float TopShare)
{
	const float Overhang = FMath::Max(0.0f, SpriteHalf - CapsuleHalf) + UmbrellaFrameConst::CeilingSpritePad;
	// View height V with the picture top at V/2 - TopShare*V above the centre: V = (ArenaHeight + 2*Overhang) / (1 - 2*TopShare).
	const float Clear = 1.0f - 2.0f * FMath::Clamp(TopShare, 0.0f, 0.25f);
	return (ArenaHeight + 2.0f * Overhang) * AspectRatio / Clear;
}

float UFrameCompositionSubsystem::FrameTopZ(float CameraZ, float OrthoWidth, float AspectRatio)
{
	return CameraZ + OrthoWidth / AspectRatio * 0.5f;
}

void UFrameCompositionSubsystem::ApplyCameraMargin(AUmbrellaArena* Arena, const ACharacter* Ella, bool bTitleBand)
{
	UCameraComponent* Camera = Arena ? Arena->GetPlayCamera() : nullptr;
	const UCapsuleComponent* Capsule = Ella ? Ella->GetCapsuleComponent() : nullptr;
	if (!Camera || !Capsule)
	{
		return;
	}
	const FArenaCameraTuning& T = GetDefault<UUmbrellaTuning>()->ArenaCamera;
	const float Current = Camera->OrthoWidth;
	const bool bOurs = FMath::IsNearlyEqual(Current, T.ArenaWidth, UmbrellaFrameConst::OrthoMatchTolerance)
		|| (LastMarginOrthoWidth > 0.0f && FMath::IsNearlyEqual(Current, LastMarginOrthoWidth, UmbrellaFrameConst::OrthoMatchTolerance));
	if (!bOurs)
	{
		return;
	}
	const float Wanted = MarginOrthoWidth(T.ArenaHeight, T.CameraAspectRatio,
		SpriteHalfHeight(static_cast<float>(Ella->GetActorScale3D().Z)), Capsule->GetScaledCapsuleHalfHeight(),
		bTitleBand ? UmbrellaFrameConst::TitleBandShare : 0.0f);
	LastMarginOrthoWidth = Wanted;
	if (FMath::IsNearlyEqual(Current, Wanted, UmbrellaFrameConst::OrthoMatchTolerance))
	{
		return;
	}
	Camera->SetOrthoWidth(Wanted);
}

void UFrameCompositionSubsystem::Tick(float DeltaTime)
{
	static const bool bDump = FParse::Param(FCommandLine::Get(), TEXT("VisualQADump"));
	SinceLastDump += DeltaTime;
	if (bDump && SinceLastDump >= UmbrellaFrameConst::DumpInterval)
	{
		SinceLastDump = 0.0f;
		UE_LOG(LogUmbrellaFrame, Display, TEXT("VQDUMP begin t=%.1f meshes=%d"), GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f, DumpVisibleMeshes());
	}
	// A world with no arena is a menu or loading world: nothing to compose.
	AUmbrellaArena* PlayArena = FindArena();
	if (!PlayArena)
	{
		return;
	}
	SinceLastPass += DeltaTime;
	SinceFullPass += DeltaTime;
	if (SinceLastPass >= UmbrellaFrameConst::PassInterval || !bPassedOnce)
	{
		SinceLastPass = 0.0f;
		const bool bFull = SinceFullPass >= UmbrellaFrameConst::FullPassInterval || !bPassedOnce;
		if (bFull)
		{
			SinceFullPass = 0.0f;
		}
		bPassedOnce = true;
		ComposePass(bFull);
		const APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
		if (const ACharacter* Ella = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr)
		{
			// Director's Cut shows its title at the top of the play screen (B11): keep Ella below that band.
			const AUmbrellaPlayerController* Flow = Cast<AUmbrellaPlayerController>(PC);
			ApplyCameraMargin(PlayArena, Ella, Flow && Flow->GetPlayMode() == EUmbrellaPlayMode::DirectorsCut);
		}
	}
}

TStatId UFrameCompositionSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UFrameCompositionSubsystem, STATGROUP_Tickables);
}
