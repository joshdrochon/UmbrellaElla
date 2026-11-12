#include "Level/LevelCatalogue.h"
#include "Level/LevelRules.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#define UMBRELLAELLA_LEVEL_TEST_FLAGS (EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelCatalogueSize, "UmbrellaElla.Level.CatalogueHas24Variants", UMBRELLAELLA_LEVEL_TEST_FLAGS)
bool FLevelCatalogueSize::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("24 variants"), LevelCatalogue::All().Num(), 24);
	TestNotNull(TEXT("CH12B"), LevelCatalogue::Find(12, TEXT('B')));
	TestNull(TEXT("no CH13"), LevelCatalogue::Find(13, TEXT('A')));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelSeedDeterministic, "UmbrellaElla.Level.SameSeedSameRoute", UMBRELLAELLA_LEVEL_TEST_FLAGS)
bool FLevelSeedDeterministic::RunTest(const FString& Parameters)
{
	for (const int64 Seed : {1001LL, 1002LL, 1003LL, 77LL, 123456789LL})
	{
		const FRoute A = LevelCatalogue::Generate(Seed);
		const FRoute B = LevelCatalogue::Generate(Seed);
		TestEqual(TEXT("same seed same route"), A.Signature(), B.Signature());
		TestEqual(TEXT("nine slots"), A.Slots.Num(), 9);
		TestTrue(TEXT("valid"), LevelCatalogue::ValidateRoute(A).IsEmpty());
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelGrammar, "UmbrellaElla.Level.NineSlotGrammar", UMBRELLAELLA_LEVEL_TEST_FLAGS)
bool FLevelGrammar::RunTest(const FString& Parameters)
{
	TSet<FString> Signatures;
	for (int64 Seed = 1; Seed <= 200; ++Seed)
	{
		const FRoute R = LevelCatalogue::Generate(Seed);
		Signatures.Add(R.Signature());
		TestTrue(TEXT("group A fixed"), R.Slots[0].Chunk == 1 && R.Slots[1].Chunk == 2 && R.Slots[2].Chunk == 3);
		TestEqual(TEXT("slot 4 is CH04"), R.Slots[3].Chunk, 4);
		TestTrue(TEXT("slot 5 mill"), R.Slots[4].Chunk == 5 || R.Slots[4].Chunk == 6);
		TestTrue(TEXT("slot 6 shutter/bellows"), R.Slots[5].Chunk == 7 || R.Slots[5].Chunk == 8);
		TestTrue(TEXT("slot 7 eave/switchback"), R.Slots[6].Chunk == 9 || R.Slots[6].Chunk == 10);
		TestTrue(TEXT("slot 9 warden-mill/stilt-courier"), R.Slots[8].Chunk == 11 || R.Slots[8].Chunk == 12);
		TestTrue(TEXT("slot 8 not yet used"), R.Slots[7].Chunk >= 5 && R.Slots[7].Chunk <= 8 && R.Slots[7].Chunk != R.Slots[4].Chunk && R.Slots[7].Chunk != R.Slots[5].Chunk);
	}
	TestTrue(TEXT("seeds give variety"), Signatures.Num() > 20);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelValidateRejects, "UmbrellaElla.Level.ValidateRejectsBadRoutes", UMBRELLAELLA_LEVEL_TEST_FLAGS)
bool FLevelValidateRejects::RunTest(const FString& Parameters)
{
	FRoute Good = LevelCatalogue::FallbackRoute();
	TestTrue(TEXT("fallback is valid"), LevelCatalogue::ValidateRoute(Good).IsEmpty());
	FRoute Short = Good;
	Short.Slots.RemoveAt(8);
	TestFalse(TEXT("short route rejected"), LevelCatalogue::ValidateRoute(Short).IsEmpty());
	FRoute Swapped = Good;
	Swapped.Slots.Swap(0, 1);
	TestFalse(TEXT("grammar break rejected"), LevelCatalogue::ValidateRoute(Swapped).IsEmpty());
	FRoute NoReturn = Good;
	NoReturn.Slots[3].bReturnFlow = false;
	TestFalse(TEXT("missing return flow rejected"), LevelCatalogue::ValidateRoute(NoReturn).IsEmpty());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelFallbackAndRetry, "UmbrellaElla.Level.FallbackAndAvoidRepeat", UMBRELLAELLA_LEVEL_TEST_FLAGS)
bool FLevelFallbackAndRetry::RunTest(const FString& Parameters)
{
	const FRoute Fallback = LevelCatalogue::FallbackRoute();
	TestEqual(TEXT("seed 1001 fixture"), Fallback.Signature(), FString(TEXT("01A,02A,03A,04A,05A,07A,09A,08A,11A")));
	const FRoute First = LevelCatalogue::Generate(5);
	const FRoute Next = LevelCatalogue::GenerateAvoiding(5, First.Signature());
	TestNotEqual(TEXT("consecutive signature avoided"), Next.Signature(), First.Signature());
	TestTrue(TEXT("avoiding route valid"), LevelCatalogue::ValidateRoute(Next).IsEmpty());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelLayout, "UmbrellaElla.Level.RefugesAndLength", UMBRELLAELLA_LEVEL_TEST_FLAGS)
bool FLevelLayout::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("slot 0 at 0"), LevelCatalogue::SlotStartX(0), 0.0f);
	TestEqual(TEXT("slot 1 one chunk in"), LevelCatalogue::SlotStartX(1), 1920.0f);
	TestEqual(TEXT("refuge 1 after three chunks"), LevelCatalogue::RefugeStartX(1), 3.0f * 1920.0f);
	TestTrue(TEXT("slot 3 starts after refuge"), LevelCatalogue::SlotStartX(3) > LevelCatalogue::RefugeStartX(1));
	TestEqual(TEXT("length is nine chunks plus three refuges"), LevelCatalogue::RouteLength(), 9.0f * 1920.0f + 3.0f * 960.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelContainment, "UmbrellaElla.Level.GroundContainment", UMBRELLAELLA_LEVEL_TEST_FLAGS)
