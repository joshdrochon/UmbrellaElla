#include "Field/WindCurrent.h"
#include "Components/BoxComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/StaticMesh.h"
#include "Engine/Texture2D.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Materials/MaterialInterface.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/StaticMesh.h"
#include "GameFramework/Pawn.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Umbrella/UmbrellaPlayerIds.h"

namespace
{
	const TCHAR* WindFieldCubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
	const TCHAR* WindFieldMaterialPath = TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
	const FName WindFieldColourParameter(TEXT("Color"));
}

AWindCurrent::AWindCurrent()
{
	PrimaryActorTick.bCanEverTick = false;
	Volume = CreateDefaultSubobject<UBoxComponent>(TEXT("Volume"));
	Volume->SetCollisionProfileName(TEXT("OverlapAllDynamic"));
	Volume->SetGenerateOverlapEvents(true);
	RootComponent = Volume;
	Field = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Field"));
	Field->SetupAttachment(Volume);
	Field->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Field->SetGenerateOverlapEvents(false);
	Field->SetCastShadow(false);
	// Behind Ella in the draw order: the field reads as space she flies through.
	Field->SetRelativeLocation(FVector(0.0, UmbrellaDrawOrder::HazardY - UmbrellaDrawOrder::EllaY, 0.0));
}

EWindKind AWindCurrent::KindFor(const FVector& InDirection, bool bInHasLocalField)
{
	if (bInHasLocalField || DirectionLabel(InDirection) == FName(TEXT("Up")))
	{
		return EWindKind::Rescue;
	}
	return DirectionLabel(InDirection) == FName(TEXT("Down")) ? EWindKind::Descent : EWindKind::Transport;
}

FVector2D AWindCurrent::GetUsableSize() const
{
	const FVector Extent = Volume->GetScaledBoxExtent();
	return FVector2D(Extent.X * 2.0, Extent.Z * 2.0);
}

FVector2D AWindCurrent::GetDrawnSize() const
{
	if (!Field->IsVisible() || !Field->GetStaticMesh())
	{
		return FVector2D::ZeroVector;
	}
	return FVector2D(2.0 * Field->Bounds.BoxExtent.X, 2.0 * Field->Bounds.BoxExtent.Z);
}

void AWindCurrent::BeginPlay()
{
	Super::BeginPlay();
	RefreshField();
}

FName AWindCurrent::RoleLabel(const FVector& InDirection)
{
	const FName Label = DirectionLabel(InDirection);
	if (Label == TEXT("Left"))
	{
		return TEXT("Return");
	}
	if (Label == TEXT("Up"))
	{
		return TEXT("Lift");
	}
	if (Label == TEXT("Down"))
	{
		return TEXT("Descent");
	}
	return TEXT("Transport");
}

FLinearColor AWindCurrent::FieldColourFor(FName Role)
{
	const FFieldTuning& T = GetDefault<UUmbrellaTuning>()->Field;
	if (Role == TEXT("Return"))
	{
		return T.ReturnFieldColour;
	}
	if (Role == TEXT("Lift"))
	{
		return T.LiftFieldColour;
	}
	if (Role == TEXT("Descent"))
	{
		return T.DescentFieldColour;
	}
	return T.TransportFieldColour;
}

float AWindCurrent::GetUsableWidth() const
{
	return 2.0f * Volume->GetScaledBoxExtent().X;
}

float AWindCurrent::GetDrawnWidth() const
{
	return Field->IsVisible() && Field->GetStaticMesh() ? 2.0f * Field->Bounds.BoxExtent.X : 0.0f;
}

void AWindCurrent::RefreshField()
{
	if (!IsFeatureEnabled(EFeatureId::FLOW_25))
	{
		Field->SetVisibility(false);
		return;
	}
	if (!Field->GetStaticMesh())
	{
		if (UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, WindFieldCubePath, nullptr, LOAD_NoWarn | LOAD_Quiet))
		{
			Field->SetStaticMesh(Cube);
		}
	}
	if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, WindFieldMaterialPath, nullptr, LOAD_NoWarn | LOAD_Quiet))
	{
		UMaterialInstanceDynamic* Material = Cast<UMaterialInstanceDynamic>(Field->GetMaterial(0));
		if (!Material || Material->Parent != Base)
		{
			Material = UMaterialInstanceDynamic::Create(Base, this);
			Field->SetMaterial(0, Material);
		}
		Material->SetVectorParameterValue(WindFieldColourParameter, FieldColourFor(GetKind() == EWindKind::Rescue ? FName(TEXT("Lift")) : RoleLabel(Direction)));
	}
	const FVector Extent = Volume->GetUnscaledBoxExtent();
	Field->SetRelativeScale3D(FVector(2.0 * Extent.X / WindCurrentConst::CubeSize, GetDefault<UUmbrellaTuning>()->Field.FieldDepthScale, 2.0 * Extent.Z / WindCurrentConst::CubeSize));
	Field->SetVisibility(true);
	Field->UpdateBounds();
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
	RefreshField();
}

void AWindCurrent::SetCurrent(const FVector& NewDirection, float NewForce)
{
	Direction = NewDirection.GetSafeNormal();
	Force = NewForce;
	RefreshField();
}

FName AWindCurrent::TargetIdFor(const AActor* Other)
{
	if (!IsValid(Other))
	{
		return NAME_None;
	}
	// The Motor answers to the player id, not the pawn's actor name: Ella (or any player-controlled pawn) is "Ella".
	const APawn* Pawn = Cast<APawn>(Other);
	if (IsFeatureEnabled(EFeatureId::WIND_03) && (Other->IsA<AEllaCharacter>() || (Pawn && Pawn->IsPlayerControlled())))
	{
		return UmbrellaPlayerIds::Ella;
	}
	return Other->GetFName();
}

void AWindCurrent::SetLocalVerticalField(float Gain, float CentreZ, float Compensation)
{
	bHasLocalField = true;
	LocalGain = Gain;
	LocalCentreZ = CentreZ;
	LocalCompensation = Compensation;
	RefreshField();
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
		Event.TargetId = TargetIdFor(Other);
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
		Event.TargetId = TargetIdFor(Other);
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
