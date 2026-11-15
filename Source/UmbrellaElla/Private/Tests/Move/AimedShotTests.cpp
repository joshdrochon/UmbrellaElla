#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Attack/AimedBeamActor.h"
#include "Attack/AttackEmitterComponent.h"
#include "Attack/AttackTuning.h"
#include "Components/StaticMeshComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaTuning.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Enemy/UmbrellaEnemy.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Feedback/Art/ArtSlot.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Owl/KeeperOfTime.h"
#include "Owl/KeeperPartComponent.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Projectile/UmbrellaShotSpec.h"
#include "Tests/Shared/UmbrellaTestWorld.h"

/**
 * D-new-aimed-shot (Josh, 14 Nov): tap Shoot = Small Blasts hip-fire as before; hold Shoot ~0.5 s = one long beam to the
 * right that hits the Keeper and enemies along its line for more than a hip-fire shot. Ella keeps falling throughout.
 */
namespace
{
	constexpr EAutomationTestFlags AimFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter;
	constexpr float AimStep = 1.0f / 60.0f;

	const FAttackTuning& AimTuning()
	{
		return GetDefault<UUmbrellaTuning>()->Attack;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAimedShotTapIsHipFire, "UmbrellaElla.Move.World.AimedShotTapIsHipFire", AimFlags)
bool FAimedShotTapIsHipFire::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla(FVector(0.0, 0.0, 2000.0));
	UAttackEmitterComponent* Emitter = Ella ? Ella->GetAttack() : nullptr;
	if (!TestNotNull(TEXT("ella"), Ella) || !TestNotNull(TEXT("emitter"), Emitter))
	{
		return false;
	}
	const float StartZ = static_cast<float>(Ella->GetActorLocation().Z);
	Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
	Test.TickSeconds(0.12f, AimStep);
	const float ReleaseZ = static_cast<float>(Ella->GetActorLocation().Z);
	Ella->GetInputAdapter()->ApplyRelease(EUmbrellaInputAction::Shoot);
	const int32 Shots = Emitter->GetShotsFired();
	Test.TickSeconds(1.0f, AimStep);
	TestTrue(FString::Printf(TEXT("a tap fires Small Blasts (%d shots)"), Shots), Shots >= 1);
	TestEqual(TEXT("a tap never fires the aimed beam"), Emitter->GetAimedBeamsFired(), 0);
	TestNull(TEXT("no beam on screen"), Emitter->GetAimedBeam());
	TestTrue(FString::Printf(TEXT("she fell while shooting (%.1f -> %.1f)"), StartZ, ReleaseZ), ReleaseZ < StartZ);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAimedShotHoldFiresBeam, "UmbrellaElla.Move.World.AimedShotHoldFiresBeam", AimFlags)
