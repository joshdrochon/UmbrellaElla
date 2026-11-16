#include "Misc/AutomationTest.h"
#include "Arena/UmbrellaArena.h"
#include "Components/CapsuleComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/World.h"
#include "Health/UmbrellaHealthComponent.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Motor/EllaMotorComponent.h"
#include "Tests/Shared/UmbrellaTestWorld.h"

#if WITH_AUTOMATION_TESTS

// Josh, 14 Nov: "if you shoot you fall [and can fall to your death]. Also if you rise beyond the top of the ceiling it's
// also game over." Bottom = WIND-03, top = D-new-ceiling-lethal. The line is where the clamp stops her root (her head at
// the arena top, her feet at the arena bottom), so the ceiling clamp can never hold her alive. Start Game (arena x) and
// the Director's Cut route (x near the Keeper handoff, past the arena's own ceiling box) are both checked.
namespace MoveBoundaryTest
{
	const float RouteXs[] = {-1.0f, 19777.0f};
	const float Delta = 1.0f / 60.0f;

	struct FSetup
	{
		AUmbrellaArena* Arena = nullptr;
		AEllaCharacter* Ella = nullptr;
		float TopLine = 0.0f;
		float BottomLine = 0.0f;
		int32 Defeats = 0;
	};

	bool Spawn(FAutomationTestBase& T, FUmbrellaTestWorld& Test, float RouteX, FSetup& Out)
	{
		Out.Arena = Test.GetWorld()->SpawnActor<AUmbrellaArena>(FVector::ZeroVector, FRotator::ZeroRotator);
		if (!T.TestNotNull(TEXT("arena spawned"), Out.Arena))
		{
			return false;
		}
		FVector Start = Out.Arena->GetPlayerStartLocation();
		if (RouteX >= 0.0f)
		{
			Start.X = RouteX;
		}
		Out.Ella = Test.SpawnElla(Start);
		if (!T.TestNotNull(TEXT("Ella spawned"), Out.Ella) || !T.TestNotNull(TEXT("Ella has health"), Out.Ella->GetHealth()))
		{
			return false;
		}
		Out.Ella->GetMotor()->ClearPlayBounds();
		const float HalfHeight = Out.Ella->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
		Out.TopLine = static_cast<float>(Out.Arena->LocalPoint(0.0f, 1.0f).Z) - HalfHeight;
		Out.BottomLine = static_cast<float>(Out.Arena->LocalPoint(0.0f, 0.0f).Z) + HalfHeight;
		if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(Out.Ella))
		{
			int32* Count = &Out.Defeats;
			Bus->On(EUmbrellaEventType::PlayerDefeated).AddLambda([Count](const FUmbrellaEvent&) { ++*Count; });
		}
		return true;
	}

	void PlaceAt(AEllaCharacter* Ella, float Z)
	{
		FVector At = Ella->GetActorLocation();
		At.Z = Z;
		Ella->SetActorLocation(At);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldAboveCeilingDiesTest, "UmbrellaElla.Move.World.RisingPastCeilingTopDefeats", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldAboveCeilingDiesTest::RunTest(const FString& Parameters)
{
	for (const float RouteX : MoveBoundaryTest::RouteXs)
	{
		const FString At = RouteX < 0.0f ? TEXT(" (Start Game)") : TEXT(" (Director's Cut route)");
		// Placed above the top line: one tick defeats her.
		{
			FUmbrellaTestWorld Test;
			MoveBoundaryTest::FSetup S;
			if (!MoveBoundaryTest::Spawn(*this, Test, RouteX, S))
			{
				return false;
			}
			MoveBoundaryTest::PlaceAt(S.Ella, S.TopLine + 50.0f);
			Test.TickFrames(1, MoveBoundaryTest::Delta);
			TestTrue(TEXT("above the ceiling top is defeated") + At, S.Ella->GetHealth()->GetState().IsDefeated());
			Test.TickFrames(10, MoveBoundaryTest::Delta);
			TestEqual(TEXT("one PlayerDefeated") + At, S.Defeats, 1);
		}
		// Rising with nothing held from just under the line reaches it and dies: the ceiling cannot hold her alive.
		{
			FUmbrellaTestWorld Test;
			MoveBoundaryTest::FSetup S;
			if (!MoveBoundaryTest::Spawn(*this, Test, RouteX, S))
			{
				return false;
			}
			MoveBoundaryTest::PlaceAt(S.Ella, S.TopLine - 30.0f);
			Test.TickSeconds(3.0f, MoveBoundaryTest::Delta);
			TestTrue(TEXT("overhead rise into the ceiling is defeated") + At, S.Ella->GetHealth()->GetState().IsDefeated());
			TestEqual(TEXT("one PlayerDefeated on the rise") + At, S.Defeats, 1);
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldUnderCeilingLivesTest, "UmbrellaElla.Move.World.UnderCeilingLineLives", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldUnderCeilingLivesTest::RunTest(const FString& Parameters)
{
	for (const float RouteX : MoveBoundaryTest::RouteXs)
	{
		const FString At = RouteX < 0.0f ? TEXT(" (Start Game)") : TEXT(" (Director's Cut route)");
		FUmbrellaTestWorld Test;
		MoveBoundaryTest::FSetup S;
		if (!MoveBoundaryTest::Spawn(*this, Test, RouteX, S))
		{
			return false;
		}
		// At the ceiling, just under the line, holding Shoot: she falls away and lives.
		MoveBoundaryTest::PlaceAt(S.Ella, S.TopLine - 2.0f);
		S.Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
		Test.TickSeconds(0.5f, MoveBoundaryTest::Delta);
		TestFalse(TEXT("under the line lives") + At, S.Ella->GetHealth()->GetState().IsDefeated());
		TestEqual(TEXT("no PlayerDefeated") + At, S.Defeats, 0);
		TestTrue(TEXT("moved down from the ceiling") + At, S.Ella->GetActorLocation().Z < S.TopLine - 2.0f);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldShootFallsToDeathTest, "UmbrellaElla.Move.World.ShootHeldFallsAtFallSpeedToLethalBottom", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldShootFallsToDeathTest::RunTest(const FString& Parameters)
{
	const float FallSpeed = GetDefault<UUmbrellaTuning>()->Motor.FallSpeed;
	for (const float RouteX : MoveBoundaryTest::RouteXs)
	{
		const FString At = RouteX < 0.0f ? TEXT(" (Start Game)") : TEXT(" (Director's Cut route)");
		FUmbrellaTestWorld Test;
		MoveBoundaryTest::FSetup S;
		if (!MoveBoundaryTest::Spawn(*this, Test, RouteX, S))
		{
			return false;
		}
		MoveBoundaryTest::PlaceAt(S.Ella, S.TopLine - 100.0f);
		S.Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
		Test.TickSeconds(0.2f, MoveBoundaryTest::Delta);
		const float Z0 = static_cast<float>(S.Ella->GetActorLocation().Z);
		Test.TickSeconds(0.5f, MoveBoundaryTest::Delta);
		const float Z1 = static_cast<float>(S.Ella->GetActorLocation().Z);
		TestTrue(TEXT("shoot-held Ella descends") + At, Z1 < Z0);
		TestEqual(TEXT("descends at feel.json fall_speed") + At, (Z0 - Z1) * 2.0f, FallSpeed, FallSpeed * 0.02f);
		TestFalse(TEXT("alive in mid-air") + At, S.Ella->GetHealth()->GetState().IsDefeated());
		// Keep holding Shoot: she reaches the bottom and dies there.
		Test.TickSeconds(6.0f, MoveBoundaryTest::Delta);
		TestTrue(TEXT("reached the bottom") + At, S.Ella->GetMotor()->IsAtPlayFloor());
		TestTrue(TEXT("the bottom is lethal") + At, S.Ella->GetHealth()->GetState().IsDefeated());
		TestEqual(TEXT("one PlayerDefeated at the bottom") + At, S.Defeats, 1);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldSmokeHoldKeepsEllaAliveTest, "UmbrellaElla.Move.World.SmokeBoundaryHoldKeepsIdleEllaAlive", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldSmokeHoldKeepsEllaAliveTest::RunTest(const FString& Parameters)
{
	// plumefix, 14 Nov: an idle -SmokeKeeper run died at the ceiling at 4.5 s, before the first gust, so the GustTravel
	// capture was never taken. The smoke hook holds boundary death until its shot is out; letting go restores the rule.
	FUmbrellaTestWorld Test;
	MoveBoundaryTest::FSetup S;
	if (!MoveBoundaryTest::Spawn(*this, Test, MoveBoundaryTest::RouteXs[0], S))
	{
		return false;
	}
	UEllaMotorComponent* Motor = S.Ella->FindComponentByClass<UEllaMotorComponent>();
	if (!TestNotNull(TEXT("motor"), Motor))
	{
		return false;
	}
	Motor->SetBoundaryDeathHeld(true);
	MoveBoundaryTest::PlaceAt(S.Ella, S.TopLine - 30.0f);
	Test.TickSeconds(8.0f, MoveBoundaryTest::Delta);
	TestTrue(TEXT("held: idle Ella reaches the ceiling"), Motor->IsAtPlayCeiling());
	TestFalse(TEXT("held: idle Ella lives past the first gust (8 s)"), S.Ella->GetHealth()->GetState().IsDefeated());
	Motor->SetBoundaryDeathHeld(false);
	Test.TickFrames(2, MoveBoundaryTest::Delta);
	TestTrue(TEXT("released: the ceiling line defeats her again"), S.Ella->GetHealth()->GetState().IsDefeated());
	return true;
}

#endif
