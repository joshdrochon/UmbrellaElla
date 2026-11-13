#include "Misc/AutomationTest.h"
#include "Core/UmbrellaTuning.h"
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
	using EStep = USmokeHookSubsystem::EInputStep;
	const float ShotDelay = GetDefault<UUmbrellaTuning>()->Flow.SmokeShotDelaySeconds;
	const float Gap = USmokeHookSubsystem::InputGapSeconds;
	const float Hold = USmokeHookSubsystem::InputHoldSeconds;

	TestEqual(TEXT("idle waits for the shot delay"), static_cast<int32>(USmokeHookSubsystem::NextInputStep(EStep::Idle, 0.0, ShotDelay, ShotDelay, true, true)), static_cast<int32>(EStep::Idle));
	TestEqual(TEXT("no player map goes straight to done"), static_cast<int32>(USmokeHookSubsystem::NextInputStep(EStep::Idle, 0.0, ShotDelay + Gap, ShotDelay, false, true)), static_cast<int32>(EStep::Done));

	// Walk the machine in 0.1 s ticks: it must reach Done, and before the default 15 s quit.
	EStep Step = EStep::Idle;
	double Since = 0.0;
	double InStep = 0.0;
	const double Tick = 0.1;
	while (Step != EStep::Done && Since < 60.0)
	{
		const EStep Next = USmokeHookSubsystem::NextInputStep(Step, InStep, Since, ShotDelay, true, true);
		Since += Tick;
		InStep = Next == Step ? InStep + Tick : 0.0;
		Step = Next;
	}
	TestEqual(TEXT("input check reaches done"), static_cast<int32>(Step), static_cast<int32>(EStep::Done));
	TestTrue(TEXT("input check ends before 15 s"), Since < 15.0);
	TestTrue(TEXT("input check takes at least the shot delay and its holds"), Since >= ShotDelay + Gap + Hold * 3.0f + Gap * 2.0f - 0.5);
	return true;
}

#endif