bool FAimedShotHoldFiresBeam::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	UAttackEmitterComponent* Emitter = Ella ? Ella->GetAttack() : nullptr;
	UEllaAnimPresenterComponent* Look = Ella ? Ella->GetAnimPresenter() : nullptr;
	if (!TestNotNull(TEXT("ella"), Ella) || !TestNotNull(TEXT("emitter"), Emitter) || !TestNotNull(TEXT("presenter"), Look))
	{
		return false;
	}
	const FAttackTuning& Tuning = AimTuning();
	UWorld* World = Test.GetWorld();
	// On the beam line (muzzle +111 / +39), far enough that the Small Blasts fired meanwhile have not reached it.
	AUmbrellaEnemy* Target = World->SpawnActor<AUmbrellaEnemy>(AUmbrellaEnemy::StaticClass(), FTransform(FVector(900.0, 0.0, Tuning.AimedMuzzleOffset.Z)));
	if (!TestNotNull(TEXT("enemy"), Target))
	{
		return false;
	}
	Target->Configure(EEnemyType::Roadwarden, EEnemyGender::Male, EUmbrellaShotKind::EnemyRed);
	const float Start = Target->GetHp();

	Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
	float Held = 0.0f;
	bool bSawAimPose = false;
	while (Emitter->GetAimedBeamsFired() == 0 && Held < 1.0f)
	{
		Ella->SetActorLocation(FVector::ZeroVector);   // read the beam, not the fall
		Test.TickFrames(1, AimStep);
		Held += AimStep;
		bSawAimPose |= Look->GetVisualState() == EEllaVisualState::AimShot;
	}
	AddInfo(FString::Printf(TEXT("beam fired after %.3f s held"), Held));
	TestEqual(TEXT("one beam"), Emitter->GetAimedBeamsFired(), 1);
	TestEqual(TEXT("it fires after the charge time"), Held, Tuning.AimedChargeSeconds, 2.0f * AimStep);
	TestTrue(TEXT("Ella showed the aim pose while charging"), bSawAimPose);
	const AAimedBeamActor* Beam = Emitter->GetAimedBeam();
	if (!TestNotNull(TEXT("the beam is on screen"), Beam))
	{
		return false;
	}
	TestEqual(TEXT("beam length"), Beam->GetEffectiveLength(), Tuning.AimedBeamLength, 1.0f);
	const float Lost = Start - Target->GetHp();
	TestEqual(TEXT("the enemy on the line takes the beam damage once"), Lost, Tuning.AimedDamage, 0.01f);
	TestTrue(TEXT("a beam hits harder than a hip-fire shot"), Tuning.AimedDamage > Tuning.SmallDamage);
	TestTrue(TEXT("the beam is drawn with art (a ribbon texture), not a flat box"), Beam->GetRibbon() != nullptr && Beam->GetVisual()->GetStaticMesh() != nullptr);

	// While the beam shows, the pose holds its last cell (the flash at the tip).
	Ella->SetActorLocation(FVector::ZeroVector);
	Test.TickFrames(2, AimStep);
	const FArtSlotRow* AimRow = ArtSlot::Find(TEXT("ella-state:AimShot"));
	TestEqual(TEXT("presenter shows AimShot during the beam"), Look->GetVisualState(), EEllaVisualState::AimShot);
	if (AimRow && Look->IsShowingArt() && AimRow->Cols * AimRow->Rows > 1)
	{
		TestEqual(TEXT("AimShot holds its last cell while the beam fires"), Look->GetDrawnFrame(), AimRow->Cols * AimRow->Rows - 1);
	}
	// Still held: no second beam this hold, and the beam leaves after its time.
	Test.TickSeconds(Tuning.AimedBeamSeconds + 0.2f, AimStep);
	TestEqual(TEXT("one beam per hold"), Emitter->GetAimedBeamsFired(), 1);
	TestNull(TEXT("the beam is gone after its time"), Emitter->GetAimedBeam());
	TestNotEqual(TEXT("the aim pose ends with the beam"), Look->GetVisualState(), EEllaVisualState::AimShot);
	Ella->GetInputAdapter()->ApplyRelease(EUmbrellaInputAction::Shoot);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAimedShotRibbonIsPainted, "UmbrellaElla.Move.AimedShotRibbonIsGradedNotFlat", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FAimedShotRibbonIsPainted::RunTest(const FString& Parameters)
{
	// visual_qa's flat-box detector fails one flat colour with hard edges: the ribbon must grade across and vary along.
	const FColor Core = AAimedBeamActor::RibbonTexel(AAimedBeamActor::RibbonWidth / 2, AAimedBeamActor::RibbonHeight / 2);
	const FColor Edge = AAimedBeamActor::RibbonTexel(AAimedBeamActor::RibbonWidth / 2, 2);
	TestTrue(TEXT("soft edge: the border is far more transparent than the core"), Edge.A + 100 < Core.A);
	TestTrue(TEXT("warm light, no neon: red >= green >= blue in the core"), Core.R >= Core.G && Core.G >= Core.B);
	TSet<uint32> Along;
	for (int32 X = 0; X < AAimedBeamActor::RibbonWidth; X += 16)
	{
		Along.Add(AAimedBeamActor::RibbonTexel(X, AAimedBeamActor::RibbonHeight / 2 - 6).DWColor());
	}
	TestTrue(FString::Printf(TEXT("painted grain along the beam (%d distinct texels of 32)"), Along.Num()), Along.Num() >= 16);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FAimedShotHitsKeeper, "UmbrellaElla.Move.World.AimedBeamDamagesKeeper", AimFlags)
bool FAimedShotHitsKeeper::RunTest(const FString& Parameters)
{
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	UWorld* World = UWorld::CreateWorld(EWorldType::Game, false, FName(TEXT("AimedKeeperWorld")));
	FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
	Context.SetCurrentWorld(World);
	World->InitializeActorsForPlay(FURL());
	World->BeginPlay();
	UEncounterDirectorSubsystem* Director = World->GetSubsystem<UEncounterDirectorSubsystem>();
	bool bOk = TestNotNull(TEXT("director"), Director);
	if (bOk)
	{
		Director->SetManualStepping(true);
		AActor* Player = World->SpawnActor<AActor>();
		USceneComponent* Root = NewObject<USceneComponent>(Player, TEXT("Root"));
		Player->SetRootComponent(Root);
		Root->RegisterComponent();
		Player->SetActorLocation(FVector(-900.0f, 0.0f, 0.0f));
		Director->SetPlayerActor(Player);
		Director->BeginKeeperFight();
		for (float T = 0.0f; T < 2.2f; T += 0.05f)
		{
			Director->AdvanceFight(0.05f);
		}
		AKeeperOfTime* Keeper = Director->GetKeeper();
		UKeeperPartComponent* Wings = Keeper ? Keeper->GetPartComponent(EKeeperPart::Wings) : nullptr;
		bOk = TestNotNull(TEXT("keeper wings"), Wings);
		if (bOk)
		{
			const FVector Center = Wings->Bounds.GetBox().GetCenter();
			const float Before = Director->GetModel().GetPartHp(EKeeperPart::Wings);
			AAimedBeamActor* Beam = World->SpawnActor<AAimedBeamActor>();
			Beam->Place(FVector(Center.X - 600.0, 0.0, Center.Z), AimTuning().AimedBeamLength, AimTuning().AimedBeamWidth);
			FUmbrellaShotSpec Shot;
			Shot.Kind = EUmbrellaShotKind::PlayerBlast;
			Shot.Damage = AimTuning().AimedDamage;
			const int32 Hit = Beam->Fire(Shot);
			const FBox WingBox = Wings->Bounds.GetBox();
			AddInfo(FString::Printf(TEXT("beam hit %d actor(s); wings %.1f -> %.1f; beam length %.0f muzzle %s; wings box %s collision %d"), Hit, Before,
				Director->GetModel().GetPartHp(EKeeperPart::Wings), Beam->GetEffectiveLength(), *Beam->GetMuzzle().ToString(), *WingBox.ToString(),
				static_cast<int32>(Wings->GetCollisionEnabled())));
			TestTrue(TEXT("the beam reaches the Keeper"), Hit >= 1);
			TestEqual(TEXT("the Keeper's wings take the beam damage"), Director->GetModel().GetPartHp(EKeeperPart::Wings), Before - AimTuning().AimedDamage, 0.01f);
		}
	}
	GEngine->DestroyWorldContext(World);
	World->DestroyWorld(false);
	return bOk;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FHipFireHitsKeeper, "UmbrellaElla.Move.World.HipFireShotDamagesKeeperPart", AimFlags)
