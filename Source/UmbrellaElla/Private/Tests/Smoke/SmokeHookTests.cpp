#include "Misc/AutomationTest.h"
#include "Smoke/SmokeHookSubsystem.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSmokeLowFpsMeanOfSlowest, "UmbrellaElla.Smoke.LowFpsIsMeanOfSlowestShare",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FSmokeLowFpsMeanOfSlowest::RunTest(const FString& Parameters)
{
	TArray<float> Frames;
	for (int32 Index = 0; Index < 99; ++Index)
	{
		Frames.Add(0.01f);
	}
	Frames.Add(0.1f);
	// The slowest 1% of 100 frames is the one 100 ms frame: 10 fps.
	TestEqual(TEXT("1% low is the slowest frame"), USmokeHookSubsystem::ComputeLowFps(Frames, 0.01f), 10.0f, 0.01f);
	TestEqual(TEXT("no frames reads zero"), USmokeHookSubsystem::ComputeLowFps(TArray<float>(), 0.01f), 0.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSmokeInputTimeline, "UmbrellaElla.Smoke.InputCheckFitsBeforeQuit",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FSmokeInputTimeline::RunTest(const FString& Parameters)
{
	// Key hold + gap + pad hold + dash window + gap must end inside the 15 s default quit with the 5 s shot delay.
	const float Total = 5.0f + USmokeHookSubsystem::InputGapSeconds * 3.0f + USmokeHookSubsystem::InputHoldSeconds * 3.0f;
	TestTrue(TEXT("input check ends before 15 s"), Total < 15.0f);
	return true;
}

#endif
