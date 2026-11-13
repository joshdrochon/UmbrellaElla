#include "Misc/AutomationTest.h"
#include "Core/UmbrellaTuning.h"
#include "Smoke/SmokeHookSubsystem.h"
#include "Enemy/EnemyTypes.h"

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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSmokeShotFrameCount, "UmbrellaElla.Smoke.ShotWaitsForRenderedFrames",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FSmokeShotFrameCount::RunTest(const FString& Parameters)
{
	TestFalse(TEXT("level not ready: no shot however many frames"), USmokeHookSubsystem::IsShotDue(false, 1000, 60));
	TestFalse(TEXT("59 frames is early"), USmokeHookSubsystem::IsShotDue(true, 59, 60));
	TestTrue(TEXT("60 frames is due"), USmokeHookSubsystem::IsShotDue(true, 60, 60));
	TestEqual(TEXT("default frames"), USmokeHookSubsystem::ResolveShotFrames(0), USmokeHookSubsystem::DefaultShotFrames);
	TestEqual(TEXT("negative falls back"), USmokeHookSubsystem::ResolveShotFrames(-3), USmokeHookSubsystem::DefaultShotFrames);
	TestEqual(TEXT("explicit N wins"), USmokeHookSubsystem::ResolveShotFrames(7), 7);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSmokeShotReadiness, "UmbrellaElla.Smoke.ShotWaitsForShadersTexturesAndPlayer",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FSmokeShotReadiness::RunTest(const FString& Parameters)
{
	TestTrue(TEXT("all settled and Ella alive"), USmokeHookSubsystem::IsShotReady(0, 0, 0, true));
	TestFalse(TEXT("shader jobs pending"), USmokeHookSubsystem::IsShotReady(3, 0, 0, true));
	TestFalse(TEXT("textures still streaming (Preparing Textures)"), USmokeHookSubsystem::IsShotReady(0, 12, 0, true));
	TestFalse(TEXT("assets still compiling"), USmokeHookSubsystem::IsShotReady(0, 0, 1, true));
	TestFalse(TEXT("no live player"), USmokeHookSubsystem::IsShotReady(0, 0, 0, false));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSmokeViewPixelInFrame, "UmbrellaElla.Smoke.ViewPixelInFrame",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FSmokeViewPixelInFrame::RunTest(const FString& Parameters)
{
	const FVector2D SmokeViewSize(1280.0, 720.0);
	TestTrue(TEXT("centre is in frame"), USmokeHookSubsystem::IsPixelInFrame(true, FVector2D(640.0, 360.0), SmokeViewSize));
	TestTrue(TEXT("top-left corner is in frame"), USmokeHookSubsystem::IsPixelInFrame(true, FVector2D(0.0, 0.0), SmokeViewSize));
	TestFalse(TEXT("right edge is outside"), USmokeHookSubsystem::IsPixelInFrame(true, FVector2D(1280.0, 10.0), SmokeViewSize));
	TestFalse(TEXT("below the frame"), USmokeHookSubsystem::IsPixelInFrame(true, FVector2D(10.0, 900.0), SmokeViewSize));
	TestFalse(TEXT("left of the frame"), USmokeHookSubsystem::IsPixelInFrame(true, FVector2D(-5.0, 10.0), SmokeViewSize));
	TestFalse(TEXT("projection failed (behind the camera)"), USmokeHookSubsystem::IsPixelInFrame(false, FVector2D(640.0, 360.0), SmokeViewSize));
	TestFalse(TEXT("no viewport"), USmokeHookSubsystem::IsPixelInFrame(true, FVector2D(0.0, 0.0), FVector2D::ZeroVector));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSmokeShotPathAndSwitches, "UmbrellaElla.Smoke.ShotPathAndSceneSwitches",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FSmokeShotPathAndSwitches::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("relative path resolves against the project"), USmokeHookSubsystem::ResolveShotPath(TEXT("pipeline/a.png"), TEXT("/proj/")), FString(TEXT("/proj/pipeline/a.png")));
	TestEqual(TEXT("absolute path stays"), USmokeHookSubsystem::ResolveShotPath(TEXT("/tmp/a.png"), TEXT("/proj/")), FString(TEXT("/tmp/a.png")));
	EEnemyType Type = EEnemyType::Roadwarden;
	TestTrue(TEXT("floodstrider parses"), USmokeHookSubsystem::HasEnemyFamilyName(TEXT("floodstrider"), Type));
	TestEqual(TEXT("floodstrider type"), static_cast<int32>(Type), static_cast<int32>(EEnemyType::Floodstrider));
	TestTrue(TEXT("sky courier parses"), USmokeHookSubsystem::HasEnemyFamilyName(TEXT("SkyCourier"), Type));
	TestEqual(TEXT("sky courier type"), static_cast<int32>(Type), static_cast<int32>(EEnemyType::SkyCourier));
	TestFalse(TEXT("unknown family"), USmokeHookSubsystem::HasEnemyFamilyName(TEXT("owl"), Type));
	return true;
}

#endif
