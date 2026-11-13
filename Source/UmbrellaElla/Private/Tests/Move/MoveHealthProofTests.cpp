#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaTuning.h"
#include "Health/HealthModel.h"
#include "Health/HealthTuning.h"
#include "Health/UmbrellaHealthComponent.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "UI/ClockHudModel.h"
#include "Umbrella/UmbrellaPlayerIds.h"
#include "Umbrella/UmbrellaStateComponent.h"

namespace
{
	AUmbrellaProjectile* MoveHealthProofFire(UWorld* World, AEllaCharacter* Ella, EUmbrellaShotKind Kind, float Damage)
	{
		FUmbrellaShotSpec Spec;
		Spec.Kind = Kind;
		Spec.Origin = Ella->GetActorLocation();
		Spec.Radius = 8.0f;
		Spec.Damage = Damage;
		Spec.LifetimeSeconds = 2.0f;
		Spec.SourceId = FName(TEXT("HealthProofSource"));
		return AUmbrellaProjectile::Fire(World, Spec);
	}
}

// SURV-05: a Shoot-only fall never auto-catches a yellow: it hurts and stays a hit.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveProofShootFallNoCatch, "UmbrellaElla.Move.World.ShootFallDoesNotAutoCatch", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveProofShootFallNoCatch::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
	Test.TickFrames(2, 1.0f / 60.0f);
	TestEqual(TEXT("dropping in Shoot fall"), Ella->GetUmbrellaState()->GetAction(), EUmbrellaAction::ShootFall);
	MoveHealthProofFire(Test.GetWorld(), Ella, EUmbrellaShotKind::EnemyYellow, 0.0f);
	Test.TickFrames(1, 1.0f / 60.0f);
	TestEqual(TEXT("yellow hurt instead of healing"), Ella->GetHealth()->GetState().Active, 2.0f, 1.0e-4f);
	return true;
}

// SURV-05: no absorption cooldown: yellows caught back to back in one Absorb fall each heal.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveProofNoAbsorbCooldown, "UmbrellaElla.Move.World.RepeatedCatchesHaveNoCooldown", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveProofNoAbsorbCooldown::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	UUmbrellaHealthComponent* Health = Ella->GetHealth();
	MoveHealthProofFire(Test.GetWorld(), Ella, EUmbrellaShotKind::EnemyRed, 2.0f);
	Test.TickSeconds(1.0f, 1.0f / 60.0f);
	TestEqual(TEXT("hurt to 1"), Health->GetState().Active, 1.0f, 1.0e-4f);
	Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Absorb);
	Test.TickFrames(1, 1.0f / 60.0f);
	for (int32 Catch = 1; Catch <= 4; ++Catch)
	{
		AUmbrellaProjectile* Yellow = MoveHealthProofFire(Test.GetWorld(), Ella, EUmbrellaShotKind::EnemyYellow, 0.0f);
		TestTrue(*FString::Printf(TEXT("catch %d consumed"), Catch), Yellow && Yellow->IsActorBeingDestroyed());
		TestEqual(*FString::Printf(TEXT("catch %d healed"), Catch), Health->GetState().Active, 1.0f + 0.5f * Catch, 1.0e-4f);
		Test.TickFrames(1, 1.0f / 60.0f);
	}
	return true;
}

// FLOW-31 / FLOW-33: losing a life (reserve handover) adds no protection window beyond the ordinary post-hit one.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveProofHandoverNoProtection, "UmbrellaElla.Move.World.LifeHandoverAddsNoProtection", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveProofHandoverNoProtection::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	UUmbrellaHealthComponent* Health = Ella->GetHealth();
	const float Window = GetDefault<UUmbrellaTuning>()->Health.PostHitProtectionSeconds;
	const FName Source(TEXT("HealthProofSource"));
	TestEqual(TEXT("ordinary hit lands"), Health->TakeHitAt(1.0f, Source, 10.0), EHitResult::Landed);
	const float OrdinaryWindow = Health->GetProtectionRemaining(10.0);
	TestEqual(TEXT("second hit lands"), Health->TakeHitAt(1.0f, Source, 20.0), EHitResult::Landed);
	TestEqual(TEXT("handover hit lands"), Health->TakeHitAt(1.5f, Source, 30.0), EHitResult::Landed);
	TestEqual(TEXT("a life was handed over"), Health->GetState().Lives, 2);
	TestEqual(TEXT("overflow carried into the new life"), Health->GetState().Active, 2.5f, 1.0e-4f);
	TestEqual(TEXT("ordinary window is the tuned one"), OrdinaryWindow, Window, 1.0e-3f);
	TestEqual(TEXT("handover window equals the ordinary one"), Health->GetProtectionRemaining(30.0), OrdinaryWindow, 1.0e-3f);
	TestEqual(TEXT("hit just after the ordinary window lands"), Health->TakeHitAt(1.0f, Source, 30.0 + Window + 0.01), EHitResult::Landed);
	return true;
}

