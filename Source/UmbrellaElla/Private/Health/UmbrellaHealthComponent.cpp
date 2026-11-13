#include "Health/UmbrellaHealthComponent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaSourceIds.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/World.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "Umbrella/UmbrellaPlayerIds.h"

namespace
{
	const FName DamageDetail(TEXT("Damage"));
	const FName HealDetail(TEXT("Heal"));
	const FName CaptureDetail(TEXT("FullCapture"));
	const FName ResetDetail(TEXT("Reset"));
	const FName ConfigDetail(TEXT("Config"));
}

UUmbrellaHealthComponent::UUmbrellaHealthComponent()
{
	PrimaryComponentTick.bCanEverTick = false;
	const FHealthTuning& Tuning = GetDefault<UUmbrellaTuning>()->Health;
	State = HealthRules::MakeFull(Tuning.HitsPerLife, Tuning.MaxLives);
}

void UUmbrellaHealthComponent::BindInput(UEnhancedInputComponent* Input)
{
}

void UUmbrellaHealthComponent::BeginPlay()
{
	Super::BeginPlay();
	const FHealthTuning& Tuning = GetDefault<UUmbrellaTuning>()->Health;
	State = HealthRules::MakeFull(State.Capacity > 0.0f ? State.Capacity : Tuning.HitsPerLife, State.MaxLives);
	ProtectedUntil = -1.0;
	BroadcastHealth(NAME_None, ConfigDetail);
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		RetryHandle = Bus->On(EUmbrellaEventType::CheckpointRetried).AddUObject(this, &UUmbrellaHealthComponent::OnCheckpointRetried);
	}
}

void UUmbrellaHealthComponent::EndPlay(const EEndPlayReason::Type Reason)
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		Bus->On(EUmbrellaEventType::CheckpointRetried).Remove(RetryHandle);
	}
	RetryHandle.Reset();
	Super::EndPlay(Reason);
}

void UUmbrellaHealthComponent::OnCheckpointRetried(const FUmbrellaEvent& Event)
{
	if (Event.TargetId == UmbrellaPlayerIds::Ella && Event.Amount == State.MaxLives)
	{
		ResetForRetry();
	}
}

bool UUmbrellaHealthComponent::ShouldBypassProtection(FName SourceId)
{
	return SourceId == UmbrellaSourceIds::GustBand();
}

EUmbrellaShotResult UUmbrellaHealthComponent::ReceiveShot(const FUmbrellaShotSpec& Shot, const FVector& HitLocation)
{
	if (!IsFeatureEnabled(EFeatureId::FLOW_33) || Shot.Kind == EUmbrellaShotKind::PlayerBlast)
	{
		return EUmbrellaShotResult::Ignored;
	}
	if (State.IsDefeated())
	{
		return EUmbrellaShotResult::Ignored;
	}
	const float Raw = Shot.Damage > 0.0f ? Shot.Damage : GetDefault<UUmbrellaTuning>()->Keeper.ProjectileDamage;
	TakeHit(Raw, Shot.SourceId);
	// A hit during protection still spends the shot: it must not wait outside and land the moment protection ends.
	return EUmbrellaShotResult::Consumed;
}

EHitResult UUmbrellaHealthComponent::TakeHit(float RawDamage, FName SourceId)
{
	const UWorld* World = GetWorld();
	return TakeHitAt(RawDamage, SourceId, World ? World->GetTimeSeconds() : 0.0);
}

