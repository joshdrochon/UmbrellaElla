#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Attack/AttackEmitterComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaPlayMode.h"
#include "Engine/GameInstance.h"
#include "HAL/FileManager.h"
#include "Health/UmbrellaHealthComponent.h"
#include "Input/EllaInputAdapterComponent.h"
#include "InputMappingContext.h"
#include "InputCoreTypes.h"
#include "Misc/Paths.h"
#include "Motor/EllaMotorComponent.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Settings/SettingsMenuSubsystem.h"
#include "Settings/SettingsModel.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "Umbrella/UmbrellaStateComponent.h"

namespace
{
	void MoveRideProofWind(UWorld* World, EUmbrellaEventType Type, float Speed)
	{
		FUmbrellaEvent Event;
		Event.Type = Type;
		Event.SourceId = FName(TEXT("RideProofCurrent"));
		Event.TargetId = FName(TEXT("Ella"));
		Event.Detail = Type == EUmbrellaEventType::WindEntered ? FName(TEXT("Right")) : NAME_None;
		Event.Value = Speed;
		UUmbrellaEventBus::Get(World)->Broadcast(Event);
	}

	AUmbrellaProjectile* MoveCatchProofFire(UWorld* World, AEllaCharacter* Ella, EUmbrellaShotKind Kind)
	{
		FUmbrellaShotSpec Spec;
		Spec.Kind = Kind;
		Spec.Origin = Ella->GetActorLocation();
		Spec.Radius = 8.0f;
		Spec.Damage = 1.0f;
		Spec.LifetimeSeconds = 2.0f;
		Spec.SourceId = FName(TEXT("CatchProofSource"));
		return AUmbrellaProjectile::Fire(World, Spec);
	}

	/** Which adapter action the live IMC_Default sends Key to (Count when none). */
	EUmbrellaInputAction MoveRemapProofActionFor(UEllaInputAdapterComponent* Adapter, const FKey& Key)
	{
		for (const FEnhancedActionKeyMapping& Mapping : Adapter->GetMappingContext()->GetMappings())
		{
			if (Mapping.Key != Key)
			{
				continue;
			}
			for (int32 Index = 0; Index < static_cast<int32>(EUmbrellaInputAction::Count); ++Index)
			{
				const EUmbrellaInputAction Id = static_cast<EUmbrellaInputAction>(Index);
				if (Adapter->GetInputAction(Id) == Mapping.Action)
				{
					return Id;
				}
			}
		}
		return EUmbrellaInputAction::Count;
	}

	struct FMoveCatchProofRun
	{
		int32 ShotsAfter = 0;
		float LastDamage = 0.0f;
		float ActiveBefore = 0.0f;
		float ActiveAfter = 0.0f;
		bool bCaught = false;
	};

	/** Hurt Ella once, optionally catch a yellow in absorb-fall, then shoot-fall for two seconds. */
	FMoveCatchProofRun MoveCatchProofRun(FAutomationTestBase& Owner, bool bCatch, EUmbrellaPlayMode Mode)
	{
		FMoveCatchProofRun Run;
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!Owner.TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return Run;
		}
		UAttackEmitterComponent* Emitter = Ella->GetAttack();
		Emitter->SetPlayMode(Mode);
		Emitter->SetDirectorLevel(1);
		UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();
		MoveCatchProofFire(Test.GetWorld(), Ella, EUmbrellaShotKind::EnemyRed);
		Test.TickSeconds(1.0f, 1.0f / 60.0f);
		Run.ActiveBefore = Ella->GetHealth()->GetState().Active;
		Adapter->ApplyPress(EUmbrellaInputAction::Absorb);
		Test.TickFrames(2, 1.0f / 60.0f);
		if (bCatch)
		{
			AUmbrellaProjectile* Yellow = MoveCatchProofFire(Test.GetWorld(), Ella, EUmbrellaShotKind::EnemyYellow);
			Run.bCaught = Yellow && Yellow->IsActorBeingDestroyed();
		}
		Test.TickFrames(2, 1.0f / 60.0f);
		Run.ActiveAfter = Ella->GetHealth()->GetState().Active;
		Adapter->ApplyRelease(EUmbrellaInputAction::Absorb);
		Test.TickFrames(2, 1.0f / 60.0f);
		const int32 Start = Emitter->GetShotsFired();
		Adapter->ApplyPress(EUmbrellaInputAction::Shoot);
		Test.TickSeconds(2.0f, 1.0f / 60.0f);
		Run.ShotsAfter = Emitter->GetShotsFired() - Start;
		Run.LastDamage = Emitter->GetLastShot().Damage;
		return Run;
	}
}

