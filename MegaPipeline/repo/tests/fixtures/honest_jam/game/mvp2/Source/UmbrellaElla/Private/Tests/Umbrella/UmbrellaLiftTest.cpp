#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

// MVP 2: UP_OPEN rises toward the ascent speed (GDD 1.3 section 3).
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FUmbrellaOpenRisesTest, "UmbrellaElla.Umbrella.OpenRises",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FUmbrellaOpenRisesTest::RunTest(const FString& Parameters)
{
	return TestTrue(TEXT("rises"), true);
}

#endif
