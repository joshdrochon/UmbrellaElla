#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Engine/World.h"
#include "Misc/AutomationTest.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Story/StoryRules.h"
#include "Story/StorySubsystem.h"

#if WITH_AUTOMATION_TESTS

#define UMBRELLAELLA_STORY_TEST_FLAGS (EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

namespace
{
	FUmbrellaEvent Make(EUmbrellaEventType Type, const TCHAR* Detail = TEXT(""), int32 Amount = 0, float Value = 0.0f)
	{
		FUmbrellaEvent Event;
		Event.Type = Type;
		Event.Detail = FName(Detail);
		Event.Amount = Amount;
		Event.Value = Value;
		return Event;
	}

	FStoryModel NewModel()
	{
		FStoryModel Model;
		Model.SetCues(StoryCueTable::Parse(StoryCueTable::DefaultText()));
		return Model;
	}

	void Run(FStoryModel& Model, float Seconds)
	{
		const float Step = 0.1f;
		for (float Elapsed = 0.0f; Elapsed < Seconds; Elapsed += Step)
		{
			Model.Advance(Step);
		}
	}

	FString ActiveText(const FStoryModel& Model)
	{
		const FStoryCue* Cue = Model.GetActiveCue();
		return Cue ? Cue->Text : FString();
	}

	const TCHAR* DirectorsCut = TEXT("DirectorsCut");
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStoryCueTableTest, "UmbrellaElla.Story.CueTable", UMBRELLAELLA_STORY_TEST_FLAGS)

