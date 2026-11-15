#include "Attack/StreamBeamActor.h"
#include "Feedback/Art/ArtSlot.h"
#include "Attack/SpellRules.h"
#include "Attack/SpellPresentation.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Attack/AttackTuning.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Engine/OverlapResult.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Projectile/UmbrellaShotReceiver.h"

namespace
{
	const TCHAR* BeamCubePath = TEXT("/Engine/BasicShapes/Cube.Cube");
	const TCHAR* BeamMaterialPath = TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial");
	const FName BeamColorParameter(TEXT("Color"));
	/** Each strand is drawn as two straight parts: canopy to body edge, then along the edge to the tip. */
	constexpr int32 BeamStrandSegments = 2;

	void BeamPaintPart(UStaticMeshComponent* Part, UObject* Outer, const FLinearColor& Color)
	{
		ArtSlot::SetFlatUnlit(Part, Outer, Color);
		if (!ArtSlot::IsUnlit(Part))
		{
			if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, BeamMaterialPath, nullptr, LOAD_NoWarn | LOAD_Quiet))
			{
				UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(Base, Outer);
				Material->SetVectorParameterValue(BeamColorParameter, Color);
				Part->SetMaterial(0, Material);
			}
		}
	}

	TArray<IUmbrellaShotReceiver*> BeamGatherReceivers(AActor* Target)
	{
		TArray<IUmbrellaShotReceiver*> Found;
		if (IUmbrellaShotReceiver* OnActor = Cast<IUmbrellaShotReceiver>(Target))
		{
			Found.Add(OnActor);
		}
		TInlineComponentArray<UActorComponent*> Components(Target);
		for (UActorComponent* Component : Components)
		{
			if (IUmbrellaShotReceiver* OnComponent = Cast<IUmbrellaShotReceiver>(Component))
			{
				Found.Add(OnComponent);
			}
		}
		Found.StableSort([](const IUmbrellaShotReceiver& A, const IUmbrellaShotReceiver& B)
		{
			return A.GetShotPriority() > B.GetShotPriority();
		});
		return Found;
	}
}

AStreamBeamActor::AStreamBeamActor()
{
	PrimaryActorTick.bCanEverTick = false;
	Visual = CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Visual"));
	Visual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Visual->SetGenerateOverlapEvents(false);
	SetRootComponent(Visual);
}

void AStreamBeamActor::SetBeam(const FVector& Muzzle, float Length, float Width)
{
	const FAttackTuning& Tuning = GetDefault<UUmbrellaTuning>()->Attack;
	const float HalfDepth = Tuning.StreamDepthHalfExtent;
	if (!IsFeatureEnabled(EFeatureId::COM_07))
	{
		Length = 0.0f;
	}
	BeamMuzzle = Muzzle;
	BeamMuzzle.Y = UmbrellaDrawOrder::ProjectileY;
	RequestedLength = FMath::Max(Length, 0.0f);
	BeamWidth = Width;

	EffectiveLength = ClipToBlockers(GetWorld(), this, BeamMuzzle, RequestedLength, BeamWidth, HalfDepth);

	SetActorLocation(BeamMuzzle + FVector(EffectiveLength * 0.5f, 0.0f, 0.0f));
	if (!Visual->GetStaticMesh())
	{
		BodyColor = Tuning.StreamBodyColor;
		StrandColor = Tuning.StreamStrandColor;
		if (UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, BeamCubePath, nullptr, LOAD_NoWarn | LOAD_Quiet))
		{
			Visual->SetStaticMesh(Mesh);
			BeamPaintPart(Visual, this, BodyColor);
		}
	}
	Visual->SetWorldScale3D(FVector(FMath::Max(EffectiveLength, MinVisualLength) / CubeSize, BeamWidth / CubeSize * VisualDepthFraction, BeamWidth / CubeSize));
	Visual->SetVisibility(EffectiveLength > 0.0f);
	PlaceStrands();
}

float AStreamBeamActor::ClipToBlockers(UWorld* World, const AActor* Ignore, const FVector& Muzzle, float Length, float Width, float HalfDepth)
{
	// A solid blocker (blocks the player shot channel, has no receiver) ends the beam early.
	TOptional<float> StopDistance;
	if (World && Length > 0.0f)
	{
		TArray<FOverlapResult> Overlaps;
		const FVector Center = Muzzle + FVector(Length * 0.5f, 0.0f, 0.0f);
		const FCollisionShape Box = FCollisionShape::MakeBox(FVector(Length * 0.5f, HalfDepth, Width * 0.5f));
		FCollisionQueryParams Params(SCENE_QUERY_STAT(UmbrellaBeam), false, Ignore);
		if (World->OverlapMultiByObjectType(Overlaps, Center, FQuat::Identity, FCollisionObjectQueryParams(FCollisionObjectQueryParams::AllObjects), Box, Params))
		{
			for (const FOverlapResult& Overlap : Overlaps)
			{
				AActor* Other = Overlap.GetActor();
				UPrimitiveComponent* Component = Overlap.GetComponent();
				if (!Other || !ProjectileRules::CanShotTouch(EUmbrellaShotKind::PlayerBlast, Other))
				{
					continue;
				}
				if (ProjectileRules::IsSolidStop(EUmbrellaShotKind::PlayerBlast, Component, BeamGatherReceivers(Other).Num() > 0))
				{
					const float Distance = FMath::Max(0.0f, static_cast<float>(Component->Bounds.GetBox().Min.X - Muzzle.X));
					StopDistance = StopDistance.IsSet() ? FMath::Min(StopDistance.GetValue(), Distance) : Distance;
				}
			}
		}
	}
	return SpellRules::BeamClippedLength(Length, StopDistance);
}

