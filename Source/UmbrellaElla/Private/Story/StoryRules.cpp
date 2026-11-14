#include "Story/StoryRules.h"
#include "Core/UmbrellaTuning.h"
#include "Core/UmbrellaEvent.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Projectile/UmbrellaShotSpec.h"

namespace
{
	const FName DirectorsCutName(TEXT("DirectorsCut"));
	const FName OpeningId(TEXT("OpeningMother"));
	const FName EndingTrigger(TEXT("Ending.Story"));
	/** The Detail the projectile service stamps on a player shot's ProjectileSpawned (the enum's own name,
	 *  "EUmbrellaShotKind::PlayerBlast"). A bare "PlayerBlast" never matched, so Journey Complete showed Shots fired 0. */
	FName StoryPlayerBlastName()
	{
		return StaticEnum<EUmbrellaShotKind>()->GetNameByValue(static_cast<int64>(EUmbrellaShotKind::PlayerBlast));
	}

	float DurationFor(const FStoryCue& Cue)
	{
		if (Cue.DurationSeconds > 0.0f)
		{
			return Cue.DurationSeconds;
		}
		const FStoryTuning& Tuning = GetDefault<UUmbrellaTuning>()->Story;
		return Cue.Id == OpeningId ? Tuning.OpeningCaptionSeconds : Tuning.EndingLineSeconds;
	}

	bool StoryOn()
	{
		return IsFeatureEnabled(EFeatureId::NAR_02);
	}
}

TArray<TPair<FString, FString>> StoryStatsRows(const FStoryRunStats& Stats)
{
	const float UnitsPerMetre = GetDefault<UUmbrellaTuning>()->Story.UnitsPerMetre;
	TArray<TPair<FString, FString>> Rows;
	Rows.Emplace(TEXT("Enemies defeated"), FString::FromInt(Stats.EnemiesDefeated));
	Rows.Emplace(TEXT("Experience earned"), FString::FromInt(Stats.XpEarned));
	Rows.Emplace(TEXT("Deaths"), FString::FromInt(Stats.Deaths));
	Rows.Emplace(TEXT("Distance flown"), FString::Printf(TEXT("%.0f m"), Stats.DistanceFlownUnits / UnitsPerMetre));
	Rows.Emplace(TEXT("Shots fired"), FString::FromInt(Stats.ShotsFired));
	Rows.Emplace(TEXT("Shots fired at you"), FString::FromInt(Stats.ShotsFiredAtYou));
	Rows.Emplace(TEXT("Damage taken"), FString::Printf(TEXT("%.1f"), Stats.DamageTaken));
	Rows.Emplace(TEXT("Health restored"), FString::Printf(TEXT("%.1f"), Stats.HealthRestored));
	return Rows;
}

const FString& StoryCueTable::DefaultText()
{
	static const FString Text(
		TEXT("# id\ttrigger\tdelay_seconds\tduration_seconds\ttext   (tab separated; duration 0 = tuning value; ending lines show in file order)\n")
		TEXT("OpeningMother\tModeSelected.DirectorsCut\t0\t0\tMother: Keep it open, Ella. It'll protect you from the owl.\n")
		TEXT("LightShadow\tModeSelected.DirectorsCut\t5\t5\tThe abyss is endless. The open umbrella's shadow follows her.\n")
		TEXT("KeeperArrival\tPhaseStarted.wings\t0\t5\tThe clock keeps one hand. Beside it is an empty place.\n")
		TEXT("ShaftClue\tBossPartDestroyed\t0\t5\tThe umbrella's shaft matches the bronze of the clock.\n")
		TEXT("EndingStory1\tEnding.Story\t0\t0\tThe owl's pursuit ends. He goes back into the darkness.\n")
		TEXT("EndingStory2\tEnding.Story\t0\t0\tElla is alive, but still suspended between worlds.\n")
		TEXT("EndingStory3\tEnding.Story\t0\t0\tPerhaps the owl has only postponed his judgment.\n"));
	return Text;
}

TArray<FStoryCue> StoryCueTable::Parse(const FString& Text)
{
	TArray<FStoryCue> Out;
	TArray<FString> Lines;
	Text.ParseIntoArrayLines(Lines);
	for (const FString& Line : Lines)
	{
		if (Line.IsEmpty() || Line.StartsWith(TEXT("#")))
		{
			continue;
		}
		TArray<FString> Cells;
		Line.ParseIntoArray(Cells, TEXT("\t"), false);
		if (Cells.Num() < StoryCueColumn::Count || Cells[StoryCueColumn::Id].IsEmpty() || Cells[StoryCueColumn::Text].IsEmpty())
		{
			continue;
		}
		FStoryCue Cue;
		Cue.Id = FName(*Cells[StoryCueColumn::Id]);
		Cue.Trigger = FName(*Cells[StoryCueColumn::Trigger]);
		Cue.DelaySeconds = FMath::Max(0.0f, FCString::Atof(*Cells[StoryCueColumn::Delay]));
		Cue.DurationSeconds = FMath::Max(0.0f, FCString::Atof(*Cells[StoryCueColumn::Duration]));
		Cue.Text = Cells[StoryCueColumn::Text];
		Out.Add(Cue);
	}
	return Out;
}

