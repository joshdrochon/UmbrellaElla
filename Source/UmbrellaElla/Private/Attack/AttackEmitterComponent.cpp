#include "Attack/AttackEmitterComponent.h"
#include "Attack/AttackCadence.h"
#include "Attack/AttackTuning.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
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
	// Fire is driven by the Umbrella State (Shoot held while dropping); spell keys arrive through the Input Adapter.
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
	const FAttackTuning& Tuning = GetDefault<UUmbrellaTuning>()->Attack;

	// A spell key held past the wheel time opens the wheel (it pauses gameplay).
	if (HeldKey != EUmbrellaSpell::Count && !bWheelOpen)
	{
		KeyHeldSeconds += DeltaSeconds;
		if (KeyHeldSeconds >= Tuning.WheelHoldSeconds)
		{
			OpenWheel();
		}
	}

	if (!UmbrellaState)
	{
		UmbrellaState = Owner->FindComponentByClass<UUmbrellaStateComponent>();
	}
	// Every spell fires only in the shooting fall.
	const bool bWantsFire = UmbrellaState && UmbrellaActionRules::CanFire(UmbrellaState->GetAction());
	if (bWantsFire && Equipped == EUmbrellaSpell::StreamedBlast)
	{
		StreamHeldSeconds += DeltaSeconds;
	}
	else
	{
		StreamHeldSeconds = 0.0f;
	}
	const FSpellProfile Profile = SpellRules::GetProfile(Equipped, Tuning);
	const int32 Due = AttackCadence::Step(Countdown, DeltaSeconds, Profile.ShotsPerSecond, bWantsFire);
	for (int32 Index = 0; Index < Due; ++Index)
	{
		FireVolley();
	}
}

void UAttackEmitterComponent::FireVolley()
{
	const FAttackTuning& Tuning = GetDefault<UUmbrellaTuning>()->Attack;
	FVector Muzzle = GetOwner()->GetActorLocation() + Tuning.MuzzleOffset;
	Muzzle.Y = UmbrellaDrawOrder::ProjectileY;
	for (const FUmbrellaShotSpec& Spec : SpellRules::BuildVolley(Equipped, Muzzle, Tuning))
	{
		LastShot = Spec;
		++ShotsFired;
		AUmbrellaProjectile::Fire(GetWorld(), Spec);
	}
}

void UAttackEmitterComponent::SetPlayMode(EUmbrellaPlayMode Mode)
{
	PlayMode = Mode;
	if (!CanEquip(Equipped))
	{
		Equip(EUmbrellaSpell::SmallBlasts);
	}
}

void UAttackEmitterComponent::SetDirectorLevel(int32 Level)
{
	// Unlocking never equips: the equipped spell stays as it is.
	DirectorLevel = FMath::Max(Level, 0);
	if (!CanEquip(Equipped))
	{
		Equip(EUmbrellaSpell::SmallBlasts);
	}
}

bool UAttackEmitterComponent::CanEquip(EUmbrellaSpell Spell) const
{
	return SpellRules::IsAvailable(Spell, PlayMode, DirectorLevel, GetDefault<UUmbrellaTuning>()->Attack);
}

void UAttackEmitterComponent::SelectSpell(EUmbrellaSpell Spell)
{
	if (CanEquip(Spell))
	{
		Equip(Spell);
	}
}

void UAttackEmitterComponent::CycleSpell(int32 Direction)
{
	Equip(SpellRules::Cycle(Equipped, Direction, PlayMode, DirectorLevel, GetDefault<UUmbrellaTuning>()->Attack));
}

void UAttackEmitterComponent::Equip(EUmbrellaSpell Spell)
{
	if (Spell == Equipped)
	{
		return;
	}
	Equipped = Spell;
	Countdown = 0.0f;
	StreamHeldSeconds = 0.0f;
	EquippedChanged.Broadcast(Equipped);
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::UmbrellaConfigChanged;
		Event.SourceId = UmbrellaPlayerIds::Ella;
		Event.Detail = SpellRules::SpellName(Equipped);
		Event.Amount = static_cast<int32>(Equipped);
		Bus->Broadcast(Event);
	}
}

void UAttackEmitterComponent::PressSpellKey(EUmbrellaSpell Spell)
{
	if (bWheelOpen)
	{
		// In the wheel a direction only previews; release confirms.
		if (CanEquip(Spell))
		{
			WheelPreview = Spell;
		}
		return;
	}
	if (CanEquip(Spell))
	{
		Equip(Spell);
	}
	HeldKey = Spell;
	WheelPreview = Equipped;
	KeyHeldSeconds = 0.0f;
}

void UAttackEmitterComponent::ReleaseSpellKey(EUmbrellaSpell Spell)
{
	if (bWheelOpen)
	{
		Equip(WheelPreview);
		CloseWheel();
	}
	if (Spell == HeldKey || bWheelOpen)
	{
		HeldKey = EUmbrellaSpell::Count;
		KeyHeldSeconds = 0.0f;
	}
}

void UAttackEmitterComponent::OpenWheel()
{
	bWheelOpen = true;
	WheelPreview = Equipped;
	if (UmbrellaState && !UmbrellaState->IsLocked())
	{
		UmbrellaState->SetLocked(true);
		bWheelLockedState = true;
	}
}

void UAttackEmitterComponent::CloseWheel()
{
	bWheelOpen = false;
	if (UmbrellaState && bWheelLockedState)
	{
		UmbrellaState->SetLocked(false);
	}
	bWheelLockedState = false;
}

float UAttackEmitterComponent::GetStreamLength() const
{
	return StreamHeldSeconds > 0.0f && UmbrellaState && UmbrellaActionRules::CanFire(UmbrellaState->GetAction()) ? SpellRules::StreamLength(StreamHeldSeconds, GetDefault<UUmbrellaTuning>()->Attack) : 0.0f;
}
