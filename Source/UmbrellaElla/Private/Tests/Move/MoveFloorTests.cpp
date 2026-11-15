#include "Misc/AutomationTest.h"
#include "Arena/UmbrellaArena.h"
#include "Attack/AttackEmitterComponent.h"
#include "Components/CapsuleComponent.h"
#include "Core/EllaCharacter.h"
#include "Engine/World.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Motor/EllaMotorComponent.h"
#include "Tests/Shared/UmbrellaTestWorld.h"

#if WITH_AUTOMATION_TESTS

// Agentplay blocker: holding Shoot for a long fight dropped Ella to z = -28063 with play bounds cleared. The arena
// bottom is the lethal boundary (WIND-03, game-spec "the bottom is lethal"): Ella must never fall through it.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldArenaFloorTest, "UmbrellaElla.Move.World.ArenaBottomHoldsEllaWithBoundsCleared", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldArenaFloorTest::RunTest(const FString& Parameters)
{
	const float MoveFloorDeltas[] = {1.0f / 30.0f, 1.0f / 60.0f, 1.0f / 120.0f};
	for (const float Delta : MoveFloorDeltas)
	{
		FUmbrellaTestWorld Test;
		AUmbrellaArena* Arena = Test.GetWorld()->SpawnActor<AUmbrellaArena>(FVector::ZeroVector, FRotator::ZeroRotator);
		if (!TestNotNull(TEXT("arena spawned"), Arena))
		{
			return false;
		}
		AEllaCharacter* Ella = Test.SpawnElla(Arena->GetPlayerStartLocation());
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		// What the agentplay hook and the playtest harness do before a fight.
		Ella->GetMotor()->ClearPlayBounds();
		const float BottomZ = static_cast<float>(Arena->LocalPoint(0.0f, 0.0f).Z);
		const float HalfHeight = Ella->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
		Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
		float LowestZ = TNumericLimits<float>::Max();
		const int32 MoveFloorFrames = FMath::RoundToInt(30.0f / Delta);
		for (int32 Frame = 0; Frame < MoveFloorFrames; ++Frame)
		{
			Test.TickFrames(1, Delta);
			LowestZ = FMath::Min(LowestZ, static_cast<float>(Ella->GetActorLocation().Z));
		}
		const FString At = FString::Printf(TEXT(" (dt %.4f)"), Delta);
		TestTrue(TEXT("never below the arena bottom") + At, LowestZ >= BottomZ + HalfHeight - 0.01f);
		TestEqual(TEXT("rests on the arena bottom, whole body on screen") + At, static_cast<float>(Ella->GetActorLocation().Z), BottomZ + HalfHeight, 0.01f);
		TestTrue(TEXT("motor reports the lethal bottom") + At, Ella->GetMotor()->IsAtPlayFloor());
		TestTrue(TEXT("Shoot still fires on the bottom") + At, Ella->GetAttack()->GetShotsFired() > 0);
		// Releasing Shoot rises off the bottom again.
		Ella->GetInputAdapter()->ApplyRelease(EUmbrellaInputAction::Shoot);
		Test.TickSeconds(0.5f, Delta);
		TestTrue(TEXT("rises off the bottom") + At, Ella->GetActorLocation().Z > BottomZ + HalfHeight + 1.0f);
		TestFalse(TEXT("left the bottom") + At, Ella->GetMotor()->IsAtPlayFloor());
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveFloorRuleTest, "UmbrellaElla.Move.Rules.ClampToPlayFloor", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveFloorRuleTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("below the floor is lifted to it"), UEllaMotorComponent::ClampToPlayFloor(-28063.0f, 44.0f), 44.0f);
	TestEqual(TEXT("above the floor is untouched"), UEllaMotorComponent::ClampToPlayFloor(540.0f, 44.0f), 540.0f);
	TestEqual(TEXT("no arena: no floor"), UEllaMotorComponent::ClampToPlayFloor(-28063.0f, TNumericLimits<float>::Lowest()), -28063.0f);
	return true;
}

#endif