UStaticMeshComponent* AStreamBeamActor::MakePart(const FName& Name, const FLinearColor& Color)
{
	UStaticMeshComponent* Part = NewObject<UStaticMeshComponent>(this, Name);
	Part->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Part->SetGenerateOverlapEvents(false);
	Part->SetupAttachment(Visual);
	Part->SetAbsolute(true, true, true);
	if (UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, BeamCubePath, nullptr, LOAD_NoWarn | LOAD_Quiet))
	{
		Part->SetStaticMesh(Mesh);
	}
	Part->RegisterComponent();
	BeamPaintPart(Part, this, Color);
	return Part;
}

void AStreamBeamActor::PlaceStrands()
{
	const FAttackTuning& Tuning = GetDefault<UUmbrellaTuning>()->Attack;
	const TArray<FBeamStrand> Strands = SpellPresentationRules::BeamStrands(EffectiveLength, BeamWidth, Tuning);
	const int32 Needed = Strands.Num() * BeamStrandSegments;
	while (StrandParts.Num() < Needed)
	{
		StrandParts.Add(MakePart(*FString::Printf(TEXT("Strand%d"), StrandParts.Num()), StrandColor));
	}
	const float Depth = BeamWidth / CubeSize * VisualDepthFraction;
	// Strands sit just in front of the body (larger Y draws nearer) so the light reads around the dark core.
	const float FrontY = BeamMuzzle.Y + Tuning.StreamDepthHalfExtent * VisualDepthFraction;
	for (int32 Index = 0; Index < StrandParts.Num(); ++Index)
	{
		UStaticMeshComponent* Part = StrandParts[Index];
		const int32 StrandIndex = Index / BeamStrandSegments;
		if (!Strands.IsValidIndex(StrandIndex))
		{
			Part->SetVisibility(false);
			continue;
		}
		const FBeamStrand& Strand = Strands[StrandIndex];
		const bool bFirst = Index % BeamStrandSegments == 0;
		const FVector2D From = bFirst ? Strand.Start : Strand.Converge;
		const FVector2D To = bFirst ? Strand.Converge : Strand.End;
		const FVector A(BeamMuzzle.X + From.X, FrontY, BeamMuzzle.Z + From.Y);
		const FVector B(BeamMuzzle.X + To.X, FrontY, BeamMuzzle.Z + To.Y);
		const FVector Span = B - A;
		const float SpanLength = static_cast<float>(Span.Size());
		Part->SetWorldLocationAndRotation((A + B) * 0.5f, SpanLength > 0.0f ? FRotationMatrix::MakeFromX(Span).Rotator() : FRotator::ZeroRotator);
		Part->SetWorldScale3D(FVector(FMath::Max(SpanLength, MinVisualLength) / CubeSize, Depth, Tuning.StreamStrandThickness / CubeSize));
		Part->SetVisibility(SpanLength > 0.0f);
	}
}

int32 AStreamBeamActor::ApplyTick(const FUmbrellaShotSpec& Tick)
{
	return HitBox(GetWorld(), this, BeamMuzzle, EffectiveLength, BeamWidth, GetDefault<UUmbrellaTuning>()->Attack.StreamDepthHalfExtent, Tick);
}

int32 AStreamBeamActor::HitBox(UWorld* World, const AActor* Ignore, const FVector& Muzzle, float Length, float Width, float HalfDepth, const FUmbrellaShotSpec& Tick)
{
	if (!World || Length <= 0.0f)
	{
		return 0;
	}
	TArray<FOverlapResult> Overlaps;
	const FVector Center = Muzzle + FVector(Length * 0.5f, 0.0f, 0.0f);
	const FCollisionShape Box = FCollisionShape::MakeBox(FVector(Length * 0.5f, HalfDepth, Width * 0.5f));
	FCollisionQueryParams Params(SCENE_QUERY_STAT(UmbrellaBeamTick), false, Ignore);
	World->OverlapMultiByObjectType(Overlaps, Center, FQuat::Identity, FCollisionObjectQueryParams(FCollisionObjectQueryParams::AllObjects), Box, Params);

	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World);
	TSet<AActor*> Routed;
	for (const FOverlapResult& Overlap : Overlaps)
	{
		AActor* Target = Overlap.GetActor();
		if (!Target || Routed.Contains(Target) || !ProjectileRules::CanShotTouch(Tick.Kind, Target))
		{
			continue;
		}
		const TArray<IUmbrellaShotReceiver*> Receivers = BeamGatherReceivers(Target);
		if (Receivers.IsEmpty())
		{
			continue;
		}
		Routed.Add(Target);
		const FBox Bounds = Overlap.GetComponent() ? Overlap.GetComponent()->Bounds.GetBox() : Target->GetComponentsBoundingBox();
		FVector Location = Center;
		Location.X = FMath::Clamp(Bounds.Min.X, Muzzle.X, Muzzle.X + Length);
		bool bConsumed = false;
		for (IUmbrellaShotReceiver* Receiver : Receivers)
		{
			if (Receiver->ReceiveShot(Tick, Location) == EUmbrellaShotResult::Consumed)
			{
				bConsumed = true;
				break;
			}
		}
		if (Bus)
		{
			FUmbrellaEvent Event;
			Event.Type = EUmbrellaEventType::ProjectileContact;
			Event.SourceId = Tick.SourceId;
			Event.TargetId = Target->GetFName();
			Event.Detail = bConsumed ? FName(TEXT("Consumed")) : FName(TEXT("Passed"));
			Event.Value = Tick.Damage;
			Bus->Broadcast(Event);
		}
	}
	return Routed.Num();
}
