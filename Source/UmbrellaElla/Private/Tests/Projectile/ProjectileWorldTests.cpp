#include "Tests/Health/HealthTestWorld.h"
#include "Misc/AutomationTest.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Components/BoxComponent.h"
#include "Core/UmbrellaCollision.h"

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

namespace
{
	/** A wall box at X=2300 whose response to the given shot channel is set by the test. */
	AActor* SpawnWall(UWorld* World, ECollisionChannel Channel, ECollisionResponse Response)
	{
		AActor* Wall = World->SpawnActor<AActor>();
		UBoxComponent* Box = NewObject<UBoxComponent>(Wall);
		Box->SetBoxExtent(FVector(20.0, 200.0, 400.0));
		Box->SetCollisionEnabled(ECollisionEnabled::QueryOnly);
		Box->SetCollisionObjectType(ECC_WorldStatic);
		Box->SetCollisionResponseToAllChannels(ECR_Ignore);
		Box->SetCollisionResponseToChannel(Channel, Response);
		Wall->SetRootComponent(Box);
		Box->RegisterComponent();
		Wall->SetActorLocation(FVector(2300.0, 0.0, 2000.0));
		return Wall;
	}

	bool ShotHitsWall(UWorld* World, EUmbrellaShotKind Kind, ECollisionResponse Response)
	{
		SpawnWall(World, ProjectileRules::ShotChannel(Kind), Response);
		FUmbrellaShotSpec Spec;
		Spec.Kind = Kind;
		Spec.Origin = FVector(2000.0, 0.0, 2000.0);
		Spec.Velocity = FVector(1000.0, 0.0, 0.0);
		Spec.Radius = 8.0f;
		Spec.Damage = 1.0f;
		Spec.LifetimeSeconds = 5.0f;
		AUmbrellaProjectile* Shot = AUmbrellaProjectile::Fire(World, Spec);
		if (!Shot)
		{
			return false;
		}
		Shot->AdvanceShot(0.4f); // 400 units: crosses the wall at X 2280..2320
		return Shot->IsActorBeingDestroyed();
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProjectileWorldWalls, "UmbrellaElla.Projectile.World.BlockingWallDestroysShot",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FProjectileWorldWalls::RunTest(const FString& Parameters)
{
	{
		FHealthTestWorld Test;
		TestTrue(TEXT("player shot stops at a wall that blocks PlayerShot"), ShotHitsWall(Test.World, EUmbrellaShotKind::PlayerBlast, ECR_Block));
	}
	{
		FHealthTestWorld Test;
		TestTrue(TEXT("enemy shot stops at a wall that blocks EnemyShot"), ShotHitsWall(Test.World, EUmbrellaShotKind::EnemyRed, ECR_Block));
	}
	{
		FHealthTestWorld Test;
		TestFalse(TEXT("shot flies through a wall that ignores its channel"), ShotHitsWall(Test.World, EUmbrellaShotKind::EnemyRed, ECR_Ignore));
	}
	return true;
}

#endif
