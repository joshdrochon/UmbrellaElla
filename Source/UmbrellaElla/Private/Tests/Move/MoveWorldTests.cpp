#include "Engine/Engine.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Attack/AttackEmitterComponent.h"
#include "Components/CapsuleComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaTuning.h"
#include "Motor/HeroSizeRules.h"
#include "Core/UmbrellaEventBus.h"
#include "Field/WindCurrent.h"
#include "EngineUtils.h"
#include "Input/EllaInputAdapterComponent.h"
#include "InputMappingContext.h"
#include "Motor/EllaMotorComponent.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Settings/SettingsMenuSubsystem.h"
#include "Settings/SettingsModel.h"
#include "Engine/GameInstance.h"
#include "HAL/FileManager.h"
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
		TestEqual(TEXT("rises 240 in 1 s (D-new-move-speeds)"), static_cast<float>(Ella->GetActorLocation().Z), 240.0f, 0.5f);
		TestEqual(TEXT("no sideways drift"), static_cast<float>(Ella->GetActorLocation().X), 0.0f, 0.001f);
		TestEqual(TEXT("overhead state"), Ella->GetUmbrellaState()->GetAction(), EUmbrellaAction::Rise);
		TestEqual(TEXT("velocity up"), static_cast<float>(Ella->GetMotor()->GetVelocity().Z), 240.0f, 0.01f);
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
		TestEqual(TEXT("shoot-fall velocity"), static_cast<float>(Ella->GetMotor()->GetVelocity().Z), -660.0f, 0.01f);
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
		TestEqual(TEXT("absorb-fall falls 660"), static_cast<float>(Ella->GetActorLocation().Z), -660.0f, 0.5f);
		TestEqual(TEXT("absorb-fall does not shoot"), Ella->GetAttack()->GetShotsFired(), 0);

		// Both held: fast free fall, no shooting, no absorbing.
		Adapter->ApplyPress(EUmbrellaInputAction::Shoot);
		TestEqual(TEXT("free fall state"), Ella->GetUmbrellaState()->GetAction(), EUmbrellaAction::FreeFall);
		const double StartZ = Ella->GetActorLocation().Z;
		Test.TickSeconds(1.0f, Delta);
		TestEqual(TEXT("free fall falls 1220"), static_cast<float>(StartZ - Ella->GetActorLocation().Z), 1220.0f, 0.5f);
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
			TestEqual(TEXT("hop velocity"), static_cast<float>(Ella->GetMotor()->GetVelocity().X), 80.0f / 0.22f, 0.01f);
			TestTrue(TEXT("hop protects"), Ella->GetMotor()->IsHopProtected());
			Test.TickSeconds(0.5f, Delta);
			TestEqual(TEXT("hop moved 80"), static_cast<float>(Ella->GetActorLocation().X), 80.0f, 0.01f);
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
			TestEqual(TEXT("dash velocity"), static_cast<float>(Ella->GetMotor()->GetVelocity().X), 170.0f / 0.16f, 0.01f);
			TestFalse(TEXT("dash does not protect"), Ella->GetMotor()->IsHopProtected());
			Test.TickSeconds(0.5f, Delta);
			TestEqual(TEXT("dash moved 170"), static_cast<float>(Ella->GetActorLocation().X), 170.0f, 0.01f);
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
		TestEqual(TEXT("wind speed"), static_cast<float>(Ella->GetMotor()->GetVelocity().X), 400.0f, 5.0f);

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

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldWindVolumeTest, "UmbrellaElla.Move.World.RideCurrentFromVolume", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldWindVolumeTest::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla(FVector(-5000.0, 0.0, 0.0));
	AWindCurrent* Wind = Test.GetWorld()->SpawnActor<AWindCurrent>(FVector::ZeroVector, FRotator::ZeroRotator);
	if (!TestNotNull(TEXT("Ella spawned"), Ella) || !TestNotNull(TEXT("current spawned"), Wind))
	{
		return false;
	}
	Wind->SetHalfExtent(10000.0f, 10000.0f);
	Wind->SetCurrent(FVector(1.0, 0.0, 0.0), 200.0f);
	Test.TickFrames(2, 1.0f / 60.0f);
	TestFalse(TEXT("outside: not riding"), Ella->GetMotor()->IsRiding());

	// Move Ella into the volume, as the player does; the real overlap event carries the actor name as TargetId.
	Ella->SetActorLocation(FVector(0.0, 0.0, 0.0), false, nullptr, ETeleportType::TeleportPhysics);
	Test.TickFrames(2, 1.0f / 60.0f);
	Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Ride);
	const double XStart = Ella->GetActorLocation().X;
	Test.TickSeconds(1.0f, 1.0f / 60.0f);
	TestTrue(TEXT("riding the volume current"), Ella->GetMotor()->IsRiding());
	TestTrue(TEXT("positive X velocity"), Ella->GetMotor()->GetVelocity().X > 0.0);
	TestTrue(TEXT("carried right"), Ella->GetActorLocation().X > XStart + 50.0);
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
	TestEqual(TEXT("rise slowed"), static_cast<float>(Ella->GetMotor()->GetVelocity().Z), 240.0f * (0.3f + 0.7f / 3.0f), 0.01f);
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
	TestEqual(TEXT("trim up rises faster"), static_cast<float>(Ella->GetActorLocation().Z), 288.0f, 0.5f);
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


