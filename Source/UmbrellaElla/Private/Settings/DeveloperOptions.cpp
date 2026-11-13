#include "Settings/DeveloperOptions.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Settings/SettingsLiveTuning.h"

#define LOCTEXT_NAMESPACE "UmbrellaDeveloperOptions"

namespace
{
	FDeveloperOptionSpec MakeDevSpec(EDeveloperOption Id, const TCHAR* Name, const FText& Label, EDeveloperOptionKind Kind, int32 Low)
	{
		FDeveloperOptionSpec Spec;
		Spec.Id = Id;
		Spec.Name = FName(Name);
		Spec.Label = Label;
		Spec.Kind = Kind;
		switch (Kind)
		{
		case EDeveloperOptionKind::Percent:
			Spec.Low = Low;
			Spec.High = DeveloperOptionLimits::PercentHigh;
			Spec.Step = DeveloperOptionLimits::PercentStep;
			Spec.Default = DeveloperOptionLimits::PercentUnit;
			break;
		case EDeveloperOptionKind::Offset:
			Spec.Low = DeveloperOptionLimits::OffsetLow;
			Spec.High = DeveloperOptionLimits::OffsetHigh;
			Spec.Step = DeveloperOptionLimits::OffsetStep;
			Spec.Default = 0;
			break;
		case EDeveloperOptionKind::Toggle:
			Spec.Low = DeveloperOptionLimits::ToggleOff;
			Spec.High = DeveloperOptionLimits::ToggleOn;
			Spec.Step = DeveloperOptionLimits::OffsetStep;
			Spec.Default = Low;
			break;
		case EDeveloperOptionKind::Link:
		default:
			break;
		}
		return Spec;
	}

#if UMBRELLAELLA_WORKBENCH
	float DevPercentScale(int32 Percent)
	{
		return static_cast<float>(Percent) / static_cast<float>(DeveloperOptionLimits::PercentUnit);
	}

	void DevScale(float& Value, int32 Percent)
	{
		Value *= DevPercentScale(Percent);
	}

	void DevScaleInt(int32& Value, int32 Percent)
	{
		Value = FMath::RoundToInt(static_cast<float>(Value) * DevPercentScale(Percent));
	}
#endif

	int32 DevCount(int32 Base, int32 Offset)
	{
		return FMath::Max(DeveloperOptionLimits::CountFloor, Base + Offset);
	}
}

