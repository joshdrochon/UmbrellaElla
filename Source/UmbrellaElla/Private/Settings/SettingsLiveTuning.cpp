#include "Settings/SettingsLiveTuning.h"
#include "Core/UmbrellaTuning.h"

FSettingsLiveTuning FSettingsLiveTuning::ReadFrom(const UUmbrellaTuning* Tuning)
{
	FSettingsLiveTuning Copy;
	if (!Tuning)
	{
		return Copy;
	}
	Copy.Motor = Tuning->Motor;
	Copy.Field = Tuning->Field;
	Copy.Keeper = Tuning->Keeper;
	Copy.Health = Tuning->Health;
	Copy.Attack = Tuning->Attack;
	Copy.Progression = Tuning->Progression;
	Copy.Flow = Tuning->Flow;
	Copy.Encounter = Tuning->Encounter;
	Copy.UmbrellaFlight = Tuning->UmbrellaFlight;
	return Copy;
}

void FSettingsLiveTuning::WriteTo(UUmbrellaTuning* Tuning) const
{
	if (!Tuning)
	{
		return;
	}
	Tuning->Motor = Motor;
	Tuning->Field = Field;
	Tuning->Keeper = Keeper;
	Tuning->Health = Health;
	Tuning->Attack = Attack;
	Tuning->Progression = Progression;
	Tuning->Flow = Flow;
	Tuning->Encounter = Encounter;
	Tuning->UmbrellaFlight = UmbrellaFlight;
}
