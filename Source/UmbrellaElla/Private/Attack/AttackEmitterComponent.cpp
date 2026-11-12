#include "Attack/AttackEmitterComponent.h"
#include "Attack/AttackCadence.h"
#include "Attack/AttackTuning.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/World.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Umbrella/UmbrellaAction.h"
#include "Umbrella/UmbrellaPlayerIds.h"
#include "Umbrella/UmbrellaStateComponent.h"

UAttackEmitterComponent::UAttackEmitterComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostPhysics;
}

void UAttackEmitterComponent::BindInput(UEnhancedInputComponent* Input)
{
	// Fire is driven by the Umbrella State (Shoot held while dropping); nothing to bind here.
}

void UAttackEmitterComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);
	StepEmitter(DeltaTime);
}

void UAttackEmitterComponent::StepEmitter(float DeltaSeconds)
{
	AActor* Owner = GetOwner();
	if (!Owner || !IsFeatureEnabled(EFeatureId::COM_06))
	{
		return;
	}
	if (!UmbrellaState)
	{
		UmbrellaState = Owner->FindComponentByClass<UUmbrellaStateComponent>();
	}
	// Start Game exposes only Small Blasts; they fire only in the shooting fall.
	const bool bWantsFire = UmbrellaState && UmbrellaActionRules::CanFire(UmbrellaState->GetAction());
	const FAttackTuning& Tuning = GetDefault<UUmbrellaTuning>()->Attack;
	const int32 Due = AttackCadence::Step(Countdown, DeltaSeconds, Tuning.SmallShotsPerSecond, bWantsFire);
	for (int32 Index = 0; Index < Due; ++Index)
	{
		FireSmallBlast();
	}
}

void UAttackEmitterComponent::FireSmallBlast()
{
	const FAttackTuning& Tuning = GetDefault<UUmbrellaTuning>()->Attack;
	FUmbrellaShotSpec Spec;
	Spec.Kind = EUmbrellaShotKind::PlayerBlast;
	Spec.Origin = GetOwner()->GetActorLocation() + Tuning.MuzzleOffset;
	Spec.Origin.Y = UmbrellaDrawOrder::ProjectileY;
	// Always to +X: fire never follows travel direction or an aim.
	Spec.Velocity = FVector(Tuning.SmallSpeed, 0.0, 0.0);
	Spec.Radius = Tuning.BlastRadius;
	Spec.Damage = Tuning.SmallDamage;
	Spec.LifetimeSeconds = Tuning.SmallRange / Tuning.SmallSpeed;
	Spec.SourceId = UmbrellaPlayerIds::Ella;
	LastShot = Spec;
	++ShotsFired;
	AUmbrellaProjectile::Fire(GetWorld(), Spec);
}
