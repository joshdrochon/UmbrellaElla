#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Components/SceneComponent.h"
#include "Core/UmbrellaEventBus.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "GameFramework/Actor.h"
#include "Motor/EllaMotorComponent.h"
#include "Motor/MotorModel.h"
#include "Owl/KeeperOfTime.h"
#include "Owl/KeeperLook.h"
#include "Feedback/Vfx/VfxSheetVisual.h"
#include "Feedback/Vfx/PaintedWarningArt.h"
#include "Engine/Texture2D.h"
#include "Feedback/Art/FrameCompositionSubsystem.h"
#include "Components/StaticMeshComponent.h"
#include "Owl/KeeperPartComponent.h"
#include "Core/UmbrellaSourceIds.h"
#include "Core/UmbrellaTuning.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "Umbrella/UmbrellaStateComponent.h"

namespace
{
	constexpr EAutomationTestFlags WorldFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter;

	/** A transient game world with the Event Bus and the Encounter Director, stepped by hand. */
	struct FKeeperWorld
	{
		UWorld* World = nullptr;
		UEncounterDirectorSubsystem* Director = nullptr;
		AActor* Ella = nullptr;
		TSharedRef<TArray<FUmbrellaEvent>> Shared = MakeShared<TArray<FUmbrellaEvent>>();
		TArray<FDelegateHandle> Handles;

