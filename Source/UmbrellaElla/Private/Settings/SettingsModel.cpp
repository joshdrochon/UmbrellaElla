#include "Settings/SettingsModel.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Settings/SettingsConstants.h"

#define LOCTEXT_NAMESPACE "UmbrellaSettings"

bool FUmbrellaSettingsData::operator==(const FUmbrellaSettingsData& Other) const
{
	if (MasterVolume != Other.MasterVolume || SfxVolume != Other.SfxVolume || MusicVolume != Other.MusicVolume
		|| TextScalePercent != Other.TextScalePercent || bReducedMotion != Other.bReducedMotion || bReducedFlash != Other.bReducedFlash
		|| Bindings.Num() != Other.Bindings.Num() || DeveloperValues != Other.DeveloperValues)
	{
		return false;
	}
	for (int32 Index = 0; Index < Bindings.Num(); ++Index)
	{
		const FUmbrellaDefaultBinding& A = Bindings[Index];
		const FUmbrellaDefaultBinding& B = Other.Bindings[Index];
		if (A.Action != B.Action || A.Key != B.Key || !FMath::IsNearlyEqual(A.Scale, B.Scale))
		{
			return false;
		}
	}
	return true;
}

FUmbrellaSettingsData SettingsRules::MakeDefaults()
{
	FUmbrellaSettingsData Data;
	Data.MasterVolume = SettingsConstants::DefaultVolume;
	Data.SfxVolume = SettingsConstants::DefaultVolume;
	Data.MusicVolume = SettingsConstants::DefaultVolume;
	Data.TextScalePercent = SettingsConstants::TextScaleMin;
	Data.bReducedMotion = false;
	Data.bReducedFlash = false;
	Data.Bindings = UmbrellaInputBindings::BuildDefaults();
	Data.DeveloperValues = DeveloperOptionRules::MakeDefaultValues();
	return Data;
}

int32 SettingsRules::ClampVolume(int32 Value)
{
	return FMath::Clamp(Value, SettingsConstants::SliderMin, SettingsConstants::SliderMax);
}

int32 SettingsRules::ClampTextScale(int32 Percent)
{
	return FMath::Clamp(Percent, SettingsConstants::TextScaleMin, SettingsConstants::TextScaleMax);
}

float SettingsRules::VolumeToClassScale(int32 Value)
{
	return static_cast<float>(ClampVolume(Value)) / static_cast<float>(SettingsConstants::SliderMax);
}

bool SettingsRules::IsPageAvailable(ESettingsPage Page, EUmbrellaPlayMode Mode)
{
	switch (Page)
	{
	case ESettingsPage::Sound:
		return IsFeatureEnabled(EFeatureId::FLOW_36) && IsFeatureEnabled(EFeatureId::FLOW_37);
	case ESettingsPage::Controller:
		return IsFeatureEnabled(EFeatureId::FLOW_36) && IsFeatureEnabled(EFeatureId::MOVE_17);
	case ESettingsPage::Credits:
		return IsFeatureEnabled(EFeatureId::FLOW_36) && IsFeatureEnabled(EFeatureId::FLOW_39);
	case ESettingsPage::GameOptions:
		return Mode == EUmbrellaPlayMode::DirectorsCut && IsFeatureEnabled(EFeatureId::FLOW_36)
			&& IsFeatureEnabled(EFeatureId::FLOW_38);
	default:
		return false;
	}
}

TArray<ESettingsPage> SettingsRules::GetPages(EUmbrellaPlayMode Mode)
{
	TArray<ESettingsPage> Pages;
	const ESettingsPage Order[] = {ESettingsPage::Sound, ESettingsPage::Controller, ESettingsPage::Credits, ESettingsPage::GameOptions};
	for (const ESettingsPage Page : Order)
	{
		if (IsPageAvailable(Page, Mode))
		{
			Pages.Add(Page);
		}
	}
	return Pages;
}

TArray<FName> SettingsRules::GetDeveloperOptionNames(EUmbrellaPlayMode Mode)
{
	TArray<FName> Names;
	if (!IsPageAvailable(ESettingsPage::GameOptions, Mode) || !IsFeatureEnabled(EFeatureId::FLOW_44))
	{
		return Names;
	}
	// FLOW-44 candidates, in the GDD's order (DeveloperOptionRules). No ammunition or energy controls.
	for (const FDeveloperOptionSpec& Spec : DeveloperOptionRules::AllSpecs())
	{
		Names.Add(Spec.Name);
	}
	return Names;
}

