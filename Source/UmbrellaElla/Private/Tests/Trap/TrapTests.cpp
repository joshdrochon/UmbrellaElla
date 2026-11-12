#include "Core/UmbrellaEventBus.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/World.h"
#include "Enemy/EnemyTuning.h"
#include "Misc/AutomationTest.h"
#include "Trap/TrapRules.h"
#include "Trap/TrapTuning.h"
#include "Trap/UmbrellaTrap.h"

#if WITH_AUTOMATION_TESTS

#define UMBRELLAELLA_TRAP_FLAGS (EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

namespace
{
	struct FContactProbe
	{
		TArray<FUmbrellaEvent> Seen;
		void OnEvent(const FUmbrellaEvent& Event) { Seen.Add(Event); }
	};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTrapShutterCycle, "UmbrellaElla.Trap.ShutterCycle", UMBRELLAELLA_TRAP_FLAGS)
bool FTrapShutterCycle::RunTest(const FString& Parameters)
{
	const FTrapTuning Tuning;
	const FTrapCycle Cycle = FTrapRules::MakeCycle(ETrapKind::TimedShutter, Tuning);
	TestTrue(TEXT("warning at least 1 s"), Cycle.WarningSeconds >= 1.0f);
	TestEqual(TEXT("strike 0.6 s"), Cycle.ActiveSeconds, 0.6f);
	TestTrue(TEXT("recovery at least 1.4 s"), Cycle.RecoverySeconds >= 1.4f);
	TestEqual(TEXT("warning first"), Cycle.PhaseAt(0.5f), ETrapPhase::Warning);
	TestEqual(TEXT("then strike"), Cycle.PhaseAt(1.2f), ETrapPhase::Active);
	TestEqual(TEXT("then open recovery"), Cycle.PhaseAt(2.0f), ETrapPhase::Recovery);
	TestEqual(TEXT("loops"), Cycle.PhaseAt(Cycle.GetCycleSeconds() + 0.5f), ETrapPhase::Warning);
	TestTrue(TEXT("strike hurts"), FTrapRules::IsPhaseDamaging(ETrapKind::TimedShutter, ETrapPhase::Active));
	TestFalse(TEXT("warning is harmless"), FTrapRules::IsPhaseDamaging(ETrapKind::TimedShutter, ETrapPhase::Warning));
	TestFalse(TEXT("open gap is harmless"), FTrapRules::IsPhaseDamaging(ETrapKind::TimedShutter, ETrapPhase::Recovery));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTrapBellowsCycle, "UmbrellaElla.Trap.BellowsCycle", UMBRELLAELLA_TRAP_FLAGS)
