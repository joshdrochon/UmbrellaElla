#include "Tests/Health/HealthTestWorld.h"
#include "Misc/AutomationTest.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Projectile/UmbrellaProjectile.h"

#if WITH_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProjectileRuleAdvance, "UmbrellaElla.Projectile.MovesInXZAndKeepsDepth",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProjectileRuleAdvance::RunTest(const FString& Parameters)
{
	const FVector Next = ProjectileRules::Advance(FVector(10.0, 999.0, 20.0), FVector(100.0, 50.0, -40.0), 0.5f);
	TestEqual(TEXT("X"), Next.X, 60.0, 1.0e-4);
	TestEqual(TEXT("Z"), Next.Z, 0.0, 1.0e-4);
	TestEqual(TEXT("Y is the projectile depth"), Next.Y, static_cast<double>(UmbrellaDrawOrder::ProjectileY), 1.0e-4);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProjectileWorldMotion, "UmbrellaElla.Projectile.World.MovesAndExpires",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProjectileWorldMotion::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	FUmbrellaShotSpec Spec;
	Spec.Kind = EUmbrellaShotKind::EnemyRed;
	Spec.Origin = FVector(2000.0, 0.0, 2000.0);
	Spec.Velocity = FVector(240.0, 0.0, 0.0);
	Spec.Radius = 8.0f;
	Spec.Damage = 1.0f;
	Spec.LifetimeSeconds = 1.0f;
	AUmbrellaProjectile* Shot = AUmbrellaProjectile::Fire(Test.World, Spec);
	if (!TestNotNull(TEXT("shot"), Shot))
	{
		return false;
	}
	Shot->AdvanceShot(0.5f);
	TestEqual(TEXT("moved 120 in X"), Shot->GetActorLocation().X, 2120.0, 1.0e-3);
	TestEqual(TEXT("Z unchanged"), Shot->GetActorLocation().Z, 2000.0, 1.0e-3);
	TestEqual(TEXT("lifetime left"), Shot->GetLifetimeRemaining(), 0.5f, 1.0e-4f);
	TestFalse(TEXT("alive"), Shot->IsActorBeingDestroyed());
	Shot->AdvanceShot(0.5f);
	TestTrue(TEXT("expired"), Shot->IsActorBeingDestroyed());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProjectileWorldFastShot, "UmbrellaElla.Projectile.World.FastShotDoesNotTunnelThroughElla",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProjectileWorldFastShot::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	if (!TestNotNull(TEXT("Ella"), Test.Ella))
	{
		return false;
	}
	FUmbrellaShotSpec Spec;
	Spec.Kind = EUmbrellaShotKind::EnemyRed;
	Spec.Origin = Test.Ella->GetActorLocation() + FVector(-300.0, 0.0, 0.0);
	Spec.Velocity = FVector(3000.0, 0.0, 0.0);
	Spec.Radius = 8.0f;
	Spec.Damage = 1.0f;
	Spec.LifetimeSeconds = 2.0f;
	AUmbrellaProjectile* Shot = AUmbrellaProjectile::Fire(Test.World, Spec);
	if (!TestNotNull(TEXT("shot"), Shot))
	{
		return false;
	}
	TestFalse(TEXT("not yet in contact"), Shot->IsActorBeingDestroyed());
	Shot->AdvanceShot(0.2f); // 600 units in one step, past Ella
	TestTrue(TEXT("swept hit consumed the shot"), Shot->IsActorBeingDestroyed());
	TestEqual(TEXT("one hit"), Test.Ella->GetHealth()->GetState().Active, 2.0f, 1.0e-4f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProjectileWorldRouting, "UmbrellaElla.Projectile.World.RoutingRules",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProjectileWorldRouting::RunTest(const FString& Parameters)
{
	FHealthTestWorld Test;
	if (!TestNotNull(TEXT("Ella"), Test.Ella))
	{
		return false;
	}
	AActor* Other = Test.World->SpawnActor<AActor>();
	TestFalse(TEXT("player shot skips Ella"), ProjectileRules::CanShotTouch(EUmbrellaShotKind::PlayerBlast, Test.Ella));
	TestTrue(TEXT("player shot reaches others"), ProjectileRules::CanShotTouch(EUmbrellaShotKind::PlayerBlast, Other));
	TestTrue(TEXT("enemy shot reaches Ella"), ProjectileRules::CanShotTouch(EUmbrellaShotKind::EnemyRed, Test.Ella));
	TestFalse(TEXT("enemy shot never reaches the Keeper or any other actor"), ProjectileRules::CanShotTouch(EUmbrellaShotKind::EnemyRed, Other));
	TestFalse(TEXT("null target"), ProjectileRules::CanShotTouch(EUmbrellaShotKind::EnemyYellow, nullptr));
	return true;
}

#endif
