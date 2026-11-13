#include "Field/WindCurrent.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Core/UmbrellaTuning.h"
#include "GameFramework/Pawn.h"
#include "Harness/UmbrellaFeatureFlags.h"

AWindCurrent::AWindCurrent()
{
	PrimaryActorTick.bCanEverTick = false;
	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	Volume->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	Volume->SetGenerateOverlapEvents(true);
	RootComponent = Volume;

	Drawn = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Drawn"));
	Drawn->SetupAttachment(Volume);
	Drawn->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Drawn->SetGenerateOverlapEvents(false);
	Drawn->SetCastShadow(false);
	Drawn->SetUsingAbsoluteRotation(true);
	Drawn->SetUsingAbsoluteScale(true);
	Drawn->SetVisibility(false);
}

namespace
{
	const TCHAR* const WindPlanePath = TEXT("/Engine/BasicShapes/Plane.Plane");
	const TCHAR* const WindSpillMaterialPath = TEXT("/Game/UmbrellaElla/Art/VFX/M_VFX_Spill_PH.M_VFX_Spill_PH");

	/** The painted slot (T_VFX_Gust, no _PH) when artfx has shipped it; null while only the placeholder exists. */
	UTexture2D* LoadGustSlot()
	{
		return LoadObject<UTexture2D>(nullptr, TEXT("/Game/UmbrellaElla/Art/VFX/T_VFX_Gust.T_VFX_Gust"), nullptr, LOAD_NoWarn | LOAD_Quiet);
	}
}

void AWindCurrent::PostInitializeComponents()
{
	Super::PostInitializeComponents();
	RefreshDrawn();
}

EWindKind AWindCurrent::KindFor(const FVector& InDirection, bool bInHasLocalField)
{
	if (bInHasLocalField || DirectionLabel(InDirection) == FName(TEXT("Up")))
	{
		return EWindKind::Rescue;
	}
	return DirectionLabel(InDirection) == FName(TEXT("Down")) ? EWindKind::Descent : EWindKind::Transport;
}

FLinearColor AWindCurrent::KindTint(EWindKind Kind)
{
	const FFieldTuning& T = GetDefault<UUmbrellaTuning>()->Field;
	switch (Kind)
	{
	case EWindKind::Descent: return T.WindDescentTint;
	case EWindKind::Rescue: return T.WindRescueTint;
	default: return T.WindTransportTint;
	}
}

float AWindCurrent::KindOpacity(EWindKind Kind)
{
	const FFieldTuning& T = GetDefault<UUmbrellaTuning>()->Field;
	switch (Kind)
	{
	case EWindKind::Descent: return T.WindDescentOpacity;
	case EWindKind::Rescue: return T.WindRescueOpacity;
	default: return T.WindTransportOpacity;
	}
}

FVector2D AWindCurrent::GetUsableSize() const
{
	const FVector Extent = Volume->GetScaledBoxExtent();
	return FVector2D(Extent.X * 2.0, Extent.Z * 2.0);
}

FVector2D AWindCurrent::GetDrawnSize() const
{
	if (!bDrawn || !IsValid(Drawn) || !Drawn->GetStaticMesh())
	{
		return FVector2D::ZeroVector;
	}
	// The plane lies in XY rotated to face the camera, so its local Y scale is the world Z height.
	const FVector Scale = Drawn->GetComponentScale();
	return FVector2D(Scale.X * AWindCurrent::PlaneEdge, Scale.Y * AWindCurrent::PlaneEdge);
}

