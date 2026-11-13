#include "Owl/KeeperOfTime.h"
#include "Feedback/Art/ArtSlot.h"

#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/StaticMesh.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Owl/KeeperLook.h"
#include "Owl/KeeperPartComponent.h"

namespace
{
	const TCHAR* CubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
	const TCHAR* BasicMaterialPath = TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
	const FName ColourParameter(TEXT("Color"));
	/** The flat unlit stand-in material (ArtSlot::SetFlatUnlit) reads its colour from Tint, not Color. */
	const FName TintParameter(TEXT("Tint"));
}

AKeeperOfTime::AKeeperOfTime()
{
	PrimaryActorTick.bCanEverTick = true;
	USceneComponent* Root = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));
	SetRootComponent(Root);

	const FKeeperTuning& T = GetDefault<UUmbrellaTuning>()->Keeper;
	WingsPart = MakePart(TEXT("WingsPart"), EKeeperPart::Wings, T.WingsOffset, T.WingsHalfExtent);
	ClockPart = MakePart(TEXT("ClockPart"), EKeeperPart::Clock, T.ClockOffset, T.ClockHalfExtent);
	EyePart = MakePart(TEXT("EyePart"), EKeeperPart::Eye, T.EyeOffset, T.EyeHalfExtent);
	FrontPart = MakePart(TEXT("FrontPart"), EKeeperPart::Front, T.FrontOffset, T.MechanismHalfExtent);
	MiddlePart = MakePart(TEXT("MiddlePart"), EKeeperPart::Middle, T.MiddleOffsetPos, T.MechanismHalfExtent);
	RearPart = MakePart(TEXT("RearPart"), EKeeperPart::Rear, T.RearOffset, T.MechanismHalfExtent);
	const FVector2D HeadHalf(T.ChainHeadWidth * 0.5f, T.ChainHeadWidth * 0.5f);
	FrontHead = MakePart(TEXT("FrontHead"), EKeeperPart::Front, T.FrontOffset, HeadHalf);
	MiddleHead = MakePart(TEXT("MiddleHead"), EKeeperPart::Middle, T.MiddleOffsetPos, HeadHalf);
	RearHead = MakePart(TEXT("RearHead"), EKeeperPart::Rear, T.RearOffset, HeadHalf);

	WingsVisual = MakeVisual(TEXT("WingsVisual"));
	ClockVisual = MakeVisual(TEXT("ClockVisual"));
	EyeVisual = MakeVisual(TEXT("EyeVisual"));
	FrontVisual = MakeVisual(TEXT("FrontVisual"));
	MiddleVisual = MakeVisual(TEXT("MiddleVisual"));
	RearVisual = MakeVisual(TEXT("RearVisual"));
	HeadVisual = MakeVisual(TEXT("HeadVisual"));
	TalonVisual = MakeVisual(TEXT("TalonVisual"));
	GustVisual = MakeVisual(TEXT("GustVisual"));
	TelegraphVisual = MakeVisual(TEXT("TelegraphVisual"));
}

UKeeperPartComponent* AKeeperOfTime::MakePart(FName Name, EKeeperPart Part, const FVector2D& Offset, const FVector2D& HalfExtent)
{
	UKeeperPartComponent* Component = CreateDefaultSubobject<UKeeperPartComponent>(Name);
	Component->SetupAttachment(GetRootComponent());
	Component->SetRelativeLocation(FVector(Offset.X, 0.0f, Offset.Y));
	Component->Configure(Part, HalfExtent);
	return Component;
}

UStaticMeshComponent* AKeeperOfTime::MakeVisual(FName Name)
{
	UStaticMeshComponent* Visual = CreateDefaultSubobject<UStaticMeshComponent>(Name);
	Visual->SetupAttachment(GetRootComponent());
	Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Visual->SetCastShadow(false);
	return Visual;
}