TArray<FSettingsCreditLine> SettingsRules::GetCredits()
{
	// Supplied by Rick (GDD section 7); his role is Executive Producer (D-new-credits-ep).
	TArray<FSettingsCreditLine> Lines;
	Lines.Add({TEXT("Rick Rispoli"), TEXT("Executive Producer")});
	Lines.Add({TEXT("Richard"), TEXT("Producer")});
	Lines.Add({TEXT("Josh Rochon"), TEXT("Technical Lead")});
	return Lines;
}

int32 SettingsRules::FindBindingIndex(const TArray<FUmbrellaDefaultBinding>& Bindings, EUmbrellaInputAction Action, int32 Slot)
{
	int32 Seen = 0;
	for (int32 Index = 0; Index < Bindings.Num(); ++Index)
	{
		if (Bindings[Index].Action == Action)
		{
			if (Seen == Slot)
			{
				return Index;
			}
			++Seen;
		}
	}
	return INDEX_NONE;
}

int32 SettingsRules::CountBindings(const TArray<FUmbrellaDefaultBinding>& Bindings, EUmbrellaInputAction Action)
{
	int32 Count = 0;
	for (const FUmbrellaDefaultBinding& Binding : Bindings)
	{
		if (Binding.Action == Action)
		{
			++Count;
		}
	}
	return Count;
}

bool SettingsRules::HasShootAbsorbConflict(const TArray<FUmbrellaDefaultBinding>& Bindings)
{
	for (const FUmbrellaDefaultBinding& Shoot : Bindings)
	{
		if (Shoot.Action != EUmbrellaInputAction::Shoot)
		{
			continue;
		}
		for (const FUmbrellaDefaultBinding& Absorb : Bindings)
		{
			if (Absorb.Action == EUmbrellaInputAction::Absorb && Absorb.Key == Shoot.Key)
			{
				return true;
			}
		}
	}
	return false;
}

FString SettingsRules::KeyLabel(const FKey& Key)
{
	return Key.GetDisplayName().ToString();
}

FString SettingsRules::FirstKeyLabel(const TArray<FUmbrellaDefaultBinding>& Bindings, EUmbrellaInputAction Action)
{
	// Remap-aware instructions: prefer a keyboard or mouse key, then any other.
	const FUmbrellaDefaultBinding* Fallback = nullptr;
	for (const FUmbrellaDefaultBinding& Binding : Bindings)
	{
		if (Binding.Action != Action || Binding.Scale < 0.0f)
		{
			continue;
		}
		if (!Binding.Key.IsGamepadKey())
		{
			return KeyLabel(Binding.Key);
		}
		if (!Fallback)
		{
			Fallback = &Binding;
		}
	}
	return Fallback ? KeyLabel(Fallback->Key) : FString();
}

FText SettingsRules::ActionDisplayName(EUmbrellaInputAction Action)
{
	switch (Action)
	{
	case EUmbrellaInputAction::Shoot:
		return LOCTEXT("Shoot", "Shoot");
	case EUmbrellaInputAction::Absorb:
		return LOCTEXT("Absorb", "Absorb");
	case EUmbrellaInputAction::Hop:
		return LOCTEXT("Hop", "Hop");
	case EUmbrellaInputAction::DashBack:
		return LOCTEXT("DashBack", "Dash back");
	case EUmbrellaInputAction::DashForward:
		return LOCTEXT("DashForward", "Dash forward");
	case EUmbrellaInputAction::Ride:
		return LOCTEXT("Ride", "Ride");
	case EUmbrellaInputAction::Trim:
		return LOCTEXT("Trim", "Trim (up/down)");
	case EUmbrellaInputAction::MoveX:
		return LOCTEXT("MoveX", "Movement (left/right)");
	case EUmbrellaInputAction::Spell1:
		return LOCTEXT("Spell1", "Spell 1");
	case EUmbrellaInputAction::Spell2:
		return LOCTEXT("Spell2", "Spell 2");
	case EUmbrellaInputAction::Spell3:
		return LOCTEXT("Spell3", "Spell 3");
	case EUmbrellaInputAction::Spell4:
		return LOCTEXT("Spell4", "Spell 4");
	case EUmbrellaInputAction::SpellNext:
		return LOCTEXT("SpellNext", "Next spell");
	case EUmbrellaInputAction::SpellPrevious:
		return LOCTEXT("SpellPrevious", "Previous spell");
	default:
		return FText::GetEmpty();
	}
}

FSettingsSession::FSettingsSession()
	: Saved(SettingsRules::MakeDefaults())
	, Draft(Saved)
{
}

FSettingsSession::FSettingsSession(const FUmbrellaSettingsData& InSaved)
	: Saved(InSaved)
	, Draft(InSaved)
{
}

bool FSettingsSession::IsDirty() const
{
	return !(Draft == Saved);
}

