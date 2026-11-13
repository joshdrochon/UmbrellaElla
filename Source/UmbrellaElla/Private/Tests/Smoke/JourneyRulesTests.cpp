#include "Misc/AutomationTest.h"
#include "Smoke/JourneyHookSubsystem.h"
#include "Flow/FlowRules.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJourneyParsesScript, "UmbrellaElla.Smoke.Journey.ParsesScript",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FJourneyParsesScript::RunTest(const FString& Parameters)
{
	TArray<FString> Errors;
	const TArray<FJourneyStep> Steps = JourneyRules::ParseScript(
		TEXT("# lose path\nwait Title 30\nclick Start Game\n\nhits Defeat 3 1.5 60   # assisted\nkey Enter\nfly away\n"), Errors);
	TestEqual(TEXT("steps"), Steps.Num(), 4);
	TestEqual(TEXT("one error"), Errors.Num(), 1);
	TestTrue(TEXT("error names its line"), Errors.Num() == 1 && Errors[0].Contains(TEXT("line 7")));
	if (Steps.Num() == 4)
	{
		TestEqual(TEXT("wait arg"), Steps[0].Arg, FString(TEXT("Title")));
		TestEqual(TEXT("wait timeout"), Steps[0].Numbers.Num() == 1 ? Steps[0].Numbers[0] : -1.0f, 30.0f);
		TestEqual(TEXT("click label keeps its spaces"), Steps[1].Arg, FString(TEXT("Start Game")));
		TestEqual(TEXT("hits numbers"), Steps[2].Numbers.Num(), 3);
		TestEqual(TEXT("hits interval"), Steps[2].Numbers.Num() == 3 ? Steps[2].Numbers[1] : -1.0f, 1.5f);
		TestEqual(TEXT("line number"), Steps[3].Line, 6);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJourneyNamesScreens, "UmbrellaElla.Smoke.Journey.NamesScreensAndLabels",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FJourneyNamesScreens::RunTest(const FString& Parameters)
{
	uint8 Screen = 0;
	TestTrue(TEXT("defeat"), JourneyRules::HasScreenNamed(TEXT("defeat"), Screen));
	TestEqual(TEXT("defeat value"), Screen, static_cast<uint8>(EFlowScreen::Defeat));
	TestEqual(TEXT("name back"), JourneyRules::ScreenName(static_cast<uint8>(EFlowScreen::Credits)), FString(TEXT("Credits")));
	TestFalse(TEXT("unknown"), JourneyRules::HasScreenNamed(TEXT("Lobby"), Screen));
	TestTrue(TEXT("label case"), JourneyRules::IsLabelMatch(TEXT(" START GAME "), TEXT("Start Game")));
	TestFalse(TEXT("other label"), JourneyRules::IsLabelMatch(TEXT("Start Director's Cut"), TEXT("Start Game")));
	TestFalse(TEXT("empty wanted"), JourneyRules::IsLabelMatch(TEXT(""), TEXT(" ")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FJourneyParsesRouteSteps, "UmbrellaElla.Smoke.Journey.ParsesRouteSteps",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FJourneyParsesRouteSteps::RunTest(const FString& Parameters)
{
	// The Director's Cut journey: real-key route walk with trim, the named checkpoint assist, the purchase-screen skip.
	TArray<FString> Errors;
	const TArray<FJourneyStep> Steps = JourneyRules::ParseScript(TEXT("route 2 60 1\nrouteassist 4\nskipunless Purchase 5\n"), Errors);
	TestEqual(TEXT("no errors"), Errors.Num(), 0);
	if (TestEqual(TEXT("steps"), Steps.Num(), 3))
	{
		TestEqual(TEXT("route numbers"), Steps[0].Numbers.Num(), 3);
		TestTrue(TEXT("route arg empty"), Steps[0].Arg.IsEmpty());
		TestEqual(TEXT("routeassist checkpoint"), Steps[1].Numbers.Num() == 1 ? Steps[1].Numbers[0] : -1.0f, 4.0f);
		TestEqual(TEXT("skipunless screen"), Steps[2].Arg, FString(TEXT("Purchase")));
		TestEqual(TEXT("skipunless count"), Steps[2].Numbers.Num() == 1 ? Steps[2].Numbers[0] : -1.0f, 5.0f);
	}
	return true;
}

#endif
