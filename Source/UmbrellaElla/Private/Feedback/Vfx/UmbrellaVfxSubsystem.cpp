#include "Feedback/Vfx/UmbrellaVfxSubsystem.h"
#include "Components/PointLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/StaticMesh.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "GameFramework/Actor.h"
#include "Harness/UmbrellaFeatureFlags.h"

namespace
{
	const EUmbrellaEventType VfxEvents[] = {
		EUmbrellaEventType::ProjectileSpawned,
		EUmbrellaEventType::ProjectileContact,
		EUmbrellaEventType::CatchSucceeded,
		EUmbrellaEventType::CatchFailed,
		EUmbrellaEventType::BossTargetHit,
		EUmbrellaEventType::BossAttackTelegraphed,
		EUmbrellaEventType::BossPartDestroyed,
	};
}

void UUmbrellaVfxSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Collection.InitializeDependency<UUmbrellaEventBus>();
	Super::Initialize(Collection);
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		for (const EUmbrellaEventType Type : VfxEvents)
		{
			Handles.Add(Bus->On(Type).AddUObject(this, &UUmbrellaVfxSubsystem::PlayForEvent));
		}
	}
}

void UUmbrellaVfxSubsystem::Deinitialize()
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		for (int32 Index = 0; Index < Handles.Num(); ++Index)
		{
			Bus->On(VfxEvents[Index]).Remove(Handles[Index]);
		}
	}
	Handles.Reset();
	Super::Deinitialize();
}

FName UUmbrellaVfxSubsystem::EffectForEvent(const FUmbrellaEvent& Event)
{
	switch (Event.Type)
	{
	case EUmbrellaEventType::ProjectileSpawned:
		return TEXT("ShotMuzzle");
	case EUmbrellaEventType::ProjectileContact:
		return TEXT("ShotImpact");
	case EUmbrellaEventType::CatchSucceeded:
		return TEXT("AbsorbBurst");
	case EUmbrellaEventType::CatchFailed:
		return TEXT("AbsorbFizzle");
	case EUmbrellaEventType::BossTargetHit:
		return Event.Detail == TEXT("Enemy") ? FName(TEXT("ShotImpact")) : FName(TEXT("KeeperHitFlash"));
	case EUmbrellaEventType::BossAttackTelegraphed:
		return TEXT("KeeperTelegraph");
	case EUmbrellaEventType::BossPartDestroyed:
		return TEXT("KeeperPartBreak");
	default:
		return NAME_None;
	}
}

FVfxEffectSpec UUmbrellaVfxSubsystem::SpecForEffect(FName Effect)
{
	// Layer: combat effects on the VFX layer above shots; the Keeper telegraph on the hazard layer behind Ella.
	if (Effect == TEXT("ShotMuzzle"))
	{
		return { Effect, UmbrellaDrawOrder::VfxY, UmbrellaVfxConst::StandInLifeSeconds, UmbrellaVfxConst::StandInScale, false, true };
	}
	if (Effect == TEXT("ShotImpact"))
	{
		return { Effect, UmbrellaDrawOrder::VfxY, UmbrellaVfxConst::StandInLifeSeconds, UmbrellaVfxConst::StandInScale, true, true };
	}
	if (Effect == TEXT("AbsorbBurst"))
	{
		return { Effect, UmbrellaDrawOrder::VfxY, UmbrellaVfxConst::StandInLifeSeconds, UmbrellaVfxConst::BurstScale, true, true };
	}
	if (Effect == TEXT("AbsorbFizzle"))
	{
		return { Effect, UmbrellaDrawOrder::VfxY, UmbrellaVfxConst::StandInLifeSeconds, UmbrellaVfxConst::StandInScale, false, false };
	}
	if (Effect == TEXT("KeeperHitFlash"))
	{
		return { Effect, UmbrellaDrawOrder::VfxY, UmbrellaVfxConst::StandInLifeSeconds, UmbrellaVfxConst::HitScale, true, true };
	}
	if (Effect == TEXT("KeeperTelegraph"))
	{
		return { Effect, UmbrellaDrawOrder::HazardY, UmbrellaVfxConst::LongLifeSeconds, UmbrellaVfxConst::TelegraphScale, false, true };
	}
	if (Effect == TEXT("KeeperPartBreak"))
	{
		return { Effect, UmbrellaDrawOrder::VfxY, UmbrellaVfxConst::LongLifeSeconds, UmbrellaVfxConst::BreakScale, true, true };
	}
	return FVfxEffectSpec();
}

TArray<FName> UUmbrellaVfxSubsystem::AllEffects()
{
	return { TEXT("ShotMuzzle"), TEXT("ShotImpact"), TEXT("AbsorbBurst"), TEXT("AbsorbFizzle"),
		TEXT("KeeperHitFlash"), TEXT("KeeperTelegraph"), TEXT("KeeperPartBreak") };
}

