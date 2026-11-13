#include "Misc/AutomationTest.h"
#include "Smoke/AgentPlayRules.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAgentPlayKeysAreDefaultControls, "UmbrellaElla.Smoke.AgentPlay.OnlyDefaultControlsResolve",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FAgentPlayKeysAreDefaultControls::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("space"), AgentPlayRules::ResolveKeyName(TEXT("Space")), FName(TEXT("SpaceBar")));
	TestEqual(TEXT("J"), AgentPlayRules::ResolveKeyName(TEXT("j")), FName(TEXT("J")));
	TestEqual(TEXT("1"), AgentPlayRules::ResolveKeyName(TEXT("1")), FName(TEXT("One")));
	TestEqual(TEXT("left mouse"), AgentPlayRules::ResolveKeyName(TEXT("LeftMouse")), FName(TEXT("LeftMouseButton")));
	// Nothing outside the default controls: no console, no function keys, no escape.
	for (const TCHAR* Word : {TEXT("Tilde"), TEXT("F1"), TEXT("Escape"), TEXT("Enter"), TEXT("Gamepad_FaceButton_Bottom"), TEXT("")})
	{
		TestTrue(FString::Printf(TEXT("%s refused"), Word), AgentPlayRules::ResolveKeyName(Word).IsNone());
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAgentPlayTurnSchedule, "UmbrellaElla.Smoke.AgentPlay.TurnScriptSchedulesKeyEvents",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FAgentPlayTurnSchedule::RunTest(const FString& Parameters)
{
	const AgentPlayRules::FTurn Turn = AgentPlayRules::ParseTurn(TEXT("hold D 600\ntap J\nwait 300\n# note\ndown K\nwait 200\nup K\n"));
	TestTrue(TEXT("valid"), Turn.IsValid());
	// D down 0, J down 0, J up 80, D up 600, K down 300, K up 500.
	TestEqual(TEXT("event count"), Turn.Events.Num(), 6);
	TestEqual(TEXT("turn lasts to the last event"), Turn.DurationMillis, 600);
	if (Turn.Events.Num() == 6)
	{
		TestEqual(TEXT("first at zero"), Turn.Events[0].Millis, 0);
		TestEqual(TEXT("sorted"), Turn.Events[5].Millis, 600);
		TestFalse(TEXT("last is a release"), Turn.Events[5].bPressed);
		TestEqual(TEXT("tap releases after the tap time"), Turn.Events[2].Millis, AgentPlayRules::TapMillis);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAgentPlayTurnRefusals, "UmbrellaElla.Smoke.AgentPlay.BadTurnsAreRefusedWhole",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FAgentPlayTurnRefusals::RunTest(const FString& Parameters)
{
	TestFalse(TEXT("console key"), AgentPlayRules::ParseTurn(TEXT("tap Tilde")).IsValid());
	TestFalse(TEXT("unknown verb"), AgentPlayRules::ParseTurn(TEXT("teleport 100 200")).IsValid());
	TestFalse(TEXT("negative wait"), AgentPlayRules::ParseTurn(TEXT("wait -5")).IsValid());
	TestFalse(TEXT("long wait"), AgentPlayRules::ParseTurn(TEXT("wait 3001")).IsValid());
	TestFalse(TEXT("long turn"), AgentPlayRules::ParseTurn(TEXT("wait 2000\nwait 2000")).IsValid());
	TestFalse(TEXT("hold without time"), AgentPlayRules::ParseTurn(TEXT("hold J")).IsValid());
	FString Many;
	for (int32 Index = 0; Index <= AgentPlayRules::MaxLines; ++Index)
	{
		Many += TEXT("tap J\n");
	}
	TestFalse(TEXT("too many lines"), AgentPlayRules::ParseTurn(Many).IsValid());
	TestTrue(TEXT("empty turn is a short wait"), AgentPlayRules::ParseTurn(TEXT("")).IsValid());
	TestEqual(TEXT("empty turn length"), AgentPlayRules::ParseTurn(TEXT("")).DurationMillis, 100);
	// A refused script keeps its good lines out of play: the caller must check IsValid before it runs anything.
	const AgentPlayRules::FTurn Mixed = AgentPlayRules::ParseTurn(TEXT("tap J\ntap Tilde"));
	TestFalse(TEXT("mixed refused"), Mixed.IsValid());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAgentPlayReleaseBeforePress, "UmbrellaElla.Smoke.AgentPlay.TwoTapsPressTwice",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FAgentPlayReleaseBeforePress::RunTest(const FString& Parameters)
{
	const int32 Gap = AgentPlayRules::TapMillis;
	const AgentPlayRules::FTurn Turn = AgentPlayRules::ParseTurn(FString::Printf(TEXT("tap J\nwait %d\ntap J"), Gap));
	TestEqual(TEXT("four events"), Turn.Events.Num(), 4);
	if (Turn.Events.Num() == 4)
	{
		// Release (80) sorts before the second press (80).
		TestFalse(TEXT("release first"), Turn.Events[1].bPressed);
		TestTrue(TEXT("then press"), Turn.Events[2].bPressed);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAgentPlayFilesAndFrames, "UmbrellaElla.Smoke.AgentPlay.FileNamesAndFrameTiming",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FAgentPlayFilesAndFrames::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("turn file"), AgentPlayRules::TurnFileName(7), FString(TEXT("turn_0007.txt")));
	TestEqual(TEXT("frame file"), AgentPlayRules::FrameFileName(12), FString(TEXT("f000012.jpg")));
	TestFalse(TEXT("frame not due"), AgentPlayRules::IsFrameDue(0.10, 0.15));
	TestTrue(TEXT("frame due"), AgentPlayRules::IsFrameDue(0.15, 0.15));
	TestEqual(TEXT("idle share"), AgentPlayRules::IdleShare(5.0f, 10.0f), 0.5f, 0.001f);
	TestEqual(TEXT("idle share with no time"), AgentPlayRules::IdleShare(0.0f, 0.0f), 1.0f, 0.001f);
	return true;
}

#endif
