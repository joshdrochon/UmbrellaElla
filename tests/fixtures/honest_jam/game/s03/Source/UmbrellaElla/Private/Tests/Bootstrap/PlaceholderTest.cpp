#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

// Card 0.3 placeholder; card 0.5 removes it.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FBootstrapPlaceholderTest, "UmbrellaElla.Bootstrap.Placeholder",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FBootstrapPlaceholderTest::RunTest(const FString& Parameters)
{
	return TestTrue(TEXT("placeholder"), true);
}

#endif
