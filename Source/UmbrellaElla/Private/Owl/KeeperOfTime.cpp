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

void AKeeperOfTime::PlaceVisual(UStaticMeshComponent* Visual, const FVector2D& Centre, const FVector2D& HalfExtent, const FLinearColor& Colour, EKeeperCubeState State)
{
	if (!Visual)
	{
		return;
	}
	// Slot art is one static picture per part: it shows the default state only. A part in a state the art cannot show
	// (broken, clock open) keeps its coloured cube over the art as the cue.
	Visual->SetVisibility(State == EKeeperCubeState::StateCue || !IsCoveredByArt(Visual));
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
	PlaceVisual(WingsVisual, AnchorXZ + T.WingsOffset, T.WingsHalfExtent, bWingsAlive ? KeeperLook::Body : KeeperLook::Broken, bWingsAlive ? EKeeperCubeState::Default : EKeeperCubeState::StateCue);

	// Clock: always a collider (a closed clock consumes shots); bright while open.
	ClockPart->SetHittable(!Model.IsEnded());
	PlaceVisual(ClockVisual, AnchorXZ + T.ClockOffset, T.ClockHalfExtent, Model.IsClockOpen() ? KeeperLook::ClockOpen : KeeperLook::ClockClosed, Model.IsClockOpen() ? EKeeperCubeState::StateCue : EKeeperCubeState::Default);

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
		PlaceVisual(Slot.Visual, AnchorXZ + Slot.Offset, T.MechanismHalfExtent, bAlive ? KeeperLook::Body : KeeperLook::Broken, bAlive ? EKeeperCubeState::Default : EKeeperCubeState::StateCue);
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
	// Gust: drawn as ash-blue ribbons (the lane while it warns, then the travelling front); the old flat front cube and
	// the flat telegraph box are never shown for a gust (Josh 21:42: no flat filled box across the lane).
	const bool bGust = Model.IsGustTravelling();
	HideVisual(GustVisual);
	const bool bWarning = Model.GetStage() == EKeeperStage::Warning;
	const bool bGustWarning = bWarning && Model.GetPhysical() == EKeeperPhysical::Gust;
	const bool bWingsAliveNow = !Model.IsPartBroken(EKeeperPart::Wings);
	WingGustCell = WingGustCellFor(Model.GetPhysical(), Model.GetStage(), Model.GetStageRemaining(), bWingsAliveNow, T);
	TArray<FKeeperGustStroke> Strokes;
	if (bWingsAliveNow && (bGust || bGustWarning))
	{
		const float LaneLength = T.GustSpeed * T.GustLifetimeSeconds;
		const FVector2D LaneStart(GustLaneStart.X, Model.GetGustBandZ());
		const float Progress = bGustWarning ? FMath::Clamp(1.0f - Model.GetStageRemaining() / FMath::Max(T.GustWarningSeconds, UE_SMALL_NUMBER), 0.0f, 1.0f) : 1.0f;
		GustStrokes(LaneStart, LaneLength, T.GustBandWidth, bGust, Progress, Model.GetGustFront().X, T.GustFrontThickness, TimeSeconds, Strokes);
	}
	DrawGustRibbons(Strokes);
	bTelegraphShown = bWarning;
	if (bWarning && !bGustWarning)
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
		// The locked altitude band, centred on the locked height (the model's hit band is BandZ +- width/2).
		GustLaneStart = Command.A;
		TelegraphFrom = FVector2D(Command.A.X - T.GustSpeed * T.GustLifetimeSeconds, Command.A.Y - T.GustBandWidth * 0.5f);
		TelegraphTo = FVector2D(Command.A.X, Command.A.Y + T.GustBandWidth * 0.5f);
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
	DrawGustRibbons(TArray<FKeeperGustStroke>());
	WingGustCell = INDEX_NONE;
	bTelegraphShown = false;
}

