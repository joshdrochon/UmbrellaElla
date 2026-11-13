#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Attack/AttackEmitterComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaPlayMode.h"
#include "Core/UmbrellaSourceIds.h"
#include "Core/UmbrellaTuning.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Health/UmbrellaHealthComponent.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Owl/KeeperOfTime.h"
#include "Owl/KeeperPartComponent.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "Umbrella/UmbrellaStateComponent.h"

namespace
{
	constexpr EAutomationTestFlags MoveKeeperFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter;

	/** Real Ella (health, state, motor) plus the Encounter Director stepped by hand, with the bus events recorded. */
	struct FMoveKeeperRig
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = nullptr;
		UEncounterDirectorSubsystem* Director = nullptr;
		TSharedRef<TArray<FUmbrellaEvent>> Seen = MakeShared<TArray<FUmbrellaEvent>>();
		FDelegateHandle CheckpointHandle;
		double Clock = 10.0;

		explicit FMoveKeeperRig(EUmbrellaPlayMode Mode)
		{
			Ella = Test.SpawnElla();
			Director = Test.GetWorld()->GetSubsystem<UEncounterDirectorSubsystem>();
			if (Ella)
			{
				Ella->GetAttack()->SetPlayMode(Mode);
			}
			if (Director && Ella)
			{
				Director->SetManualStepping(true);
				Director->SetPlayerActor(Ella);
			}
			if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(Test.GetWorld()))
			{
				CheckpointHandle = Bus->On(EUmbrellaEventType::CheckpointReached).AddLambda([Sink = Seen](const FUmbrellaEvent& Event) { Sink->Add(Event); });
			}
		}

		~FMoveKeeperRig()
		{
			if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(Test.GetWorld()))
			{
				Bus->On(EUmbrellaEventType::CheckpointReached).Remove(CheckpointHandle);
			}
		}

		bool Ready() const { return Ella && Director; }

		void Advance(float Seconds)
		{
			for (float T = 0.0f; T < Seconds; T += 0.05f)
			{
				Director->AdvanceFight(0.05f);
			}
		}

		/** One ordinary hit that lands (clock moves past the post-hit window each time). */
		void Hit(float Damage = 1.0f)
		{
			Clock += 5.0;
			Ella->GetHealth()->TakeHitAt(Damage, NAME_None, Clock);
		}

		void Shoot(EKeeperPart Part, float Damage)
		{
			UKeeperPartComponent* Component = Director->GetKeeper() ? Director->GetKeeper()->GetPartComponent(Part) : nullptr;
			if (Component)
			{
				FUmbrellaShotSpec Shot;
				Shot.Kind = EUmbrellaShotKind::PlayerBlast;
				Shot.Damage = Damage;
				Component->ReceiveShot(Shot, FVector::ZeroVector);
			}
		}
	};
}

// FLOW-09: death then checkpoint retry returns Ella with exactly 3 current lives and a full life, in both modes.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveKeeperRetryThreeLives, "UmbrellaElla.Move.World.KeeperRetryGivesThreeLivesInBothModes", MoveKeeperFlags)
bool FMoveKeeperRetryThreeLives::RunTest(const FString& Parameters)
{
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	for (const EUmbrellaPlayMode Mode : {EUmbrellaPlayMode::StartGame, EUmbrellaPlayMode::DirectorsCut})
	{
		FMoveKeeperRig Rig(Mode);
		if (!TestTrue(TEXT("rig built"), Rig.Ready()))
		{
			return false;
		}
		Rig.Director->BeginKeeperFight();
		Rig.Advance(0.5f);
		// Lose lives first: the retry must restore 3 regardless of how many were left at the checkpoint.
		Rig.Hit(3.0f);
		TestEqual(TEXT("two lives left"), Rig.Ella->GetHealth()->GetState().Lives, 2);
		for (int32 Index = 0; Index < 6; ++Index)
		{
			Rig.Hit(1.0f);
		}
		TestTrue(TEXT("defeated"), Rig.Ella->GetHealth()->GetState().IsDefeated());
		TestTrue(TEXT("ENDING_FAILURE"), Rig.Director->GetState() == EEncounterState::EndingFailure);
		Rig.Director->ResetForRestart();
		TestEqual(TEXT("exactly 3 lives after retry"), Rig.Ella->GetHealth()->GetState().Lives, 3);
		TestEqual(TEXT("active life full"), Rig.Ella->GetHealth()->GetState().Active, Rig.Ella->GetHealth()->GetState().Capacity, 1.0e-4f);
	}
	return true;
}

