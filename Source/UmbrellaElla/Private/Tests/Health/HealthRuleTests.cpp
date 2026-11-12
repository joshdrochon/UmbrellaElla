#include "Health/HealthModel.h"
#include "Health/HealthTuning.h"
#include "Owl/KeeperTuning.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

namespace
{
	constexpr float Tol = 1.0e-4f;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthDamageScale, "UmbrellaElla.Health.DamageScaleByDefenseRank",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthDamageScale::RunTest(const FString& Parameters)
{
	const FHealthTuning Tuning;
	const FKeeperTuning KeeperTuning;
	TestEqual(TEXT("rank 0"), HealthRules::ScaleDamage(1.0f, 0, Tuning), 1.0f, Tol);
	TestEqual(TEXT("rank I"), HealthRules::ScaleDamage(1.0f, 1, Tuning), 0.9f, Tol);
	TestEqual(TEXT("rank II"), HealthRules::ScaleDamage(1.0f, 2, Tuning), 0.8f, Tol);
	TestEqual(TEXT("rank III"), HealthRules::ScaleDamage(1.0f, 3, Tuning), 0.7f, Tol);
	TestEqual(TEXT("rank clamps at III"), HealthRules::ScaleDamage(1.0f, 9, Tuning), 0.7f, Tol);
	TestEqual(TEXT("chain"), HealthRules::ScaleDamage(KeeperTuning.ChainDamage, 0, Tuning), 1.25f, Tol);
	TestEqual(TEXT("talon"), HealthRules::ScaleDamage(KeeperTuning.TalonDamage, 0, Tuning), 1.5f, Tol);
	TestEqual(TEXT("defense applies once to chain"), HealthRules::ScaleDamage(KeeperTuning.ChainDamage, 2, Tuning), 1.0f, Tol);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthThreeHitsLoseALife, "UmbrellaElla.Health.ThreeHitsCostALife",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthThreeHitsLoseALife::RunTest(const FString& Parameters)
{
	const FHealthTuning Tuning;
	FHealthState State = HealthRules::MakeFull(Tuning.HitsPerLife, Tuning.MaxLives);
	TestEqual(TEXT("starts 3 lives"), State.Lives, 3);
	HealthRules::ApplyDamage(State, 1.0f);
	HealthRules::ApplyDamage(State, 1.0f);
	TestEqual(TEXT("two hits keep the life"), State.Lives, 3);
	TestEqual(TEXT("active after two hits"), State.Active, 1.0f, Tol);
	const FHealthDamageOutcome Outcome = HealthRules::ApplyDamage(State, 1.0f);
	TestEqual(TEXT("third hit loses one life"), Outcome.LivesLost, 1);
	TestEqual(TEXT("lives left"), State.Lives, 2);
	TestEqual(TEXT("active refilled"), State.Active, 3.0f, Tol);
	TestFalse(TEXT("not defeated"), Outcome.bDefeatedNow);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthOverflow, "UmbrellaElla.Health.DamageOverflowCarriesAcrossLives",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthOverflow::RunTest(const FString& Parameters)
{
	FHealthState State = HealthRules::MakeFull(3.0f, 3);
	State.Active = 0.5f;
	HealthRules::ApplyDamage(State, 1.5f);
	TestEqual(TEXT("one life gone"), State.Lives, 2);
	TestEqual(TEXT("1.0 carries into the next life"), State.Active, 2.0f, Tol);

	FHealthState Big = HealthRules::MakeFull(3.0f, 3);
	const FHealthDamageOutcome Outcome = HealthRules::ApplyDamage(Big, 7.0f);
	TestEqual(TEXT("seven damage takes two lives"), Outcome.LivesLost, 2);
	TestEqual(TEXT("one life left"), Big.Lives, 1);
	TestEqual(TEXT("1 of 3 used in the last life"), Big.Active, 2.0f, Tol);
	TestFalse(TEXT("still alive"), Big.IsDefeated());

	FHealthState Exact = HealthRules::MakeFull(3.0f, 3);
	HealthRules::ApplyDamage(Exact, 3.0f);
	TestEqual(TEXT("exactly one life of damage"), Exact.Lives, 2);
	TestEqual(TEXT("fresh life"), Exact.Active, 3.0f, Tol);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthFinalDefeat, "UmbrellaElla.Health.FinalDepletionDefeatsOnceAndNoRevival",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthFinalDefeat::RunTest(const FString& Parameters)
{
	FHealthState State = HealthRules::MakeFull(3.0f, 3);
	const FHealthDamageOutcome Big = HealthRules::ApplyDamage(State, 100.0f);
	TestTrue(TEXT("defeated"), Big.bDefeatedNow);
	TestEqual(TEXT("two lives lost on the way"), Big.LivesLost, 2);
	TestEqual(TEXT("both hands at XII"), State.Lives, 0);
	TestEqual(TEXT("health hand at XII"), HealthRules::HealthHandDegrees(State), 0.0f, Tol);
	const FHealthDamageOutcome Again = HealthRules::ApplyDamage(State, 1.0f);
	TestFalse(TEXT("defeat reports once"), Again.bDefeatedNow);
	const FHealthHealOutcome Heal = HealthRules::ApplyHeal(State, 5.0f);
	TestTrue(TEXT("no revival"), Heal.bNothingChanged);
	TestEqual(TEXT("still dead"), State.Lives, 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthHealing, "UmbrellaElla.Health.HealingActiveFirstThenReserves",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthHealing::RunTest(const FString& Parameters)
{
	const FHealthTuning Tuning;
	TestEqual(TEXT("rank 0"), HealthRules::HealAmount(0, Tuning), 0.5f, Tol);
	TestEqual(TEXT("rank I"), HealthRules::HealAmount(1, Tuning), 0.8f, Tol);
	TestEqual(TEXT("rank II"), HealthRules::HealAmount(2, Tuning), 1.1f, Tol);
	TestEqual(TEXT("rank III"), HealthRules::HealAmount(3, Tuning), 1.4f, Tol);
	TestEqual(TEXT("no fourth rank"), HealthRules::HealAmount(4, Tuning), 1.4f, Tol);

	FHealthState State = HealthRules::MakeFull(3.0f, 3);
	State.Active = 2.0f;
	HealthRules::ApplyHeal(State, 0.5f);
	TestEqual(TEXT("active takes the heal first"), State.Active, 2.5f, Tol);

	// Overflow of the same shot goes to reserve progress.
	const FHealthHealOutcome Over = HealthRules::ApplyHeal(State, 0.8f);
	TestEqual(TEXT("active filled"), State.Active, 3.0f, Tol);
	TestEqual(TEXT("active gained"), Over.ActiveGained, 0.5f, Tol);
	TestEqual(TEXT("rest is reserve progress"), State.ReserveProgress, 0.0f, Tol);

	// One spent reserve needs one full capacity of healing.
	FHealthState Spent = HealthRules::MakeFull(3.0f, 3);
	Spent.Lives = 2;
	for (int32 Yellow = 0; Yellow < 5; ++Yellow)
	{
		HealthRules::ApplyHeal(Spent, 0.5f);
	}
	TestEqual(TEXT("2.5 of 3 stored, reserve not back"), Spent.Lives, 2);
	TestEqual(TEXT("progress"), Spent.ReserveProgress, 2.5f, Tol);
	const FHealthHealOutcome Back = HealthRules::ApplyHeal(Spent, 0.5f);
	TestEqual(TEXT("reserve restored"), Spent.Lives, 3);
	TestEqual(TEXT("restored count"), Back.ReservesRestored, 1);

	// Never beyond maximum lives, and a full catch is not healing.
	const FHealthHealOutcome Full = HealthRules::ApplyHeal(Spent, 0.5f);
	TestTrue(TEXT("full capture changes nothing"), Full.bNothingChanged);
	TestEqual(TEXT("lives stay at max"), Spent.Lives, 3);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthLift, "UmbrellaElla.Health.LiftFollowsActiveHealthOnly",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthLift::RunTest(const FString& Parameters)
{
	const FHealthTuning Tuning;
	FHealthState State = HealthRules::MakeFull(3.0f, 3);
	TestEqual(TEXT("full"), HealthRules::LiftMultiplier(State, Tuning.MinLift), 1.0f, Tol);
	State.Active = 1.5f;
	TestEqual(TEXT("half"), HealthRules::LiftMultiplier(State, Tuning.MinLift), 0.65f, Tol);
	State.Lives = 1;
	TestEqual(TEXT("reserve count is not part of it"), HealthRules::LiftMultiplier(State, Tuning.MinLift), 0.65f, Tol);
	State.Active = 0.0f;
	TestEqual(TEXT("empty"), HealthRules::LiftMultiplier(State, Tuning.MinLift), 0.3f, Tol);
	FHealthState Wide = HealthRules::MakeFull(6.0f, 4);
	Wide.Active = 3.0f;
	TestEqual(TEXT("half at capacity 6"), HealthRules::LiftMultiplier(Wide, Tuning.MinLift), 0.65f, Tol);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthHand, "UmbrellaElla.Health.HealthHandIsIIIWhenFullXIIWhenEmpty",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthHand::RunTest(const FString& Parameters)
{
	FHealthState State = HealthRules::MakeFull(3.0f, 3);
	TestEqual(TEXT("full is III"), HealthRules::HealthHandDegrees(State), 90.0f, Tol);
	HealthRules::ApplyDamage(State, 1.0f);
	TestEqual(TEXT("damage moves backward toward XII"), HealthRules::HealthHandDegrees(State), 60.0f, Tol);
	HealthRules::ApplyHeal(State, 0.5f);
	TestEqual(TEXT("healing moves toward III"), HealthRules::HealthHandDegrees(State), 75.0f, Tol);
	return true;
}

#endif
