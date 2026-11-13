#include "Misc/AutomationTest.h"
#include "Core/UmbrellaTuning.h"
#include "Smoke/PlaytestRun.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSmokePlaytestEnvelope, "UmbrellaElla.Smoke.PlaytestEnvelopeFromMotorTuning",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FSmokePlaytestEnvelope::RunTest(const FString& Parameters)
{
	const FMotorTuning& Motor = GetDefault<UUmbrellaTuning>()->Motor;
	const float Trim = 1.0f + Motor.VerticalTrimPct * FPlaytestRun::PercentToFraction;
	float Min = 0.0f;
	float Max = 0.0f;
	FPlaytestRun::VerticalEnvelope(2.0f, Min, Max);
	TestEqual(TEXT("rise side is rise speed with trim"), Max, Motor.RiseSpeed * Trim * 2.0f, 0.01f);
	TestEqual(TEXT("fall side is free-fall speed with trim"), Min, -Motor.FreeFallSpeed * Trim * 2.0f, 0.01f);
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
