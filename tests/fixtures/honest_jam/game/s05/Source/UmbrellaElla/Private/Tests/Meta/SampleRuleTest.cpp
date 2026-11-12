#include "Misc/AutomationTest.h"

#if WITH_DEV_AUTOMATION_TESTS

// Card 0.5: the rule-test pattern (a pure function, no world).
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMetaSampleRuleTest, "UmbrellaElla.Meta.SampleRule",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)

bool FMetaSampleRuleTest::RunTest(const FString& Parameters)
{
	return TestEqual(TEXT("sum"), 1 + 1, 2);
}

#endif