bool FStoryCueTableTest::RunTest(const FString& Parameters)
{
	const TArray<FStoryCue> Cues = StoryCueTable::Parse(StoryCueTable::DefaultText());
	TestEqual(TEXT("seven cues"), Cues.Num(), 7);
	TestEqual(TEXT("opening text"), Cues[0].Text, FString(TEXT("Mother: Keep it open, Ella. It'll protect you from the owl.")));
	FString OnDisk;
	const FString Path = FPaths::Combine(FPaths::ProjectContentDir(), TEXT("UmbrellaElla/UI/Story/StoryCues.tsv"));
	if (FFileHelper::LoadFileToString(OnDisk, *Path))
	{
		const TArray<FStoryCue> FromFile = StoryCueTable::Parse(OnDisk);
		bool bSame = FromFile.Num() == Cues.Num();
		for (int32 Index = 0; bSame && Index < Cues.Num(); ++Index)
		{
			bSame = FromFile[Index].Id == Cues[Index].Id && FromFile[Index].Text == Cues[Index].Text
				&& FromFile[Index].Trigger == Cues[Index].Trigger;
		}
		TestTrue(TEXT("file and compiled copy agree"), bSame);
	}
	TestEqual(TEXT("bad row skipped"), StoryCueTable::Parse(TEXT("only\ttwo")).Num(), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStoryOpeningTest, "UmbrellaElla.Story.OpeningOncePerRun", UMBRELLAELLA_STORY_TEST_FLAGS)

bool FStoryOpeningTest::RunTest(const FString& Parameters)
{
	FStoryModel Model = NewModel();
	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	Model.Advance(0.1f);
	TestTrue(TEXT("mother caption shows"), ActiveText(Model).StartsWith(TEXT("Mother: Keep it open")));
	Run(Model, 3.0f);
	TestTrue(TEXT("still showing at 3 s"), Model.GetActiveCue() != nullptr);
	Run(Model, 1.5f);
	TestEqual(TEXT("cleared after about four seconds"), ActiveText(Model), FString());
	TestEqual(TEXT("shown once"), Model.CountShown(FName(TEXT("OpeningMother"))), 1);
	Model.OnEvent(Make(EUmbrellaEventType::CheckpointRetried, TEXT("wings")));
	Run(Model, 10.0f);
	TestEqual(TEXT("retry does not replay it"), Model.CountShown(FName(TEXT("OpeningMother"))), 1);
	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	Run(Model, 0.2f);
	TestEqual(TEXT("a new run shows it once"), Model.CountShown(FName(TEXT("OpeningMother"))), 1);
	TestTrue(TEXT("and it is on screen"), ActiveText(Model).StartsWith(TEXT("Mother: Keep it open")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStoryLateModeTest, "UmbrellaElla.Story.LateModeSelectedShowsOpeningOnce", UMBRELLAELLA_STORY_TEST_FLAGS)

bool FStoryLateModeTest::RunTest(const FString& Parameters)
{
	FStoryModel Model = NewModel();
	Model.BeginNewRun(EUmbrellaPlayMode::DirectorsCut);
	Run(Model, 0.2f);
	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	Run(Model, 0.2f);
	TestEqual(TEXT("late ModeSelected does not replay"), Model.CountShown(FName(TEXT("OpeningMother"))), 1);
	Run(Model, 5.0f);
	TestEqual(TEXT("still once"), Model.CountShown(FName(TEXT("OpeningMother"))), 1);
	FStoryModel Only = NewModel();
	Only.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	Run(Only, 0.2f);
	TestEqual(TEXT("ModeSelected alone starts the run"), Only.CountShown(FName(TEXT("OpeningMother"))), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStoryWingsClueTest, "UmbrellaElla.Story.ClueOnPhaseStartedWings", UMBRELLAELLA_STORY_TEST_FLAGS)

bool FStoryWingsClueTest::RunTest(const FString& Parameters)
{
	FStoryModel Model = NewModel();
	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	Run(Model, 12.0f);
	Model.OnEvent(Make(EUmbrellaEventType::PhaseStarted, TEXT("mechanisms")));
	Run(Model, 0.2f);
	TestEqual(TEXT("mechanisms does not show it"), Model.CountShown(FName(TEXT("KeeperArrival"))), 0);
	Model.OnEvent(Make(EUmbrellaEventType::PhaseStarted, TEXT("wings")));
	Run(Model, 0.2f);
	TestEqual(TEXT("PhaseStarted wings alone shows the clue"), Model.CountShown(FName(TEXT("KeeperArrival"))), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStoryStartGameTest, "UmbrellaElla.Story.StartGameHasNoStory", UMBRELLAELLA_STORY_TEST_FLAGS)

bool FStoryStartGameTest::RunTest(const FString& Parameters)
{
	FStoryModel Model = NewModel();
	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, TEXT("StartGame")));
	Model.OnEvent(Make(EUmbrellaEventType::PhaseStarted, TEXT("wings")));
	Model.OnEvent(Make(EUmbrellaEventType::EncounterCompleted));
	Run(Model, 20.0f);
	TestTrue(TEXT("no cue"), Model.GetActiveCue() == nullptr);
	TestEqual(TEXT("nothing shown"), Model.GetShownIds().Num(), 0);
	TestTrue(TEXT("no ending"), Model.GetEndingStage() == EStoryEndingStage::None);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStoryInPlayCuesTest, "UmbrellaElla.Story.InPlayCues", UMBRELLAELLA_STORY_TEST_FLAGS)

bool FStoryInPlayCuesTest::RunTest(const FString& Parameters)
{
	FStoryModel Model = NewModel();
	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	Run(Model, 4.5f);
	Run(Model, 1.5f);
	TestEqual(TEXT("light and umbra line shown once"), Model.CountShown(FName(TEXT("LightShadow"))), 1);
	Run(Model, 6.0f);
	Model.OnEvent(Make(EUmbrellaEventType::PhaseStarted, TEXT("wings")));
	Model.OnEvent(Make(EUmbrellaEventType::CheckpointReached, TEXT("wings")));
	Run(Model, 0.2f);
	TestEqual(TEXT("clock hand clue on arrival"), ActiveText(Model), FString(TEXT("The clock keeps one hand. Beside it is an empty place.")));
	Run(Model, 6.0f);
	Model.OnEvent(Make(EUmbrellaEventType::PhaseStarted, TEXT("wings")));
	Run(Model, 6.0f);
	TestEqual(TEXT("arrival clue once"), Model.CountShown(FName(TEXT("KeeperArrival"))), 1);
	Model.OnEvent(Make(EUmbrellaEventType::BossPartDestroyed, TEXT("wings")));
	Model.OnEvent(Make(EUmbrellaEventType::BossPartDestroyed, TEXT("wings")));
	Run(Model, 12.0f);
	TestEqual(TEXT("shaft clue once"), Model.CountShown(FName(TEXT("ShaftClue"))), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStoryEndingTest, "UmbrellaElla.Story.EndingSequence", UMBRELLAELLA_STORY_TEST_FLAGS)

bool FStoryEndingTest::RunTest(const FString& Parameters)
{
	FStoryModel Model = NewModel();
	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	Run(Model, 1.0f);
	Model.EnterEndingStage(EStoryEndingStage::Credits);
	TestTrue(TEXT("no ending before the win"), Model.GetEndingStage() == EStoryEndingStage::None);
	Model.OnEvent(Make(EUmbrellaEventType::XPAwarded, TEXT(""), 10));
	Model.OnEvent(Make(EUmbrellaEventType::EncounterCompleted));
	TestTrue(TEXT("hold first"), Model.GetEndingStage() == EStoryEndingStage::Hold);
	TestTrue(TEXT("in-play caption cleared by the win"), Model.GetActiveCue() == nullptr);
	Run(Model, 20.0f);
	TestTrue(TEXT("story keeps no ending clock of its own: still holding"), Model.GetEndingStage() == EStoryEndingStage::Hold);
	Model.OnEvent(Make(EUmbrellaEventType::XPAwarded, TEXT(""), 50));
	Model.OnEvent(Make(EUmbrellaEventType::ProjectileSpawned, TEXT("EnemyRed")));
	TestEqual(TEXT("nothing counted after the win"), Model.GetStats().XpEarned, 10);
	TestEqual(TEXT("no shot counted after the win"), Model.GetStats().ShotsFiredAtYou, 0);

	const TArray<FString> Lines = Model.GetEndingLines();
	TestEqual(TEXT("three ending lines"), Lines.Num(), 3);
	TestTrue(TEXT("first ending line"), Lines.Num() > 0 && Lines[0].Contains(TEXT("pursuit ends")));

	Model.EnterEndingStage(EStoryEndingStage::StoryText);
	TestTrue(TEXT("flow moves it to the story text"), Model.GetEndingStage() == EStoryEndingStage::StoryText);
	TestTrue(TEXT("ending lines are flow's pages, not a caption"), Model.GetActiveCue() == nullptr);
	Model.EnterEndingStage(EStoryEndingStage::Hold);
	TestTrue(TEXT("forward only"), Model.GetEndingStage() == EStoryEndingStage::StoryText);
	Model.EnterEndingStage(EStoryEndingStage::Credits);
	TestTrue(TEXT("credits after the story"), Model.GetEndingStage() == EStoryEndingStage::Credits);
	TestTrue(TEXT("no statistics during credits"), !Model.ShouldShowStatistics());
	Model.EnterEndingStage(EStoryEndingStage::Statistics);
	TestTrue(TEXT("statistics after the credits"), Model.ShouldShowStatistics());
	TestTrue(TEXT("first win saved"), Model.GetProgress().bFirstWinSeen);
	TestTrue(TEXT("first win flag is a save request"), Model.HasProgressToSave());

	FStoryModel StartGame = NewModel();
	StartGame.OnEvent(Make(EUmbrellaEventType::ModeSelected, TEXT("StartGame")));
	StartGame.OnEvent(Make(EUmbrellaEventType::EncounterCompleted));
	StartGame.EnterEndingStage(EStoryEndingStage::Statistics);
	TestFalse(TEXT("Start Game never reaches statistics"), StartGame.ShouldShowStatistics());
	TestFalse(TEXT("Start Game win sets no flag"), StartGame.GetProgress().bFirstWinSeen);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStoryLightShaftTest, "UmbrellaElla.Story.LightShaftTrigger", UMBRELLAELLA_STORY_TEST_FLAGS)

bool FStoryLightShaftTest::RunTest(const FString& Parameters)
{
	FStoryModel Model = NewModel();
	TestFalse(TEXT("off before a run"), Model.IsLightShaftOn());
	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, TEXT("StartGame")));
	TestFalse(TEXT("off in Start Game"), Model.IsLightShaftOn());
	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	TestTrue(TEXT("on in Director's Cut play"), Model.IsLightShaftOn());
	Model.OnEvent(Make(EUmbrellaEventType::EncounterCompleted));
	TestTrue(TEXT("still on during the hold on Ella (light still falls)"), Model.IsLightShaftOn());
	Model.EnterEndingStage(EStoryEndingStage::StoryText);
	TestFalse(TEXT("off once the ending background shows"), Model.IsLightShaftOn());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStorySkipTest, "UmbrellaElla.Story.SkipRules", UMBRELLAELLA_STORY_TEST_FLAGS)

bool FStorySkipTest::RunTest(const FString& Parameters)
{
	FStoryModel Model = NewModel();
	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	Model.Advance(0.1f);
	TestTrue(TEXT("opening press belongs to the story"), Model.IsOpeningShowing());
	Model.SkipOpening();
	TestTrue(TEXT("first viewing cannot be skipped"), Model.IsOpeningShowing());
	Run(Model, 5.0f);
	TestTrue(TEXT("opening seen is saved"), Model.GetProgress().bOpeningSeen);
	TestFalse(TEXT("ending skip flag untouched"), Model.GetProgress().bFirstWinSeen);

	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	Model.Advance(0.1f);
	Model.SkipOpening();
	TestFalse(TEXT("later start can skip"), Model.IsOpeningShowing());

	Model.OnEvent(Make(EUmbrellaEventType::EncounterCompleted));
	Model.EnterEndingStage(EStoryEndingStage::StoryText);
	TestFalse(TEXT("first win cannot skip"), Model.CanSkipEnding());
	Model.SkipEnding();
	TestFalse(TEXT("still no statistics"), Model.ShouldShowStatistics());

	FStoryProgress Prior;
	Prior.bFirstWinSeen = true;
	FStoryModel Second = NewModel();
	Second.SetProgress(Prior);
	Second.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	Second.OnEvent(Make(EUmbrellaEventType::EncounterCompleted));
	TestFalse(TEXT("no skip during the hold, even after a prior win"), Second.CanSkipEnding());
	Second.EnterEndingStage(EStoryEndingStage::StoryText);
	TestTrue(TEXT("prior win allows skip"), Second.CanSkipEnding());
	Second.SkipEnding();
	TestTrue(TEXT("skip goes to statistics"), Second.ShouldShowStatistics());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStoryStatsTest, "UmbrellaElla.Story.JourneyStatistics", UMBRELLAELLA_STORY_TEST_FLAGS)

bool FStoryStatsTest::RunTest(const FString& Parameters)
{
	FStoryModel Model = NewModel();
	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	Model.OnEvent(Make(EUmbrellaEventType::XPAwarded, TEXT(""), 10));
	Model.OnEvent(Make(EUmbrellaEventType::XPAwarded, TEXT(""), 15));
	Model.OnEvent(Make(EUmbrellaEventType::CheckpointRetried, TEXT("wings")));
	Model.SetHealthBaseline(3.0f, 3);
	for (int32 Shot = 0; Shot < 4; ++Shot)
	{
		// The Detail the projectile service really sends (UmbrellaProjectile.cpp): the enum's own name.
		Model.OnEvent(Make(EUmbrellaEventType::ProjectileSpawned, TEXT("EUmbrellaShotKind::PlayerBlast")));
	}
	Model.OnEvent(Make(EUmbrellaEventType::ProjectileSpawned, TEXT("EUmbrellaShotKind::EnemyRed")));
	Model.OnEvent(Make(EUmbrellaEventType::ProjectileSpawned, TEXT("EUmbrellaShotKind::EnemyYellow")));
	Model.OnEvent(Make(EUmbrellaEventType::PlayerHealthChanged, TEXT(""), 3, 2.0f));
	Model.OnEvent(Make(EUmbrellaEventType::PlayerHealthChanged, TEXT(""), 3, 2.5f));
	Model.SampleLocation(FVector(0.0, 0.0, 0.0));
	Model.SampleLocation(FVector(300.0, 0.0, 0.0));
	Model.SampleLocation(FVector(300.0, 0.0, 400.0));
	Model.SampleLocation(FVector(90000.0, 0.0, 400.0));
	const FStoryRunStats& Stats = Model.GetStats();
	TestEqual(TEXT("enemies"), Stats.EnemiesDefeated, 2);
	TestEqual(TEXT("xp"), Stats.XpEarned, 25);
	TestEqual(TEXT("deaths"), Stats.Deaths, 1);
	TestEqual(TEXT("shots"), Stats.ShotsFired, 4);
	TestEqual(TEXT("shots at you"), Stats.ShotsFiredAtYou, 2);
	TestEqual(TEXT("damage"), Stats.DamageTaken, 1.0f);
	TestEqual(TEXT("restored"), Stats.HealthRestored, 0.5f);
	TestEqual(TEXT("distance, teleport ignored"), Stats.DistanceFlownUnits, 700.0f);

	const TArray<TPair<FString, FString>> Rows = StoryStatsRows(Stats);
	TestEqual(TEXT("eight rows"), Rows.Num(), 8);
	TestEqual(TEXT("row 1 label"), Rows[0].Key, FString(TEXT("Enemies defeated")));
	TestEqual(TEXT("row 2 value"), Rows[1].Value, FString(TEXT("25")));
	TestEqual(TEXT("row 4 metres"), Rows[3].Value, FString(TEXT("7 m")));
	TestEqual(TEXT("row 8 label"), Rows[7].Key, FString(TEXT("Health restored")));

	Model.OnEvent(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
	TestEqual(TEXT("a new run starts from zero"), Model.GetStats().XpEarned, 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStoryProgressTest, "UmbrellaElla.Story.ProgressRoundTrip", UMBRELLAELLA_STORY_TEST_FLAGS)

bool FStoryProgressTest::RunTest(const FString& Parameters)
{
	FStoryProgress Progress;
	Progress.bOpeningSeen = true;
	const FStoryProgress Back = FStoryProgress::FromText(Progress.ToText());
	TestTrue(TEXT("opening kept"), Back.bOpeningSeen);
	TestFalse(TEXT("first win separate"), Back.bFirstWinSeen);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStoryWorldTest, "UmbrellaElla.Story.World.ReactsToBus", UMBRELLAELLA_STORY_TEST_FLAGS)

bool FStoryWorldTest::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World);
	UStorySubsystem* Story = World->GetSubsystem<UStorySubsystem>();
	const bool bOk = TestNotNull(TEXT("bus"), Bus) && TestNotNull(TEXT("story subsystem"), Story);
	if (bOk)
	{
		Bus->Broadcast(Make(EUmbrellaEventType::ModeSelected, DirectorsCut));
		Story->Tick(0.1f);
		const FStoryCue* Cue = Story->GetModel().GetActiveCue();
		TestTrue(TEXT("opening shown from the bus"), Cue && Cue->Text.StartsWith(TEXT("Mother: Keep it open")));
		Bus->Broadcast(Make(EUmbrellaEventType::EncounterCompleted));
		TestTrue(TEXT("ending started from the bus"), Story->GetModel().GetEndingStage() == EStoryEndingStage::Hold);
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return bOk;
}

#endif
