#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FUmbrellaEllaBootstrapPlaceholder, "UmbrellaElla.Bootstrap.Placeholder",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FUmbrellaEllaBootstrapPlaceholder::RunTest(const FString& Parameters)
{
	return TestTrue(TEXT("placeholder runs"), true);
}

#endif
