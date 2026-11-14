#include "Misc/AutomationTest.h"
#include "Feedback/Anim/KeeperPresenterSubsystem.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperIdleFrameLoops, "UmbrellaElla.Feedback.KeeperIdleFrameLoops",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FKeeperIdleFrameLoops::RunTest(const FString& Parameters)
{
	// Top-row ping-pong on a 6x4 grid at 6 fps: 0 1 2 3 4 5 4 3 2 1 0 ...
	const int32 Expected[] = {0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 0, 1};
	for (int32 Step = 0; Step < UE_ARRAY_COUNT(Expected); ++Step)
	{
		const double Seconds = (Step + 0.5) / 6.0;
		TestEqual(FString::Printf(TEXT("ping-pong step %d"), Step),
			UKeeperPresenterSubsystem::IdleFrameAt(Seconds, 6.0f, 6, 4, EKeeperGridPlayback::TopRowPingPong), Expected[Step]);
	}
	// Every cell stays in row 0 under ping-pong (the material samples only the top row).
	for (int32 Step = 0; Step < 60; ++Step)
	{
		const int32 Frame = UKeeperPresenterSubsystem::IdleFrameAt((Step + 0.5) / 6.4, 6.4f, 6, 4, EKeeperGridPlayback::TopRowPingPong);
		TestTrue(FString::Printf(TEXT("ping-pong frame %d in row 0"), Frame), Frame >= 0 && Frame < 6);
	}
	// All cells: 0..23 then back to 0.
	TestEqual(TEXT("all cells frame 23"), UKeeperPresenterSubsystem::IdleFrameAt(23.5 / 6.0, 6.0f, 6, 4, EKeeperGridPlayback::AllCells), 23);
	TestEqual(TEXT("all cells wraps to 0"), UKeeperPresenterSubsystem::IdleFrameAt(24.5 / 6.0, 6.0f, 6, 4, EKeeperGridPlayback::AllCells), 0);
	// A single picture never steps; negative time is frame 0.
	TestEqual(TEXT("single picture"), UKeeperPresenterSubsystem::IdleFrameAt(10.0, 6.0f, 1, 1, EKeeperGridPlayback::TopRowPingPong), 0);
	TestEqual(TEXT("negative time"), UKeeperPresenterSubsystem::IdleFrameAt(-1.0, 6.0f, 6, 4, EKeeperGridPlayback::AllCells), 0);
	return true;
}

#endif
