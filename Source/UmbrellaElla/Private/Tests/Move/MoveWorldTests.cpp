#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Attack/AttackEmitterComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEventBus.h"
#include "EngineUtils.h"
#include "Input/EllaInputAdapterComponent.h"
#include "InputMappingContext.h"
#include "Motor/EllaMotorComponent.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Settings/SettingsMenuSubsystem.h"
#include "Settings/SettingsModel.h"
#include "Engine/GameInstance.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "Umbrella/UmbrellaStateComponent.h"

namespace
{
	struct FLiftSpy
	{
		void OnLift(const FUmbrellaEvent& Event)
		{
			SeenLift = Event.Value;
		}

		float SeenLift = -1.0f;
	};

	const float WorldDeltas[] = {1.0f / 30.0f, 1.0f / 60.0f, 1.0f / 120.0f};

	void Broadcast(UWorld* World, EUmbrellaEventType Type, FName Source, FName Target, FName Detail, float Value, int32 Amount = 0)
	{
		FUmbrellaEvent Event;
		Event.Type = Type;
		Event.SourceId = Source;
		Event.TargetId = Target;
		Event.Detail = Detail;
		Event.Value = Value;
		Event.Amount = Amount;
		UUmbrellaEventBus::Get(World)->Broadcast(Event);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldRiseTest, "UmbrellaElla.Move.World.RiseWithNothingHeld", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldRiseTest::RunTest(const FString& Parameters)
{
	for (const float Delta : WorldDeltas)
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		Test.TickSeconds(1.0f, Delta);
		TestEqual(TEXT("rises 120 in 1 s"), static_cast<float>(Ella->GetActorLocation().Z), 120.0f, 0.5f);
		TestEqual(TEXT("no sideways drift"), static_cast<float>(Ella->GetActorLocation().X), 0.0f, 0.001f);
		TestEqual(TEXT("overhead state"), Ella->GetUmbrellaState()->GetAction(), EUmbrellaAction::Rise);
		TestEqual(TEXT("velocity up"), static_cast<float>(Ella->GetMotor()->GetVelocity().Z), 120.0f, 0.01f);
		TestEqual(TEXT("no shots while rising"), Ella->GetAttack()->GetShotsFired(), 0);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldShootFallTest, "UmbrellaElla.Move.World.ShootFallFiresRightOnlyWhileDropping", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldShootFallTest::RunTest(const FString& Parameters)
{
	for (const float Delta : WorldDeltas)
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		Test.TickSeconds(0.5f, Delta);
		TestEqual(TEXT("nothing fired while rising"), Ella->GetAttack()->GetShotsFired(), 0);

		Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
		Test.TickSeconds(1.0f, Delta);
		const int32 Fired = Ella->GetAttack()->GetShotsFired();
		TestTrue(FString::Printf(TEXT("about 5 shots in 1 s of shoot-fall at delta %f, got %d"), Delta, Fired), Fired >= 5 && Fired <= 6);
		TestEqual(TEXT("shoot-fall velocity"), static_cast<float>(Ella->GetMotor()->GetVelocity().Z), -330.0f, 0.01f);
		TestEqual(TEXT("every shot became a projectile"), Test.CountActors<AUmbrellaProjectile>(), Fired);
		for (TActorIterator<AUmbrellaProjectile> It(Test.GetWorld()); It; ++It)
		{
			const FUmbrellaShotSpec& Spec = It->GetSpec();
			TestEqual(TEXT("kind"), Spec.Kind, EUmbrellaShotKind::PlayerBlast);
			TestTrue(TEXT("always to +X"), Spec.Velocity.X > 0.0 && Spec.Velocity.Z == 0.0 && Spec.Velocity.Y == 0.0);
			TestEqual(TEXT("speed 700"), static_cast<float>(Spec.Velocity.X), 700.0f);
			TestEqual(TEXT("damage 10"), Spec.Damage, 10.0f);
			TestEqual(TEXT("range 1500"), Spec.Velocity.X * Spec.LifetimeSeconds, 1500.0, 0.01);
		}

		// Releasing Shoot rises again and stops fire.
		Ella->GetInputAdapter()->ApplyRelease(EUmbrellaInputAction::Shoot);
		Test.TickSeconds(1.0f, Delta);
		TestEqual(TEXT("no more shots after release"), Ella->GetAttack()->GetShotsFired(), Fired);
		TestEqual(TEXT("rising again"), Ella->GetUmbrellaState()->GetAction(), EUmbrellaAction::Rise);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldAbsorbFallTest, "UmbrellaElla.Move.World.AbsorbFallAndFreeFall", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldAbsorbFallTest::RunTest(const FString& Parameters)
{
	for (const float Delta : WorldDeltas)
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();
		Adapter->ApplyPress(EUmbrellaInputAction::Absorb);
		Test.TickSeconds(1.0f, Delta);
		TestEqual(TEXT("absorb-fall state"), Ella->GetUmbrellaState()->GetAction(), EUmbrellaAction::AbsorbFall);
		TestEqual(TEXT("absorb-fall falls 330"), static_cast<float>(Ella->GetActorLocation().Z), -330.0f, 0.5f);
		TestEqual(TEXT("absorb-fall does not shoot"), Ella->GetAttack()->GetShotsFired(), 0);

		// Both held: fast free fall, no shooting, no absorbing.
		Adapter->ApplyPress(EUmbrellaInputAction::Shoot);
		TestEqual(TEXT("free fall state"), Ella->GetUmbrellaState()->GetAction(), EUmbrellaAction::FreeFall);
		const double StartZ = Ella->GetActorLocation().Z;
		Test.TickSeconds(1.0f, Delta);
		TestEqual(TEXT("free fall falls 610"), static_cast<float>(StartZ - Ella->GetActorLocation().Z), 610.0f, 0.5f);
		TestEqual(TEXT("free fall does not shoot"), Ella->GetAttack()->GetShotsFired(), 0);
		TestEqual(TEXT("no projectiles"), Test.CountActors<AUmbrellaProjectile>(), 0);

		// Letting Absorb go while Shoot is held: shoot-fall.
		Adapter->ApplyRelease(EUmbrellaInputAction::Absorb);
		TestEqual(TEXT("back to shoot-fall"), Ella->GetUmbrellaState()->GetAction(), EUmbrellaAction::ShootFall);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldHopDashTest, "UmbrellaElla.Move.World.HopAndDashMoveAsTuned", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldHopDashTest::RunTest(const FString& Parameters)
{
	for (const float Delta : WorldDeltas)
	{
		{
			FUmbrellaTestWorld Test;
			AEllaCharacter* Ella = Test.SpawnElla();
			if (!TestNotNull(TEXT("Ella spawned"), Ella))
			{
				return false;
			}
			Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Hop);
			Test.TickFrames(1, Delta);
			TestEqual(TEXT("hop velocity"), static_cast<float>(Ella->GetMotor()->GetVelocity().X), 40.0f / 0.22f, 0.01f);
			TestTrue(TEXT("hop protects"), Ella->GetMotor()->IsHopProtected());
			Test.TickSeconds(0.5f, Delta);
			TestEqual(TEXT("hop moved 40"), static_cast<float>(Ella->GetActorLocation().X), 40.0f, 0.01f);
			TestFalse(TEXT("protection over"), Ella->GetMotor()->IsHopProtected());
		}
		{
			FUmbrellaTestWorld Test;
			AEllaCharacter* Ella = Test.SpawnElla();
			if (!TestNotNull(TEXT("Ella spawned"), Ella))
			{
				return false;
			}
			UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();
			Adapter->ApplyPress(EUmbrellaInputAction::Shoot);
			Adapter->ApplyPress(EUmbrellaInputAction::DashForward);
			Test.TickFrames(1, Delta);
			TestEqual(TEXT("dash velocity"), static_cast<float>(Ella->GetMotor()->GetVelocity().X), 85.0f / 0.16f, 0.01f);
			TestFalse(TEXT("dash does not protect"), Ella->GetMotor()->IsHopProtected());
			Test.TickSeconds(0.5f, Delta);
			TestEqual(TEXT("dash moved 85"), static_cast<float>(Ella->GetActorLocation().X), 85.0f, 0.01f);
			Adapter->ApplyAxis(EUmbrellaInputAction::MoveX, -1.0f);
			Adapter->ApplyPress(EUmbrellaInputAction::Hop);
			Test.TickSeconds(0.5f, Delta);
			TestEqual(TEXT("context dash back with left input"), static_cast<float>(Ella->GetActorLocation().X), 0.0f, 0.01f);
			TestEqual(TEXT("still dropping the whole time"), Ella->GetUmbrellaState()->GetAction(), EUmbrellaAction::ShootFall);
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldWindTest, "UmbrellaElla.Move.World.RideCurrentFromEvents", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldWindTest::RunTest(const FString& Parameters)
{
	for (const float Delta : WorldDeltas)
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();
		Broadcast(Test.GetWorld(), EUmbrellaEventType::WindEntered, FName(TEXT("Current1")), FName(TEXT("Ella")), FName(TEXT("Right")), 200.0f);
		Test.TickSeconds(1.0f, Delta);
		TestEqual(TEXT("inside but not riding: no push"), static_cast<float>(Ella->GetActorLocation().X), 0.0f, 0.001f);
		Adapter->ApplyPress(EUmbrellaInputAction::Ride);
		Test.TickSeconds(2.0f, Delta);
		TestTrue(TEXT("riding"), Ella->GetMotor()->IsRiding());
		TestTrue(TEXT("carried right"), Ella->GetActorLocation().X > 100.0);
		TestEqual(TEXT("wind speed"), static_cast<float>(Ella->GetMotor()->GetVelocity().X), 200.0f, 5.0f);

		// Entering a fall disengages the ride.
		Adapter->ApplyPress(EUmbrellaInputAction::Shoot);
		Test.TickSeconds(0.5f, Delta);
		TestFalse(TEXT("not riding in a fall"), Ella->GetMotor()->IsRiding());
		TestTrue(TEXT("momentum decayed"), FMath::Abs(Ella->GetMotor()->GetVelocity().X) < 1.0);
		Adapter->ApplyRelease(EUmbrellaInputAction::Shoot);

		// Leaving the current ends the push.
		Broadcast(Test.GetWorld(), EUmbrellaEventType::WindExited, FName(TEXT("Current1")), FName(TEXT("Ella")), NAME_None, 0.0f);
		const double XAfter = Ella->GetActorLocation().X;
		Test.TickSeconds(1.0f, Delta);
		TestEqual(TEXT("no push after exit"), static_cast<float>(Ella->GetActorLocation().X), static_cast<float>(XAfter), 1.0f);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldLiftTest, "UmbrellaElla.Move.World.LiftScalesWithHealth", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldLiftTest::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	FLiftSpy Spy;
	FDelegateHandle Handle = UUmbrellaEventBus::Get(Test.GetWorld())->On(EUmbrellaEventType::LiftAvailabilityChanged).AddRaw(&Spy, &FLiftSpy::OnLift);
	Broadcast(Test.GetWorld(), EUmbrellaEventType::PlayerHealthChanged, FName(TEXT("Health")), FName(TEXT("Ella")), NAME_None, 1.0f, 3);
	Test.TickFrames(1, 1.0f / 60.0f);
	TestEqual(TEXT("lift event"), Spy.SeenLift, 0.3f + 0.7f / 3.0f, 0.001f);
	TestEqual(TEXT("lift on the motor"), Ella->GetMotor()->GetLiftMultiplier(), 0.3f + 0.7f / 3.0f, 0.001f);
	TestEqual(TEXT("rise slowed"), static_cast<float>(Ella->GetMotor()->GetVelocity().Z), 120.0f * (0.3f + 0.7f / 3.0f), 0.01f);
	Broadcast(Test.GetWorld(), EUmbrellaEventType::PlayerHealthChanged, FName(TEXT("Health")), FName(TEXT("Ella")), NAME_None, 3.0f, 3);
	Test.TickFrames(1, 1.0f / 60.0f);
	TestEqual(TEXT("repair restores lift"), Ella->GetMotor()->GetLiftMultiplier(), 1.0f, 0.001f);
	UUmbrellaEventBus::Get(Test.GetWorld())->On(EUmbrellaEventType::LiftAvailabilityChanged).Remove(Handle);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldLockTest, "UmbrellaElla.Move.World.LockStopsMotionAndFire", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldLockTest::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
	Ella->GetUmbrellaState()->SetLocked(true);
	Test.TickSeconds(1.0f, 1.0f / 60.0f);
	TestEqual(TEXT("locked: no motion"), static_cast<float>(Ella->GetActorLocation().Z), 0.0f, 0.001f);
	TestEqual(TEXT("locked: no shots"), Ella->GetAttack()->GetShotsFired(), 0);
	Ella->GetUmbrellaState()->SetLocked(false);
	Test.TickSeconds(0.5f, 1.0f / 60.0f);
	TestEqual(TEXT("trigger held through the lock does not fire"), Ella->GetAttack()->GetShotsFired(), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldBoundsTest, "UmbrellaElla.Move.World.BoundsClampPosition", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldBoundsTest::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	Ella->GetMotor()->SetPlayBounds(FBox2D(FVector2D(-100.0, -50.0), FVector2D(100.0, 50.0)));
	Test.TickSeconds(2.0f, 1.0f / 60.0f);
	TestEqual(TEXT("ceiling holds"), static_cast<float>(Ella->GetActorLocation().Z), 50.0f, 0.001f);
	Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Absorb);
	Test.TickSeconds(3.0f, 1.0f / 60.0f);
	TestEqual(TEXT("floor holds"), static_cast<float>(Ella->GetActorLocation().Z), -50.0f, 0.001f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldAssetsTest, "UmbrellaElla.Move.World.InputAssetsBuilt", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldAssetsTest::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();
	Adapter->BuildInputAssets();
	TestNotNull(TEXT("IMC_Default"), Adapter->GetMappingContext());
	TestNotNull(TEXT("IA_Shoot"), Adapter->GetInputAction(EUmbrellaInputAction::Shoot));
	TestNotNull(TEXT("IA_Ride"), Adapter->GetInputAction(EUmbrellaInputAction::Ride));
	TestNotNull(TEXT("IA_Trim"), Adapter->GetInputAction(EUmbrellaInputAction::Trim));
	TestEqual(TEXT("mappings"), Adapter->GetMappingContext()->GetMappings().Num(), UmbrellaInputBindings::BuildDefaults().Num());
	Adapter->ApplyAxis(EUmbrellaInputAction::Trim, 1.0f);
	Test.TickSeconds(1.0f, 1.0f / 60.0f);
	TestEqual(TEXT("trim up rises faster"), static_cast<float>(Ella->GetActorLocation().Z), 144.0f, 0.5f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldSavedRemapTest, "UmbrellaElla.Move.World.SavedRemapReachesLiveContext", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldSavedRemapTest::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();
	Adapter->BuildInputAssets();
	TestEqual(TEXT("no settings leaves the context alone"), Adapter->ApplySavedBindings(nullptr), 0);

	const FString Path = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("UmbrellaEllaTests"), TEXT("Move"), TEXT("remap.ini"));
	USettingsMenuSubsystem* Settings = NewObject<USettingsMenuSubsystem>(NewObject<UGameInstance>(GEngine));
	Settings->SetStorePath(Path);
	Settings->ReloadFromStore();
	Settings->EditSession().Remap(EUmbrellaInputAction::Shoot, 0, EKeys::F);
	Settings->SaveSettings(ESettingsPage::Controller);

	TestTrue(TEXT("mappings made"), Adapter->ApplySavedBindings(Settings) > 0);
	const UInputAction* Shoot = Adapter->GetInputAction(EUmbrellaInputAction::Shoot);
	bool bHasF = false;
	for (const FEnhancedActionKeyMapping& Mapping : Adapter->GetMappingContext()->GetMappings())
	{
		bHasF |= Mapping.Action == Shoot && Mapping.Key == EKeys::F;
	}
	TestTrue(TEXT("live IMC_Default maps Shoot to the saved F"), bHasF);
	IFileManager::Get().Delete(*Path);
	return true;
}

#endif