// FLOW-33: passing a checkpoint normally does not heal.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveProofCheckpointNoHeal, "UmbrellaElla.Move.World.CheckpointPassageDoesNotHeal", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveProofCheckpointNoHeal::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	UUmbrellaHealthComponent* Health = Ella->GetHealth();
	Health->TakeHitAt(4.0f, FName(TEXT("HealthProofSource")), 1.0);
	const FHealthState Before = Health->GetState();
	TestEqual(TEXT("hurt into the second life"), Before.Lives, 2);
	FUmbrellaEvent Event;
	Event.Type = EUmbrellaEventType::CheckpointReached;
	Event.SourceId = FName(TEXT("Checkpoint1"));
	Event.TargetId = UmbrellaPlayerIds::Ella;
	Event.Amount = Before.MaxLives;
	UUmbrellaEventBus::Get(Test.GetWorld())->Broadcast(Event);
	Test.TickFrames(2, 1.0f / 60.0f);
	TestEqual(TEXT("active health unchanged"), Health->GetState().Active, Before.Active, 1.0e-4f);
	TestEqual(TEXT("lives unchanged"), Health->GetState().Lives, Before.Lives);
	return true;
}

// FLOW-33: an ordinary red or yellow projectile with no damage of its own costs exactly 1 health.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveProofOrdinaryDamageOne, "UmbrellaElla.Move.World.OrdinaryProjectileDamageIsOne", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveProofOrdinaryDamageOne::RunTest(const FString& Parameters)
{
	const EUmbrellaShotKind Kinds[] = {EUmbrellaShotKind::EnemyRed, EUmbrellaShotKind::EnemyYellow};
	for (const EUmbrellaShotKind Kind : Kinds)
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		MoveHealthProofFire(Test.GetWorld(), Ella, Kind, 0.0f);
		Test.TickFrames(1, 1.0f / 60.0f);
		TestEqual(*FString::Printf(TEXT("kind %d costs 1"), static_cast<int32>(Kind)), Ella->GetHealth()->GetState().Active, 2.0f, 1.0e-4f);
	}
	return true;
}

// FLOW-32: partial damage and partial healing move only the health hand; the life hand stays.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveProofLifeHandSteady, "UmbrellaElla.Move.LifeHandSteadyOnPartialChanges", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveProofLifeHandSteady::RunTest(const FString& Parameters)
{
	const FHudTuning& Hud = GetDefault<UUmbrellaTuning>()->Hud;
	for (int32 SpentLives = 0; SpentLives < 2; ++SpentLives)
	{
		FHealthState State = HealthRules::MakeFull(3.0f, 3);
		HealthRules::ApplyDamage(State, 3.0f * SpentLives);
		const float LifeHand = ClockHudRules::LifeHandDegrees(State, Hud);
		const float HealthHand = HealthRules::HealthHandDegrees(State);
		HealthRules::ApplyDamage(State, 1.0f);
		TestEqual(*FString::Printf(TEXT("spent %d: life hand still after partial damage"), SpentLives), ClockHudRules::LifeHandDegrees(State, Hud), LifeHand, 1.0e-3f);
		TestTrue(*FString::Printf(TEXT("spent %d: health hand moved on damage"), SpentLives), !FMath::IsNearlyEqual(HealthRules::HealthHandDegrees(State), HealthHand));
		HealthRules::ApplyHeal(State, 0.5f);
		TestEqual(*FString::Printf(TEXT("spent %d: life hand still after partial heal"), SpentLives), ClockHudRules::LifeHandDegrees(State, Hud), LifeHand, 1.0e-3f);
	}
	return true;
}

#endif
