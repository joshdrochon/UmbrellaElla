#include "Feedback/Anim/WindPresenterSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Feedback/Art/ArtSlot.h"
#include "Field/WindCurrent.h"
#include "Harness/UmbrellaFeatureFlags.h"

namespace
{
	const FName WindRibbonTag(TEXT("WindRibbon"));

	FName WindRibbonName(int32 Strand, int32 Segment)
	{
		return FName(*FString::Printf(TEXT("WindRibbon_%d_%d"), Strand, Segment));
	}

	FLinearColor WindRibbonColour()
	{
		return FLinearColor::FromSRGBColor(FColor(UmbrellaWindPresenterConst::RibbonR, UmbrellaWindPresenterConst::RibbonG, UmbrellaWindPresenterConst::RibbonB));
	}

	/** Stable per-strand numbers so strands differ without randomness (tests and captures repeat). */
	float WindStrandPhase(int32 Strand)
	{
		return UmbrellaWindPresenterConst::StrandPhaseStep * static_cast<float>(Strand) + UmbrellaWindPresenterConst::StrandPhaseBase;
	}
}

int32 UWindPresenterSubsystem::StrandCount(float Width)
{
	return FMath::Clamp(FMath::RoundToInt32(FMath::Max(Width, 0.0f) / UmbrellaWindPresenterConst::StrandSpacing), UmbrellaWindPresenterConst::MinStrands, UmbrellaWindPresenterConst::MaxStrands);
}

int32 UWindPresenterSubsystem::SegmentCount(float Length)
{
	return FMath::Clamp(FMath::CeilToInt32(FMath::Max(Length, 0.0f) / UmbrellaWindPresenterConst::SegmentLength), UmbrellaWindPresenterConst::MinSegments, UmbrellaWindPresenterConst::MaxSegments);
}

FVector2D UWindPresenterSubsystem::StrandPoint(float Length, float Width, int32 Strand, int32 Strands, int32 Index, int32 Segments, float Seconds)
{
	const float T = Segments > 0 ? static_cast<float>(Index) / static_cast<float>(Segments) : 0.0f;
	const float Along = (T - 0.5f) * Length;
	const float Base = Strands > 0 ? ((static_cast<float>(Strand) + 0.5f) / static_cast<float>(Strands) - 0.5f) * Width * UmbrellaWindPresenterConst::BandShare : 0.0f;
	const float Amplitude = FMath::Min(Width * UmbrellaWindPresenterConst::AmplitudeShare, UmbrellaWindPresenterConst::MaxAmplitude);
	const float Wave = 2.0f * PI * Along / UmbrellaWindPresenterConst::Wavelength + WindStrandPhase(Strand) - UmbrellaWindPresenterConst::WaveSpeed * Seconds;
	// A second, slower bend keeps neighbouring strands from running parallel (the study's ribbons cross and part).
	const float Drift = UmbrellaWindPresenterConst::DriftShare * FMath::Sin(UmbrellaWindPresenterConst::DriftRate * Wave + UmbrellaWindPresenterConst::DriftStrandStep * static_cast<float>(Strand));
	return FVector2D(Along, Base + Amplitude * (FMath::Sin(Wave) + Drift) / (1.0f + UmbrellaWindPresenterConst::DriftShare));
}

float UWindPresenterSubsystem::StrandThickness(int32 Strand, float T)
{
	// Middle strands thickest; the ends taper to a hair, as the study's ribbons fade into the dark.
	const int32 Cycle = Strand % UmbrellaWindPresenterConst::StrandScaleCycle;
	const float Scale = Cycle == 1 ? UmbrellaWindPresenterConst::StrandThinScale : (Cycle == 2 ? UmbrellaWindPresenterConst::StrandMidScale : 1.0f);
	const float Taper = FMath::Sin(PI * FMath::Clamp(T, 0.0f, 1.0f));
	return FMath::Max(UmbrellaWindPresenterConst::ThinEnd, UmbrellaWindPresenterConst::ThickMiddle * Scale * Taper);
}

TArray<UStaticMeshComponent*> UWindPresenterSubsystem::RibbonsOf(const AWindCurrent* Wind)
{
	TArray<UStaticMeshComponent*> Out;
	if (IsValid(Wind))
	{
		TInlineComponentArray<UStaticMeshComponent*> Meshes(Wind);
		for (UStaticMeshComponent* Mesh : Meshes)
		{
			if (Mesh->ComponentHasTag(WindRibbonTag))
			{
				Out.Add(Mesh);
			}
		}
	}
	return Out;
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
		Winds.AddUnique(Wind);
	}
}

