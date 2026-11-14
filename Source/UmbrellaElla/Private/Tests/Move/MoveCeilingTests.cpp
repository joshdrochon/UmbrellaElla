#include "Misc/AutomationTest.h"
#include "Arena/UmbrellaArena.h"
#include "Components/CapsuleComponent.h"
#include "Core/EllaCharacter.h"
#include "Engine/World.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Motor/EllaMotorComponent.h"
#include "Tests/Shared/UmbrellaTestWorld.h"

#if WITH_AUTOMATION_TESTS

// Agentplay B7: on the Director's Cut route Ella rose without limit with nothing held (z 14 962 after 60 s), while in
// Start Game the arena ceiling stopped her at z 1 036. The GDD names a ceiling constraint (MOVE-19) but no number, so the
// arena's top is the ceiling. The route places Ella far right of the arena's own ceiling box, so the test does the same.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldRouteCeilingTest, "UmbrellaElla.Move.World.RouteCeilingHoldsEllaInPicture", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldRouteCeilingTest::RunTest(const FString& Parameters)
{
	const float MoveCeilingDeltas[] = {1.0f / 30.0f, 1.0f / 60.0f, 1.0f / 120.0f};
	// Route x near the Keeper handoff (LevelPlan::KeeperHandoffX, about 19 777): far past the arena's ceiling box.
	const float MoveCeilingRouteX = 19777.0f;
	for (const float Delta : MoveCeilingDeltas)
	{
		FUmbrellaTestWorld Test;
		AUmbrellaArena* Arena = Test.GetWorld()->SpawnActor<AUmbrellaArena>(FVector::ZeroVector, FRotator::ZeroRotator);
		if (!TestNotNull(TEXT("arena spawned"), Arena))
		{
			return false;
		}
		FVector Start = Arena->GetPlayerStartLocation();
		Start.X = MoveCeilingRouteX;
		AEllaCharacter* Ella = Test.SpawnElla(Start);
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		Ella->GetMotor()->ClearPlayBounds();
		const float TopZ = static_cast<float>(Arena->LocalPoint(0.0f, 1.0f).Z);
		const float HalfHeight = Ella->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
		float HighestZ = TNumericLimits<float>::Lowest();
		const int32 MoveCeilingFrames = FMath::RoundToInt(60.0f / Delta);
		for (int32 Frame = 0; Frame < MoveCeilingFrames; ++Frame)
		{
			Test.TickFrames(1, Delta);
			HighestZ = FMath::Max(HighestZ, static_cast<float>(Ella->GetActorLocation().Z));
		}
		const FString At = FString::Printf(TEXT(" (dt %.4f)"), Delta);
		TestTrue(TEXT("never above the arena top, nothing held for 60 s") + At, HighestZ <= TopZ - HalfHeight + 0.01f);
		TestEqual(TEXT("rests at the ceiling, whole body in the picture") + At, static_cast<float>(Ella->GetActorLocation().Z), TopZ - HalfHeight, 0.01f);
		TestTrue(TEXT("motor reports the ceiling") + At, Ella->GetMotor()->IsAtPlayCeiling());
		TestTrue(TEXT("no upward speed stored at the ceiling") + At, Ella->GetMotor()->GetVelocity().Z <= 0.0f);
		// Holding Shoot drops her off the ceiling at once (no stored rise to burn off).
		Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
		Test.TickSeconds(0.5f, Delta);
		TestTrue(TEXT("drops off the ceiling on Shoot") + At, Ella->GetActorLocation().Z < TopZ - HalfHeight - 1.0f);
		TestFalse(TEXT("left the ceiling") + At, Ella->GetMotor()->IsAtPlayCeiling());
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveCeilingRuleTest, "UmbrellaElla.Move.Rules.ClampToPlayCeiling", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveCeilingRuleTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("above the ceiling is lowered to it"), UEllaMotorComponent::ClampToPlayCeiling(14962.0f, 1036.0f), 1036.0f);
	TestEqual(TEXT("below the ceiling is untouched"), UEllaMotorComponent::ClampToPlayCeiling(540.0f, 1036.0f), 540.0f);
	TestEqual(TEXT("no arena: no ceiling"), UEllaMotorComponent::ClampToPlayCeiling(14962.0f, TNumericLimits<float>::Max()), 14962.0f);
	return true;
}

#endif
