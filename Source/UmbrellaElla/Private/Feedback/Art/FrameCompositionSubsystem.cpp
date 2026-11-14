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

DEFINE_LOG_CATEGORY_STATIC(LogUmbrellaFrame, Log, All);

namespace
{
	bool FrameIsBrighter(const FLinearColor& A, const FLinearColor& B)
	{
		return A.R + A.G + A.B > B.R + B.G + B.B + UmbrellaFrameConst::AppliedTolerance;
	}
}

EFrameTreatment UFrameCompositionSubsystem::TreatmentFor(FName ComponentName, float WorldY, bool bDrawsArt, bool bSlotMaterial, const FLinearColor& Tint)
{
	if (!bSlotMaterial)
	{
		return EFrameTreatment::Keep;
	}
	if (!bDrawsArt && ComponentName == FName(UmbrellaFrameConst::KeeperStandInName))
	{
		return EFrameTreatment::Hide;
	}
	if (WorldY < UmbrellaFrameConst::BehindPlayY)
	{
		if (bDrawsArt)
		{
			return Tint.Equals(UmbrellaFrameConst::BackdropDim, UmbrellaFrameConst::AppliedTolerance) ? EFrameTreatment::Keep : EFrameTreatment::DimBackdropArt;
		}
		return FrameIsBrighter(Tint, UmbrellaFrameConst::BackdropFlat) ? EFrameTreatment::DarkenBackdropPanel : EFrameTreatment::Keep;
	}
	if (!bDrawsArt && Tint.Equals(UmbrellaArtSlotConst::StandInDefaultColor, UmbrellaFrameConst::RoleTolerance))
	{
		return EFrameTreatment::TintIsland;
	}
	if (!bDrawsArt && Tint.Equals(UmbrellaArtSlotConst::StandInEnemyColor, UmbrellaFrameConst::RoleTolerance))
	{
		return EFrameTreatment::TintEnemy;
	}
	return EFrameTreatment::Keep;
}

int32 UFrameCompositionSubsystem::ComposeNow()
{
	int32 Changed = 0;
	UWorld* World = GetWorld();
	if (!World)
	{
		return 0;
	}
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		TInlineComponentArray<UStaticMeshComponent*> Meshes(*It);
		for (UStaticMeshComponent* Mesh : Meshes)
		{
			if (!IsValid(Mesh) || Mesh->bHiddenInGame || !ArtSlot::IsUnlit(Mesh))
			{
				continue;
			}
			const bool bArt = ArtSlot::IsDrawingArt(Mesh);
			const FLinearColor Tint = ArtSlot::GetTint(Mesh);
			const EFrameTreatment Treatment = TreatmentFor(Mesh->GetFName(), static_cast<float>(Mesh->GetComponentLocation().Y), bArt, true, Tint);
			switch (Treatment)
			{
			case EFrameTreatment::Hide: Mesh->SetHiddenInGame(true); break;
			case EFrameTreatment::DimBackdropArt: ArtSlot::SetTint(Mesh, UmbrellaFrameConst::BackdropDim); break;
			case EFrameTreatment::DarkenBackdropPanel: ArtSlot::SetTint(Mesh, UmbrellaFrameConst::BackdropFlat); break;
			case EFrameTreatment::TintIsland: ArtSlot::SetTint(Mesh, UmbrellaFrameConst::IslandUmber); break;
			case EFrameTreatment::TintEnemy: ArtSlot::SetTint(Mesh, UmbrellaFrameConst::EnemyShadow); break;
			default: continue;
			}
			++Changed;
		}
	}
	return Changed;
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

float UFrameCompositionSubsystem::MarginOrthoWidth(float ArenaHeight, float AspectRatio, float SpriteHalf, float CapsuleHalf)
{
	const float Overhang = FMath::Max(0.0f, SpriteHalf - CapsuleHalf) + UmbrellaFrameConst::CeilingSpritePad;
	return (ArenaHeight + 2.0f * Overhang) * AspectRatio;
}

float UFrameCompositionSubsystem::FrameTopZ(float CameraZ, float OrthoWidth, float AspectRatio)
{
	return CameraZ + OrthoWidth / AspectRatio * 0.5f;
}

void UFrameCompositionSubsystem::ApplyCameraMargin(AUmbrellaArena* Arena, const ACharacter* Ella)
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
		SpriteHalfHeight(static_cast<float>(Ella->GetActorScale3D().Z)), Capsule->GetScaledCapsuleHalfHeight());
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
	SinceLastPass += DeltaTime;
	if (SinceLastPass >= UmbrellaFrameConst::PassInterval || SinceLastPass == 0.0f)
	{
		SinceLastPass = 0.0f;
		ComposeNow();
		const APlayerController* PC = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
		const ACharacter* Ella = PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
		if (Ella)
		{
			for (TActorIterator<AUmbrellaArena> It(GetWorld()); It; ++It)
			{
				ApplyCameraMargin(*It, Ella);
			}
		}
	}
}

TStatId UFrameCompositionSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UFrameCompositionSubsystem, STATGROUP_Tickables);
}