bool FHipFireHitsKeeper::RunTest(const FString& Parameters)
{
	// ellashoot, 14 Nov: a real-input Keeper run fired 58 Small Blasts and hit the Keeper 0 times: the shots fly on the
	// shot plane (Y 25) and the part boxes sat at Y -70..-30. A Small Blast flown at a live part must damage it.
	AddExpectedError(TEXT("no arena in the world"), EAutomationExpectedErrorFlags::Contains, 0);
	FUmbrellaTestWorld Test;   // a world whose actors tick (the shot flies)
	UWorld* World = Test.GetWorld();
	UEncounterDirectorSubsystem* Director = World->GetSubsystem<UEncounterDirectorSubsystem>();
	bool bOk = TestNotNull(TEXT("director"), Director);
	if (bOk)
	{
		Director->SetManualStepping(true);
		AActor* Player = World->SpawnActor<AActor>();
		USceneComponent* Root = NewObject<USceneComponent>(Player, TEXT("Root"));
		Player->SetRootComponent(Root);
		Root->RegisterComponent();
		Player->SetActorLocation(FVector(-900.0f, 0.0f, 0.0f));
		Director->SetPlayerActor(Player);
		Director->BeginKeeperFight();
		for (float T = 0.0f; T < 2.2f; T += 0.05f)
		{
			Director->AdvanceFight(0.05f);
		}
		AKeeperOfTime* Keeper = Director->GetKeeper();
		UKeeperPartComponent* Wings = Keeper ? Keeper->GetPartComponent(EKeeperPart::Wings) : nullptr;
		bOk = TestNotNull(TEXT("keeper wings"), Wings);
		if (bOk)
		{
			const FVector Center = Wings->Bounds.GetBox().GetCenter();
			const float Before = Director->GetModel().GetPartHp(EKeeperPart::Wings);
			const FAttackTuning& Tuning = AimTuning();
			FUmbrellaShotSpec Shot;
			Shot.Kind = EUmbrellaShotKind::PlayerBlast;
			Shot.Origin = FVector(Center.X - 400.0, 0.0, Center.Z);
			Shot.Velocity = FVector(Tuning.SmallSpeed, 0.0, 0.0);
			Shot.Radius = Tuning.BlastRadius;
			Shot.Damage = Tuning.SmallDamage;
			Shot.LifetimeSeconds = Tuning.SmallRange / Tuning.SmallSpeed;
			AUmbrellaProjectile::Fire(World, Shot);
			Test.TickSeconds(1.0f, 1.0f / 60.0f);
			const float After = Director->GetModel().GetPartHp(EKeeperPart::Wings);
			// The wider part box (KeeperLook::PartShotHalfDepth) must not change enemy shots: a red shot flown through the
			// wings on the same plane is not a Keeper hit and is not stopped by the part (it has a receiver, so no wall).
			FUmbrellaShotSpec Red = Shot;
			Red.Kind = EUmbrellaShotKind::EnemyRed;
			TWeakObjectPtr<AUmbrellaProjectile> RedShot = AUmbrellaProjectile::Fire(World, Red);
			const int32 RedFrames = FMath::CeilToInt((Center.X - Red.Origin.X) / Tuning.SmallSpeed * 60.0f) + 6;
			Test.TickFrames(RedFrames, 1.0f / 60.0f);
			TestEqual(TEXT("an enemy shot through the wider part box does not damage the Keeper"), Director->GetModel().GetPartHp(EKeeperPart::Wings), After);
			TestTrue(TEXT("an enemy shot passes through the part box (not a solid stop)"), RedShot.IsValid() && RedShot->GetActorLocation().X > Center.X);
			AddInfo(FString::Printf(TEXT("wings %.1f -> %.1f; part box %s"), Before, After, *Wings->Bounds.GetBox().ToString()));
			TestEqual(TEXT("a Small Blast on the shot plane damages the Keeper's wings"), After, Before - Tuning.SmallDamage, 0.01f);
		}
	}
	return bOk;
}

#endif
