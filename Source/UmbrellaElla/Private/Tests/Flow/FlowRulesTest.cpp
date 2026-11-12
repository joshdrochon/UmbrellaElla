#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Flow/FlowRules.h"
#include "Smoke/SmokeHookSubsystem.h"
#include "Story/FlowStoryText.h"

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowStartTest, "UmbrellaElla.Flow.TitleStartsPlaying",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowStartTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("start from title"), FFlowRules::Next(EFlowScreen::Title, EFlowCommand::StartMode), EFlowScreen::Playing);
	TestEqual(TEXT("pause is ignored on the title"), FFlowRules::Next(EFlowScreen::Title, EFlowCommand::Pause), EFlowScreen::Title);
	TestFalse(TEXT("title blocks gameplay input"), !FFlowRules::IsInputBlockedOn(EFlowScreen::Title));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowPauseTest, "UmbrellaElla.Flow.PauseCycle",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowPauseTest::RunTest(const FString& Parameters)
{
	EFlowScreen Screen = FFlowRules::Next(EFlowScreen::Playing, EFlowCommand::Pause);
	TestEqual(TEXT("pause opens the menu"), Screen, EFlowScreen::Paused);
	TestTrue(TEXT("paused blocks gameplay input"), FFlowRules::IsInputBlockedOn(Screen));
	TestTrue(TEXT("paused freezes the world"), FFlowRules::IsWorldPausedOn(Screen));

	Screen = FFlowRules::Next(Screen, EFlowCommand::OpenSettings);
	TestEqual(TEXT("settings page"), Screen, EFlowScreen::Settings);
	Screen = FFlowRules::Next(Screen, EFlowCommand::Back);
	TestEqual(TEXT("back to pause"), Screen, EFlowScreen::Paused);

	Screen = FFlowRules::Next(Screen, EFlowCommand::Continue);
	TestEqual(TEXT("continue waits for neutral input"), Screen, EFlowScreen::Resuming);
	TestTrue(TEXT("resume wait still blocks gameplay input"), FFlowRules::IsInputBlockedOn(Screen));
	Screen = FFlowRules::Next(Screen, EFlowCommand::NeutralReached);
	TestEqual(TEXT("neutral hands control back"), Screen, EFlowScreen::Playing);
	TestFalse(TEXT("playing does not block gameplay input"), FFlowRules::IsInputBlockedOn(Screen));
	TestFalse(TEXT("playing does not freeze the world"), FFlowRules::IsWorldPausedOn(Screen));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowDefeatTest, "UmbrellaElla.Flow.DefeatIsNotTheWin",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowDefeatTest::RunTest(const FString& Parameters)
{
	const EFlowScreen Defeat = FFlowRules::Next(EFlowScreen::Playing, EFlowCommand::PlayerDefeated);
	TestEqual(TEXT("death shows the retry screen"), Defeat, EFlowScreen::Defeat);
	TestEqual(TEXT("the win ending never plays on death"), FFlowRules::Next(Defeat, EFlowCommand::EncounterCompleted), EFlowScreen::Defeat);
	TestEqual(TEXT("retry waits for neutral input"), FFlowRules::Next(Defeat, EFlowCommand::Retry), EFlowScreen::Resuming);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowWinTest, "UmbrellaElla.Flow.WinStoryThenCredits",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowWinTest::RunTest(const FString& Parameters)
{
	EFlowScreen Screen = FFlowRules::Next(EFlowScreen::Playing, EFlowCommand::EncounterCompleted);
	TestEqual(TEXT("the win shows story first"), Screen, EFlowScreen::Story);
	TestEqual(TEXT("credits only after the story"), FFlowRules::Next(Screen, EFlowCommand::TimelineDone), EFlowScreen::Credits);
	Screen = FFlowRules::Next(EFlowScreen::Credits, EFlowCommand::TimelineDone);
	TestEqual(TEXT("credits end at the title"), Screen, EFlowScreen::Title);
	TestTrue(TEXT("story shows the moving background"), FFlowRules::IsBackgroundShownOn(EFlowScreen::Story));
	TestTrue(TEXT("title shows the moving background"), FFlowRules::IsBackgroundShownOn(EFlowScreen::Title));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowTimelineTest, "UmbrellaElla.Flow.TimelinesAndNeutral",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowTimelineTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("page 0 at start"), FFlowRules::StoryPageAt(0.0f, 8.0f, 2), 0);
	TestEqual(TEXT("page 1 after one page"), FFlowRules::StoryPageAt(8.5f, 8.0f, 2), 1);
	TestEqual(TEXT("story over after the last page"), FFlowRules::StoryPageAt(16.0f, 8.0f, 2), static_cast<int32>(INDEX_NONE));
	TestTrue(TEXT("timeline done at its duration"), FFlowRules::IsTimelineDone(24.0f, 24.0f));
	TestFalse(TEXT("timeline not done before"), FFlowRules::IsTimelineDone(23.0f, 24.0f));
	TestEqual(TEXT("neutral grows while released"), FFlowRules::AdvanceNeutral(0.1f, 0.1f, false), 0.2f);
	TestEqual(TEXT("neutral resets on a held key"), FFlowRules::AdvanceNeutral(0.1f, 0.1f, true), 0.0f);
	TestTrue(TEXT("ending story has text"), FFlowStoryText::GetEndingPages().Num() > 0);
	bool bHasRole = false;
	bool bHasProducer = false;
	for (const FText& Line : FFlowStoryText::GetCreditsLines())
	{
		bHasRole |= Line.ToString() == TEXT("[ROLE - Josh to supply]");
		bHasProducer |= Line.ToString() == TEXT("[EXECUTIVE PRODUCER NAME - Josh to supply]");
	}
	TestTrue(TEXT("credits carry the role placeholder"), bHasRole);
	TestTrue(TEXT("credits carry the executive producer placeholder"), bHasProducer);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowSmokeFpsTest, "UmbrellaElla.Flow.SmokeLowFps",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowSmokeFpsTest::RunTest(const FString& Parameters)
{
	TArray<float> Frames;
	Frames.Init(0.01f, 99);
	Frames.Add(0.05f);
	TestEqual(TEXT("1% low reads the slowest frame"), USmokeHookSubsystem::ComputeLowFps(Frames, 0.01f), 20.0f);
	TestEqual(TEXT("no frames reads zero"), USmokeHookSubsystem::ComputeLowFps(TArray<float>(), 0.01f), 0.0f);
	return true;
}

#endif