FName StoryCueTable::TriggerFor(const FUmbrellaEvent& Event)
{
	const FString EventName = StaticEnum<EUmbrellaEventType>()->GetNameStringByValue(static_cast<int64>(Event.Type));
	return FName(*FString::Printf(TEXT("%s.%s"), *EventName, *Event.Detail.ToString()));
}

FString FStoryProgress::ToText() const
{
	return FString::Printf(TEXT("OpeningSeen=%d\nFirstWinSeen=%d\n"), bOpeningSeen ? 1 : 0, bFirstWinSeen ? 1 : 0);
}

FStoryProgress FStoryProgress::FromText(const FString& Text)
{
	FStoryProgress Out;
	TArray<FString> Lines;
	Text.ParseIntoArrayLines(Lines);
	for (const FString& Line : Lines)
	{
		FString Key;
		FString Value;
		if (Line.Split(TEXT("="), &Key, &Value))
		{
			const bool bOn = Value.TrimStartAndEnd() == TEXT("1");
			if (Key == TEXT("OpeningSeen"))
			{
				Out.bOpeningSeen = bOn;
			}
			else if (Key == TEXT("FirstWinSeen"))
			{
				Out.bFirstWinSeen = bOn;
			}
		}
	}
	return Out;
}

int32 FStoryModel::CountShown(FName Id) const
{
	int32 Count = 0;
	for (const FName& Name : Shown)
	{
		Count += Name == Id ? 1 : 0;
	}
	return Count;
}

void FStoryModel::BeginRunState()
{
	Stats = FStoryRunStats();
	Pending.Reset();
	Shown.Reset();
	bHasActive = false;
	ActiveRemaining = 0.0f;
	Stage = EStoryEndingStage::None;
	bHaveLocation = false;
	bHaveHealth = false;
	bRunLive = true;
}

void FStoryModel::BeginNewRun(EUmbrellaPlayMode NewMode)
{
	Mode = NewMode;
	BeginRunState();
}

void FStoryModel::SetHealthBaseline(float Health, int32 Lives)
{
	LastHealth = Health;
	LastLives = Lives;
	bHaveHealth = true;
}

void FStoryModel::Queue(const FStoryCue& Cue)
{
	if (Shown.Contains(Cue.Id))
	{
		return;
	}
	for (const FPending& Entry : Pending)
	{
		if (Entry.Cue.Id == Cue.Id)
		{
			return;
		}
	}
	if (bHasActive && Active.Id == Cue.Id)
	{
		return;
	}
	FPending Entry;
	Entry.Cue = Cue;
	Entry.Remaining = Cue.DelaySeconds;
	Pending.Add(Entry);
}

void FStoryModel::StartCue(const FStoryCue& Cue)
{
	Active = Cue;
	bHasActive = true;
	ActiveRemaining = DurationFor(Cue);
	Shown.Add(Cue.Id);
}

void FStoryModel::FinishActive()
{
	if (bHasActive && Active.Id == OpeningId && !Progress.bOpeningSeen)
	{
		Progress.bOpeningSeen = true;
		bProgressDirty = true;
	}
	bHasActive = false;
	ActiveRemaining = 0.0f;
}

void FStoryModel::OnEvent(const FUmbrellaEvent& Event)
{
	if (!StoryOn())
	{
		return;
	}
	if (Event.Type == EUmbrellaEventType::ModeSelected)
	{
		const EUmbrellaPlayMode Selected = Event.Detail == DirectorsCutName ? EUmbrellaPlayMode::DirectorsCut : EUmbrellaPlayMode::StartGame;
		// A late ModeSelected after flow already called BeginNewRun for an untouched run must not replay the opening.
		const bool bUntouched = bRunLive && Mode == Selected && Stage == EStoryEndingStage::None && Stats.Deaths == 0
			&& Stats.EnemiesDefeated == 0 && Stats.ShotsFired == 0 && Stats.ShotsFiredAtYou == 0;
		if (!bUntouched)
		{
			BeginNewRun(Selected);
		}
	}
	if (!IsDirectorsCut() || !bRunLive || Stage != EStoryEndingStage::None)
	{
		// After the win the run is over: nothing more is counted or captioned (NAR-07; Journey Complete shows current-run stats).
		return;
	}

	switch (Event.Type)
	{
	case EUmbrellaEventType::CheckpointRetried:
		++Stats.Deaths;
		bHaveHealth = false;
		break;
	case EUmbrellaEventType::XPAwarded:
		Stats.XpEarned += FMath::Max(0, Event.Amount);
		++Stats.EnemiesDefeated;
		break;
	case EUmbrellaEventType::ProjectileSpawned:
		(Event.Detail == StoryPlayerBlastName() ? Stats.ShotsFired : Stats.ShotsFiredAtYou) += 1;
		break;
	case EUmbrellaEventType::PlayerHealthChanged:
		HandleHealth(Event);
		break;
	case EUmbrellaEventType::EncounterCompleted:
		if (IsFeatureEnabled(EFeatureId::NAR_07))
		{
			EnterStage(EStoryEndingStage::Hold);
		}
		return;
	default:
		break;
	}

	const FName Full = StoryCueTable::TriggerFor(Event);
	const FString EventName = StaticEnum<EUmbrellaEventType>()->GetNameStringByValue(static_cast<int64>(Event.Type));
	for (const FStoryCue& Cue : Cues)
	{
		if (Cue.Trigger == Full || Cue.Trigger == FName(*EventName))
		{
			Queue(Cue);
		}
	}
}

