#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaSourceIds.h"
#include "Engine/World.h"
#include "Health/UmbrellaHealthComponent.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Motor/EllaMotorComponent.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "Umbrella/UmbrellaPlayerIds.h"

namespace
{
	constexpr EAutomationTestFlags MoveRetryFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter;
	const FName MoveRetryShot(TEXT("MoveRetryTestShot"));
}

// FLOW-09: a retry gives exactly 3 current lives and keeps the bought maximum (here 4), through the real bus event.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveRetryKeepsMax, "UmbrellaElla.Move.World.RetryGivesThreeLivesKeepsPurchasedMaximum", MoveRetryFlags)
bool FMoveRetryKeepsMax::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	UUmbrellaHealthComponent* Health = Ella->GetHealth();
	Health->SetCapacity(4.0f, 4);
	Health->TakeHitAt(6.0f, MoveRetryShot, 10.0);
	TestTrue(TEXT("lives were spent"), Health->GetState().Lives < 4);

	FUmbrellaEvent Retry;
	Retry.Type = EUmbrellaEventType::CheckpointRetried;
	Retry.TargetId = UmbrellaPlayerIds::Ella;
	Retry.Amount = 3;
	UUmbrellaEventBus::Get(Test.GetWorld())->Broadcast(Retry);

	TestEqual(TEXT("exactly 3 current lives"), Health->GetState().Lives, 3);
	TestEqual(TEXT("purchased maximum kept"), Health->GetState().MaxLives, 4);
	TestEqual(TEXT("active life full at its capacity"), Health->GetState().Active, 4.0f, 1.0e-4f);
	return true;
}

// OWL-16 / MOVE-21: the GDD baseline has dash invulnerability OFF, so a dash gives no protection and a hit lands.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveDashNoProtection, "UmbrellaElla.Move.World.DashGivesNoProtectionByDefault", MoveRetryFlags)
bool FMoveDashNoProtection::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();
	Adapter->ApplyPress(EUmbrellaInputAction::Shoot);
	Test.TickFrames(2, 1.0f / 60.0f);
	const FVector Before = Ella->GetActorLocation();
	Adapter->ApplyPress(EUmbrellaInputAction::DashForward);
	Test.TickFrames(2, 1.0f / 60.0f);
	TestTrue(TEXT("the dash is moving Ella"), FMath::Abs(Ella->GetActorLocation().X - Before.X) > 1.0f);
	TestFalse(TEXT("dash grants no protection"), Ella->GetMotor()->IsProtectingFromHits());
	UUmbrellaHealthComponent* Health = Ella->GetHealth();
	const float Full = Health->GetState().Active;
	TestEqual(TEXT("a hit during the dash lands"), Health->TakeHitAt(1.0f, MoveRetryShot, Test.GetWorld()->GetTimeSeconds()), EHitResult::Landed);
	TestTrue(TEXT("and costs health"), Health->GetState().Active < Full);
	return true;
}

#endif
