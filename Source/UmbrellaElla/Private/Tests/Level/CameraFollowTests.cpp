// dcseamless (Josh, Nov 14: "not seamless: pressing Space to move forward jolts the view"). Real input on main b79af92a
// measured per-frame camera steps of -480..+960 units at 30 fps: the follow lead (+-0.25 x view width) flipped with the
// sign of Ella's X velocity in one frame, so every stop snapped the view back 480 units and every restart 480 forward.
// This test drives the follow with the same stop/start pattern and fails on any frame-to-frame change in camera step
// bigger than Ella's own (the old follow: 480).
#include "Core/UmbrellaTuning.h"
#include "Level/UmbrellaLevelDirector.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

namespace
{
	constexpr float CamFollowTestDt = 1.0f / 30.0f;
	/** Ella's flying speed measured in the trace (vx 531). */
	constexpr float CamFollowTestSpeed = 531.0f;
	/** Largest change of the camera's per-frame step allowed: below Ella's own stop (531 / 30 = 17.7 units). */
	constexpr float CamFollowTestMaxStepChange = 10.0f;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelCameraFollowSmooth, "UmbrellaElla.Level.CameraFollowSmooth",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FLevelCameraFollowSmooth::RunTest(const FString& Parameters)
{
	const float Lead = GetDefault<UUmbrellaTuning>()->Field.CameraLeadFraction * GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaWidth;
	FCameraFollowState State;
	float EllaX = 1000.0f;
	float Camera = AUmbrellaLevelDirector::StepCameraFollow(State, EllaX, 1, 0.0f, Lead);
	TestEqual(TEXT("first call places the camera at Ella plus the lead"), Camera, EllaX + Lead);
	float LastStep = 0.0f;
	float WorstChange = 0.0f;
	float WorstStep = 0.0f;
	// 12 s: fly 0.30 s, stop 0.10 s (a flap / key release), repeat; from 8 s on, fly left.
	for (int32 Frame = 1; Frame < 360; ++Frame)
	{
		const float T = Frame * CamFollowTestDt;
		const bool bMoving = FMath::Fmod(T, 0.4f) < 0.3f;
		const int32 Direction = bMoving ? (T < 8.0f ? 1 : -1) : 0;
		EllaX += Direction * CamFollowTestSpeed * CamFollowTestDt;
		const float Next = AUmbrellaLevelDirector::StepCameraFollow(State, EllaX, Direction, CamFollowTestDt, Lead);
		const float Step = Next - Camera;
		WorstChange = FMath::Max(WorstChange, FMath::Abs(Step - LastStep));
		WorstStep = FMath::Max(WorstStep, FMath::Abs(Step));
		LastStep = Step;
		Camera = Next;
	}
	TestTrue(*FString::Printf(TEXT("camera step never jumps (worst change %.1f units/frame)"), WorstChange), WorstChange <= CamFollowTestMaxStepChange);
	TestTrue(*FString::Printf(TEXT("camera never moves more than twice Ella's speed (worst %.1f units/frame)"), WorstStep), WorstStep <= 2.0f * CamFollowTestSpeed * CamFollowTestDt);
	// A stop keeps the lead (no snap back); a cut (checkpoint place) still snaps.
	FCameraFollowState Stop;
	AUmbrellaLevelDirector::StepCameraFollow(Stop, 0.0f, 1, 0.0f, Lead);
	TestEqual(TEXT("a stop keeps the lead"), AUmbrellaLevelDirector::StepCameraFollow(Stop, 0.0f, 0, CamFollowTestDt, Lead), Lead);
	TestEqual(TEXT("a cut snaps"), AUmbrellaLevelDirector::StepCameraFollow(Stop, 20000.0f, 1, CamFollowTestDt, Lead), 20000.0f + Lead);
	return true;
}

#endif