TArray<FDeveloperOptionSpec> DeveloperOptionRules::AllSpecs()
{
	TArray<FDeveloperOptionSpec> Specs;
	if (!IsFeatureEnabled(EFeatureId::FLOW_44))
	{
		return Specs;
	}
	using EKind = EDeveloperOptionKind;
	const int32 Low = DeveloperOptionLimits::PercentLow;
	const int32 Off = DeveloperOptionLimits::PercentOffLow;
	Specs.Add(MakeDevSpec(EDeveloperOption::EntryRetries, TEXT("EntryRetries"), LOCTEXT("EntryRetries", "Entry and retries (lives)"), EKind::Offset, 0));
	Specs.Add(MakeDevSpec(EDeveloperOption::Movement, TEXT("Movement"), LOCTEXT("Movement", "Movement speed"), EKind::Percent, Low));
	Specs.Add(MakeDevSpec(EDeveloperOption::Hop, TEXT("Hop"), LOCTEXT("Hop", "Hop distance"), EKind::Percent, Low));
	Specs.Add(MakeDevSpec(EDeveloperOption::Dash, TEXT("Dash"), LOCTEXT("Dash", "Dash distance"), EKind::Percent, Low));
	Specs.Add(MakeDevSpec(EDeveloperOption::VoluntaryCurrents, TEXT("VoluntaryCurrents"), LOCTEXT("VoluntaryCurrents", "Wind current strength"), EKind::Percent, Off));
	Specs.Add(MakeDevSpec(EDeveloperOption::HostileGusts, TEXT("HostileGusts"), LOCTEXT("HostileGusts", "Hostile gust strength"), EKind::Percent, Off));
	Specs.Add(MakeDevSpec(EDeveloperOption::Missiles, TEXT("Missiles"), LOCTEXT("Missiles", "Enemy shot speed"), EKind::Percent, Low));
	Specs.Add(MakeDevSpec(EDeveloperOption::Absorption, TEXT("Absorption"), LOCTEXT("Absorption", "Absorb range and pull"), EKind::Percent, Low));
	Specs.Add(MakeDevSpec(EDeveloperOption::HealthGround, TEXT("HealthGround"), LOCTEXT("HealthGround", "Hits per life"), EKind::Offset, 0));
	Specs.Add(MakeDevSpec(EDeveloperOption::FourWeapons, TEXT("FourWeapons"), LOCTEXT("FourWeapons", "All four spells unlocked"), EKind::Toggle, DeveloperOptionLimits::ToggleOff));
	Specs.Add(MakeDevSpec(EDeveloperOption::ProgressionScarf, TEXT("ProgressionScarf"), LOCTEXT("ProgressionScarf", "Experience gained"), EKind::Percent, Off));
	Specs.Add(MakeDevSpec(EDeveloperOption::OwlParts, TEXT("OwlParts"), LOCTEXT("OwlParts", "Keeper part health"), EKind::Percent, Low));
	Specs.Add(MakeDevSpec(EDeveloperOption::Clock, TEXT("Clock"), LOCTEXT("Clock", "Keeper clock health"), EKind::Percent, Low));
	Specs.Add(MakeDevSpec(EDeveloperOption::Stun, TEXT("Stun"), LOCTEXT("Stun", "Part-break stun time"), EKind::Percent, Off));
	Specs.Add(MakeDevSpec(EDeveloperOption::Slow, TEXT("Slow"), LOCTEXT("Slow", "Keeper slow attack"), EKind::Toggle, DeveloperOptionLimits::ToggleOn));
	Specs.Add(MakeDevSpec(EDeveloperOption::EyesBlackout, TEXT("EyesBlackout"), LOCTEXT("EyesBlackout", "Eye blackout time"), EKind::Percent, Off));
	Specs.Add(MakeDevSpec(EDeveloperOption::Tutorial, TEXT("Tutorial"), LOCTEXT("Tutorial", "First-play tutorials"), EKind::Toggle, DeveloperOptionLimits::ToggleOn));
	Specs.Add(MakeDevSpec(EDeveloperOption::Remapping, TEXT("Remapping"), LOCTEXT("Remapping", "Remap controls"), EKind::Link, 0));
	Specs.Add(MakeDevSpec(EDeveloperOption::SizeHitbox, TEXT("SizeHitbox"), LOCTEXT("SizeHitbox", "Ella's hit area"), EKind::Percent, Low));
	Specs.Add(MakeDevSpec(EDeveloperOption::Background, TEXT("Background"), LOCTEXT("Background", "Menu background motion"), EKind::Percent, Off));
	return Specs;
}

FDeveloperOptionSpec DeveloperOptionRules::SpecFor(EDeveloperOption Option)
{
	for (const FDeveloperOptionSpec& Spec : AllSpecs())
	{
		if (Spec.Id == Option)
		{
			return Spec;
		}
	}
	return FDeveloperOptionSpec();
}

TArray<int32> DeveloperOptionRules::MakeDefaultValues()
{
	TArray<int32> Values;
	Values.SetNumZeroed(static_cast<int32>(EDeveloperOption::Count));
	for (const FDeveloperOptionSpec& Spec : AllSpecs())
	{
		Values[static_cast<int32>(Spec.Id)] = Spec.Default;
	}
	return Values;
}

int32 DeveloperOptionRules::ClampValue(EDeveloperOption Option, int32 Value)
{
	const FDeveloperOptionSpec Spec = SpecFor(Option);
	if (Spec.Id == EDeveloperOption::Count || Spec.Kind == EDeveloperOptionKind::Link)
	{
		return Spec.Default;
	}
	const int32 Step = FMath::Max(1, Spec.Step);
	const int32 Snapped = Spec.Low + FMath::RoundToInt(static_cast<float>(Value - Spec.Low) / static_cast<float>(Step)) * Step;
	return FMath::Clamp(Snapped, Spec.Low, Spec.High);
}

