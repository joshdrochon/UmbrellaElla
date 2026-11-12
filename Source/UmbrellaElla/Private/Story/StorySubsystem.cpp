#include "Story/StorySubsystem.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/World.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/Pawn.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "HAL/PlatformFileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UI/Story/StoryWidgets.h"

namespace
{
	const EUmbrellaEventType Watched[] = {
		EUmbrellaEventType::ModeSelected,
		EUmbrellaEventType::PhaseStarted,
		EUmbrellaEventType::CheckpointReached,
		EUmbrellaEventType::CheckpointRetried,
		EUmbrellaEventType::BossPartDestroyed,
		EUmbrellaEventType::EncounterCompleted,
		EUmbrellaEventType::RunCompleted,
		EUmbrellaEventType::XPAwarded,
		EUmbrellaEventType::ProjectileSpawned,
		EUmbrellaEventType::PlayerHealthChanged,
	};
}

bool UStorySubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
	const UWorld* World = Cast<UWorld>(Outer);
	return World && World->IsGameWorld() && Super::ShouldCreateSubsystem(Outer);
}

TStatId UStorySubsystem::GetStatId() const
{
	RETURN_QUICK_DECLARE_CYCLE_STAT(UStorySubsystem, STATGROUP_Tickables);
}

FString UStorySubsystem::ProgressPath()
{
	return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("Story"), TEXT("StoryProgress.txt"));
}

FStoryProgress UStorySubsystem::LoadProgress(const FString& Path)
{
	FString Text;
	return FFileHelper::LoadFileToString(Text, *Path) ? FStoryProgress::FromText(Text) : FStoryProgress();
}

void UStorySubsystem::SaveProgress(const FString& Path, const FStoryProgress& Progress)
{
	FFileHelper::SaveStringToFile(Progress.ToText(), *Path);
}

void UStorySubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Collection.InitializeDependency<UUmbrellaEventBus>();
	Super::Initialize(Collection);

	// The staged table wins; the compiled copy is used when the file is not staged (a test keeps them equal).
	FString TableText;
	const FString TablePath = FPaths::Combine(FPaths::ProjectContentDir(), TEXT("UmbrellaElla/UI/Story/StoryCues.tsv"));
	if (!FFileHelper::LoadFileToString(TableText, *TablePath))
	{
		TableText = StoryCueTable::DefaultText();
	}
	Model.SetCues(StoryCueTable::Parse(TableText));
	Model.SetProgress(LoadProgress(ProgressPath()));
}

void UStorySubsystem::PostInitialize()
{
	Super::PostInitialize();
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		for (const EUmbrellaEventType Type : Watched)
		{
			Handles.Emplace(Type, Bus->On(Type).AddUObject(this, &UStorySubsystem::HandleEvent));
		}
	}
}

void UStorySubsystem::Deinitialize()
{
	if (Statistics)
	{
		Statistics->GetTryAgainDelegate().RemoveAll(this);
		Statistics->GetMainMenuDelegate().RemoveAll(this);
	}
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		for (const TPair<EUmbrellaEventType, FDelegateHandle>& Entry : Handles)
		{
			Bus->On(Entry.Key).Remove(Entry.Value);
		}
	}
	Handles.Reset();
	Super::Deinitialize();
}

void UStorySubsystem::HandleEvent(const FUmbrellaEvent& Event)
{
	if (Event.Type == EUmbrellaEventType::ModeSelected)
	{
		bStatisticsShown = false;
		if (Statistics)
		{
			Statistics->RemoveFromParent();
		}
	}
	Model.OnEvent(Event);
	Refresh();
}

void UStorySubsystem::ShowDirectorsCutEnding()
{
	if (Model.IsDirectorsCut() && Model.GetEndingStage() == EStoryEndingStage::None)
	{
		FUmbrellaEvent Done;
		Done.Type = EUmbrellaEventType::EncounterCompleted;
		Model.OnEvent(Done);
		Refresh();
	}
}

bool UStorySubsystem::IsSkipPressForStory() const
{
	return Model.IsOpeningShowing() || Model.CanSkipEnding();
}

void UStorySubsystem::HandleSkipPressed()
{
	Model.SkipOpening();
	Model.SkipEnding();
	Refresh();
}

void UStorySubsystem::HandleTryAgain()
{
	TryAgainDelegate.Broadcast();
}

void UStorySubsystem::HandleMainMenu()
{
	MainMenuDelegate.Broadcast();
}

void UStorySubsystem::EnsureWidgets()
{
	APlayerController* Owner = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
	if (!Owner)
	{
		return;
	}
	if (!Caption)
	{
		Caption = CreateWidget<UStoryCaptionWidget>(Owner);
		if (Caption)
		{
			Caption->AddToViewport(FStoryTuning::Get().CaptionZOrder);
		}
	}
}

void UStorySubsystem::Refresh()
{
	if (Model.HasProgressToSave())
	{
		SaveProgress(ProgressPath(), Model.GetProgress());
		Model.MarkProgressSaved();
	}
	EnsureWidgets();
	if (Caption)
	{
		const FStoryCue* Cue = Model.GetActiveCue();
		const EStoryCaptionPlace Place = Model.GetEndingStage() == EStoryEndingStage::StoryText ? EStoryCaptionPlace::Centre : EStoryCaptionPlace::Bottom;
		Caption->SetCaption(Cue ? Cue->Text : FString(), Place);
	}
	if (Model.ShouldShowStatistics() && !bStatisticsShown && IsFeatureEnabled(EFeatureId::FLOW_49))
	{
		APlayerController* Owner = GetWorld() ? GetWorld()->GetFirstPlayerController() : nullptr;
		Statistics = Owner ? CreateWidget<UJourneyCompleteWidget>(Owner) : nullptr;
		if (Statistics)
		{
			Statistics->SetStats(Model.GetStats());
			Statistics->GetTryAgainDelegate().AddUObject(this, &UStorySubsystem::HandleTryAgain);
			Statistics->GetMainMenuDelegate().AddUObject(this, &UStorySubsystem::HandleMainMenu);
			Statistics->AddToViewport(FStoryTuning::Get().StatisticsZOrder);
			bStatisticsShown = true;
		}
	}
}

void UStorySubsystem::Tick(float DeltaTime)
{
	if (!Model.IsDirectorsCut())
	{
		return;
	}
	if (const APlayerController* Owner = GetWorld()->GetFirstPlayerController())
	{
		if (const APawn* Pawn = Owner->GetPawn())
		{
			Model.SampleLocation(Pawn->GetActorLocation());
		}
	}
	Model.Advance(DeltaTime);
	Refresh();
}
