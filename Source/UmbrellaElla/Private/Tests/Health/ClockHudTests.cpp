#include "Core/UmbrellaTuning.h"
#include "Health/HealthModel.h"
#include "Misc/AutomationTest.h"
#include "UI/ClockHudModel.h"
#include "UI/HudTuning.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FClockHudLayout, "UmbrellaElla.Health.ClockHudInsideSixteenByNineView",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FClockHudLayout::RunTest(const FString& Parameters)
{
	const FHudTuning Tuning;
	const FVector2D Canvases[] = { FVector2D(1280, 720), FVector2D(1920, 1080), FVector2D(3840, 2160), FVector2D(1600, 1200), FVector2D(2560, 1080) };
	for (const FVector2D& Canvas : Canvases)
	{
		const FClockLayout Layout = ClockHudRules::ComputeLayout(Canvas, Tuning);
		const FVector2D Size = Layout.View.GetSize();
		TestEqual(TEXT("view is 16:9"), Size.X / Size.Y, 16.0 / 9.0, 1.0e-3);
		TestTrue(TEXT("view inside canvas"), Layout.View.Min.X >= -1.0e-3 && Layout.View.Min.Y >= -1.0e-3 && Layout.View.Max.X <= Canvas.X + 1.0e-3 && Layout.View.Max.Y <= Canvas.Y + 1.0e-3);
		TestTrue(TEXT("clock inside the view"), Layout.View.IsInside(Layout.ClockBounds));
		TestTrue(TEXT("clock is top-left"), Layout.Center.X < Layout.View.GetCenter().X && Layout.Center.Y < Layout.View.GetCenter().Y);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FClockHudText, "UmbrellaElla.Health.ClockHudTextAtLeast18Px",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FClockHudText::RunTest(const FString& Parameters)
{
	const FHudTuning Tuning;
	const float Heights[] = { 720.0f, 1080.0f, 2160.0f };
	const float FontHeights[] = { 12.0f, 20.0f, 36.0f };
	for (const float ViewHeight : Heights)
	{
		for (const float FontHeight : FontHeights)
		{
			const float Px = FontHeight * ClockHudRules::TextScale(FontHeight, ViewHeight, Tuning);
			TestTrue(TEXT("text >= 18 px"), Px >= 18.0f - 1.0e-3f);
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FClockHudLifeHand, "UmbrellaElla.Health.LifeHandAdvancesTowardXIIAndEndsAtXII",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FClockHudLifeHand::RunTest(const FString& Parameters)
{
	const FHudTuning Tuning;
	FHealthState State = HealthRules::MakeFull(3.0f, 3);
	const float Three = ClockHudRules::LifeHandDegrees(State, Tuning);
	HealthRules::ApplyDamage(State, 3.0f);
	const float Two = ClockHudRules::LifeHandDegrees(State, Tuning);
	HealthRules::ApplyDamage(State, 3.0f);
	const float One = ClockHudRules::LifeHandDegrees(State, Tuning);
	HealthRules::ApplyDamage(State, 3.0f);
	const float None = ClockHudRules::LifeHandDegrees(State, Tuning);
	TestTrue(TEXT("each lost life moves the hand toward XII"), Three < Two && Two < One && One < None);
	TestEqual(TEXT("defeat: XII"), None, 360.0f, 1.0e-3f);
	TestEqual(TEXT("health hand at XII on defeat"), HealthRules::HealthHandDegrees(State), 0.0f, 1.0e-3f);

	// Restoring progress moves the hand back toward the next slot.
	FHealthState Spent = HealthRules::MakeFull(3.0f, 3);
	Spent.Lives = 2;
	const float Before = ClockHudRules::LifeHandDegrees(Spent, Tuning);
	HealthRules::ApplyHeal(Spent, 1.5f);
	TestTrue(TEXT("progress moves it back"), ClockHudRules::LifeHandDegrees(Spent, Tuning) < Before);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FClockHudHands, "UmbrellaElla.Health.HandsDifferWithoutColor",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FClockHudHands::RunTest(const FString& Parameters)
{
	const FHudTuning Tuning;
	TestTrue(TEXT("different length"), Tuning.HealthHandLength > Tuning.LifeHandLength);
	TestTrue(TEXT("different thickness"), Tuning.LifeHandThickness > Tuning.HealthHandThickness);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FClockHudFollow, "UmbrellaElla.Health.DrawnHandFollowsWithoutGameplayDelay",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FClockHudFollow::RunTest(const FString& Parameters)
{
	const FHudTuning Tuning;
	TestEqual(TEXT("one frame moves at most the capped speed"), ClockHudRules::FollowAngle(90.0f, 0.0f, 0.1f, Tuning), 90.0f - Tuning.HandSpeedDegreesPerSecond * 0.1f, 1.0e-3f);
	TestEqual(TEXT("arrives and stops"), ClockHudRules::FollowAngle(10.0f, 0.0f, 1.0f, Tuning), 0.0f, 1.0e-3f);
	return true;
}

#endif
