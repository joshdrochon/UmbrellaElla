#include "Feedback/Art/ArtSlot.h"
#include "Attack/StreamBeamActor.h"
#include "Attack/SpellRules.h"
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

	// A solid blocker (blocks the player shot channel, has no receiver) ends the beam early.
	TOptional<float> StopDistance;
	if (UWorld* World = GetWorld())
	{
		TArray<FOverlapResult> Overlaps;
		const FVector Center = BeamMuzzle + FVector(RequestedLength * 0.5f, 0.0f, 0.0f);
		const FCollisionShape Box = FCollisionShape::MakeBox(FVector(RequestedLength * 0.5f, HalfDepth, BeamWidth * 0.5f));
		FCollisionQueryParams Params(SCENE_QUERY_STAT(UmbrellaBeam), false, this);
		if (RequestedLength > 0.0f && World->OverlapMultiByObjectType(Overlaps, Center, FQuat::Identity, FCollisionObjectQueryParams(FCollisionObjectQueryParams::AllObjects), Box, Params))
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
					const float Distance = FMath::Max(0.0f, static_cast<float>(Component->Bounds.GetBox().Min.X - BeamMuzzle.X));
					StopDistance = StopDistance.IsSet() ? FMath::Min(StopDistance.GetValue(), Distance) : Distance;
				}
			}
		}
	}
	EffectiveLength = SpellRules::BeamClippedLength(RequestedLength, StopDistance);

	SetActorLocation(BeamMuzzle + FVector(EffectiveLength * 0.5f, 0.0f, 0.0f));
	if (!Visual->GetStaticMesh())
	{
		if (UStaticMesh* Mesh = LoadObject<UStaticMesh>(nullptr, BeamCubePath, nullptr, LOAD_NoWarn | LOAD_Quiet))
		{
			Visual->SetStaticMesh(Mesh);
			if (ArtSlot::ApplyFlatUnlit(Visual, this, Tuning.StreamPlaceholderColor))
			{
			}
			else if (UMaterialInterface* Base = LoadObject<UMaterialInterface>(nullptr, BeamMaterialPath, nullptr, LOAD_NoWarn | LOAD_Quiet))
			{
				UMaterialInstanceDynamic* Material = UMaterialInstanceDynamic::Create(Base, this);
				Material->SetVectorParameterValue(BeamColorParameter, Tuning.StreamPlaceholderColor);
				Visual->SetMaterial(0, Material);
			}
		}
	}
	Visual->SetWorldScale3D(FVector(FMath::Max(EffectiveLength, MinVisualLength) / CubeSize, BeamWidth / CubeSize * VisualDepthFraction, BeamWidth / CubeSize));
	Visual->SetVisibility(EffectiveLength > 0.0f);
}

int32 AStreamBeamActor::ApplyTick(const FUmbrellaShotSpec& Tick)
{
	UWorld* World = GetWorld();
	const float HalfDepth = GetDefault<UUmbrellaTuning>()->Attack.StreamDepthHalfExtent;
	if (!World || EffectiveLength <= 0.0f)
	{
		return 0;
	}
	TArray<FOverlapResult> Overlaps;
	const FVector Center = BeamMuzzle + FVector(EffectiveLength * 0.5f, 0.0f, 0.0f);
	const FCollisionShape Box = FCollisionShape::MakeBox(FVector(EffectiveLength * 0.5f, HalfDepth, BeamWidth * 0.5f));
	FCollisionQueryParams Params(SCENE_QUERY_STAT(UmbrellaBeamTick), false, this);
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
		Location.X = FMath::Clamp(Bounds.Min.X, BeamMuzzle.X, BeamMuzzle.X + EffectiveLength);
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