bool FLevelContainment::RunTest(const FString& Parameters)
{
	TestTrue(TEXT("inside"), LevelCatalogue::IsFootprintOnSupport(100.0f, 30.0f, 0.0f, 200.0f));
	TestFalse(TEXT("hangs off right"), LevelCatalogue::IsFootprintOnSupport(180.0f, 30.0f, 0.0f, 200.0f));
	TestEqual(TEXT("clamped right"), LevelCatalogue::ClampPatrolCentre(190.0f, 30.0f, 0.0f, 200.0f), 170.0f);
	TestEqual(TEXT("clamped left"), LevelCatalogue::ClampPatrolCentre(-50.0f, 30.0f, 0.0f, 200.0f), 30.0f);
	TestEqual(TEXT("narrow support centres"), LevelCatalogue::ClampPatrolCentre(5.0f, 60.0f, 0.0f, 100.0f), 50.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelCameraRules, "UmbrellaElla.Level.CameraLeadAndReveal", UMBRELLAELLA_LEVEL_TEST_FLAGS)
bool FLevelCameraRules::RunTest(const FString& Parameters)
{
	const float W = 1600.0f;
	TestEqual(TEXT("leads right"), CameraRules::ScrollCentreX(2000.0f, 1, W, 0.0f, 10000.0f), 2400.0f);
	TestEqual(TEXT("leads left"), CameraRules::ScrollCentreX(2000.0f, -1, W, 0.0f, 10000.0f), 1600.0f);
	TestEqual(TEXT("clamped at start"), CameraRules::ScrollCentreX(100.0f, -1, W, 0.0f, 10000.0f), 800.0f);
	TestEqual(TEXT("clamped at end"), CameraRules::ScrollCentreX(9900.0f, 1, W, 0.0f, 10000.0f), 9200.0f);
	TestEqual(TEXT("1.2 s lead"), CameraRules::RevealLeadSeconds(600.0f, 500.0f), 1.2f);
	const FBox2D View(FVector2D(0, 0), FVector2D(1600, 900));
	TestTrue(TEXT("fully revealed"), LevelRules::IsFullyRevealed(FBox2D(FVector2D(500, 300), FVector2D(700, 500)), View, 48.0f));
	TestFalse(TEXT("clipped by edge"), LevelRules::IsFullyRevealed(FBox2D(FVector2D(1580, 300), FVector2D(1700, 500)), View, 48.0f));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FLevelRulesMath, "UmbrellaElla.Level.ClearanceAndInterface", UMBRELLAELLA_LEVEL_TEST_FLAGS)
bool FLevelRulesMath::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("margin uses larger of 3% H and quarter diameter"), LevelRules::ClearanceMargin(900.0f, 200.0f), 50.0f);
	TestEqual(TEXT("margin height wins"), LevelRules::ClearanceMargin(900.0f, 40.0f), 27.0f);
	TestTrue(TEXT("opening fits"), LevelRules::CanOpeningFit(200.0f, 200.0f, 40.0f, 40.0f, 20.0f));
	TestFalse(TEXT("opening too narrow"), LevelRules::CanOpeningFit(100.0f, 200.0f, 40.0f, 40.0f, 20.0f));
	TestEqual(TEXT("interface at half height"), LevelRules::InterfaceHeight(900.0f), 450.0f);
	TestEqual(TEXT("vestibule 0.2 W"), LevelRules::VestibuleLength(1600.0f), 320.0f);
	TestEqual(TEXT("clearance floor 0.3 H"), LevelRules::MinVerticalClearance(900.0f, 100.0f), 270.0f);
	TestEqual(TEXT("clearance envelope wins"), LevelRules::MinVerticalClearance(900.0f, 400.0f), 400.0f);
	TestTrue(TEXT("ray clears"), LevelRules::IsRayClearOfCircle(FVector2D(0, 0), FVector2D(100, 0), FVector2D(50, 100), 50.0f, 8.0f, 0.0f));
	TestFalse(TEXT("ray hits rotor"), LevelRules::IsRayClearOfCircle(FVector2D(0, 0), FVector2D(100, 0), FVector2D(50, 40), 50.0f, 8.0f, 0.0f));
	return true;
}

#endif
