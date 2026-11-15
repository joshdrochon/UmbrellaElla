#include "Attack/AttackEmitterComponent.h"
#include "Attack/AimedBeamActor.h"
#include "Attack/AttackCadence.h"
#include "Attack/AttackTuning.h"
#include "Attack/StreamBeamActor.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/World.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Motor/HeroSizeRules.h"
#include "Motor/MotorTuning.h"
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

FVector UAttackEmitterComponent::SizedMuzzle(const FAttackTuning& Tuning) const
{
	const bool bHeroSize = IsFeatureEnabled(EFeatureId::HAZ_10) && IsFeatureEnabled(EFeatureId::HAZ_13) && IsFeatureEnabled(EFeatureId::HAZ_14);
	return bHeroSize ? HeroSizeRules::MuzzleOffset(Tuning.MuzzleOffset, ActiveMotor()) : Tuning.MuzzleOffset;
}

void UAttackEmitterComponent::StepEmitter(float DeltaSeconds)
{
	AActor* Owner = GetOwner();
	if (!Owner || bCom06OffForTest || !IsFeatureEnabled(EFeatureId::COM_06))
	{
		PendingBurstDelays.Reset();
		HideBeam();
		HideAimedBeam();
		AimHeldSeconds = 0.0f;
		return;
	}
	const FAttackTuning& Tuning = ActiveTuning();
	// Time moves the canopy on before this step's shots, so a shot fired now shows as snapped open now.
	SpellPresentationRules::Step(Canopy, DeltaSeconds, Tuning);

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
	StepAimedShot(DeltaSeconds, Tuning);
}

bool UAttackEmitterComponent::IsAimCharging() const
{
	return AimHeldSeconds > 0.0f && !bAimFiredThisHold && AimCooldownLeft <= 0.0f;
}

FVector UAttackEmitterComponent::AimedMuzzle(const FAttackTuning& Tuning) const
{
	return GetOwner()->GetActorLocation() + Tuning.AimedMuzzleOffset;
}

void UAttackEmitterComponent::StepAimedShot(float DeltaSeconds, const FAttackTuning& Tuning)
{
	const bool bShooting = UmbrellaState && UmbrellaActionRules::CanFire(UmbrellaState->GetAction());
	// D-new-aimed-shot (Josh, 14 Nov): tap Shoot = the Small Blasts above (unchanged); hold it AimedChargeSeconds and one
	// long beam fires to the right. Ella keeps falling throughout: the beam needs the shooting fall like every shot.
	AimCooldownLeft = FMath::Max(0.0f, AimCooldownLeft - DeltaSeconds);
	if (AimedBeam)
	{
		AimedBeamAge += DeltaSeconds;
		if (AimedBeamAge >= Tuning.AimedBeamSeconds)
		{
			HideAimedBeam();
		}
		else
		{
			AimedBeam->Follow(AimedMuzzle(Tuning), AimedBeamAge / FMath::Max(Tuning.AimedBeamSeconds, KINDA_SMALL_NUMBER));
		}
	}
	if (!bShooting || Equipped != EUmbrellaSpell::SmallBlasts)
	{
		AimHeldSeconds = 0.0f;
		bAimFiredThisHold = false;
		return;
	}
	if (bAimFiredThisHold || AimCooldownLeft > 0.0f)
	{
		AimHeldSeconds = 0.0f;
		return;
	}
	AimHeldSeconds += DeltaSeconds;
	if (AimHeldSeconds + UE_KINDA_SMALL_NUMBER >= Tuning.AimedChargeSeconds)
	{
		FireAimedBeam(Tuning);
	}
}

void UAttackEmitterComponent::FireAimedBeam(const FAttackTuning& Tuning)
{
	bAimFiredThisHold = true;
	AimHeldSeconds = 0.0f;
	AimCooldownLeft = Tuning.AimedBeamSeconds + Tuning.AimedCooldownSeconds;
	HideAimedBeam();
	if (UWorld* World = GetWorld())
	{
		FActorSpawnParameters Params;
		Params.SpawnCollisionHandlingOverride = ESpawnActorCollisionHandlingMethod::AlwaysSpawn;
		AimedBeam = World->SpawnActor<AAimedBeamActor>(AAimedBeamActor::StaticClass(), FTransform(GetOwner()->GetActorLocation()), Params);
	}
	if (!AimedBeam)
	{
		return;
	}
	AimedBeamAge = 0.0f;
	AimedBeam->Place(AimedMuzzle(Tuning), Tuning.AimedBeamLength, Tuning.AimedBeamWidth);
	FUmbrellaShotSpec Shot;
	Shot.Kind = EUmbrellaShotKind::PlayerBlast;
	Shot.Origin = AimedBeam->GetMuzzle();
	Shot.Damage = Tuning.AimedDamage;
	Shot.Radius = Tuning.AimedBeamWidth * 0.5f;
	Shot.SourceId = UmbrellaPlayerIds::Ella;
	AimedBeam->Fire(Shot);
	++AimedBeamsFired;   // LastShot stays the last Small Blast: the beam is not a traveling shot
}

void UAttackEmitterComponent::HideAimedBeam()
{
	if (AimedBeam)
	{
		AimedBeam->Destroy();
		AimedBeam = nullptr;
	}
	AimedBeamAge = 0.0f;
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
		FVector Muzzle = GetOwner()->GetActorLocation() + SizedMuzzle(Tuning);
		Beam->SetBeam(Muzzle, SpellRules::StreamLength(StreamHeldSeconds, Tuning), Tuning.StreamWidth);
	}
}

void UAttackEmitterComponent::FireVolley()
{
	const FAttackTuning& Tuning = ActiveTuning();
	FVector Muzzle = GetOwner()->GetActorLocation() + SizedMuzzle(Tuning);
	Muzzle.Y = UmbrellaDrawOrder::ProjectileY;
	// One emission, one canopy pulse (a Twin Stars pair is one emission; Small Blasts are the only spell that folds).
	SpellPresentationRules::OnEmission(Canopy, Equipped, Tuning);
	for (const FUmbrellaShotSpec& Spec : SpellRules::BuildVolley(Equipped, Muzzle, Tuning))
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
	Canopy = SpellPresentationRules::RestingCycle(Spell);
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
	HideAimedBeam();
	Super::EndPlay(Reason);
}

float UAttackEmitterComponent::GetStreamLength() const
{
	return StreamHeldSeconds > 0.0f && UmbrellaState && UmbrellaActionRules::CanFire(UmbrellaState->GetAction()) ? SpellRules::StreamLength(StreamHeldSeconds, ActiveTuning()) : 0.0f;
}

TArray<FSpellWheelEntry> UAttackEmitterComponent::GetWheelEntries() const
{
	return SpellPresentationRules::WheelEntries(PlayMode, DirectorLevel, ActiveTuning());
}
