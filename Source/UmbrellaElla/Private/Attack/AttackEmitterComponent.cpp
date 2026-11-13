#include "Attack/AttackEmitterComponent.h"
#include "Attack/AttackCadence.h"
#include "Attack/AttackTuning.h"
#include "Attack/StreamBeamActor.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/World.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Motor/HeroSizeRules.h"
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

const FAttackTuning& UAttackEmitterComponent::ActiveTuning() const
{
	return TuningOverride ? *TuningOverride : GetDefault<UUmbrellaTuning>()->Attack;
}

const FMotorTuning& UAttackEmitterComponent::ActiveMotor() const
{
	return MotorOverride ? *MotorOverride : GetDefault<UUmbrellaTuning>()->Motor;
}

void UAttackEmitterComponent::StepEmitter(float DeltaSeconds)
{
	AActor* Owner = GetOwner();
	if (!Owner || bCom06OffForTest || !IsFeatureEnabled(EFeatureId::COM_06))
	{
		PendingBurstDelays.Reset();
		HideBeam();
		return;
	}
	const FAttackTuning& Tuning = ActiveTuning();

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

	// Burst shots already queued (COM-06): they leave only while the fall is still shooting.
	if (!bWantsFire)
	{
		PendingBurstDelays.Reset();
	}
	for (int32 Index = PendingBurstDelays.Num() - 1; Index >= 0; --Index)
	{
		PendingBurstDelays[Index] -= DeltaSeconds;
		if (PendingBurstDelays[Index] <= UE_KINDA_SMALL_NUMBER)
		{
			PendingBurstDelays.RemoveAtSwap(Index);
			FireVolley();
		}
	}

	const int32 Due = AttackCadence::Step(Countdown, DeltaSeconds, Profile.ShotsPerSecond, bWantsFire);
	const int32 Burst = SpellRules::BurstShots(Equipped, Tuning);
	for (int32 Index = 0; Index < Due; ++Index)
	{
		FireVolley();
		for (int32 Extra = 1; Extra < Burst; ++Extra)
		{
			PendingBurstDelays.Add(SpellRules::BurstDelay(Extra, Tuning));
		}
	}
	if (bWantsFire && Equipped == EUmbrellaSpell::StreamedBlast)
	{
		ShowBeam(Tuning);
	}
	else
	{
		HideBeam();
	}
}

void UAttackEmitterComponent::HideBeam()
{
	if (Beam)
	{
		Beam->Destroy();
		Beam = nullptr;
	}
}

void UAttackEmitterComponent::ShowBeam(const FAttackTuning& Tuning)
{
	if (!IsFeatureEnabled(EFeatureId::COM_07))
	{
		return;
	}
	if (!Beam && GetWorld())
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		Beam = GetWorld()->SpawnActor<AStreamBeamActor>(AStreamBeamActor::StaticClass(), FTransform(GetOwner()->GetActorLocation()), Params);
	}
	if (Beam)
	{
		FVector Muzzle = GetOwner()->GetActorLocation() + HeroSizeRules::MuzzleOffset(Tuning.MuzzleOffset, ActiveMotor());
		Beam->SetBeam(Muzzle, SpellRules::StreamLength(StreamHeldSeconds, Tuning), Tuning.StreamWidth);
	}
}

void UAttackEmitterComponent::FireVolley()
{
	const FAttackTuning& Tuning = ActiveTuning();
	FVector Muzzle = GetOwner()->GetActorLocation() + HeroSizeRules::MuzzleOffset(Tuning.MuzzleOffset, ActiveMotor());
	Muzzle.Y = UmbrellaDrawOrder::ProjectileY;
	for (const FUmbrellaShotSpec& Spec : SpellRules::BuildVolley(Equipped, Muzzle, Tuning, HeroSizeRules::ClampedHeroSize(ActiveMotor())))
	{
		LastShot = Spec;
		++ShotsFired;
		if (Equipped == EUmbrellaSpell::StreamedBlast)
		{
			// A damage tick on the beam, not a traveling shot. The beam is placed first so its length is current.
			ShowBeam(Tuning);
			if (Beam)
			{
				Beam->ApplyTick(Spec);
			}
			continue;
		}
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
	return SpellRules::IsAvailable(Spell, PlayMode, DirectorLevel, ActiveTuning());
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
	Equip(SpellRules::Cycle(Equipped, Direction, PlayMode, DirectorLevel, ActiveTuning()));
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
	PendingBurstDelays.Reset();
	HideBeam();
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

void UAttackEmitterComponent::EndPlay(const EEndPlayReason::Type Reason)
{
	HideBeam();
	Super::EndPlay(Reason);
}

float UAttackEmitterComponent::GetStreamLength() const
{
	return StreamHeldSeconds > 0.0f && UmbrellaState && UmbrellaActionRules::CanFire(UmbrellaState->GetAction()) ? SpellRules::StreamLength(StreamHeldSeconds, ActiveTuning()) : 0.0f;
}