EHitResult UUmbrellaHealthComponent::TakeHitAt(float RawDamage, FName SourceId, double NowSeconds)
{
	const bool bBypass = ShouldBypassProtection(SourceId);
	if (!IsFeatureEnabled(EFeatureId::SURV_05) || State.IsDefeated() || (!bBypass && NowSeconds < ProtectedUntil))
	{
		return EHitResult::Blocked;
	}
	const FHealthTuning& Tuning = GetDefault<UUmbrellaTuning>()->Health;
	const float Scaled = HealthRules::ScaleDamage(RawDamage, DefenseRank, Tuning);
	if (Scaled <= 0.0f)
	{
		return EHitResult::Blocked;
	}
	// The protection window starts on the hit and is not renewed by a life handover.
	if (!bBypass)
	{
		ProtectedUntil = NowSeconds + Tuning.PostHitProtectionSeconds;
	}
	const FHealthDamageOutcome Outcome = HealthRules::ApplyDamage(State, Scaled);
	BroadcastHealth(SourceId, DamageDetail);
	for (int32 Lost = 0; Lost < Outcome.LivesLost; ++Lost)
	{
		Broadcast(EUmbrellaEventType::LifeLost, SourceId, DamageDetail, State.Active, State.Lives);
	}
	if (Outcome.bDefeatedNow)
	{
		Broadcast(EUmbrellaEventType::PlayerDefeated, SourceId, DamageDetail, 0.0f, 0);
	}
	return EHitResult::Landed;
}

FHealthHealOutcome UUmbrellaHealthComponent::HealFromYellow(FName SourceId)
{
	if (!IsFeatureEnabled(EFeatureId::SURV_07))
	{
		FHealthHealOutcome Off;
		Off.bNothingChanged = true;
		return Off;
	}
	const FHealthTuning& Tuning = GetDefault<UUmbrellaTuning>()->Health;
	const FHealthHealOutcome Outcome = HealthRules::ApplyHeal(State, HealthRules::HealAmount(RecoveryRank, Tuning));
	BroadcastHealth(SourceId, Outcome.bNothingChanged ? CaptureDetail : HealDetail);
	return Outcome;
}

void UUmbrellaHealthComponent::ResetForRetry()
{
	State = HealthRules::MakeFull(State.Capacity, State.MaxLives);
	ProtectedUntil = -1.0;
	BroadcastHealth(NAME_None, ResetDetail);
}

void UUmbrellaHealthComponent::SetCapacity(float NewCapacity, int32 NewMaxLives)
{
	State.Capacity = FMath::Clamp(NewCapacity, 1.0f, static_cast<float>(HealthConstants::MaxTrackValue));
	State.MaxLives = FMath::Clamp(NewMaxLives, 1, HealthConstants::MaxTrackValue);
	State.Lives = FMath::Clamp(State.Lives, State.IsDefeated() ? 0 : 1, State.MaxLives);
	State.Active = FMath::Clamp(State.Active, 0.0f, State.Capacity);
	State.ReserveProgress = FMath::Clamp(State.ReserveProgress, 0.0f, State.Capacity);
	BroadcastHealth(NAME_None, ConfigDetail);
}

void UUmbrellaHealthComponent::SetDefenseRank(int32 Rank)
{
	DefenseRank = FMath::Clamp(Rank, 0, GetDefault<UUmbrellaTuning>()->Health.MaxDefenseRank);
}

void UUmbrellaHealthComponent::SetRecoveryRank(int32 Rank)
{
	RecoveryRank = FMath::Clamp(Rank, 0, GetDefault<UUmbrellaTuning>()->Health.MaxRecoveryRank);
}

float UUmbrellaHealthComponent::GetLiftMultiplier() const
{
	if (!IsFeatureEnabled(EFeatureId::SURV_05))
	{
		return 1.0f;
	}
	return HealthRules::LiftMultiplier(State, GetDefault<UUmbrellaTuning>()->Health.MinLift);
}

float UUmbrellaHealthComponent::GetProtectionRemaining(double NowSeconds) const
{
	return static_cast<float>(FMath::Max(ProtectedUntil - NowSeconds, 0.0));
}

void UUmbrellaHealthComponent::Broadcast(EUmbrellaEventType Type, FName Source, FName Detail, float Value, int32 Amount) const
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = Type;
		Event.SourceId = Source;
		Event.TargetId = GetOwner() ? GetOwner()->GetFName() : NAME_None;
		Event.Detail = Detail;
		Event.Value = Value;
		Event.Amount = Amount;
		Bus->Broadcast(Event);
	}
}

void UUmbrellaHealthComponent::BroadcastHealth(FName Source, FName Detail) const
{
	Broadcast(EUmbrellaEventType::PlayerHealthChanged, Source, Detail, State.Active, State.Lives);
}