// MOVE-20: entering Absorb fall or Free fall disengages Ride; residual momentum decays.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveProofRideEndsInAbsorbAndFreeFall, "UmbrellaElla.Move.World.AbsorbAndFreeFallDisengageRide", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveProofRideEndsInAbsorbAndFreeFall::RunTest(const FString& Parameters)
{
	for (int32 Case = 0; Case < 2; ++Case)
	{
		const bool bFreeFall = Case == 1;
		const TCHAR* Label = bFreeFall ? TEXT("FreeFall") : TEXT("AbsorbFall");
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();
		MoveRideProofWind(Test.GetWorld(), EUmbrellaEventType::WindEntered, 200.0f);
		Adapter->ApplyPress(EUmbrellaInputAction::Ride);
		Test.TickSeconds(1.0f, 1.0f / 60.0f);
		TestTrue(*FString::Printf(TEXT("%s: riding before the fall"), Label), Ella->GetMotor()->IsRiding());

		Adapter->ApplyPress(EUmbrellaInputAction::Absorb);
		if (bFreeFall)
		{
			Adapter->ApplyPress(EUmbrellaInputAction::Shoot);
		}
		Test.TickFrames(1, 1.0f / 60.0f);
		TestEqual(*FString::Printf(TEXT("%s: state"), Label), Ella->GetUmbrellaState()->GetAction(), bFreeFall ? EUmbrellaAction::FreeFall : EUmbrellaAction::AbsorbFall);
		TestFalse(*FString::Printf(TEXT("%s: ride disengaged at once"), Label), Ella->GetMotor()->IsRiding());
		Test.TickSeconds(0.5f, 1.0f / 60.0f);
		TestFalse(*FString::Printf(TEXT("%s: still not riding with Ride held"), Label), Ella->GetMotor()->IsRiding());
		TestTrue(*FString::Printf(TEXT("%s: momentum decayed (%.2f)"), Label, Ella->GetMotor()->GetVelocity().X), FMath::Abs(Ella->GetMotor()->GetVelocity().X) < 1.0);
	}
	return true;
}

// MOVE-20: remapped Shoot and Absorb keys still give all four combinations (Rise, Shoot, Absorb, Free fall).
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveProofRemapKeepsCombos, "UmbrellaElla.Move.World.RemapKeepsFourCombinations", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveProofRemapKeepsCombos::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();
	Adapter->BuildInputAssets();
	const FString Path = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("UmbrellaEllaTests"), TEXT("Move"), TEXT("remap-combos.ini"));
	USettingsMenuSubsystem* Settings = NewObject<USettingsMenuSubsystem>(NewObject<UGameInstance>(GEngine));
	Settings->SetStorePath(Path);
	Settings->ReloadFromStore();
	Settings->EditSession().Remap(EUmbrellaInputAction::Shoot, 0, EKeys::F);
	Settings->EditSession().Remap(EUmbrellaInputAction::Absorb, 0, EKeys::G);
	Settings->SaveSettings(ESettingsPage::Controller);
	TestTrue(TEXT("mappings made"), Adapter->ApplySavedBindings(Settings) > 0);

	const EUmbrellaInputAction FAction = MoveRemapProofActionFor(Adapter, EKeys::F);
	const EUmbrellaInputAction GAction = MoveRemapProofActionFor(Adapter, EKeys::G);
	TestEqual(TEXT("F sends Shoot"), FAction, EUmbrellaInputAction::Shoot);
	TestEqual(TEXT("G sends Absorb"), GAction, EUmbrellaInputAction::Absorb);
	if (FAction == EUmbrellaInputAction::Count || GAction == EUmbrellaInputAction::Count)
	{
		IFileManager::Get().Delete(*Path);
		return false;
	}

	struct FCombo { bool bF; bool bG; EUmbrellaAction Expected; };
	const FCombo Combos[] = {
		{false, false, EUmbrellaAction::Rise},
		{true, false, EUmbrellaAction::ShootFall},
		{false, true, EUmbrellaAction::AbsorbFall},
		{true, true, EUmbrellaAction::FreeFall},
	};
	for (const FCombo& Combo : Combos)
	{
		Combo.bF ? Adapter->ApplyPress(FAction) : Adapter->ApplyRelease(FAction);
		Combo.bG ? Adapter->ApplyPress(GAction) : Adapter->ApplyRelease(GAction);
		Test.TickFrames(1, 1.0f / 60.0f);
		TestEqual(*FString::Printf(TEXT("F=%d G=%d"), Combo.bF, Combo.bG), Ella->GetUmbrellaState()->GetAction(), Combo.Expected);
	}
	IFileManager::Get().Delete(*Path);
	return true;
}

// UMB-05 / COM-05: a catch gives no ammunition, stored energy or weapon charge; reward eligibility never disables repair.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveProofCatchGivesNoCharge, "UmbrellaElla.Move.World.CatchGivesNoChargeButRepairs", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveProofCatchGivesNoCharge::RunTest(const FString& Parameters)
{
	const EUmbrellaPlayMode Modes[] = {EUmbrellaPlayMode::StartGame, EUmbrellaPlayMode::DirectorsCut};
	for (const EUmbrellaPlayMode Mode : Modes)
	{
		const TCHAR* Label = Mode == EUmbrellaPlayMode::DirectorsCut ? TEXT("DirectorsCut") : TEXT("StartGame");
		const FMoveCatchProofRun Plain = MoveCatchProofRun(*this, false, Mode);
		const FMoveCatchProofRun Caught = MoveCatchProofRun(*this, true, Mode);
		TestTrue(*FString::Printf(TEXT("%s: the yellow was caught"), Label), Caught.bCaught);
		TestTrue(*FString::Printf(TEXT("%s: hurt before the catch (%.2f)"), Label, Caught.ActiveBefore), Caught.ActiveBefore < 3.0f);
		TestEqual(*FString::Printf(TEXT("%s: catch repairs 0.5"), Label), Caught.ActiveAfter, Caught.ActiveBefore + 0.5f, 1.0e-4f);
		TestTrue(*FString::Printf(TEXT("%s: shots fired"), Label), Plain.ShotsAfter > 0);
		TestEqual(*FString::Printf(TEXT("%s: same shot count after a catch"), Label), Caught.ShotsAfter, Plain.ShotsAfter);
		TestEqual(*FString::Printf(TEXT("%s: same shot damage after a catch"), Label), Caught.LastDamage, Plain.LastDamage, 1.0e-4f);
	}
	return true;
}

#endif