void AKeeperOfTime::BeginPlay()
{
	Super::BeginPlay();
	UStaticMesh* Cube = LoadObject<UStaticMesh>(nullptr, CubePath);
	UMaterialInterface* Material = LoadObject<UMaterialInterface>(nullptr, BasicMaterialPath);
	TArray<UStaticMeshComponent*> All = {WingsVisual, ClockVisual, EyeVisual, FrontVisual, MiddleVisual, RearVisual, HeadVisual, TalonVisual, GustVisual, TelegraphVisual};
	for (UStaticMeshComponent* Visual : All)
	{
		if (Visual && Cube)
		{
			Visual->SetStaticMesh(Cube);
			ArtSlot::SetFlatUnlit(Visual, this, UmbrellaArtSlotConst::StandInKeeperColor);
			if (!ArtSlot::IsUnlit(Visual) && Material)
			{
				Visual->SetMaterial(0, Material);
			}
			Visual->SetVisibility(false);
		}
	}
}

FVector AKeeperOfTime::ToWorld(const FVector2D& Position) const
{
	return FVector(Position.X, UmbrellaDrawOrder::KeeperY, Position.Y);
}

void AKeeperOfTime::HideVisual(UStaticMeshComponent* Visual)
{
	if (Visual)
	{
		Visual->SetVisibility(false);
	}
}

void AKeeperOfTime::PlaceVisual(UStaticMeshComponent* Visual, const FVector2D& Centre, const FVector2D& HalfExtent, const FLinearColor& Colour, bool bStateCue)
{
	if (!Visual)
	{
		return;
	}
	// Slot art is one static picture per part: it shows the default state only. A part in a state the art cannot show
	// (broken, clock open) keeps its coloured cube over the art as the cue.
	Visual->SetVisibility(bStateCue || !IsCoveredByArt(Visual));
	Visual->SetWorldLocation(ToWorld(Centre));
	Visual->SetWorldScale3D(FVector(HalfExtent.X * 2.0f / KeeperLook::CubeEdge, KeeperLook::VisualDepth / KeeperLook::CubeEdge, HalfExtent.Y * 2.0f / KeeperLook::CubeEdge));
	if (UMaterialInstanceDynamic* Dynamic = Visual->CreateDynamicMaterialInstance(0))
	{
		Dynamic->SetVectorParameterValue(ColourParameter, Colour);
		Dynamic->SetVectorParameterValue(TintParameter, Colour);
	}
}

UStaticMeshComponent* AKeeperOfTime::GetStandInVisual(EKeeperPart Part) const
{
	switch (Part)
	{
	case EKeeperPart::Wings: return WingsVisual;
	case EKeeperPart::Clock: return ClockVisual;
	case EKeeperPart::Eye: return EyeVisual;
	case EKeeperPart::Front: return FrontVisual;
	case EKeeperPart::Middle: return MiddleVisual;
	case EKeeperPart::Rear: return RearVisual;
	default: return nullptr;
	}
}

void AKeeperOfTime::MarkPartArtDrawn(EKeeperPart Part)
{
	if (Part == EKeeperPart::Count)
	{
		return;
	}
	ArtDrawnParts |= static_cast<uint8>(1u << static_cast<uint8>(Part));
	HideVisual(GetStandInVisual(Part));
}

void AKeeperOfTime::ClearPartArtDrawn(EKeeperPart Part)
{
	if (Part == EKeeperPart::Count)
	{
		return;
	}
	ArtDrawnParts &= static_cast<uint8>(~(1u << static_cast<uint8>(Part)));
}

bool AKeeperOfTime::IsPartArtDrawn(EKeeperPart Part) const
{
	return Part != EKeeperPart::Count && (ArtDrawnParts & (1u << static_cast<uint8>(Part))) != 0;
}

bool AKeeperOfTime::IsCoveredByArt(const UStaticMeshComponent* Visual) const
{
	for (uint8 Index = 0; Index < static_cast<uint8>(EKeeperPart::Count); ++Index)
	{
		const EKeeperPart Part = static_cast<EKeeperPart>(Index);
		if (Visual && GetStandInVisual(Part) == Visual && IsPartArtDrawn(Part))
		{
			return true;
		}
	}
	return false;
}