		FKeeperWorld()
		{
			World = UWorld::CreateWorld(EWorldType::Game, false, FName(TEXT("KeeperTestWorld")));
			FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
			Context.SetCurrentWorld(World);
			World->InitializeActorsForPlay(FURL());
			World->BeginPlay();
			Director = World->GetSubsystem<UEncounterDirectorSubsystem>();
			if (Director)
			{
				Director->SetManualStepping(true);
				Ella = World->SpawnActor<AActor>();
				USceneComponent* Root = NewObject<USceneComponent>(Ella, TEXT("Root"));
				Ella->SetRootComponent(Root);
				Root->RegisterComponent();
				Ella->SetActorLocation(FVector(-900.0f, 0.0f, 0.0f));
				Director->SetPlayerActor(Ella);
			}
			if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World))
			{
				for (int32 Index = 0; Index < static_cast<int32>(EUmbrellaEventType::Count); ++Index)
				{
					const EUmbrellaEventType Type = static_cast<EUmbrellaEventType>(Index);
					Handles.Add(Bus->On(Type).AddLambda([Sink = Shared](const FUmbrellaEvent& Event) { Sink->Add(Event); }));
				}
			}
		}

		~FKeeperWorld()
		{
			if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World))
			{
				for (int32 Index = 0; Index < Handles.Num(); ++Index)
				{
					Bus->On(static_cast<EUmbrellaEventType>(Index)).Remove(Handles[Index]);
				}
			}
			if (GEngine)
			{
				GEngine->DestroyWorldContext(World);
			}
			if (World)
			{
				World->DestroyWorld(false);
			}
		}

		void Advance(float Seconds)
		{
			for (float T = 0.0f; T < Seconds; T += 0.05f)
			{
				Director->AdvanceFight(0.05f);
			}
		}

		int32 CountEvents(EUmbrellaEventType Type) const
		{
			int32 N = 0;
			for (const FUmbrellaEvent& Event : *Shared)
			{
				N += (Event.Type == Type) ? 1 : 0;
			}
			return N;
		}

		EUmbrellaShotResult Shoot(EKeeperPart Part, float Damage)
		{
			UKeeperPartComponent* Component = Director->GetKeeper() ? Director->GetKeeper()->GetPartComponent(Part) : nullptr;
			if (!Component)
			{
				return EUmbrellaShotResult::Ignored;
			}
			FUmbrellaShotSpec Shot;
			Shot.Kind = EUmbrellaShotKind::PlayerBlast;
			Shot.Damage = Damage;
			return Component->ReceiveShot(Shot, FVector::ZeroVector);
		}

		void Defeat()
		{
			FUmbrellaEvent Event;
			Event.Type = EUmbrellaEventType::PlayerDefeated;
			UUmbrellaEventBus::Get(World)->Broadcast(Event);
		}
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWorldSpawns, "UmbrellaElla.Keeper.World.BeginSpawnsKeeperAndEntersActive", WorldFlags)
bool FKeeperWorldSpawns::RunTest(const FString& Parameters)
{
	FKeeperWorld W;
	if (!TestNotNull(TEXT("director exists"), W.Director))
	{
		return false;
	}
	TestTrue(TEXT("starts READY"), W.Director->GetState() == EEncounterState::Ready);
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	W.Director->BeginKeeperFight();
	TestTrue(TEXT("ACTIVE"), W.Director->GetState() == EEncounterState::Active);
	TestNotNull(TEXT("keeper spawned"), W.Director->GetKeeper());
	TestEqual(TEXT("PhaseStarted wings"), W.CountEvents(EUmbrellaEventType::PhaseStarted), 1);
	TestEqual(TEXT("checkpoint at the phase start"), W.CountEvents(EUmbrellaEventType::CheckpointReached), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWorldShots, "UmbrellaElla.Keeper.World.ShotsHitEligiblePartsOnly", WorldFlags)
bool FKeeperWorldShots::RunTest(const FString& Parameters)
{
	FKeeperWorld W;
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	W.Director->BeginKeeperFight();
	W.Advance(2.2f);
	const float WingsBefore = W.Director->GetModel().GetPartHp(EKeeperPart::Wings);
	TestTrue(TEXT("wing shot consumed"), W.Shoot(EKeeperPart::Wings, 10.0f) == EUmbrellaShotResult::Consumed);
	TestEqual(TEXT("wings lost 10 HP"), W.Director->GetModel().GetPartHp(EKeeperPart::Wings), WingsBefore - 10.0f);
	TestEqual(TEXT("BossTargetHit sent"), W.CountEvents(EUmbrellaEventType::BossTargetHit), 1);
	const float FrontBefore = W.Director->GetModel().GetPartHp(EKeeperPart::Front);
	TestTrue(TEXT("front shot consumed"), W.Shoot(EKeeperPart::Front, 10.0f) == EUmbrellaShotResult::Consumed);
	TestEqual(TEXT("front ignores damage while the wings live"), W.Director->GetModel().GetPartHp(EKeeperPart::Front), FrontBefore);
	TestEqual(TEXT("no second BossTargetHit"), W.CountEvents(EUmbrellaEventType::BossTargetHit), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWorldPhases, "UmbrellaElla.Keeper.World.PhaseAdvancesWhenItsPartsBreak", WorldFlags)
bool FKeeperWorldPhases::RunTest(const FString& Parameters)
{
	FKeeperWorld W;
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	W.Director->BeginKeeperFight();
	W.Advance(2.2f);
	W.Shoot(EKeeperPart::Wings, 1000.0f);
	TestTrue(TEXT("mechanisms phase"), W.Director->GetPhase() == EKeeperPhase::Mechanisms);
	TestEqual(TEXT("BossPartDestroyed wings"), W.CountEvents(EUmbrellaEventType::BossPartDestroyed), 1);
	TestEqual(TEXT("second PhaseStarted"), W.CountEvents(EUmbrellaEventType::PhaseStarted), 2);
	TestEqual(TEXT("second checkpoint"), W.CountEvents(EUmbrellaEventType::CheckpointReached), 2);
	W.Advance(2.2f);
	W.Shoot(EKeeperPart::Front, 1000.0f);
	W.Advance(2.0f);
	W.Shoot(EKeeperPart::Middle, 1000.0f);
	W.Advance(2.0f);
	W.Shoot(EKeeperPart::Rear, 1000.0f);
	TestTrue(TEXT("clock phase"), W.Director->GetPhase() == EKeeperPhase::Clock);
	TestEqual(TEXT("four parts destroyed"), W.CountEvents(EUmbrellaEventType::BossPartDestroyed), 4);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWorldRetry, "UmbrellaElla.Keeper.World.RetryRestoresPhaseCheckpointWithThreeLives", WorldFlags)
bool FKeeperWorldRetry::RunTest(const FString& Parameters)
{
	FKeeperWorld W;
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	W.Director->BeginKeeperFight();
	W.Advance(2.2f);
	W.Shoot(EKeeperPart::Wings, 1000.0f);
	W.Advance(2.2f);
	W.Shoot(EKeeperPart::Front, 40.0f);
	TestEqual(TEXT("front damaged"), W.Director->GetModel().GetPartHp(EKeeperPart::Front), 60.0f);
	W.Defeat();
	TestTrue(TEXT("ENDING_FAILURE"), W.Director->GetState() == EEncounterState::EndingFailure);
	W.Director->ResetForRestart();
	TestEqual(TEXT("CheckpointRetried sent once"), W.CountEvents(EUmbrellaEventType::CheckpointRetried), 1);
	for (const FUmbrellaEvent& Event : *W.Shared)
	{
		if (Event.Type == EUmbrellaEventType::CheckpointRetried)
		{
			TestEqual(TEXT("retry carries exactly 3 lives"), Event.Amount, 3);
			TestEqual(TEXT("at the mechanisms checkpoint"), Event.Detail, FName(TEXT("mechanisms")));
		}
	}
	TestTrue(TEXT("fight is ACTIVE again"), W.Director->GetState() == EEncounterState::Active);
	TestTrue(TEXT("still in the mechanisms phase"), W.Director->GetPhase() == EKeeperPhase::Mechanisms);
	TestEqual(TEXT("front back to full HP"), W.Director->GetModel().GetPartHp(EKeeperPart::Front), 100.0f);
	TestTrue(TEXT("wings stay broken"), W.Director->GetModel().IsPartBroken(EKeeperPart::Wings));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWorldWin, "UmbrellaElla.Keeper.World.FinalClockHitEndsInSuccess", WorldFlags)
bool FKeeperWorldWin::RunTest(const FString& Parameters)
{
	FKeeperWorld W;
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	W.Director->BeginKeeperFightAtPhase(EKeeperPhase::Clock);
	W.Advance(2.2f);
	TestTrue(TEXT("clock exposed in the finale"), W.Director->GetModel().IsClockOpen());
	W.Shoot(EKeeperPart::Clock, 100000.0f);
	W.Advance(0.05f);
	TestTrue(TEXT("ENDING_SUCCESS"), W.Director->GetState() == EEncounterState::EndingSuccess);
	TestEqual(TEXT("EncounterCompleted once"), W.CountEvents(EUmbrellaEventType::EncounterCompleted), 1);
	W.Advance(5.0f);
	TestEqual(TEXT("still once"), W.CountEvents(EUmbrellaEventType::EncounterCompleted), 1);
	W.Defeat();
	TestTrue(TEXT("no defeat after completion"), W.Director->GetState() == EEncounterState::EndingSuccess);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWorldTie, "UmbrellaElla.Keeper.World.DefeatAndCompletionInOneFrameDefeatWins", WorldFlags)
bool FKeeperWorldTie::RunTest(const FString& Parameters)
{
	FKeeperWorld W;
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	W.Director->BeginKeeperFightAtPhase(EKeeperPhase::Clock);
	W.Advance(2.2f);
	W.Shoot(EKeeperPart::Clock, 100000.0f);
	W.Defeat(); // same frame
	W.Advance(0.05f);
	TestTrue(TEXT("ENDING_FAILURE wins the tie"), W.Director->GetState() == EEncounterState::EndingFailure);
	TestEqual(TEXT("no EncounterCompleted"), W.CountEvents(EUmbrellaEventType::EncounterCompleted), 0);
	TestTrue(TEXT("rule function agrees"), UEncounterDirectorSubsystem::ResolveEnding(true, true) == EEncounterState::EndingFailure);
	TestTrue(TEXT("win alone is success"), UEncounterDirectorSubsystem::ResolveEnding(false, true) == EEncounterState::EndingSuccess);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWorldPause, "UmbrellaElla.Keeper.World.PauseFreezesTheSchedule", WorldFlags)
bool FKeeperWorldPause::RunTest(const FString& Parameters)
{
	FKeeperWorld W;
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	W.Director->BeginKeeperFight();
	W.Advance(3.0f);
	const float RedBefore = W.Director->GetModel().GetRedCountdown();
	W.Director->SetPaused(true);
	TestTrue(TEXT("PAUSED"), W.Director->GetState() == EEncounterState::Paused);
	W.Advance(10.0f);
	TestEqual(TEXT("red countdown frozen"), W.Director->GetModel().GetRedCountdown(), RedBefore);
	TestTrue(TEXT("shots are ignored while paused"), W.Shoot(EKeeperPart::Wings, 10.0f) == EUmbrellaShotResult::Ignored);
	W.Director->SetPaused(false);
	TestTrue(TEXT("ACTIVE again"), W.Director->GetState() == EEncounterState::Active);
	W.Advance(0.5f);
	TestTrue(TEXT("schedule runs again"), W.Director->GetModel().GetRedCountdown() != RedBefore);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWorldDamage, "UmbrellaElla.Keeper.World.TalonDamageReachesElla", WorldFlags)
bool FKeeperWorldDamage::RunTest(const FString& Parameters)
{
	FKeeperWorld W;
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	struct FTally
	{
		int32 Hits = 0;
		float Damage = 0.0f;
	};
	const TSharedRef<FTally> Tally = MakeShared<FTally>();
	W.Director->OnDamageDelivered().AddLambda([Tally](FName Source, float Amount)
	{
		++Tally->Hits;
		Tally->Damage = Amount;
	});
	W.Director->BeginKeeperFight();
	W.Ella->SetActorLocation(FVector(W.Director->GetModel().GetClaw().X - 150.0f, 0.0f, W.Director->GetModel().GetClaw().Y));
	W.Advance(2.0f + 2.0f + 1.05f + 0.5f);
	TestEqual(TEXT("the talon hit Ella once"), Tally->Hits, 1);
	TestEqual(TEXT("for 1.5 health"), Tally->Damage, 1.5f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWorldHeadShootable, "UmbrellaElla.Keeper.World.MechanismHeadIsTheHittableTarget", WorldFlags)
bool FKeeperWorldHeadShootable::RunTest(const FString& Parameters)
{
	FKeeperWorld W;
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	W.Director->BeginKeeperFightAtPhase(EKeeperPhase::Mechanisms);
	W.Advance(2.0f + 2.5f + 0.9f + 0.5f);
	AKeeperOfTime* Keeper = W.Director->GetKeeper();
	if (!TestNotNull(TEXT("keeper"), Keeper))
	{
		return false;
	}
	TestTrue(TEXT("front cast extended"), W.Director->GetModel().GetPhysical() == EKeeperPhysical::FrontCast);
	TestTrue(TEXT("head hittable"), Keeper->GetHeadComponent(EKeeperPart::Front)->GetCollisionEnabled() != ECollisionEnabled::NoCollision);
	TestTrue(TEXT("no second hittable head at home"), Keeper->GetPartComponent(EKeeperPart::Front)->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWorldNoDepartureEnds, "UmbrellaElla.Keeper.World.FinalHitWithDepartureOffStillEndsInSuccess", WorldFlags)
bool FKeeperWorldNoDepartureEnds::RunTest(const FString& Parameters)
{
	FKeeperWorld W;
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	W.Director->SetDepartureEnabledForTest(false);
	W.Director->BeginKeeperFightAtPhase(EKeeperPhase::Clock);
	W.Advance(2.2f);
	W.Shoot(EKeeperPart::Clock, 100000.0f);
	W.Advance(0.05f);
	TestTrue(TEXT("ENDING_SUCCESS, not ACTIVE with a halted model"), W.Director->GetState() == EEncounterState::EndingSuccess);
	TestEqual(TEXT("EncounterCompleted once"), W.CountEvents(EUmbrellaEventType::EncounterCompleted), 1);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWorldGustViaMotor, "UmbrellaElla.Keeper.World.GustPushGoesThroughWindEventsNotPosition", WorldFlags)
bool FKeeperWorldGustViaMotor::RunTest(const FString& Parameters)
{
	FKeeperWorld W;
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	W.Director->BeginKeeperFight();
	const FVector Start = W.Ella->GetActorLocation();
	// Keep Ella in the band the gust locks to (it locks to her height) and let the front sweep through her.
	for (float T = 0.0f; T < 20.0f && W.CountEvents(EUmbrellaEventType::WindEntered) == 0; T += 0.05f)
	{
		W.Director->AdvanceFight(0.05f);
	}
	TestTrue(TEXT("Gust WindEntered was sent"), W.CountEvents(EUmbrellaEventType::WindEntered) > 0);
	for (const FUmbrellaEvent& Event : *W.Shared)
	{
		if (Event.Type == EUmbrellaEventType::WindEntered)
		{
			TestEqual(TEXT("source is GUST_Band"), Event.SourceId, UmbrellaSourceIds::GustBand());
			TestEqual(TEXT("force is the tuned push at world scale 1"), Event.Value, GetDefault<UUmbrellaTuning>()->Keeper.GustPush);
		}
	}
	TestEqual(TEXT("the director never moved Ella"), W.Ella->GetActorLocation().Z, Start.Z);
	W.Director->SetPaused(true);
	TestTrue(TEXT("wind ends when the push stops"), W.CountEvents(EUmbrellaEventType::WindExited) > 0);
	return true;
}


namespace
{
	/** Send a gust WindEntered (Up) and step a Motor; returns the vertical displacement. */
	float KeeperGustMotorDz(bool bShoot, bool bAbsorb, bool bRide, float Speed, float Seconds, EUmbrellaAction& OutAction)
	{
		UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, FName(TEXT("KeeperGustMotorWorld")));
		FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
		Context.SetCurrentWorld(World);
		World->InitializeActorsForPlay(FURL());
		World->BeginPlay();
		AActor* Ella = World->SpawnActor<AActor>();
		USceneComponent* Root = NewObject<USceneComponent>(Ella, TEXT("Root"));
		Ella->SetRootComponent(Root);
		Root->RegisterComponent();
		UEllaMotorComponent* Motor = NewObject<UEllaMotorComponent>(Ella, TEXT("Motor"));
		Motor->RegisterComponent();
		UUmbrellaStateComponent* State = NewObject<UUmbrellaStateComponent>(Ella, TEXT("State"));
		State->RegisterComponent();
		State->SetRideHeld(bRide);
		State->SetShootHeld(bShoot);
		State->SetAbsorbHeld(bAbsorb);
		Ella->DispatchBeginPlay(); // components subscribe to the bus in BeginPlay
		OutAction = State->GetAction();
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::WindEntered;
		Event.SourceId = UmbrellaSourceIds::GustBand();
		Event.Detail = FName(TEXT("Up"));
		Event.Value = Speed;
		UUmbrellaEventBus::Get(World)->Broadcast(Event);
		const float StartZ = Ella->GetActorLocation().Z;
		Motor->StepMotor(Seconds);
		const float Dz = Ella->GetActorLocation().Z - StartZ;
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
		return Dz;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperGustForcedPush, "UmbrellaElla.Keeper.World.GustForcedPushIgnoresActionAndRide", WorldFlags)
bool FKeeperGustForcedPush::RunTest(const FString& Parameters)
{
	const float Speed = 280.0f;
	const float Dt = 0.1f;
	const FMotorTuning& Tuning = GetDefault<UUmbrellaTuning>()->Motor;
	// Base vertical speed differs per action; the gust adds exactly Speed * Dt on top, at once (no ride blend).
	struct FCase { bool bShoot; bool bAbsorb; bool bRide; const TCHAR* Name; };
	const FCase Cases[] = {
		{false, false, false, TEXT("rising, not riding")},
		{true, false, false, TEXT("shooting, not riding")},
		{false, true, false, TEXT("absorbing (defense)")},
		{false, false, true, TEXT("rising, ride held")},
		{true, false, true, TEXT("shooting, ride held")},
	};
	bool bSawFalling = false;
	for (const FCase& Case : Cases)
	{
		EUmbrellaAction Action = EUmbrellaAction::Rise;
		const float Dz = KeeperGustMotorDz(Case.bShoot, Case.bAbsorb, Case.bRide, Speed, Dt, Action);
		bSawFalling |= UmbrellaActionRules::IsFalling(Action);
		FMotorInput Base;
		Base.Action = Action;
		// The gust adds exactly Speed * Dt on top of the base, at once (no ride blend).
		TestEqual(Case.Name, Dz, (MotorModel::BaseVerticalSpeed(Base, Tuning) + Speed) * Dt, 0.01f);
	}
	TestTrue(TEXT("a falling action was covered"), bSawFalling);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperGustForcedRule, "UmbrellaElla.Keeper.GustIsAForcedSourceNotACurrent", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FKeeperGustForcedRule::RunTest(const FString& Parameters)
{
	TestTrue(TEXT("GUST_Band is forced"), MotorModel::IsForcedSource(UmbrellaSourceIds::GustBand()));
	TestFalse(TEXT("an ordinary current is not"), MotorModel::IsForcedSource(FName(TEXT("Current_A"))));
	FMotorModelState State;
	FMotorInput Input;
	Input.Action = EUmbrellaAction::FreeFall;
	Input.ForcedVelocity = FVector2D(0.0f, 280.0f);
	const FMotorTuning& Tuning = GetDefault<UUmbrellaTuning>()->Motor;
	const FVector2D Move = MotorModel::Step(State, Input, Tuning, 0.05f);
	FMotorInput None = Input;
	None.ForcedVelocity = FVector2D::ZeroVector;
	FMotorModelState Fresh;
	const FVector2D Plain = MotorModel::Step(Fresh, None, Tuning, 0.05f);
	TestEqual(TEXT("lands at once: full speed in the first step"), static_cast<float>(Move.Y - Plain.Y), 280.0f * 0.05f, 0.001f);
	TestEqual(TEXT("no ride wind state"), static_cast<float>(State.Wind.Y), 0.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperGustSlowScale, "UmbrellaElla.Keeper.World.GustSpeedUsesWorldScaleOnce", WorldFlags)
bool FKeeperGustSlowScale::RunTest(const FString& Parameters)
{
	FKeeperWorld W;
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	// The gust only exists in the Wings phase and the slow only in Mechanisms, so they never overlap in play;
	// this pins that the push is Push * GetWorldScale() (once), whatever scale the model reports.
	W.Director->BeginKeeperFight();
	for (float T = 0.0f; T < 40.0f && W.CountEvents(EUmbrellaEventType::WindEntered) == 0; T += 0.05f)
	{
		W.Director->AdvanceFight(0.05f);
	}
	TestTrue(TEXT("gust sent"), W.CountEvents(EUmbrellaEventType::WindEntered) > 0);
	// The event Value is Push * model scale, integrated by the Motor in real time: scaled exactly once.
	const float Scale = W.Director->GetModel().GetWorldScale();
	for (const FUmbrellaEvent& Event : *W.Shared)
	{
		if (Event.Type == EUmbrellaEventType::WindEntered)
		{
			TestEqual(TEXT("Value = GustPush * world scale"), Event.Value, GetDefault<UUmbrellaTuning>()->Keeper.GustPush * Scale, 0.01f);
		}
	}
	return true;
}

#endif

namespace
{
	/**
	 * Steps a fight for Seconds and checks the warning marker on every tick it shows: a thin line (short side at most
	 * a fifth of the gust band), never the full-size cube. Returns the physical kinds whose
	 * warning showed the marker, one bit per EKeeperPhysical.
	 */
	uint32 CheckWarningMarkers(FAutomationTestBase& Test, FKeeperWorld& W, float Seconds)
	{
		uint32 Seen = 0;
		AKeeperOfTime* Keeper = W.Director->GetKeeper();
		UStaticMeshComponent* Marker = Keeper ? FindObjectFast<UStaticMeshComponent>(Keeper, FName(UmbrellaFrameConst::KeeperTelegraphName)) : nullptr;
		if (!Test.TestNotNull(TEXT("telegraph marker"), Marker))
		{
			return Seen;
		}
		const FKeeperTuning& T = GetDefault<UUmbrellaTuning>()->Keeper;
		// A line or streak: its short side at most 0.6 of the 120 cm gust band (the old cubes were 120-126 cm thick; the
		// painted streak's quad is 64 cm with a feathered edge and glow, its visible core about 20 cm).
		const float MaxThick = T.GustBandWidth * 0.6f;
		bool bReported = false;
		bool bSawPainted = false;
		for (float Time = 0.0f; Time < Seconds; Time += 0.05f)
		{
			W.Director->AdvanceFight(0.05f);
			const FKeeperFightModel& Model = W.Director->GetModel();
			if (Model.GetStage() != EKeeperStage::Warning || !Marker->IsVisible())
			{
				continue;
			}
			Seen |= 1u << static_cast<uint32>(Model.GetPhysical());
			const FVector Size = Marker->GetComponentScale() * KeeperLook::CubeEdge;
			// A painted quad (engine plane) lies in its local X/Y; the fallback cube shows its X/Z.
			const bool bPainted = VfxSheetVisual::HasArt(Marker);
			const bool bThin = FMath::Min(Size.X, bPainted ? Size.Y : Size.Z) <= MaxThick;
			if (bPainted && !bSawPainted)
			{
				bSawPainted = true;
			}
			if (!bThin && !bReported)
			{
				bReported = true;
				Test.AddError(FString::Printf(TEXT("warning marker for physical %d is %.0f x %.0f cm: a block, not a thin line"),
					static_cast<int32>(Model.GetPhysical()), Size.X, Size.Z));
			}
		}
		if (Seen != 0)
		{
			// Josh Nov 14: the warning is the painted streak (textured, feathered), never a flat uniform line.
			if (!bSawPainted)
			{
				Test.AddWarning(TEXT("this test world drew the flat-line fallback (no VFX sheet material here); the painted path is checked in PaintedWarningIsFeatheredNotFlat"));
			}
		}
		return Seen;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperWorldWarningMarkerLine, "UmbrellaElla.Keeper.World.WarningMarkerIsAThinRedLineForEveryKind", WorldFlags)
bool FKeeperWorldWarningMarkerLine::RunTest(const FString& Parameters)
{
	// Josh 13 Nov: a full-size salmon-pink block lay across the arena during Keeper warnings (TelegraphVisual at the
	// lane's full size in (1,0.2,0.2); the frame pass every 0.2 s could not keep it thin against the per-tick placement).
	// The test world has no slot material, so the colour is checked on the constant the Keeper places every tick.
	TestTrue(TEXT("the marker colour is shot red, not salmon pink (1,0.2,0.2)"),
		FLinearColor(KeeperLook::Telegraph).Equals(UmbrellaFrameConst::TelegraphRed, 0.0005f));
	uint32 Seen = 0;
	{
		FKeeperWorld W;
		AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
		W.Director->BeginKeeperFight();
		// Stand inside the talon's reach so it strikes (the model arms it when Ella is within TalonReach of the claw).
		const FVector2D Near = W.Director->GetModel().GetClaw() + FVector2D(-100.0f, 0.0f);
		W.Ella->SetActorLocation(FVector(Near.X, 0.0f, Near.Y));
		Seen |= CheckWarningMarkers(*this, W, 20.0f);
	}
	{
		FKeeperWorld W;
		AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
		W.Director->BeginKeeperFightAtPhase(EKeeperPhase::Mechanisms);
		Seen |= CheckWarningMarkers(*this, W, 20.0f);
	}
	TestTrue(TEXT("a talon warning showed the marker"), (Seen & (1u << static_cast<uint32>(EKeeperPhysical::Talon))) != 0);
	const uint32 Casts = (1u << static_cast<uint32>(EKeeperPhysical::FrontCast)) | (1u << static_cast<uint32>(EKeeperPhysical::MiddleCurve))
		| (1u << static_cast<uint32>(EKeeperPhysical::RearTwoStage));
	TestTrue(TEXT("a chain-cast warning showed the marker"), (Seen & Casts) != 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FKeeperPaintedWarningArt, "UmbrellaElla.Keeper.PaintedWarningIsFeatheredNotFlat", EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)
bool FKeeperPaintedWarningArt::RunTest(const FString& Parameters)
{
	// Josh Nov 14: a soft painted streak (tapered, feathered, faint tail) and a broken soft ring, never flat fills.
	TestTrue(TEXT("streak: faint tail, strong toward the strike"), PaintedWarningArt::StreakAlpha(0.05f, 0.5f) < 0.5f * PaintedWarningArt::StreakAlpha(0.85f, 0.5f));
	TestTrue(TEXT("streak: tail alpha is low"), PaintedWarningArt::StreakAlpha(0.02f, 0.5f) <= PaintedWarningArt::TailAlpha + 0.05f);
	TestTrue(TEXT("streak: feathered across (edge far below the centre)"), PaintedWarningArt::StreakAlpha(0.8f, 0.97f) < 0.2f * PaintedWarningArt::StreakAlpha(0.8f, 0.5f));
	TestTrue(TEXT("streak: soft, not a hard step (a mid value between core and edge)"),
		PaintedWarningArt::StreakAlpha(0.8f, 0.6f) > 0.05f && PaintedWarningArt::StreakAlpha(0.8f, 0.6f) < PaintedWarningArt::StreakAlpha(0.8f, 0.5f));
	float RingMin = 1.0f;
	float RingMax = 0.0f;
	for (int32 Step = 0; Step < 72; ++Step)
	{
		const float A = 2.0f * PI * Step / 72.0f;
		const float V = PaintedWarningArt::RingAlpha(0.62f * FMath::Cos(A), 0.62f * FMath::Sin(A), 0);
		RingMin = FMath::Min(RingMin, V);
		RingMax = FMath::Max(RingMax, V);
	}
	TestTrue(TEXT("ring: broken (gaps far fainter than the arcs)"), RingMin < 0.35f * RingMax);
	TestTrue(TEXT("ring: soft edge outside the band"), PaintedWarningArt::RingAlpha(0.95f, 0.0f, 0) < 0.25f * RingMax);
	TestTrue(TEXT("ring: never a solid fill"), RingMax < 0.95f);
	UTexture2D* StreakTexture = PaintedWarningArt::Streak();
	UTexture2D* Ring = PaintedWarningArt::RingSheet();
	TestNotNull(TEXT("streak texture builds"), StreakTexture);
	TestNotNull(TEXT("ring sheet builds"), Ring);
	if (Ring)
	{
		TestEqual(TEXT("ring sheet is one row of frames"), Ring->GetSizeX(), PaintedWarningArt::CellSize * PaintedWarningArt::Frames);
	}
	UStaticMeshComponent* Quad = NewObject<UStaticMeshComponent>(GetTransientPackage());
	VfxSheetVisual::ShowTexture(Quad, StreakTexture);
	TestTrue(TEXT("the streak shows on a VFX sheet quad (textured, not a flat cube)"), VfxSheetVisual::HasArt(Quad));
	TestTrue(TEXT("ring: pulses over the loop"), !FMath::IsNearlyEqual(PaintedWarningArt::RingAlpha(0.62f, 0.0f, 0), PaintedWarningArt::RingAlpha(0.62f, 0.0f, PaintedWarningArt::Frames / 2), 0.02f));
	return true;
}
