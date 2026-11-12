#include "Defense/AbsorbReceiverComponent.h"
#include "Core/UmbrellaEventBus.h"
#include "GameFramework/Actor.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Health/HealthModel.h"
#include "Health/UmbrellaHealthComponent.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "Umbrella/UmbrellaPlayerIds.h"

namespace
{
	const FName AbsorbFallDetail(TEXT("AbsorbFall"));
	const FName YellowDetail(TEXT("Yellow"));
	const FName RedDetail(TEXT("RedNotCatchable"));
}

UAbsorbReceiverComponent::UAbsorbReceiverComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
}

void UAbsorbReceiverComponent::BindInput(UEnhancedInputComponent* Input)
{
}

void UAbsorbReceiverComponent::BeginPlay()
{
	Super::BeginPlay();
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		ConfigHandle = Bus->On(EUmbrellaEventType::UmbrellaConfigChanged).AddUObject(this, &UAbsorbReceiverComponent::OnConfigChanged);
	}
}

void UAbsorbReceiverComponent::EndPlay(const EEndPlayReason::Type Reason)
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		Bus->On(EUmbrellaEventType::UmbrellaConfigChanged).Remove(ConfigHandle);
	}
	ConfigHandle.Reset();
	Super::EndPlay(Reason);
}

void UAbsorbReceiverComponent::OnConfigChanged(const FUmbrellaEvent& Event)
{
	// The umbrella state lane broadcasts every action change (Detail = new action name); absorb is open only in AbsorbFall.
	if (Event.SourceId == UmbrellaPlayerIds::Ella)
	{
		SetPose(Event.Detail == AbsorbFallDetail ? EAbsorbPose::AbsorbFall : EAbsorbPose::Closed);
	}
}

void UAbsorbReceiverComponent::SetPose(EAbsorbPose NewPose)
{
	Pose = NewPose;
}

int32 UAbsorbReceiverComponent::GetShotPriority() const
{
	return HealthConstants::AbsorbShotPriority;
}

EUmbrellaShotResult UAbsorbReceiverComponent::ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation)
{
	if (!IsFeatureEnabled(EFeatureId::SURV_07) || Pose != EAbsorbPose::AbsorbFall || Shot.Kind == EUmbrellaShotKind::PlayerBlast)
	{
		return EUmbrellaShotResult::Ignored;
	}
	Broadcast(EUmbrellaEventType::CatchAttempt, Shot.SourceId, AbsorbFallDetail, Shot.Damage);
	if (Shot.Kind == EUmbrellaShotKind::EnemyRed)
	{
		Broadcast(EUmbrellaEventType::CatchFailed, Shot.SourceId, RedDetail, Shot.Damage);
		return EUmbrellaShotResult::Ignored;
	}
	UUmbrellaHealthComponent* Health = GetOwner() ? GetOwner()->FindComponentByClass<UUmbrellaHealthComponent>() : nullptr;
	if (!Health)
	{
		Broadcast(EUmbrellaEventType::CatchFailed, Shot.SourceId, YellowDetail, Shot.Damage);
		return EUmbrellaShotResult::Ignored;
	}
	const FHealthHealOutcome Healed = Health->HealFromYellow(Shot.SourceId);
	Broadcast(EUmbrellaEventType::CatchSucceeded, Shot.SourceId, YellowDetail, Healed.ActiveGained);
	return EUmbrellaShotResult::Consumed;
}

void UAbsorbReceiverComponent::Broadcast(EUmbrellaEventType Type, FName Source, FName Detail, float Value) const
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = Type;
		Event.SourceId = Source;
		Event.TargetId = GetOwner() ? GetOwner()->GetFName() : NAME_None;
		Event.Detail = Detail;
		Event.Value = Value;
		Bus->Broadcast(Event);
	}
}