// OWL-06 / OWL-10: advancing a phase carries Ella's health over, and every phase start is a checkpoint, in both modes.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveKeeperHealthCarried, "UmbrellaElla.Move.World.KeeperPhasesCarryHealthAndCheckpointInBothModes", MoveKeeperFlags)
bool FMoveKeeperHealthCarried::RunTest(const FString& Parameters)
{
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	for (const EUmbrellaPlayMode Mode : {EUmbrellaPlayMode::StartGame, EUmbrellaPlayMode::DirectorsCut})
	{
		FMoveKeeperRig Rig(Mode);
		if (!TestTrue(TEXT("rig built"), Rig.Ready()))
		{
			return false;
		}
		Rig.Director->BeginKeeperFight();
		Rig.Hit(1.0f);
		const FHealthState Before = Rig.Ella->GetHealth()->GetState();
		TestEqual(TEXT("one hit taken"), Before.Active, 2.0f, 1.0e-4f);
		TestEqual(TEXT("wings phase: one checkpoint so far"), Rig.Seen->Num(), 1);
		Rig.Advance(2.2f);
		Rig.Shoot(EKeeperPart::Wings, 1000.0f);
		Rig.Advance(2.2f);
		TestTrue(TEXT("mechanisms phase"), Rig.Director->GetPhase() == EKeeperPhase::Mechanisms);
		TestEqual(TEXT("mechanisms start is a checkpoint"), Rig.Seen->Num(), 2);
		const FHealthState After = Rig.Ella->GetHealth()->GetState();
		TestEqual(TEXT("active health carried through the phase"), After.Active, Before.Active, 1.0e-4f);
		TestEqual(TEXT("lives carried through the phase"), After.Lives, Before.Lives);
		// Breaking a mechanism never adds a checkpoint.
		Rig.Shoot(EKeeperPart::Front, 1000.0f);
		Rig.Advance(0.5f);
		TestTrue(TEXT("front broken"), Rig.Director->GetModel().IsPartBroken(EKeeperPart::Front));
		TestEqual(TEXT("no mid-mechanism checkpoint"), Rig.Seen->Num(), 2);
	}
	return true;
}

// OWL-13: a Keeper yellow's ordinary contact costs 1 health, and Shoot alone never catches it.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveKeeperYellowContact, "UmbrellaElla.Move.World.KeeperYellowContactCostsOneAndShootNeverCatches", MoveKeeperFlags)
bool FMoveKeeperYellowContact::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella"), Ella))
	{
		return false;
	}
	Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
	Test.TickFrames(2, 1.0f / 60.0f);
	FUmbrellaShotSpec Spec;
	Spec.Kind = EUmbrellaShotKind::EnemyYellow;
	Spec.Origin = Ella->GetActorLocation();
	Spec.Radius = 8.0f;
	Spec.Damage = 0.0f; // no explicit damage: the tuned ordinary contact damage applies
	Spec.LifetimeSeconds = 2.0f;
	Spec.SourceId = UmbrellaSourceIds::YellowPacket();
	AUmbrellaProjectile::Fire(Test.GetWorld(), Spec);
	Test.TickFrames(1, 1.0f / 60.0f);
	TestEqual(TEXT("contact dealt exactly the tuned 1 health"), Ella->GetHealth()->GetState().Active, 3.0f - GetDefault<UUmbrellaTuning>()->Keeper.ProjectileDamage, 1.0e-4f);
	TestEqual(TEXT("tuned ordinary damage is 1"), GetDefault<UUmbrellaTuning>()->Keeper.ProjectileDamage, 1.0f, 1.0e-4f);
	return true;
}

#endif