UKeeperPartComponent* AKeeperOfTime::GetPartComponent(EKeeperPart Part) const
{
	switch (Part)
	{
	case EKeeperPart::Wings: return WingsPart;
	case EKeeperPart::Clock: return ClockPart;
	case EKeeperPart::Eye: return EyePart;
	case EKeeperPart::Front: return FrontPart;
	case EKeeperPart::Middle: return MiddlePart;
	case EKeeperPart::Rear: return RearPart;
	default: return nullptr;
	}
}

UKeeperPartComponent* AKeeperOfTime::GetHeadComponent(EKeeperPart Part) const
{
	switch (Part)
	{
	case EKeeperPart::Front: return FrontHead;
	case EKeeperPart::Middle: return MiddleHead;
	case EKeeperPart::Rear: return RearHead;
	default: return nullptr;
	}
}

void AKeeperOfTime::Refresh(const FKeeperFightModel& Model, float TimeSeconds)
{
	const FKeeperTuning& T = GetDefault<UUmbrellaTuning>()->Keeper;
	AnchorXZ = FVector2D(GetActorLocation().X, GetActorLocation().Z);
	const FVector2D HeadHalf(T.ChainHeadWidth * 0.5f, T.ChainHeadWidth * 0.5f);

	// Wings: hittable until broken; broken wings stay as dark cover with no collision.
	const bool bWingsAlive = !Model.IsPartBroken(EKeeperPart::Wings);
	WingsPart->SetHittable(bWingsAlive);
	PlaceVisual(WingsVisual, AnchorXZ + T.WingsOffset, T.WingsHalfExtent, bWingsAlive ? KeeperLook::Body : KeeperLook::Broken, !bWingsAlive);

	// Clock: always a collider (a closed clock consumes shots); bright while open.
	ClockPart->SetHittable(!Model.IsEnded());
	PlaceVisual(ClockVisual, AnchorXZ + T.ClockOffset, T.ClockHalfExtent, Model.IsClockOpen() ? KeeperLook::ClockOpen : KeeperLook::ClockClosed, Model.IsClockOpen());

	EyePart->SetHittable(Model.IsEyeExposed());
	if (Model.IsEyeExposed())
	{
		PlaceVisual(EyeVisual, AnchorXZ + T.EyeOffset, T.EyeHalfExtent, KeeperLook::Eye);
	}
	else
	{
		HideVisual(EyeVisual);
	}

	// Mechanisms: body collider only when alive and at home; the moving head carries the collider while extended.
	struct FMechSlot
	{
		EKeeperPart Part;
		EKeeperPhysical Cast;
		UKeeperPartComponent* Body;
		UKeeperPartComponent* Head;
		UStaticMeshComponent* Visual;
		FVector2D Offset;
	};
	const FMechSlot Slots[] = {
		{EKeeperPart::Front, EKeeperPhysical::FrontCast, FrontPart, FrontHead, FrontVisual, T.FrontOffset},
		{EKeeperPart::Middle, EKeeperPhysical::MiddleCurve, MiddlePart, MiddleHead, MiddleVisual, T.MiddleOffsetPos},
		{EKeeperPart::Rear, EKeeperPhysical::RearTwoStage, RearPart, RearHead, RearVisual, T.RearOffset},
	};
	bool bHeadShown = false;
	for (const FMechSlot& Slot : Slots)
	{
		const bool bAlive = !Model.IsPartBroken(Slot.Part);
		const bool bExtended = bAlive && Model.GetPhysical() == Slot.Cast && Model.GetStage() != EKeeperStage::Warning
			&& Model.GetStage() != EKeeperStage::Idle && Model.GetStage() != EKeeperStage::Recovery;
		Slot.Body->SetHittable(bAlive && !bExtended);
		Slot.Head->SetHittable(bExtended);
		PlaceVisual(Slot.Visual, AnchorXZ + Slot.Offset, T.MechanismHalfExtent, bAlive ? KeeperLook::Body : KeeperLook::Broken, !bAlive);
		if (bExtended)
		{
			Slot.Head->SetWorldLocation(ToWorld(Model.GetHeadPosition()));
		}
		if (bAlive && Model.GetPhysical() == Slot.Cast && Model.GetStage() != EKeeperStage::Idle)
		{
			bHeadShown = true;
			PlaceVisual(HeadVisual, Model.GetHeadPosition(), HeadHalf, Model.IsHeadHurting() ? KeeperLook::Head : KeeperLook::SafeHead);
		}
	}
	if (!bHeadShown)
	{
		HideVisual(HeadVisual);
	}

	// Talon tip, gust front and the warning marker.
	const bool bTalon = Model.GetPhysical() == EKeeperPhysical::Talon && Model.GetStage() != EKeeperStage::Idle;
	if (bTalon)
	{
		PlaceVisual(TalonVisual, Model.GetHeadPosition(), FVector2D(T.TalonTipWidth * 0.5f, T.TalonTipWidth * 0.5f), KeeperLook::Talon);
	}
	else
	{
		HideVisual(TalonVisual);
	}
	const bool bGust = Model.IsGustTravelling();
	if (bGust)
	{
		PlaceVisual(GustVisual, Model.GetGustFront(), FVector2D(T.GustFrontThickness * 0.5f, T.GustBandWidth * 0.5f), KeeperLook::Gust);
	}
	else
	{
		HideVisual(GustVisual);
	}
	const bool bWarning = Model.GetStage() == EKeeperStage::Warning;
	bTelegraphShown = bWarning;
	if (bWarning)
	{
		const FVector2D Mid = (TelegraphFrom + TelegraphTo) * 0.5f;
		const FVector2D Half(FMath::Max(FMath::Abs(TelegraphTo.X - TelegraphFrom.X) * 0.5f, T.ChainHeadWidth * 0.5f),
			FMath::Max(FMath::Abs(TelegraphTo.Y - TelegraphFrom.Y) * 0.5f, T.ChainHeadWidth * 0.5f));
		PlaceVisual(TelegraphVisual, Mid, Half, KeeperLook::Telegraph);
	}
	else
	{
		HideVisual(TelegraphVisual);
	}
	(void)TimeSeconds;
}