void FStoryModel::HandleHealth(const FUmbrellaEvent& Event)
{
	const float Now = Event.Value;
	if (bHaveHealth)
	{
		if (Event.Amount < LastLives)
		{
			// A life handover: the rest of the old life was lost, the new one is not a heal.
			Stats.DamageTaken += FMath::Max(0.0f, LastHealth);
		}
		else if (Now < LastHealth)
		{
			Stats.DamageTaken += LastHealth - Now;
		}
		else
		{
			Stats.HealthRestored += Now - LastHealth;
		}
	}
	LastHealth = Now;
	LastLives = Event.Amount;
	bHaveHealth = true;
}

void FStoryModel::SampleLocation(const FVector& Location)
{
	if (!IsDirectorsCut() || !bRunLive || Stage != EStoryEndingStage::None)
	{
		return;
	}
	if (bHaveLocation)
	{
		const float Step = static_cast<float>(FVector::Dist(Location, LastLocation));
		if (Step <= GetDefault<UUmbrellaTuning>()->Story.MaxFlownStepUnits)
		{
			Stats.DistanceFlownUnits += Step;
		}
	}
	LastLocation = Location;
	bHaveLocation = true;
}

void FStoryModel::EnterStage(EStoryEndingStage Next)
{
	Stage = Next;
	switch (Next)
	{
	case EStoryEndingStage::Hold:
		// Authoritative success: no more in-play captions; the stats are frozen from here.
		Pending.Reset();
		FinishActive();
		break;
	case EStoryEndingStage::Statistics:
		if (!Progress.bFirstWinSeen)
		{
			Progress.bFirstWinSeen = true;
			bProgressDirty = true;
		}
		bRunLive = false;
		break;
	default:
		break;
	}
}

void FStoryModel::EnterEndingStage(EStoryEndingStage Next)
{
	// Flow owns the one ending clock (NAR-07); story only follows it, forward only, once the win started it.
	if (!IsDirectorsCut() || Stage == EStoryEndingStage::None || Next <= Stage)
	{
		return;
	}
	EnterStage(Next);
}

TArray<FString> FStoryModel::GetEndingLines() const
{
	TArray<FString> Lines;
	for (const FStoryCue& Cue : Cues)
	{
		if (Cue.Trigger == EndingTrigger)
		{
			Lines.Add(Cue.Text);
		}
	}
	return Lines;
}

bool FStoryModel::IsLightShaftOn() const
{
	// NAR-05: light falls through the whole Director's Cut run and the ending hold, until the ending background.
	const bool bStageLit = Stage == EStoryEndingStage::None || Stage == EStoryEndingStage::Hold;
	return IsFeatureEnabled(EFeatureId::NAR_05) && StoryOn() && IsDirectorsCut() && bRunLive && bStageLit;
}

void FStoryModel::Advance(float DeltaSeconds)
{
	if (!StoryOn() || !bRunLive || DeltaSeconds <= 0.0f || Stage != EStoryEndingStage::None)
	{
		return;
	}
	for (int32 Index = Pending.Num() - 1; Index >= 0; --Index)
	{
		Pending[Index].Remaining -= DeltaSeconds;
	}
	if (bHasActive)
	{
		ActiveRemaining -= DeltaSeconds;
		if (ActiveRemaining <= 0.0f)
		{
			FinishActive();
		}
	}
	if (!bHasActive)
	{
		for (int32 Index = 0; Index < Pending.Num(); ++Index)
		{
			if (Pending[Index].Remaining <= 0.0f)
			{
				const FStoryCue Cue = Pending[Index].Cue;
				Pending.RemoveAt(Index);
				StartCue(Cue);
				break;
			}
		}
	}
}

bool FStoryModel::IsOpeningShowing() const
{
	return bHasActive && Active.Id == OpeningId;
}

void FStoryModel::SkipOpening()
{
	if (IsOpeningShowing() && Progress.bOpeningSeen)
	{
		FinishActive();
	}
}

bool FStoryModel::CanSkipEnding() const
{
	const bool bInSkippable = Stage == EStoryEndingStage::StoryText || Stage == EStoryEndingStage::Credits;
	return bInSkippable && Progress.bFirstWinSeen;
}

void FStoryModel::SkipEnding()
{
	if (CanSkipEnding())
	{
		EnterStage(EStoryEndingStage::Statistics);
	}
}