float UUmbrellaVfxSubsystem::LifeFor(const FVfxEffectSpec& Spec, const FUmbrellaEvent& Event)
{
	// A telegraph event carries its warning time in Value; the effect lasts that long so the warning stays readable.
	const float Wanted = (Event.Type == EUmbrellaEventType::BossAttackTelegraphed && Event.Value > 0.0f) ? Event.Value : Spec.LifeSeconds;
	return FMath::Clamp(Wanted, UmbrellaVfxConst::MinReadableSeconds, UmbrellaVfxConst::MaxLifeSeconds);
}

bool UUmbrellaVfxSubsystem::ShouldSuppress(int32 ActiveCount, bool bFlashing, float SecondsSinceLastFlash)
{
	return ActiveCount >= UmbrellaVfxConst::MaxActiveEffects
		|| (bFlashing && SecondsSinceLastFlash < UmbrellaVfxConst::MinFlashGapSeconds);
}

int32 UUmbrellaVfxSubsystem::GetActiveCount() const
{
	int32 Alive = 0;
	for (const TWeakObjectPtr<AActor>& Effect : Active)
	{
		Alive += Effect.IsValid() ? 1 : 0;
	}
	return Alive;
}

bool UUmbrellaVfxSubsystem::IsEffectEnabled(const FUmbrellaEvent& Event)
{
	if (!IsFeatureEnabled(EFeatureId::VFX_02))
	{
		return false;
	}
	switch (Event.Type)
	{
	case EUmbrellaEventType::ProjectileSpawned:
		return IsFeatureEnabled(EFeatureId::VFX_03);
	case EUmbrellaEventType::BossTargetHit:
	case EUmbrellaEventType::BossAttackTelegraphed:
	case EUmbrellaEventType::BossPartDestroyed:
		return IsFeatureEnabled(EFeatureId::VFX_05);
	default:
		return IsFeatureEnabled(EFeatureId::VFX_04);
	}
}

void UUmbrellaVfxSubsystem::PlayForEvent(const FUmbrellaEvent& Event)
{
	const FName Effect = EffectForEvent(Event);
	UWorld* World = GetWorld();
	if (Effect.IsNone() || !IsValid(World) || !IsEffectEnabled(Event))
	{
		return;
	}
	const FVfxEffectSpec Spec = SpecForEffect(Effect);
	const double Now = World->GetTimeSeconds();
	Active.RemoveAll([](const TWeakObjectPtr<AActor>& Entry) { return !Entry.IsValid(); });
	if (IsFeatureEnabled(EFeatureId::VFX_10) && ShouldSuppress(Active.Num(), Spec.bFlashing, static_cast<float>(Now - LastFlashTime)))
	{
		++SuppressedCount;
		return;
	}
	LastEffect = Effect;
	LastEventFrame = Event.Frame;
	++EffectCount;
	if (Spec.bFlashing)
	{
		LastFlashTime = Now;
	}

	// Place at the source actor when it exists; depth is the effect's own render layer (separate from sprites).
	FVector Location(0.0, IsFeatureEnabled(EFeatureId::VFX_06) ? Spec.LayerY : UmbrellaDrawOrder::VfxY, 0.0);
	for (TActorIterator<AActor> It(World); It; ++It)
	{
		if (It->GetFName() == Event.SourceId)
		{
			Location.X = It->GetActorLocation().X;
			Location.Z = It->GetActorLocation().Z;
			break;
		}
	}
	AActor* Flash = World->SpawnActor<AActor>(Location, FRotator::ZeroRotator);
	if (!IsValid(Flash))
	{
		return;
	}
	UStaticMeshComponent* Mesh = NewObject<UStaticMeshComponent>(Flash, TEXT("VfxStandIn"));
	if (UStaticMesh* Shape = LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Sphere.Sphere")))
	{
		Mesh->SetStaticMesh(Shape);
	}
	Mesh->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Mesh->SetGenerateOverlapEvents(false);
	const float Shrink = (bReducedFlash && Spec.bFlashing && IsFeatureEnabled(EFeatureId::VFX_10)) ? UmbrellaVfxConst::ReducedFlashScale : 1.0f;
	Mesh->SetRelativeScale3D(FVector(Spec.Scale * Shrink));
	Flash->SetRootComponent(Mesh);
	Mesh->RegisterComponent();
	Flash->SetActorLocation(Location);

	// Nearby surface illumination only for effects that declare a lit material (the stand-in's default material is lit).
	if (Spec.bLit && IsFeatureEnabled(EFeatureId::VFX_07) && IsFeatureEnabled(EFeatureId::VFX_08))
	{
		UPointLightComponent* Light = NewObject<UPointLightComponent>(Flash, TEXT("VfxLight"));
		Light->SetIntensity(UmbrellaVfxConst::LightIntensity * Shrink);
		Light->SetAttenuationRadius(UmbrellaVfxConst::LightRadius);
		Light->SetCastShadows(false);
		Light->SetupAttachment(Mesh);
		Light->RegisterComponent();
	}
	Flash->SetLifeSpan(IsFeatureEnabled(EFeatureId::VFX_09) ? LifeFor(Spec, Event) : Spec.LifeSeconds);
	Active.Add(Flash);
	LastActor = Flash;
}