int32 AKeeperOfTime::WingGustCellFor(EKeeperPhysical Physical, EKeeperStage Stage, float StageRemaining, bool bWingsAlive, const FKeeperTuning& T)
{
	using namespace KeeperWingGustConst;
	if (!bWingsAlive || Physical != EKeeperPhysical::Gust)
	{
		return INDEX_NONE;
	}
	const float Warning = FMath::Max(T.GustWarningSeconds, UE_SMALL_NUMBER);
	const float FlapInWarning = Warning * (1.0f - GatherShare);
	const float FlapTotal = FlapInWarning + FlapAfterLaunchSeconds;
	auto FlapCell = [&](float Seconds)
	{
		return GatherCells + FMath::Clamp(FMath::FloorToInt32(Seconds / FMath::Max(FlapTotal, UE_SMALL_NUMBER) * FlapCells), 0, FlapCells - 1);
	};
	if (Stage == EKeeperStage::Warning)
	{
		const float Elapsed = FMath::Clamp(Warning - StageRemaining, 0.0f, Warning);
		const float GatherSeconds = Warning * GatherShare;
		if (Elapsed < GatherSeconds)
		{
			return FMath::Clamp(FMath::FloorToInt32(Elapsed / FMath::Max(GatherSeconds, UE_SMALL_NUMBER) * GatherCells), 0, GatherCells - 1);
		}
		return FlapCell(Elapsed - GatherSeconds);
	}
	if (Stage == EKeeperStage::Stroke)
	{
		const float Travelled = FMath::Max(0.0f, T.GustLifetimeSeconds - StageRemaining);
		if (Travelled < FlapAfterLaunchSeconds)
		{
			return FlapCell(FlapInWarning + Travelled);
		}
		const float Recover = Travelled - FlapAfterLaunchSeconds;
		if (Recover < RecoverSeconds)
		{
			return GatherCells + FlapCells + FMath::Clamp(FMath::FloorToInt32(Recover / RecoverSeconds * RecoverCells), 0, RecoverCells - 1);
		}
	}
	return INDEX_NONE;
}

void AKeeperOfTime::GustStrokes(const FVector2D& LaneStart, float LaneLength, float BandWidth, bool bTravelling, float WarningProgress,
	float FrontX, float FrontThickness, float Seconds, TArray<FKeeperGustStroke>& Out)
{
	using namespace KeeperWingGustConst;
	Out.Reset();
	const float Z = LaneStart.Y;
	const float LaneEnd = LaneStart.X - LaneLength;
	// A wavy strand from XFrom (ahead, -X side) back to XTo, thickness from ThickA (at XFrom) to ThickB (at XTo).
	auto Strand = [&](float XFrom, float XTo, float ZOffset, float ThickA, float ThickB, float Phase)
	{
		const float Length = XTo - XFrom;
		if (Length <= 1.0f)
		{
			return;
		}
		const int32 Segments = FMath::Clamp(FMath::CeilToInt32(Length / SegmentLength), 2, MaxSegments);
		auto Point = [&](int32 Index)
		{
			const float X = XFrom + Length * static_cast<float>(Index) / static_cast<float>(Segments);
			// Bends travel toward -X, the gust's direction.
			const float Wave = 2.0f * PI * X / Wavelength + Phase + WaveSpeed * Seconds;
			return FVector2D(X, Z + ZOffset + WaveAmplitude * FMath::Sin(Wave));
		};
		for (int32 Index = 0; Index < Segments; ++Index)
		{
			const float Mid = (static_cast<float>(Index) + 0.5f) / static_cast<float>(Segments);
			Out.Add({Point(Index), Point(Index + 1), FMath::Lerp(ThickA, ThickB, Mid)});
		}
	};
	if (!bTravelling)
	{
		// The locked lane draws out toward the gust's direction (-X) while the wings gather: direction and band both read.
		const float P = FMath::Clamp(WarningProgress, 0.0f, 1.0f);
		const float Reach = LaneLength * (1.0f - FMath::Square(1.0f - P));
		const float TipX = LaneStart.X - Reach;
		if (Reach <= 1.0f)
		{
			return;
		}
		const float Edge = BandWidth * EdgeShare;
		const float Inner = BandWidth * InnerShare;
		Strand(TipX, LaneStart.X, -Edge, EdgeThick, EdgeThick, 0.0f);
		Strand(TipX, LaneStart.X, Edge, EdgeThick, EdgeThick, 2.1f);
		Strand(TipX, LaneStart.X, -Inner, InnerThick, InnerThick * 0.4f, 1.3f);
		Strand(TipX, LaneStart.X, Inner, InnerThick, InnerThick * 0.4f, 3.4f);
		// Arrow head at the reach, pointing -X.
		const float Back = BandWidth * ArrowBackShare;
		Out.Add({FVector2D(TipX, Z), FVector2D(TipX + Back, Z + Edge), ArrowThick});
		Out.Add({FVector2D(TipX, Z), FVector2D(TipX + Back, Z - Edge), ArrowThick});
		return;
	}
	// Travelling: a bowed front whose apex leads at the front's leading edge (the hit region is FrontX +- thickness/2).
	const float Half = BandWidth * 0.5f;
	const float Lead = FrontThickness * 0.5f;
	const float Bulge = FrontThickness * FrontBulgeShare;
	auto FrontPoint = [&](int32 Index)
	{
		const float S = 2.0f * static_cast<float>(Index) / static_cast<float>(FrontSegments) - 1.0f;
		return FVector2D(FrontX - Lead + Bulge * FMath::Square(S), Z + S * Half);
	};
	for (int32 Index = 0; Index < FrontSegments; ++Index)
	{
		Out.Add({FrontPoint(Index), FrontPoint(Index + 1), FrontThick});
	}
	const float TrailEnd = FMath::Min(FrontX + TrailLength, FMath::Max(FrontX, LaneStart.X));
	for (int32 Index = 0; Index < TrailStrands; ++Index)
	{
		const float Share = (static_cast<float>(Index) + 0.5f) / static_cast<float>(TrailStrands) - 0.5f;
		Strand(FrontX - Lead + Bulge * FMath::Square(2.0f * Share), TrailEnd, Share * BandWidth * 0.9f, TrailThickFront, TrailThickTail, 1.7f * static_cast<float>(Index));
	}
	// The lane still ahead: thin edge lines from the front to the lane's end.
	const float AheadFrom = FMath::Max(LaneEnd, FrontX - LaneLength);
	if (FrontX - Lead - AheadFrom > 1.0f)
	{
		Strand(AheadFrom, FrontX - Lead, -BandWidth * EdgeShare, EdgeThick, EdgeThick, 0.0f);
		Strand(AheadFrom, FrontX - Lead, BandWidth * EdgeShare, EdgeThick, EdgeThick, 2.1f);
	}
}

