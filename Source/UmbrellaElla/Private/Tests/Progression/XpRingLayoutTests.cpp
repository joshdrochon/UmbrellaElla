#include "Misc/AutomationTest.h"
#include "Core/UmbrellaTuning.h"
#include "Progression/ProgressionTuning.h"
#include "UI/ClockHudModel.h"
#include "UI/Progression/XpRingWidget.h"
#include "UI/Style/UmbrellaUIStyle.h"

#if WITH_AUTOMATION_TESTS

// FLOW-48: the XP ring is centred on the HUD clock and wraps just outside its gold rim, at every window shape.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FXpRingCentredOnClock, "UmbrellaElla.Progression.XpRingCentredOnClock", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FXpRingCentredOnClock::RunTest(const FString& Parameters)
{
	const FHudTuning Hud;
	const FProgressionTuning Tuning;
	const FVector2D Canvases[] = { FVector2D(1600.0, 900.0), FVector2D(1920.0, 1080.0), FVector2D(640.0, 360.0), FVector2D(2560.0, 1080.0), FVector2D(1280.0, 1024.0) };
	for (const FVector2D& Canvas : Canvases)
	{
		const FClockLayout Clock = ClockHudRules::ComputeLayout(Canvas, Hud);
		const FXpRingCircle Ring = UXpRingWidget::ComputeCircle(Canvas, Hud, Tuning);
		const FString At = FString::Printf(TEXT("%.0fx%.0f"), Canvas.X, Canvas.Y);
		TestTrue(*(At + TEXT(" ring centre on the clock centre")), FVector2D::Distance(Ring.Center, Clock.Center) < 0.01);
		TestTrue(*(At + TEXT(" ring inner edge outside the dial art and the drawn rim")),
			Ring.Radius - Tuning.RingThickness * 0.5f >= Clock.Radius / UmbrellaUIStyleConstants::ClockFaceRimShare
			&& Ring.Radius - Tuning.RingThickness * 0.5f >= Clock.Radius + Hud.RimThickness * 0.5f);
		TestEqual(*(At + TEXT(" ring sits the gap outside the clock edge")), Ring.Radius - Tuning.RingThickness * 0.5f - Ring.ClockEdge, Tuning.RingGapPixels, 0.01f);
		TestTrue(*(At + TEXT(" ring stays on screen")), Ring.Center.X - Ring.Radius > 0.0 && Ring.Center.Y - Ring.Radius > 0.0);
	}
	return true;
}

// FLOW-48: the ring is drawn in the clock's gold, never the old ash blue.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FXpRingClockPalette, "UmbrellaElla.Progression.XpRingClockPalette", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FXpRingClockPalette::RunTest(const FString& Parameters)
{
	const FProgressionTuning Tuning;
	const FXpRingColors Filling = UXpRingWidget::ComputeColors(false, 0.0f, Tuning);
	const FXpRingColors Max = UXpRingWidget::ComputeColors(true, 0.0f, Tuning);
	const FXpRingColors Pulse = UXpRingWidget::ComputeColors(false, 1.0f, Tuning);
	auto Warm = [](const FLinearColor& Color) { return Color.R > Color.G && Color.G > Color.B; };
	TestTrue(TEXT("brass track (gold token, darker)"), Warm(Filling.Track) && Filling.Track.R < FUmbrellaUIStyle::Gold().R);
	TestTrue(TEXT("gold fill"), Warm(Filling.Fill) && Filling.Fill.R >= FUmbrellaUIStyle::Gold().R);
	TestTrue(TEXT("track quieter than the fill"), Filling.Track.A < Filling.Fill.A);
	TestTrue(TEXT("soft halo is faint"), Filling.Halo.A < Filling.Fill.A && Warm(Filling.Halo));
	TestTrue(TEXT("full bright gold at the cap"), Max.Fill.Equals(FUmbrellaUIStyle::GoldBright().CopyWithNewOpacity(1.0f), 1e-3f));
	TestTrue(TEXT("cream flash at a level gain"), Pulse.Fill.Equals(FUmbrellaUIStyle::Cream().CopyWithNewOpacity(Tuning.RingFillAlpha), 1e-3f));
	return true;
}

#endif