void AKeeperOfTime::ShowTelegraph(const FKeeperCommand& Command)
{
	const FKeeperTuning& T = GetDefault<UUmbrellaTuning>()->Keeper;
	if (Command.Physical == EKeeperPhysical::Gust)
	{
		// The locked altitude band: a long thin marker across the arena at the locked height.
		TelegraphFrom = FVector2D(Command.A.X - T.GustSpeed * T.GustLifetimeSeconds, Command.A.Y);
		TelegraphTo = FVector2D(Command.A.X, Command.A.Y + T.GustBandWidth);
	}
	else
	{
		TelegraphFrom = Command.A;
		TelegraphTo = Command.B;
	}
	bTelegraphShown = true;
}

void AKeeperOfTime::ClearGusts()
{
	HideVisual(GustVisual);
	HideVisual(TelegraphVisual);
	bTelegraphShown = false;
}

void AKeeperOfTime::BeginDeparture(float Seconds)
{
	DepartureTotal = Seconds;
	DepartureRemaining = Seconds;
	for (EKeeperPart Part : {EKeeperPart::Wings, EKeeperPart::Clock, EKeeperPart::Eye, EKeeperPart::Front, EKeeperPart::Middle, EKeeperPart::Rear})
	{
		if (UKeeperPartComponent* Component = GetPartComponent(Part))
		{
			Component->SetHittable(false);
		}
	}
	for (EKeeperPart Part : {EKeeperPart::Front, EKeeperPart::Middle, EKeeperPart::Rear})
	{
		if (UKeeperPartComponent* Head = GetHeadComponent(Part))
		{
			Head->SetHittable(false);
		}
	}
}

void AKeeperOfTime::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);
	if (DepartureRemaining > 0.0f)
	{
		DepartureRemaining -= DeltaSeconds;
		const float Alpha = DepartureTotal > 0.0f ? FMath::Clamp(1.0f - DepartureRemaining / DepartureTotal, 0.0f, 1.0f) : 1.0f;
		AddActorWorldOffset(FVector(0.0f, 0.0f, KeeperLook::DepartureRise * DeltaSeconds / FMath::Max(DepartureTotal, UE_SMALL_NUMBER)));
		if (DepartureRemaining <= 0.0f)
		{
			SetActorHiddenInGame(true);
		}
		(void)Alpha;
	}
}