namespace
{
	/** Tuning copy with HeroSize and hitbox scale overridden. Workbench builds (editor tests) only; elsewhere the baked values. */
	FMotorTuning MoveTuningWithHeroSize(FMotorTuning Base, float HeroSize, float Hitbox)
	{
#if UMBRELLAELLA_WORKBENCH
		Base.HeroSize = HeroSize;
		Base.HitboxScale = Hitbox;
#endif
		return Base;
	}

}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveHeroSizeRuleTest, "UmbrellaElla.Move.HeroSizeRules", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveHeroSizeRuleTest::RunTest(const FString& Parameters)
{
	FMotorTuning Tuning;
	TestEqual(TEXT("reference HeroSize 1"), Tuning.HeroSize, 1.0f);
	TestEqual(TEXT("range lower 0.75"), Tuning.HeroSizeMin, 0.75f);
	TestEqual(TEXT("range upper 1.3"), Tuning.HeroSizeMax, 1.3f);
	TestEqual(TEXT("hitbox range 0.75..1"), Tuning.HitboxScaleMin, 0.75f);
	TestEqual(TEXT("hitbox upper 1"), Tuning.HitboxScaleMax, 1.0f);
	TestEqual(TEXT("actor scale 0.5 at HeroSize 1"), HeroSizeRules::ActorScale(Tuning), 0.5f);
#if UMBRELLAELLA_WORKBENCH
	Tuning = MoveTuningWithHeroSize(Tuning, 1.3f, 1.0f);
	TestEqual(TEXT("muzzle 57.2 / 7.8 at HeroSize 1.3"), static_cast<float>(HeroSizeRules::MuzzleOffset(FVector(44.0, 0.0, 6.0), Tuning).X), 57.2f, 0.01f);
	TestEqual(TEXT("muzzle Z 7.8 at HeroSize 1.3"), static_cast<float>(HeroSizeRules::MuzzleOffset(FVector(44.0, 0.0, 6.0), Tuning).Z), 7.8f, 0.01f);
	Tuning = MoveTuningWithHeroSize(Tuning, 5.0f, 1.0f);
	TestEqual(TEXT("HeroSize clamps to the range"), HeroSizeRules::ClampedHeroSize(Tuning), 1.3f);
	Tuning = MoveTuningWithHeroSize(Tuning, 5.0f, 0.1f);
	TestEqual(TEXT("hitbox scale clamps to the range"), HeroSizeRules::ClampedHitboxScale(Tuning), 0.75f);
#endif
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldHeroSizeTest, "UmbrellaElla.Move.World.HeroSizeScalesHurtboxAndMuzzle", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldHeroSizeTest::RunTest(const FString& Parameters)
{
	float RefHalfHeight = 0.0f;
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		const FMotorTuning Tuned = MoveTuningWithHeroSize(GetDefault<UUmbrellaTuning>()->Motor, 1.0f, 1.0f);
		Ella->GetMotor()->ApplyHeroSize(Tuned);
		Ella->GetAttack()->SetMotorTuningOverride(Tuned);
		TestEqual(TEXT("actor scale 0.5 at HeroSize 1"), static_cast<float>(Ella->GetActorScale3D().X), 0.5f, 0.0001f);
		RefHalfHeight = Ella->GetCapsuleComponent()->GetScaledCapsuleHalfHeight();
	}
#if !UMBRELLAELLA_WORKBENCH
	return true; // the 0.75/1.3 cases need the workbench tuning override
#endif
	const float Cases[][2] = {{0.75f, 1.0f}, {1.3f, 1.0f}, {1.0f, 0.75f}, {1.3f, 0.75f}};
	for (const float (&Case)[2] : Cases)
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		const FMotorTuning Tuned = MoveTuningWithHeroSize(GetDefault<UUmbrellaTuning>()->Motor, Case[0], Case[1]);
		Ella->GetMotor()->ApplyHeroSize(Tuned);
		Ella->GetAttack()->SetMotorTuningOverride(Tuned);
		TestEqual(TEXT("actor scale 0.5 x HeroSize"), static_cast<float>(Ella->GetActorScale3D().X), 0.5f * Case[0], 0.0001f);
		TestEqual(TEXT("hurtbox follows HeroSize and hitbox scale"), Ella->GetCapsuleComponent()->GetScaledCapsuleHalfHeight(), RefHalfHeight * Case[0] * Case[1], 0.01f);

		Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
		Test.TickSeconds(0.5f, 1.0f / 60.0f);
		const FUmbrellaShotSpec& Shot = Ella->GetAttack()->GetLastShot();
		const FVector Offset = Shot.Origin - Ella->GetActorLocation();
		TestTrue(TEXT("a shot was fired"), Ella->GetAttack()->GetShotsFired() > 0);
		TestEqual(TEXT("blast radius stays 6 (HAZ-10)"), Shot.Radius, 6.0f, 0.001f);
		// The first shot leaves from the muzzle at the moment of the volley; Ella has since fallen, so compare X only.
		TestEqual(TEXT("muzzle X follows HeroSize"), static_cast<float>(Offset.X), 44.0f * Case[0], 0.5f);
	}
	return true;
}

#endif