void FSettingsSession::SetMasterVolume(int32 Value)
{
	Draft.MasterVolume = SettingsRules::ClampVolume(Value);
}

void FSettingsSession::SetSfxVolume(int32 Value)
{
	Draft.SfxVolume = SettingsRules::ClampVolume(Value);
}

void FSettingsSession::SetMusicVolume(int32 Value)
{
	Draft.MusicVolume = SettingsRules::ClampVolume(Value);
}

void FSettingsSession::SetTextScalePercent(int32 Percent)
{
	Draft.TextScalePercent = SettingsRules::ClampTextScale(Percent);
}

void FSettingsSession::SetReducedMotion(bool bEnabled)
{
	Draft.bReducedMotion = bEnabled;
}

void FSettingsSession::SetReducedFlash(bool bEnabled)
{
	Draft.bReducedFlash = bEnabled;
}

void FSettingsSession::SetDeveloperOption(EDeveloperOption Option, int32 Value)
{
	const int32 Index = static_cast<int32>(Option);
	if (Draft.DeveloperValues.Num() != static_cast<int32>(EDeveloperOption::Count))
	{
		Draft.DeveloperValues = DeveloperOptionRules::MakeDefaultValues();
	}
	if (Draft.DeveloperValues.IsValidIndex(Index))
	{
		Draft.DeveloperValues[Index] = DeveloperOptionRules::ClampValue(Option, Value);
	}
}

void FSettingsSession::ResetDeveloperOptions()
{
	Draft.DeveloperValues = DeveloperOptionRules::MakeDefaultValues();
}

bool FSettingsSession::CanRemap(EUmbrellaInputAction Action, int32 Slot, const FKey& NewKey) const
{
	return NewKey.IsValid() && SettingsRules::FindBindingIndex(Draft.Bindings, Action, Slot) != INDEX_NONE;
}

void FSettingsSession::Remap(EUmbrellaInputAction Action, int32 Slot, const FKey& NewKey)
{
	if (CanRemap(Action, Slot, NewKey))
	{
		Draft.Bindings[SettingsRules::FindBindingIndex(Draft.Bindings, Action, Slot)].Key = NewKey;
	}
}

void FSettingsSession::ResetToDefaults()
{
	Draft = SettingsRules::MakeDefaults();
}

void FSettingsSession::ResetBindings()
{
	Draft.Bindings = UmbrellaInputBindings::BuildDefaults();
}

void FSettingsSession::Save()
{
	Saved = Draft;
}

void FSettingsSession::Discard()
{
	Draft = Saved;
}

namespace
{
	/** Copy the fields one page owns from Source to Target. */
	void CopyPage(ESettingsPage Page, const FUmbrellaSettingsData& Source, FUmbrellaSettingsData& Target)
	{
		switch (Page)
		{
		case ESettingsPage::Sound:
			Target.MasterVolume = Source.MasterVolume;
			Target.SfxVolume = Source.SfxVolume;
			Target.MusicVolume = Source.MusicVolume;
			Target.TextScalePercent = Source.TextScalePercent;
			Target.bReducedMotion = Source.bReducedMotion;
			Target.bReducedFlash = Source.bReducedFlash;
			break;
		case ESettingsPage::Controller:
			Target.Bindings = Source.Bindings;
			break;
		case ESettingsPage::GameOptions:
			Target.DeveloperValues = Source.DeveloperValues;
			break;
		default:
			break;
		}
	}
}

bool FSettingsSession::IsPageDirty(ESettingsPage Page) const
{
	FUmbrellaSettingsData Probe = Saved;
	CopyPage(Page, Draft, Probe);
	return !(Probe == Saved);
}

void FSettingsSession::SavePage(ESettingsPage Page)
{
	CopyPage(Page, Draft, Saved);
}

void FSettingsSession::DiscardPage(ESettingsPage Page)
{
	CopyPage(Page, Saved, Draft);
}

ESettingsBackResult FSettingsSession::RequestBack(ESettingsPage Page) const
{
	return IsPageDirty(Page) ? ESettingsBackResult::AskSaveDiscardKeep : ESettingsBackResult::Close;
}

ESettingsBackOutcome FSettingsSession::ResolveBack(ESettingsPage Page, ESettingsBackChoice Choice)
{
	switch (Choice)
	{
	case ESettingsBackChoice::Save:
		SavePage(Page);
		return ESettingsBackOutcome::CloseMenu;
	case ESettingsBackChoice::Discard:
		DiscardPage(Page);
		return ESettingsBackOutcome::CloseMenu;
	case ESettingsBackChoice::KeepEditing:
	default:
		return ESettingsBackOutcome::StayOpen;
	}
}

#undef LOCTEXT_NAMESPACE
