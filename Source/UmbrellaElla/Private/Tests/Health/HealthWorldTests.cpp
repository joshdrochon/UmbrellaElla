#include "Defense/AbsorbReceiverComponent.h"
#include "Tests/Health/HealthTestWorld.h"
#include "Misc/AutomationTest.h"
#include "Projectile/UmbrellaProjectile.h"

#if WITH_AUTOMATION_TESTS

namespace
{
	/** Gap that clears the post-hit protection window. */
	constexpr float PastProtection = 0.7f;

	AUmbrellaProjectile* FireAtElla(FHealthTestWorld& Test, EUmbrellaShotKind Kind, float Damage)
	{
		FUmbrellaShotSpec Spec;
		Spec.Kind = Kind;
		Spec.Origin = Test.Ella->GetActorLocation();
		Spec.Radius = 8.0f;
		Spec.Damage = Damage;
		Spec.LifetimeSeconds = 2.0f;
		Spec.SourceId = FName(TEXT("TestSource"));
		return AUmbrellaProjectile::Fire(Test.World, Spec);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthWorldRedShot, "UmbrellaElla.Health.World.RedShotCostsOneHit",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthWorldRedShot::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	if (!TestNotNull(TEXT("Ella"), Test.Ella))
	{
		return false;
	}
	UUmbrellaHealthComponent* Health = Test.Ella->GetHealth();
	AUmbrellaProjectile* Shot = FireAtElla(Test, EUmbrellaShotKind::EnemyRed, 1.0f);
	TestNotNull(TEXT("shot"), Shot);
	TestEqual(TEXT("one hit gone"), Health->GetState().Active, 2.0f, 1.0e-4f);
	TestEqual(TEXT("no life lost"), Health->GetState().Lives, 3);
	TestTrue(TEXT("shot consumed"), Shot && Shot->IsActorBeingDestroyed());
	TestEqual(TEXT("PlayerHealthChanged broadcast"), Test.CountOf(EUmbrellaEventType::PlayerHealthChanged) >= 1, true);
	TestEqual(TEXT("ProjectileSpawned broadcast"), Test.CountOf(EUmbrellaEventType::ProjectileSpawned), 1);
	TestEqual(TEXT("ProjectileContact broadcast"), Test.CountOf(EUmbrellaEventType::ProjectileContact), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthWorldThreeHits, "UmbrellaElla.Health.World.ThreeHitsCostALife",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthWorldThreeHits::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	if (!TestNotNull(TEXT("Ella"), Test.Ella))
	{
		return false;
	}
	UUmbrellaHealthComponent* Health = Test.Ella->GetHealth();
	for (int32 Hit = 0; Hit < 3; ++Hit)
	{
		FireAtElla(Test, EUmbrellaShotKind::EnemyRed, 1.0f);
		Test.Step(PastProtection);
	}
	TestEqual(TEXT("lives"), Health->GetState().Lives, 2);
	TestEqual(TEXT("active refilled"), Health->GetState().Active, 3.0f, 1.0e-4f);
	TestEqual(TEXT("LifeLost broadcast once"), Test.CountOf(EUmbrellaEventType::LifeLost), 1);
	TestEqual(TEXT("not defeated"), Test.CountOf(EUmbrellaEventType::PlayerDefeated), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthWorldDefeat, "UmbrellaElla.Health.World.LastLifeBroadcastsDefeatedOnce",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthWorldDefeat::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	if (!TestNotNull(TEXT("Ella"), Test.Ella))
	{
		return false;
	}
	UUmbrellaHealthComponent* Health = Test.Ella->GetHealth();
	for (int32 Hit = 0; Hit < 12; ++Hit)
	{
		FireAtElla(Test, EUmbrellaShotKind::EnemyRed, 1.0f);
		Test.Step(PastProtection);
	}
	TestEqual(TEXT("nine hits end it"), Health->GetState().Lives, 0);
	TestEqual(TEXT("PlayerDefeated exactly once"), Test.CountOf(EUmbrellaEventType::PlayerDefeated), 1);
	TestEqual(TEXT("LifeLost for the two reserves"), Test.CountOf(EUmbrellaEventType::LifeLost), 2);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthWorldProtection, "UmbrellaElla.Health.World.PostHitProtectionBlocksSecondHit",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthWorldProtection::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	if (!TestNotNull(TEXT("Ella"), Test.Ella))
	{
		return false;
	}
	UUmbrellaHealthComponent* Health = Test.Ella->GetHealth();
	FireAtElla(Test, EUmbrellaShotKind::EnemyRed, 1.0f);
	FireAtElla(Test, EUmbrellaShotKind::EnemyRed, 1.0f);
	TestEqual(TEXT("second hit inside the window does nothing"), Health->GetState().Active, 2.0f, 1.0e-4f);
	Test.Step(PastProtection);
	FireAtElla(Test, EUmbrellaShotKind::EnemyRed, 1.0f);
	TestEqual(TEXT("hit after the window lands"), Health->GetState().Active, 1.0f, 1.0e-4f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthWorldYellowHeals, "UmbrellaElla.Health.World.YellowDuringAbsorbFallHealsAndIsConsumed",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthWorldYellowHeals::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	if (!TestNotNull(TEXT("Ella"), Test.Ella))
	{
		return false;
	}
	UUmbrellaHealthComponent* Health = Test.Ella->GetHealth();
	FireAtElla(Test, EUmbrellaShotKind::EnemyRed, 1.0f);
	Test.Step(PastProtection);
	const float Before = Health->GetState().Active;
	Test.Ella->GetAbsorb()->SetPose(EAbsorbPose::AbsorbFall);
	AUmbrellaProjectile* Yellow = FireAtElla(Test, EUmbrellaShotKind::EnemyYellow, 1.0f);
	TestEqual(TEXT("healed 0.5"), Health->GetState().Active, Before + 0.5f, 1.0e-4f);
	TestTrue(TEXT("yellow consumed"), Yellow && Yellow->IsActorBeingDestroyed());
	TestEqual(TEXT("CatchAttempt"), Test.CountOf(EUmbrellaEventType::CatchAttempt), 1);
	TestEqual(TEXT("CatchSucceeded"), Test.CountOf(EUmbrellaEventType::CatchSucceeded), 1);
	TestEqual(TEXT("CatchFailed"), Test.CountOf(EUmbrellaEventType::CatchFailed), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthWorldYellowOutside, "UmbrellaElla.Health.World.YellowOutsideAbsorbFallDoesNotHeal",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthWorldYellowOutside::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	if (!TestNotNull(TEXT("Ella"), Test.Ella))
	{
		return false;
	}
	UUmbrellaHealthComponent* Health = Test.Ella->GetHealth();
	FireAtElla(Test, EUmbrellaShotKind::EnemyYellow, 1.0f);
	TestEqual(TEXT("ordinary yellow contact is harmful"), Health->GetState().Active, 2.0f, 1.0e-4f);
	TestEqual(TEXT("no catch attempt"), Test.CountOf(EUmbrellaEventType::CatchAttempt), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthWorldRedDuringAbsorb, "UmbrellaElla.Health.World.RedDuringAbsorbFallStillDamages",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthWorldRedDuringAbsorb::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	if (!TestNotNull(TEXT("Ella"), Test.Ella))
	{
		return false;
	}
	Test.Ella->GetAbsorb()->SetPose(EAbsorbPose::AbsorbFall);
	FireAtElla(Test, EUmbrellaShotKind::EnemyRed, 1.0f);
	TestEqual(TEXT("red cannot be captured"), Test.Ella->GetHealth()->GetState().Active, 2.0f, 1.0e-4f);
	TestEqual(TEXT("CatchFailed"), Test.CountOf(EUmbrellaEventType::CatchFailed), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthWorldFullCatch, "UmbrellaElla.Health.World.FullHealthCatchIsValidAndNotHealing",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthWorldFullCatch::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	if (!TestNotNull(TEXT("Ella"), Test.Ella))
	{
		return false;
	}
	Test.Ella->GetAbsorb()->SetPose(EAbsorbPose::AbsorbFall);
	AUmbrellaProjectile* Yellow = FireAtElla(Test, EUmbrellaShotKind::EnemyYellow, 1.0f);
	TestTrue(TEXT("caught at full health"), Yellow && Yellow->IsActorBeingDestroyed());
	TestEqual(TEXT("health unchanged"), Test.Ella->GetHealth()->GetState().Active, 3.0f, 1.0e-4f);
	TestEqual(TEXT("lives unchanged"), Test.Ella->GetHealth()->GetState().Lives, 3);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthWorldPlayerShots, "UmbrellaElla.Health.World.PlayerShotsPassThroughElla",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthWorldPlayerShots::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	if (!TestNotNull(TEXT("Ella"), Test.Ella))
	{
		return false;
	}
	AUmbrellaProjectile* Mine = FireAtElla(Test, EUmbrellaShotKind::PlayerBlast, 10.0f);
	TestTrue(TEXT("shot lives on"), Mine && !Mine->IsActorBeingDestroyed());
	TestEqual(TEXT("no damage"), Test.Ella->GetHealth()->GetState().Active, 3.0f, 1.0e-4f);
	TestEqual(TEXT("no contact"), Test.CountOf(EUmbrellaEventType::ProjectileContact), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHealthWorldRetry, "UmbrellaElla.Health.World.RetryRestoresFullLivesAndHealth",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FHealthWorldRetry::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	if (!TestNotNull(TEXT("Ella"), Test.Ella))
	{
		return false;
	}
	UUmbrellaHealthComponent* Health = Test.Ella->GetHealth();
	Health->SetCapacity(4.0f, 4);
	Health->TakeHitAt(6.0f, NAME_None, 10.0);
	TestTrue(TEXT("a life was lost"), Health->GetState().Lives < 4);
	Health->ResetForRetry();
	TestEqual(TEXT("lives back to max"), Health->GetState().Lives, 4);
	TestEqual(TEXT("active full at capacity"), Health->GetState().Active, 4.0f, 1.0e-4f);
	TestEqual(TEXT("purchased capacity kept"), Health->GetState().Capacity, 4.0f, 1.0e-4f);
	return true;
}

#endif