int32 DeveloperOptionRules::ValueOf(const TArray<int32>& Values, EDeveloperOption Option)
{
	const int32 Index = static_cast<int32>(Option);
	return Values.IsValidIndex(Index) ? Values[Index] : SpecFor(Option).Default;
}

bool DeveloperOptionRules::IsAllDefault(const TArray<int32>& Values)
{
	for (const FDeveloperOptionSpec& Spec : AllSpecs())
	{
		if (ValueOf(Values, Spec.Id) != Spec.Default)
		{
			return false;
		}
	}
	return true;
}

bool DeveloperOptionRules::IsWorkbenchBuild()
{
#if UMBRELLAELLA_WORKBENCH
	return true;
#else
	return false;
#endif
}

bool DeveloperOptionRules::CanEdit(EUmbrellaPlayMode Mode, bool bWorkbenchBuild)
{
	return IsFeatureEnabled(EFeatureId::FLOW_44) && Mode == EUmbrellaPlayMode::DirectorsCut
		&& (bWorkbenchBuild || DeveloperOptionRelease::bEditableInSubmissionBuild);
}

#if UMBRELLAELLA_WORKBENCH
void DeveloperOptionRules::Apply(const TArray<int32>& Values, FSettingsLiveTuning& Tuning)
{
	if (!IsFeatureEnabled(EFeatureId::FLOW_44))
	{
		return;
	}
	for (const FDeveloperOptionSpec& Spec : AllSpecs())
	{
		const int32 Value = ClampValue(Spec.Id, ValueOf(Values, Spec.Id));
		if (Value == Spec.Default)
		{
			// As tuned: leave the baseline alone, so a default never overrides a tuned bool or count.
			continue;
		}
		switch (Spec.Id)
		{
		case EDeveloperOption::EntryRetries:
			Tuning.Encounter.RetryLives = DevCount(Tuning.Encounter.RetryLives, Value);
			break;
		case EDeveloperOption::Movement:
			DevScale(Tuning.Motor.RiseSpeed, Value);
			DevScale(Tuning.Motor.FallSpeed, Value);
			DevScale(Tuning.Motor.FreeFallSpeed, Value);
			DevScale(Tuning.Motor.HorizontalMaxSpeed, Value);
			break;
		case EDeveloperOption::Hop:
			DevScale(Tuning.Motor.HopDistance, Value);
			break;
		case EDeveloperOption::Dash:
			DevScale(Tuning.Motor.DashDistance, Value);
			break;
		case EDeveloperOption::VoluntaryCurrents:
			DevScale(Tuning.Field.DefaultWindForce, Value);
			break;
		case EDeveloperOption::HostileGusts:
			DevScale(Tuning.Keeper.GustPush, Value);
			DevScale(Tuning.Keeper.GustDamage, Value);
			break;
		case EDeveloperOption::Missiles:
			DevScale(Tuning.Keeper.RedSpeedWings, Value);
			DevScale(Tuning.Keeper.RedSpeedMechanisms, Value);
			DevScale(Tuning.Keeper.RedSpeedClock, Value);
			DevScale(Tuning.Keeper.YellowSpeedWings, Value);
			DevScale(Tuning.Keeper.YellowSpeedMechanisms, Value);
			DevScale(Tuning.Keeper.YellowSpeedClock, Value);
			break;
		case EDeveloperOption::Absorption:
			DevScale(Tuning.UmbrellaFlight.AbsorbRange, Value);
			DevScale(Tuning.UmbrellaFlight.PullSpeed, Value);
			break;
		case EDeveloperOption::HealthGround:
			Tuning.Health.HitsPerLife = static_cast<float>(DevCount(FMath::RoundToInt(Tuning.Health.HitsPerLife), Value));
			break;
		case EDeveloperOption::FourWeapons:
			if (Value == DeveloperOptionLimits::ToggleOn)
			{
				const int32 Level = DeveloperOptionLimits::AllWeaponsUnlockLevel;
				Tuning.Attack.StreamUnlockLevel = Level;
				Tuning.Attack.TwinUnlockLevel = Level;
				Tuning.Attack.NeedleUnlockLevel = Level;
				Tuning.Progression.UnlockLevelStreamed = Level;
				Tuning.Progression.UnlockLevelTwin = Level;
				Tuning.Progression.UnlockLevelNeedle = Level;
			}
			break;
		case EDeveloperOption::ProgressionScarf:
			DevScaleInt(Tuning.Progression.XpRoadwarden, Value);
			DevScaleInt(Tuning.Progression.XpFloodstrider, Value);
			DevScaleInt(Tuning.Progression.XpCourier, Value);
			DevScaleInt(Tuning.Progression.XpWings, Value);
			DevScaleInt(Tuning.Progression.XpFront, Value);
			DevScaleInt(Tuning.Progression.XpMiddle, Value);
			DevScaleInt(Tuning.Progression.XpRear, Value);
			DevScaleInt(Tuning.Progression.XpClock, Value);
			break;
		case EDeveloperOption::OwlParts:
			DevScale(Tuning.Keeper.WingsHp, Value);
			DevScale(Tuning.Keeper.FrontHp, Value);
			DevScale(Tuning.Keeper.MiddleHp, Value);
			DevScale(Tuning.Keeper.RearHp, Value);
			break;
		case EDeveloperOption::Clock:
			DevScale(Tuning.Keeper.ClockHp, Value);
			DevScale(Tuning.Keeper.ClockReserveHp, Value);
			break;
		case EDeveloperOption::Stun:
			DevScale(Tuning.Keeper.BreakStunSeconds, Value);
			break;
		case EDeveloperOption::Slow:
			Tuning.Keeper.bSlowEnabled = Value == DeveloperOptionLimits::ToggleOn;
			break;
		case EDeveloperOption::EyesBlackout:
			DevScale(Tuning.Keeper.BlackoutSeconds, Value);
			break;
		case EDeveloperOption::SizeHitbox:
			DevScale(Tuning.Encounter.PlayerRadius, Value);
			break;
		case EDeveloperOption::Background:
			DevScale(Tuning.Flow.BackgroundDriftSpeed, Value);
			DevScale(Tuning.Flow.BackgroundSwayAmplitude, Value);
			DevScale(Tuning.Flow.FallingShapeMinSpeed, Value);
			DevScale(Tuning.Flow.FallingShapeMaxSpeed, Value);
			break;
		case EDeveloperOption::Tutorial:
		case EDeveloperOption::Remapping:
		default:
			// Tutorial has no tuning number: flow reads it through USettingsMenuSubsystem::GetDeveloperOption.
			// Remapping opens the Controller page.
			break;
		}
	}
}

#endif // UMBRELLAELLA_WORKBENCH

FText DeveloperOptionRules::ValueText(EDeveloperOption Option, int32 Value, int32 BaseRetryLives, int32 BaseHitsPerLife)
{
	const FDeveloperOptionSpec Spec = SpecFor(Option);
	switch (Spec.Kind)
	{
	case EDeveloperOptionKind::Percent:
		return FText::Format(LOCTEXT("PercentValue", "{0}%"), FText::AsNumber(Value));
	case EDeveloperOptionKind::Offset:
	{
		const int32 Base = Option == EDeveloperOption::EntryRetries ? BaseRetryLives : BaseHitsPerLife;
		return FText::AsNumber(DevCount(Base, Value));
	}
	case EDeveloperOptionKind::Toggle:
		return Value == DeveloperOptionLimits::ToggleOn ? LOCTEXT("On", "On") : LOCTEXT("Off", "Off");
	case EDeveloperOptionKind::Link:
	default:
		return LOCTEXT("Open", "Open");
	}
}

#undef LOCTEXT_NAMESPACE