bool FTrapBellowsCycle::RunTest(const FString& Parameters)
{
	const FTrapTuning Tuning;
	const FTrapCycle Cycle = FTrapRules::MakeCycle(ETrapKind::HostileBellows, Tuning);
	TestTrue(TEXT("warning at least 1 s"), Cycle.WarningSeconds >= 1.0f);
	TestTrue(TEXT("recovery at least 1.5 s"), Cycle.RecoverySeconds >= 1.5f);
	TestTrue(TEXT("gust is finite"), Cycle.ActiveSeconds > 0.0f && Cycle.ActiveSeconds < Cycle.GetCycleSeconds());
	TestFalse(TEXT("no fire in recovery"), FTrapRules::IsPhaseDamaging(ETrapKind::HostileBellows, ETrapPhase::Recovery));
	const FVector Push = FTrapRules::BellowsPush(Tuning.BellowsPushSpeed);
	TestTrue(TEXT("push bounded"), Push.Size() <= Tuning.BellowsPushSpeed + UE_KINDA_SMALL_NUMBER);
	TestTrue(TEXT("push heads down and left"), Push.X < 0.0 && Push.Z < 0.0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTrapSweptDisk, "UmbrellaElla.Trap.AirMillBlocksFullDisk", UMBRELLAELLA_TRAP_FLAGS)
bool FTrapSweptDisk::RunTest(const FString& Parameters)
{
	const FVector Centre(1120.0, 0.0, 760.0);
	TestTrue(TEXT("hub is blocked"), FTrapRules::IsInsideSweptDisk(Centre, Centre, 150.0f));
	TestTrue(TEXT("mid-blade gap is blocked"), FTrapRules::IsInsideSweptDisk(Centre + FVector(100.0, 0.0, 100.0), Centre, 150.0f));
	TestFalse(TEXT("outside the disk is free"), FTrapRules::IsInsideSweptDisk(Centre + FVector(0.0, 0.0, 151.0), Centre, 150.0f));
	TestTrue(TEXT("blade angle wraps"), FTrapRules::BladeAngle(5.0f, 90.0f) < 360.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTrapContactGate, "UmbrellaElla.Trap.PersistentOverlapDamagesOncePerWindow", UMBRELLAELLA_TRAP_FLAGS)
bool FTrapContactGate::RunTest(const FString& Parameters)
{
	FContactGate Gate;
	const FName Ella(TEXT("Ella"));
	TestEqual(TEXT("first hit deals damage"), Gate.ConsumeHit(Ella, 1.0f, 0.65f), 1.0f);
	for (int32 Frame = 0; Frame < 30; ++Frame)
	{
		Gate.Advance(0.016f);
		TestEqual(TEXT("no repeat while protected"), Gate.ConsumeHit(Ella, 1.0f, 0.65f), 0.0f);
	}
	Gate.Advance(0.5f);
	TestEqual(TEXT("damage again after the window"), Gate.ConsumeHit(Ella, 1.0f, 0.65f), 1.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FTrapHurtsEllaOnContact, "UmbrellaElla.Trap.World.EachTrapHurtsOnContact", UMBRELLAELLA_TRAP_FLAGS)
bool FTrapHurtsEllaOnContact::RunTest(const FString& Parameters)
{
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(World);
	const TSharedRef<FContactProbe> Probe = MakeShared<FContactProbe>();
	const FDelegateHandle Handle = Bus->On(EUmbrellaEventType::ProjectileContact).AddSP(Probe, &FContactProbe::OnEvent);
	const ETrapKind Kinds[] = { ETrapKind::AirMill, ETrapKind::TimedShutter, ETrapKind::HostileBellows, ETrapKind::RoofTeeth };
	for (const ETrapKind Kind : Kinds)
	{
		AUmbrellaTrap* Trap = World->SpawnActor<AUmbrellaTrap>(AUmbrellaTrap::StaticClass(), FTransform(FVector(500.0, 0.0, 500.0)));
		Trap->ConfigureKind(Kind);
		AStaticMeshActor* Ella = World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), FTransform(FVector(500.0, 0.0, 500.0)));
		// Shutter and bellows are harmless during the warning; move them into the active phase first.
		if (Kind == ETrapKind::TimedShutter || Kind == ETrapKind::HostileBellows)
		{
			TestEqual(TEXT("harmless while warning"), Trap->ApplyContact(Ella), 0.0f);
			Trap->StepSeconds(1.1f);
			TestEqual(TEXT("now active"), Trap->GetPhase(), ETrapPhase::Active);
		}
		const int32 Before = Probe->Seen.Num();
		TestEqual(TEXT("contact deals one health"), Trap->ApplyContact(Ella), 1.0f);
		TestEqual(TEXT("one contact event"), Probe->Seen.Num(), Before + 1);
		TestEqual(TEXT("event names the trap kind"), Probe->Seen.Last().Detail, FTrapRules::KindName(Kind));
		TestEqual(TEXT("event carries the damage"), Probe->Seen.Last().Value, 1.0f);
		TestEqual(TEXT("protected right after"), Trap->ApplyContact(Ella), 0.0f);
	}
	Bus->On(EUmbrellaEventType::ProjectileContact).Remove(Handle);
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FPressureContractRules, "UmbrellaElla.Trap.PressureContract", UMBRELLAELLA_TRAP_FLAGS)
bool FPressureContractRules::RunTest(const FString& Parameters)
{
	const FEnemyTuning Tuning;
	FPressureChunk Chunk;
	Chunk.PlayerLocation = FVector(0.0, 0.0, 500.0);
	FPressureEnemy Roadwarden;
	Roadwarden.Location = FVector(900.0, 0.0, 500.0);
	Chunk.Enemies.Add(Roadwarden);
	Chunk.TaughtTypes.Add(EEnemyType::Roadwarden);
	Chunk.TimingDemandsInCrossing = 1;
	TestEqual(TEXT("one taught enemy, one demand passes"), FPressureContract::Evaluate(Chunk, Tuning).Num(), 0);

	FPressureChunk TwoDemands = Chunk;
	TwoDemands.TimingDemandsInCrossing = 2;
	TestTrue(TEXT("two timing demands fail"), FPressureContract::Evaluate(TwoDemands, Tuning).Contains(EPressureViolation::TooManyTimingDemands));

	FPressureChunk Early = Chunk;
	Early.Stage = EPressureStage::Early;
	Early.TrapCount = 1;
	TestTrue(TEXT("early chunk: one problem only"), FPressureContract::Evaluate(Early, Tuning).Contains(EPressureViolation::TooManyProblemsEarly));

	FPressureChunk Intro = Chunk;
	Intro.bIsIntroduction = true;
	Intro.Enemies.Add(Roadwarden);
	TestTrue(TEXT("introduction uses one enemy"), FPressureContract::Evaluate(Intro, Tuning).Contains(EPressureViolation::IntroductionNotSingleEnemy));

	FPressureChunk Mixed = Chunk;
	FPressureEnemy Flood = Roadwarden;
	Flood.Type = EEnemyType::Floodstrider;
	FPressureEnemy Courier = Roadwarden;
	Courier.Type = EEnemyType::SkyCourier;
	Mixed.Enemies.Add(Flood);
	Mixed.Enemies.Add(Courier);
	Mixed.TaughtTypes.Add(EEnemyType::Floodstrider);
	Mixed.TaughtTypes.Add(EEnemyType::SkyCourier);
	TestTrue(TEXT("mixed chunk: at most two kinds"), FPressureContract::Evaluate(Mixed, Tuning).Contains(EPressureViolation::MixedChunkTooManyKinds));

	FPressureChunk Untaught = Chunk;
	Untaught.TaughtTypes.Reset();
	TestTrue(TEXT("later chunk uses taught enemies only"), FPressureContract::Evaluate(Untaught, Tuning).Contains(EPressureViolation::UntaughtEnemy));

	FPressureChunk OnPlayer = Chunk;
	OnPlayer.Enemies[0].Location = FVector(50.0, 0.0, 500.0);
	TestTrue(TEXT("no spawn on Ella"), FPressureContract::Evaluate(OnPlayer, Tuning).Contains(EPressureViolation::SpawnOnPlayer));

	FPressureChunk Offscreen = Chunk;
	Offscreen.Enemies[0].bOnscreen = false;
	TestTrue(TEXT("no offscreen attackers"), FPressureContract::Evaluate(Offscreen, Tuning).Contains(EPressureViolation::AttackFromOffscreen));

	FPressureChunk Neighbor = Chunk;
	Neighbor.Enemies[0].bFromClearedNeighbor = true;
	TestTrue(TEXT("no attacks from cleared neighbours"), FPressureContract::Evaluate(Neighbor, Tuning).Contains(EPressureViolation::AttackFromClearedNeighbor));

	FPressureChunk Sealed = Chunk;
	Sealed.bFireSealsEscape = true;
	TestTrue(TEXT("fire cannot seal the only escape"), FPressureContract::Evaluate(Sealed, Tuning).Contains(EPressureViolation::FireSealsEscape));
	return true;
}

#endif