void AWindCurrent::RefreshDrawn()
{
	bDrawn = false;
	if (!IsValid(Drawn) || !IsFeatureEnabled(EFeatureId::FLOW_25))
	{
		return;
	}
	UStaticMesh* Plane = Drawn->GetStaticMesh();
	if (!Plane)
	{
		Plane = LoadObject<UStaticMesh>(nullptr, WindPlanePath, nullptr, LOAD_NoWarn | LOAD_Quiet);
		if (!Plane)
		{
			return;
		}
		Drawn->SetStaticMesh(Plane);
	}
	const FVector2D Size = GetUsableSize();
	if (Size.X <= 0.0 || Size.Y <= 0.0)
	{
		return;
	}
	const EWindKind Kind = GetKind();
	if (UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, WindSpillMaterialPath, nullptr, LOAD_NoWarn | LOAD_Quiet))
	{
		UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Drawn->GetMaterial(0));
		if (!Dynamic)
		{
			Dynamic = UMaterialInstanceDynamic::Create(Material, this);
			Drawn->SetMaterial(0, Dynamic);
		}
		Dynamic->SetVectorParameterValue(TEXT("Tint"), KindTint(Kind));
		Dynamic->SetScalarParameterValue(TEXT("Opacity"), KindOpacity(Kind));
		if (UTexture2D* Painted = LoadGustSlot())
		{
			Dynamic->SetTextureParameterValue(TEXT("Sheet"), Painted);
			Dynamic->SetScalarParameterValue(TEXT("Cols"), 1.0f);
		}
	}
	// Plane X stays world X; its normal turns to +Y (toward the camera). Covers the full usable box, not a centreline.
	Drawn->SetWorldRotation(FRotationMatrix::MakeFromXZ(FVector::XAxisVector, FVector::YAxisVector).Rotator());
	Drawn->SetWorldScale3D(FVector(Size.X / AWindCurrent::PlaneEdge, Size.Y / AWindCurrent::PlaneEdge, 1.0));
	const FVector At = GetActorLocation();
	Drawn->SetWorldLocation(FVector(At.X, UmbrellaDrawOrder::VfxY - 1.0f, At.Z));
	Drawn->SetVisibility(true);
	bDrawn = true;
}

FName AWindCurrent::DirectionLabel(const FVector& InDirection)
{
	if (FMath::Abs(InDirection.X) >= FMath::Abs(InDirection.Z))
	{
		return InDirection.X < 0.0 ? FName(TEXT("Left")) : FName(TEXT("Right"));
	}
	return InDirection.Z < 0.0 ? FName(TEXT("Down")) : FName(TEXT("Up"));
}

float AWindCurrent::GetForce() const
{
	const float Used = Force < 0.0f ? GetDefault<UUmbrellaTuning>()->Field.DefaultWindForce : Force;
	return FMath::Max(0.0f, Used);
}

void AWindCurrent::SetHalfExtent(float HalfX, float HalfZ)
{
	Volume->SetBoxExtent(FVector(HalfX, Volume->GetUnscaledBoxExtent().Y, HalfZ));
	RefreshDrawn();
}

void AWindCurrent::SetCurrent(const FVector& NewDirection, float NewForce)
{
	Direction = NewDirection.GetSafeNormal();
	Force = NewForce;
	RefreshDrawn();
}

void AWindCurrent::SetLocalVerticalField(float Gain, float CentreZ, float Compensation)
{
	bHasLocalField = true;
	LocalGain = Gain;
	LocalCentreZ = CentreZ;
	LocalCompensation = Compensation;
	RefreshDrawn();
}

void AWindCurrent::BroadcastEntered(const AActor* Other) const
{
	if (!IsFeatureEnabled(EFeatureId::WIND_03) || !IsValid(Other))
	{
		return;
	}
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::WindEntered;
		Event.SourceId = GetFName();
		Event.TargetId = Other->GetFName();
		Event.Detail = bHasLocalField
			? FName(*FString::Printf(TEXT("%s@%g,%g,%g"), *DirectionLabel(Direction).ToString(), LocalGain, LocalCentreZ, LocalCompensation))
			: DirectionLabel(Direction);
		Event.Value = GetForce();
		Bus->Broadcast(Event);
	}
}

void AWindCurrent::BroadcastExited(const AActor* Other) const
{
	if (!IsFeatureEnabled(EFeatureId::WIND_03) || !IsValid(Other))
	{
		return;
	}
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::WindExited;
		Event.SourceId = GetFName();
		Event.TargetId = Other->GetFName();
		Event.Detail = DirectionLabel(Direction);
		Event.Value = GetForce();
		Bus->Broadcast(Event);
	}
}

void AWindCurrent::NotifyActorBeginOverlap(AActor* OtherActor)
{
	Super::NotifyActorBeginOverlap(OtherActor);
	if (Cast<APawn>(OtherActor))
	{
		BroadcastEntered(OtherActor);
	}
}

void AWindCurrent::NotifyActorEndOverlap(AActor* OtherActor)
{
	Super::NotifyActorEndOverlap(OtherActor);
	if (Cast<APawn>(OtherActor))
	{
		BroadcastExited(OtherActor);
	}
}
