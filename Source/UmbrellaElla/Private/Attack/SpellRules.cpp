#include "Attack/SpellRules.h"
#include "Attack/AttackTuning.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Umbrella/UmbrellaPlayerIds.h"

int32 SpellRules::UnlockLevel(EUmbrellaSpell Spell, const FAttackTuning& Tuning)
{
	switch (Spell)
	{
	case EUmbrellaSpell::StreamedBlast:
		return Tuning.StreamUnlockLevel;
	case EUmbrellaSpell::TwinStars:
		return Tuning.TwinUnlockLevel;
	case EUmbrellaSpell::Needle:
		return Tuning.NeedleUnlockLevel;
	case EUmbrellaSpell::SmallBlasts:
	case EUmbrellaSpell::Count:
	default:
		return Tuning.SmallUnlockLevel;
	}
}

bool SpellRules::IsAvailable(EUmbrellaSpell Spell, EUmbrellaPlayMode Mode, int32 DirectorLevel, const FAttackTuning& Tuning)
{
	if (Spell == EUmbrellaSpell::Count)
	{
		return false;
	}
	if (Spell == EUmbrellaSpell::SmallBlasts)
	{
		return true;
	}
	// MOVE-12: Start Game has only Small Blasts; Director's Cut has exactly the four, unlocked by level.
	if (!IsFeatureEnabled(EFeatureId::MOVE_12) || !IsFeatureEnabled(EFeatureId::COM_11))
	{
		return false;
	}
	return Mode == EUmbrellaPlayMode::DirectorsCut && DirectorLevel >= UnlockLevel(Spell, Tuning);
}

EUmbrellaSpell SpellRules::Cycle(EUmbrellaSpell Current, int32 Direction, EUmbrellaPlayMode Mode, int32 DirectorLevel, const FAttackTuning& Tuning)
{
	const int32 Step = Direction < 0 ? -1 : 1;
	const int32 Start = static_cast<int32>(Current);
	for (int32 Offset = 1; Offset <= SpellCount; ++Offset)
	{
		const int32 Index = ((Start + Step * Offset) % SpellCount + SpellCount) % SpellCount;
		const EUmbrellaSpell Candidate = static_cast<EUmbrellaSpell>(Index);
		if (IsAvailable(Candidate, Mode, DirectorLevel, Tuning))
		{
			return Candidate;
		}
	}
	return Current;
}

FSpellProfile SpellRules::GetProfile(EUmbrellaSpell Spell, const FAttackTuning& Tuning)
{
	FSpellProfile Profile;
	switch (Spell)
	{
	case EUmbrellaSpell::StreamedBlast:
		Profile.ShotsPerSecond = Tuning.StreamTicksPerSecond;
		Profile.Damage = Tuning.StreamTickDamage;
		Profile.Speed = Tuning.StreamGrowthSpeed;
		Profile.Range = Tuning.StreamMaxRange;
		Profile.RadiusScale = Tuning.StreamWidth * 0.5f / Tuning.BlastRadius;
		break;
	case EUmbrellaSpell::TwinStars:
		Profile.ShotsPerSecond = Tuning.TwinVolleysPerSecond;
		Profile.Damage = Tuning.TwinDamage;
		Profile.Speed = Tuning.TwinSpeed;
		Profile.Range = Tuning.TwinRange;
		Profile.ShotsPerVolley = 2;
		Profile.Separation = Tuning.TwinSeparation;
		break;
	case EUmbrellaSpell::Needle:
		Profile.ShotsPerSecond = Tuning.NeedleShotsPerSecond;
		Profile.Damage = Tuning.NeedleDamage;
		Profile.Speed = Tuning.NeedleSpeed;
		Profile.Range = Tuning.NeedleRange;
		Profile.RadiusScale = Tuning.NeedleSizeMultiplier;
		break;
	case EUmbrellaSpell::SmallBlasts:
	case EUmbrellaSpell::Count:
	default:
		Profile.ShotsPerSecond = Tuning.SmallShotsPerSecond;
		Profile.Damage = Tuning.SmallDamage;
		Profile.Speed = Tuning.SmallSpeed;
		Profile.Range = Tuning.SmallRange;
		break;
	}
	return Profile;
}

TArray<FUmbrellaShotSpec> SpellRules::BuildVolley(EUmbrellaSpell Spell, const FVector& Muzzle, const FAttackTuning& Tuning)
{
	const FSpellProfile Profile = GetProfile(Spell, Tuning);
	TArray<FUmbrellaShotSpec> Volley;
	for (int32 Index = 0; Index < Profile.ShotsPerVolley; ++Index)
	{
		FUmbrellaShotSpec Spec;
		Spec.Kind = EUmbrellaShotKind::PlayerBlast;
		Spec.Origin = Muzzle;
		if (Profile.ShotsPerVolley > 1)
		{
			// Two shots straddle the muzzle: one upper, one lower.
			const float Side = Index == 0 ? 0.5f : -0.5f;
			Spec.Origin.Z += Side * Profile.Separation;
		}
		// Always to +X: fire never follows travel direction or an aim.
		Spec.Velocity = FVector(Profile.Speed, 0.0, 0.0);
		Spec.Radius = Tuning.BlastRadius * Profile.RadiusScale;
		Spec.Damage = Profile.Damage;
		Spec.LifetimeSeconds = Profile.Range / Profile.Speed;
		Spec.SourceId = UmbrellaPlayerIds::Ella;
		Volley.Add(Spec);
	}
	return Volley;
}

float SpellRules::StreamLength(float HeldSeconds, const FAttackTuning& Tuning)
{
	return FMath::Clamp(Tuning.StreamGrowthSpeed * FMath::Max(HeldSeconds, 0.0f), 0.0f, Tuning.StreamMaxRange);
}

FName SpellRules::SpellName(EUmbrellaSpell Spell)
{
	switch (Spell)
	{
	case EUmbrellaSpell::StreamedBlast:
		return FName(TEXT("StreamedBlast"));
	case EUmbrellaSpell::TwinStars:
		return FName(TEXT("TwinStars"));
	case EUmbrellaSpell::Needle:
		return FName(TEXT("Needle"));
	case EUmbrellaSpell::SmallBlasts:
	case EUmbrellaSpell::Count:
	default:
		return FName(TEXT("SmallBlasts"));
	}
}
