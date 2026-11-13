#include "Misc/AutomationTest.h"
#include "Smoke/PlaytestRun.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSmokePlaytestBandExit, "UmbrellaElla.Smoke.PlaytestBandExitEdge",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FSmokePlaytestBandExit::RunTest(const FString& Parameters)
{
	// The Broken Mill lower ONWARD band: x 600-800, eligible z 210-330.
	const FBox2D Band(FVector2D(600.0, 210.0), FVector2D(800.0, 330.0));
	TestTrue(TEXT("inside"), FPlaytestRun::BandExit(FVector2D(700.0, 270.0), Band) == EPlaytestBandExit::None);
	TestTrue(TEXT("on the edge is inside"), FPlaytestRun::BandExit(FVector2D(800.0, 330.0), Band) == EPlaytestBandExit::None);
	TestTrue(TEXT("carried out the far edge"), FPlaytestRun::BandExit(FVector2D(801.0, 270.0), Band) == EPlaytestBandExit::Right);
	TestTrue(TEXT("rose out of the top"), FPlaytestRun::BandExit(FVector2D(700.0, 331.0), Band) == EPlaytestBandExit::Top);
	TestTrue(TEXT("fell out of the bottom"), FPlaytestRun::BandExit(FVector2D(700.0, 209.0), Band) == EPlaytestBandExit::Bottom);
	TestTrue(TEXT("pushed back left"), FPlaytestRun::BandExit(FVector2D(599.0, 270.0), Band) == EPlaytestBandExit::Left);
	TestTrue(TEXT("corner counts as the far edge"), FPlaytestRun::BandExit(FVector2D(801.0, 331.0), Band) == EPlaytestBandExit::Right);
	TestEqual(TEXT("log word"), FString(FPlaytestRun::BandExitName(EPlaytestBandExit::Top)), FString(TEXT("top")));
	TestEqual(TEXT("log word none"), FString(FPlaytestRun::BandExitName(EPlaytestBandExit::None)), FString(TEXT("none")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSmokePlaytestLines, "UmbrellaElla.Smoke.PlaytestIdleShareAndLineFormat",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FSmokePlaytestLines::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("half idle"), FPlaytestRun::IdleShare(5.0f, 10.0f), 0.5f, 0.001f);
	TestEqual(TEXT("clamped to one"), FPlaytestRun::IdleShare(12.0f, 10.0f), 1.0f, 0.001f);
	TestEqual(TEXT("no time counts as idle"), FPlaytestRun::IdleShare(0.0f, 0.0f), 1.0f, 0.001f);
	TestEqual(TEXT("line format"), FPlaytestRun::FormatLine(TEXT("CAM07"), {{TEXT("a"), TEXT("1")}, {TEXT("b"), TEXT("2.50")}}), FString(TEXT("PLAYTEST_CAM07 a=1 b=2.50")));
	return true;
}

#endif