void AKeeperOfTime::DrawGustRibbons(const TArray<FKeeperGustStroke>& Strokes)
{
	using namespace KeeperWingGustConst;
	if (GustRibbons.Num() == 0 && Strokes.Num() > 0 && GetRootComponent())
	{
		UStaticMesh* Plane = LoadObject<UStaticMesh>(nullptr, UmbrellaArtSlotConst::PlanePath, nullptr, LOAD_NoWarn | LOAD_Quiet);
		const FLinearColor Colour = FLinearColor::FromSRGBColor(FColor(RibbonR, RibbonG, RibbonB));
		for (int32 Index = 0; Plane && Index < PoolSize; ++Index)
		{
			UStaticMeshComponent* Ribbon = NewObject<UStaticMeshComponent>(this, FName(*FString::Printf(TEXT("GustRibbon_%d"), Index)));
			Ribbon->SetStaticMesh(Plane);
			Ribbon->SetCollisionEnabled(ECollisionEnabled::NoCollision);
			Ribbon->SetGenerateOverlapEvents(false);
			Ribbon->SetCastShadow(false);
			Ribbon->SetupAttachment(GetRootComponent());
			ArtSlot::SetFlatUnlit(Ribbon, this, Colour);
			Ribbon->RegisterComponent();
			Ribbon->SetVisibility(false);
			GustRibbons.Add(Ribbon);
		}
	}
	const int32 Drawn = FMath::Min(Strokes.Num(), GustRibbons.Num());
	for (int32 Index = 0; Index < GustRibbons.Num(); ++Index)
	{
		UStaticMeshComponent* Ribbon = GustRibbons[Index];
		if (!Ribbon)
		{
			continue;
		}
		if (Index >= Drawn)
		{
			Ribbon->SetVisibility(false);
			continue;
		}
		const FKeeperGustStroke& Stroke = Strokes[Index];
		const FVector P0(Stroke.A.X, UmbrellaDrawOrder::KeeperY + RibbonLift, Stroke.A.Y);
		const FVector P1(Stroke.B.X, UmbrellaDrawOrder::KeeperY + RibbonLift, Stroke.B.Y);
		FVector Dir = P1 - P0;
		const double SegLen = Dir.Size();
		if (!Dir.Normalize())
		{
			Dir = FVector::XAxisVector;
		}
		// Plane local X along the piece, its normal toward the camera (+Y); the overlap closes the joints.
		Ribbon->SetWorldRotation(FRotationMatrix::MakeFromXZ(Dir, FVector::YAxisVector).Rotator());
		Ribbon->SetWorldLocation((P0 + P1) * 0.5);
		Ribbon->SetWorldScale3D(FVector((SegLen + Stroke.Thick) / UmbrellaArtSlotConst::PlaneEdge, Stroke.Thick / UmbrellaArtSlotConst::PlaneEdge, 1.0));
		Ribbon->SetVisibility(true);
	}
}

int32 AKeeperOfTime::GetVisibleGustRibbonCount() const
{
	int32 Count = 0;
	for (const TObjectPtr<UStaticMeshComponent>& Ribbon : GustRibbons)
	{
		Count += (Ribbon && Ribbon->IsVisible()) ? 1 : 0;
	}
	return Count;
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