void UWindPresenterSubsystem::DrawRibbons(AWindCurrent* Wind, float Seconds)
{
	UStaticMeshComponent* Field = IsValid(Wind) ? Wind->GetField() : nullptr;
	if (!Field)
	{
		return;
	}
	const bool bShow = Field->IsVisible() && Field->GetStaticMesh() && IsFeatureEnabled(EFeatureId::FLOW_25);
	TArray<UStaticMeshComponent*> Ribbons = RibbonsOf(Wind);
	if (!bShow)
	{
		for (UStaticMeshComponent* Ribbon : Ribbons)
		{
			Ribbon->SetHiddenInGame(true);
		}
		return;
	}
	// The colour card keeps its size, colour and visibility (the field rules read them) but is never rendered: wind is
	// ribbons. Not SetHiddenInGame: in a game world IsVisible() then reads false and the card's drawn size goes to 0.
	if (Field->bRenderInMainPass || Field->bRenderInDepthPass)
	{
		Field->SetRenderInMainPass(false);
		Field->SetRenderInDepthPass(false);
	}

	const FVector BoxScale = Field->GetRelativeScale3D();
	const float SizeX = static_cast<float>(BoxScale.X) * UmbrellaWindPresenterConst::PlaneEdge;
	const float SizeZ = static_cast<float>(BoxScale.Z) * UmbrellaWindPresenterConst::PlaneEdge;
	FVector Flow = Wind->GetDirection();
	Flow.Y = 0.0;
	if (!Flow.Normalize())
	{
		Flow = FVector::XAxisVector;
	}
	// Ribbons run along the box's longer side when the flow is diagonal; along the flow axis otherwise.
	const bool bVertical = FMath::Abs(Flow.Z) > FMath::Abs(Flow.X);
	const FVector AlongAxis = bVertical ? FVector(0.0, 0.0, FMath::Sign(Flow.Z)) : FVector(FMath::Sign(Flow.X), 0.0, 0.0);
	const FVector AcrossAxis = bVertical ? FVector::XAxisVector : FVector::ZAxisVector;
	const float Length = bVertical ? SizeZ : SizeX;
	const float Width = bVertical ? SizeX : SizeZ;
	const int32 Strands = StrandCount(Width);
	const int32 Segments = SegmentCount(Length);
	const FVector Origin = Field->GetRelativeLocation() + FVector(0.0, UmbrellaWindPresenterConst::RibbonLift, 0.0);

	UStaticMesh* Plane = LoadObject<UStaticMesh>(nullptr, UmbrellaArtSlotConst::PlanePath, nullptr, LOAD_NoWarn | LOAD_Quiet);
	if (Ribbons.Num() != Strands * Segments)
	{
		for (UStaticMeshComponent* Old : Ribbons)
		{
			Old->DestroyComponent();
		}
		Ribbons.Reset();
		if (!Plane)
		{
			return;
		}
		for (int32 Strand = 0; Strand < Strands; ++Strand)
		{
			for (int32 Segment = 0; Segment < Segments; ++Segment)
			{
				UStaticMeshComponent* Ribbon = NewObject<UStaticMeshComponent>(Wind, WindRibbonName(Strand, Segment));
				Ribbon->ComponentTags.Add(WindRibbonTag);
				Ribbon->SetStaticMesh(Plane);
				Ribbon->SetCollisionEnabled(ECollisionEnabled::NoCollision);
				Ribbon->SetGenerateOverlapEvents(false);
				Ribbon->SetCastShadow(false);
				Ribbon->SetupAttachment(Field->GetAttachParent() ? Field->GetAttachParent() : Wind->GetRootComponent());
				ArtSlot::SetFlatUnlit(Ribbon, Wind, WindRibbonColour());
				Ribbon->RegisterComponent();
				Ribbons.Add(Ribbon);
			}
		}
	}
	for (int32 Strand = 0; Strand < Strands; ++Strand)
	{
		for (int32 Segment = 0; Segment < Segments; ++Segment)
		{
			UStaticMeshComponent* Ribbon = Ribbons[Strand * Segments + Segment];
			const FVector2D A = StrandPoint(Length, Width, Strand, Strands, Segment, Segments, Seconds);
			const FVector2D B = StrandPoint(Length, Width, Strand, Strands, Segment + 1, Segments, Seconds);
			const FVector P0 = Origin + AlongAxis * A.X + AcrossAxis * A.Y;
			const FVector P1 = Origin + AlongAxis * B.X + AcrossAxis * B.Y;
			FVector Dir = P1 - P0;
			const float SegLen = static_cast<float>(Dir.Size());
			if (!Dir.Normalize())
			{
				Dir = AlongAxis;
			}
			const float Thick = StrandThickness(Strand, (static_cast<float>(Segment) + 0.5f) / static_cast<float>(Segments));
			// Plane local X along the segment, its normal (local Z) toward the camera (+Y); a little overlap closes the joints.
			Ribbon->SetRelativeRotation(FRotationMatrix::MakeFromXZ(Dir, FVector::YAxisVector).Rotator());
			Ribbon->SetRelativeLocation((P0 + P1) * 0.5);
			Ribbon->SetRelativeScale3D(FVector((SegLen + Thick) / UmbrellaWindPresenterConst::PlaneEdge, Thick / UmbrellaWindPresenterConst::PlaneEdge, 1.0));
			Ribbon->SetHiddenInGame(false);
		}
	}
}

void UWindPresenterSubsystem::Tick(float DeltaTime)
{
	Winds.RemoveAll([](const TWeakObjectPtr<AWindCurrent>& Wind) { return !Wind.IsValid(); });
	const float Seconds = GetWorld() ? GetWorld()->GetTimeSeconds() : 0.0f;
	for (const TWeakObjectPtr<AWindCurrent>& Wind : Winds)
	{
		DrawRibbons(Wind.Get(), Seconds);
	}
}

TStatId UWindPresenterSubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UWindPresenterSubsystem, STATGROUP_Tickables);
}
