#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Attack/AttackEmitterComponent.h"
#include "Attack/AttackTuning.h"
#include "Attack/SpellPresentation.h"
#include "Attack/StreamBeamActor.h"
#include "Components/StaticMeshComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaSourceIds.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/World.h"
#include "Health/UmbrellaHealthComponent.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Motor/EllaMotorComponent.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "UI/ClockHudModel.h"
#include "UI/HudTuning.h"
#include "UI/UmbrellaHUD.h"
#include "Umbrella/UmbrellaStateComponent.h"

namespace MoveClauseTest
{
	const float ClauseDeltas[] = {1.0f / 30.0f, 1.0f / 60.0f, 1.0f / 120.0f};
	const FName OrdinarySource(TEXT("MoveClauseTestShot"));

	void SendHealth(UWorld* World, FName Detail)
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::PlayerHealthChanged;
		Event.Detail = Detail;
		UUmbrellaEventBus::Get(World)->Broadcast(Event);
	}
}

// MOVE-15: the overhead hop's protection blocks ordinary hits in Health, and it is not the post-hit window.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveHopBlocksHealthTest, "UmbrellaElla.Move.World.HopProtectionBlocksHealthDamage", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveHopBlocksHealthTest::RunTest(const FString& Parameters)
{
	for (const float Delta : MoveClauseTest::ClauseDeltas)
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		UUmbrellaHealthComponent* Health = Ella->GetHealth();
		const float Full = Health->GetState().Active;
		Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Hop);
		Test.TickFrames(1, Delta);
		TestTrue(TEXT("hop protects"), Ella->GetMotor()->IsHopProtected());
		const double Now = Test.GetWorld()->GetTimeSeconds();

		TestEqual(TEXT("ordinary hit during the hop is blocked"), Health->TakeHitAt(1.0f, MoveClauseTest::OrdinarySource, Now), EHitResult::Blocked);
		TestEqual(TEXT("health unchanged by the blocked hit"), Health->GetState().Active, Full);
		TestEqual(TEXT("a hop block starts no post-hit window (distinct protections)"), Health->GetProtectionRemaining(Now), 0.0f);

		TestEqual(TEXT("a hostile gust bypasses hop protection"), Health->TakeHitAt(1.0f, UmbrellaSourceIds::GustBand(), Now), EHitResult::Landed);
		TestTrue(TEXT("the gust cost health"), Health->GetState().Active < Full);
		const float AfterGust = Health->GetState().Active;

		Test.TickSeconds(0.5f, Delta);
		TestFalse(TEXT("hop protection over"), Ella->GetMotor()->IsHopProtected());
		const double Later = Test.GetWorld()->GetTimeSeconds();
		TestEqual(TEXT("ordinary hit lands once the hop is over"), Health->TakeHitAt(1.0f, MoveClauseTest::OrdinarySource, Later), EHitResult::Landed);
		TestTrue(TEXT("that hit cost health"), Health->GetState().Active < AfterGust);
		TestTrue(TEXT("and it started the post-hit window"), Health->GetProtectionRemaining(Later) > 0.0f);
	}
	return true;
}

// COM-06 / COM-11: Small Blasts fold-ready, snap open with a pulse, cock and reset; only Small cycles.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveCanopyCycleRuleTest, "UmbrellaElla.Move.SmallCanopyCycle", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveCanopyCycleRuleTest::RunTest(const FString& Parameters)
{
	const FAttackTuning Tuning;
	FCanopyCycleState Cycle = SpellPresentationRules::RestingCycle(EUmbrellaSpell::SmallBlasts);
	TestEqual(TEXT("small rests folded-ready"), Cycle.Phase, EUmbrellaCanopyPhase::FoldedReady);
	SpellPresentationRules::Step(Cycle, 1.0f, Tuning);
	TestEqual(TEXT("time alone never opens it"), Cycle.Phase, EUmbrellaCanopyPhase::FoldedReady);

	SpellPresentationRules::OnEmission(Cycle, EUmbrellaSpell::SmallBlasts, Tuning);
	TestEqual(TEXT("emission snaps open"), Cycle.Phase, EUmbrellaCanopyPhase::SnapOpen);
	TestEqual(TEXT("one pulse per emission"), Cycle.Pulses, 1);
	SpellPresentationRules::Step(Cycle, Tuning.SmallCanopyOpenSeconds + 0.001f, Tuning);
	TestEqual(TEXT("then closes and cocks"), Cycle.Phase, EUmbrellaCanopyPhase::Cock);
	SpellPresentationRules::Step(Cycle, Tuning.SmallCanopyCockSeconds, Tuning);
	TestEqual(TEXT("then resets to ready"), Cycle.Phase, EUmbrellaCanopyPhase::FoldedReady);
	TestTrue(TEXT("whole cycle fits inside one shot interval"), Tuning.SmallCanopyOpenSeconds + Tuning.SmallCanopyCockSeconds < 1.0f / Tuning.SmallShotsPerSecond);

	for (const EUmbrellaSpell Spell : {EUmbrellaSpell::StreamedBlast, EUmbrellaSpell::TwinStars, EUmbrellaSpell::Needle})
	{
		FCanopyCycleState Other = SpellPresentationRules::RestingCycle(Spell);
		TestFalse(TEXT("only Small uses fold/open/cock"), SpellPresentationRules::HasCanopyCycle(Spell));
		SpellPresentationRules::OnEmission(Other, Spell, Tuning);
		TestEqual(TEXT("other spells stay open and steady on emission"), Other.Phase, EUmbrellaCanopyPhase::Steady);
		TestEqual(TEXT("other spells never pulse the canopy"), Other.Pulses, 0);
	}
	TestTrue(TEXT("Small uses the cycle"), SpellPresentationRules::HasCanopyCycle(EUmbrellaSpell::SmallBlasts));
	return true;
}

// COM-06 / COM-11 in the world: the canopy snaps open exactly on frames a Small Blast leaves, and is ready again first.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveCanopyWorldTest, "UmbrellaElla.Move.World.CanopyCycleTiedToEmission", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveCanopyWorldTest::RunTest(const FString& Parameters)
{
	for (const float Delta : MoveClauseTest::ClauseDeltas)
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		UAttackEmitterComponent* Emitter = Ella->GetAttack();
		UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();
		Test.TickFrames(2, Delta);
		TestEqual(TEXT("no shot, no cycle"), Emitter->GetCanopyPhase(), EUmbrellaCanopyPhase::FoldedReady);
		TestEqual(TEXT("no shot, no pulse"), Emitter->GetCanopyPulses(), 0);

		Adapter->ApplyPress(EUmbrellaInputAction::Shoot);
		bool bSawCock = false;
		int32 MismatchFrames = 0;
		int32 NotReadyBeforeShot = 0;
		EUmbrellaCanopyPhase Previous = Emitter->GetCanopyPhase();
		const int32 Frames = FMath::RoundToInt(1.0f / Delta);
		for (int32 Frame = 0; Frame < Frames; ++Frame)
		{
			const int32 Before = Emitter->GetShotsFired();
			Test.TickFrames(1, Delta);
			const bool bShot = Emitter->GetShotsFired() > Before;
			const EUmbrellaCanopyPhase Now = Emitter->GetCanopyPhase();
			// A shot frame shows the canopy snapped open; a fresh snap-open never happens without a shot.
			if (bShot ? Now != EUmbrellaCanopyPhase::SnapOpen : (Now == EUmbrellaCanopyPhase::SnapOpen && Previous != EUmbrellaCanopyPhase::SnapOpen))
			{
				++MismatchFrames;
			}
			if (bShot && Before > 0 && Previous != EUmbrellaCanopyPhase::FoldedReady)
			{
				++NotReadyBeforeShot;
			}
			bSawCock |= Now == EUmbrellaCanopyPhase::Cock;
			Previous = Now;
		}
		TestTrue(TEXT("Small fired"), Emitter->GetShotsFired() >= 4);
		TestEqual(TEXT("the canopy snaps open only on frames a shot leaves"), MismatchFrames, 0);
		TestEqual(TEXT("one canopy pulse per Small emission"), Emitter->GetCanopyPulses(), Emitter->GetShotsFired());
		TestTrue(TEXT("close/cock seen"), bSawCock);
		TestEqual(TEXT("folded-ready again before every next shot (no reload input)"), NotReadyBeforeShot, 0);

		Adapter->ApplyRelease(EUmbrellaInputAction::Shoot);
		const int32 PulsesAtRelease = Emitter->GetCanopyPulses();
		Test.TickSeconds(0.5f, Delta);
		TestEqual(TEXT("no emission, no pulse"), Emitter->GetCanopyPulses(), PulsesAtRelease);
		TestEqual(TEXT("rests folded-ready"), Emitter->GetCanopyPhase(), EUmbrellaCanopyPhase::FoldedReady);

		// The other spells hold the canopy open and steady while firing.
		Emitter->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
		Emitter->SetDirectorLevel(30);
		for (const EUmbrellaSpell Spell : {EUmbrellaSpell::StreamedBlast, EUmbrellaSpell::TwinStars, EUmbrellaSpell::Needle})
		{
			Emitter->SelectSpell(Spell);
			const int32 PulsesAtEquip = Emitter->GetCanopyPulses();
			Adapter->ApplyPress(EUmbrellaInputAction::Shoot);
			const int32 ShotsBefore = Emitter->GetShotsFired();
			bool bLeftSteady = false;
			for (int32 Frame = 0; Frame < Frames; ++Frame)
			{
				Test.TickFrames(1, Delta);
				bLeftSteady |= Emitter->GetCanopyPhase() != EUmbrellaCanopyPhase::Steady;
			}
			TestTrue(TEXT("the spell fired"), Emitter->GetShotsFired() > ShotsBefore);
			TestFalse(TEXT("only Small uses fold/open/cock"), bLeftSteady);
			TestEqual(TEXT("no canopy pulses from other spells"), Emitter->GetCanopyPulses(), PulsesAtEquip);
			Adapter->ApplyRelease(EUmbrellaInputAction::Shoot);
			Test.TickFrames(1, Delta);
		}
	}
	return true;
}

// COM-07 / COM-11: RegularFall for Small/Twin/Needle, the shoulder-braced ShoulderFall for Stream.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveBodyPoseTest, "UmbrellaElla.Move.World.SpellBodyPoses", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveBodyPoseTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("Small: RegularFall"), SpellPresentationRules::BodyPoseFor(EUmbrellaSpell::SmallBlasts), EUmbrellaBodyPose::RegularFall);
	TestEqual(TEXT("Stream: ShoulderFall"), SpellPresentationRules::BodyPoseFor(EUmbrellaSpell::StreamedBlast), EUmbrellaBodyPose::ShoulderFall);
	TestEqual(TEXT("Twin: RegularFall"), SpellPresentationRules::BodyPoseFor(EUmbrellaSpell::TwinStars), EUmbrellaBodyPose::RegularFall);
	TestEqual(TEXT("Needle: RegularFall"), SpellPresentationRules::BodyPoseFor(EUmbrellaSpell::Needle), EUmbrellaBodyPose::RegularFall);

	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	UAttackEmitterComponent* Emitter = Ella->GetAttack();
	Emitter->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
	Emitter->SetDirectorLevel(30);
	TestEqual(TEXT("emitter: Small regular"), Emitter->GetBodyPose(), EUmbrellaBodyPose::RegularFall);
	Emitter->SelectSpell(EUmbrellaSpell::StreamedBlast);
	TestEqual(TEXT("emitter: Stream shoulder-braced"), Emitter->GetBodyPose(), EUmbrellaBodyPose::ShoulderFall);
	Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
	Test.TickSeconds(0.3f, 1.0f / 60.0f);
	const float StreamDamage = Emitter->GetLastShot().Damage;
	TestEqual(TEXT("posture adds no damage: tick damage is the tuned 4"), StreamDamage, GetDefault<UUmbrellaTuning>()->Attack.StreamTickDamage);
	Emitter->SelectSpell(EUmbrellaSpell::Needle);
	TestEqual(TEXT("emitter: Needle regular"), Emitter->GetBodyPose(), EUmbrellaBodyPose::RegularFall);
	return true;
}

// COM-07: canopy-interior strands converge forward around the dark beam body; looks only, the box stays the hitbox.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveStreamStrandsTest, "UmbrellaElla.Move.World.StreamStrandsConvergeOnDarkBody", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveStreamStrandsTest::RunTest(const FString& Parameters)
{
	const FAttackTuning& Tuning = GetDefault<UUmbrellaTuning>()->Attack;
	const float Length = 600.0f;
	const float Width = Tuning.StreamWidth;
	const TArray<FBeamStrand> Strands = SpellPresentationRules::BeamStrands(Length, Width, Tuning);
	TestEqual(TEXT("tuned strand count"), Strands.Num(), Tuning.StreamStrandCount);
	int32 Above = 0;
	int32 Below = 0;
	for (const FBeamStrand& Strand : Strands)
	{
		TestEqual(TEXT("strand leaves at the muzzle"), static_cast<float>(Strand.Start.X), 0.0f);
		TestTrue(TEXT("strand starts out in the canopy, wider than the body"), FMath::Abs(Strand.Start.Y) > Width * 0.5f);
		TestTrue(TEXT("strand converges forward"), Strand.Converge.X > Strand.Start.X && Strand.Converge.X < Length);
		TestEqual(TEXT("converges onto the body edge"), static_cast<float>(FMath::Abs(Strand.Converge.Y)), Width * 0.5f, 0.001f);
		TestEqual(TEXT("runs along the body to the tip"), static_cast<float>(Strand.End.X), Length, 0.001f);
		TestEqual(TEXT("stays on the body edge"), static_cast<float>(FMath::Abs(Strand.End.Y)), Width * 0.5f, 0.001f);
		(Strand.Start.Y > 0.0 ? Above : Below) += 1;
	}
	TestTrue(TEXT("strands surround the body, above and below"), Above > 0 && Below > 0);

	FUmbrellaTestWorld Test;
	AStreamBeamActor* Beam = Test.GetWorld()->SpawnActor<AStreamBeamActor>();
	if (!TestNotNull(TEXT("beam spawned"), Beam))
	{
		return false;
	}
	const FVector Muzzle(0.0, 0.0, 100.0);
	Beam->SetBeam(Muzzle, Length, Width);
	TestTrue(TEXT("dark body"), Beam->GetBodyColor().GetLuminance() < 0.1f);
	TestTrue(TEXT("bright strands around it"), Beam->GetStrandColor().GetLuminance() > Beam->GetBodyColor().GetLuminance() * 5.0f);
	TestEqual(TEXT("two parts per strand"), Beam->GetStrandParts().Num(), Tuning.StreamStrandCount * 2);
	const FVector BodyScale = Beam->GetBody()->GetComponentScale();
	TestEqual(TEXT("body is still the hitbox height"), static_cast<float>(BodyScale.Z * AStreamBeamActor::CubeSize), Width, 0.01f);
	for (const TObjectPtr<UStaticMeshComponent>& Part : Beam->GetStrandParts())
	{
		TestTrue(TEXT("strand visible"), Part->IsVisible());
		TestEqual(TEXT("strands never collide"), Part->GetCollisionEnabled(), ECollisionEnabled::NoCollision);
		TestTrue(TEXT("strands drawn in front of the body"), Part->GetComponentLocation().Y > Beam->GetBody()->GetComponentLocation().Y);
		TestTrue(TEXT("strand inside the beam span"), Part->GetComponentLocation().X >= Muzzle.X && Part->GetComponentLocation().X <= Muzzle.X + Length);
	}
	// The first part of a strand points inward (toward the body), the second runs straight along it.
	const UStaticMeshComponent* FirstLeg = Beam->GetStrandParts()[0];
	const UStaticMeshComponent* SecondLeg = Beam->GetStrandParts()[1];
	TestTrue(TEXT("upper strand descends toward the body"), FirstLeg->GetForwardVector().Z < -0.01);
	TestEqual(TEXT("then runs level along the body"), static_cast<float>(SecondLeg->GetForwardVector().Z), 0.0f, 0.001f);
	TestEqual(TEXT("tick damage untouched by strands"), Tuning.StreamTickDamage, 4.0f);
	return true;
}

// COM-11: the locked-weapon display shows the Director's Cut unlock levels 1/10/20/30.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWheelLevelsTest, "UmbrellaElla.Move.WheelShowsUnlockLevels", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWheelLevelsTest::RunTest(const FString& Parameters)
{
	const FAttackTuning& Tuning = GetDefault<UUmbrellaTuning>()->Attack;
	const TArray<FSpellWheelEntry> AtOne = SpellPresentationRules::WheelEntries(EUmbrellaPlayMode::DirectorsCut, 1, Tuning);
	if (!TestEqual(TEXT("four weapons on the wheel"), AtOne.Num(), 4))
	{
		return false;
	}
	const int32 Levels[] = {1, 10, 20, 30};
	for (int32 Index = 0; Index < 4; ++Index)
	{
		TestEqual(TEXT("unlock level"), AtOne[Index].UnlockLevel, Levels[Index]);
	}
	TestFalse(TEXT("Small unlocked at level 1"), AtOne[0].bLocked);
	TestTrue(TEXT("unlocked weapon has no lock label"), AtOne[0].LockLabel.IsEmpty());
	TestEqual(TEXT("Stream shows Lv 10"), AtOne[1].LockLabel, FString(TEXT("Lv 10")));
	TestEqual(TEXT("Twin shows Lv 20"), AtOne[2].LockLabel, FString(TEXT("Lv 20")));
	TestEqual(TEXT("Needle shows Lv 30"), AtOne[3].LockLabel, FString(TEXT("Lv 30")));

	const TArray<FSpellWheelEntry> AtTwenty = SpellPresentationRules::WheelEntries(EUmbrellaPlayMode::DirectorsCut, 20, Tuning);
	TestFalse(TEXT("Stream unlocked at 20"), AtTwenty[1].bLocked);
	TestTrue(TEXT("Twin unlocked at 20, label gone"), !AtTwenty[2].bLocked && AtTwenty[2].LockLabel.IsEmpty());
	TestEqual(TEXT("Needle still shows Lv 30"), AtTwenty[3].LockLabel, FString(TEXT("Lv 30")));

	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	UAttackEmitterComponent* Emitter = Ella->GetAttack();
	Emitter->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
	Emitter->SetDirectorLevel(10);
	const TArray<FSpellWheelEntry> Live = Emitter->GetWheelEntries();
	TestEqual(TEXT("emitter wheel: Twin locked at Lv 20"), Live[2].LockLabel, FString(TEXT("Lv 20")));
	TestTrue(TEXT("emitter wheel: Stream open at 10"), Live[1].LockLabel.IsEmpty());
	return true;
}

// FLOW-30: antique bronze/gold rim, smoky translucent face, etched ring and marks.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveClockLookTest, "UmbrellaElla.Move.ClockDialLook", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveClockLookTest::RunTest(const FString& Parameters)
{
	const FHudTuning& Tuning = GetDefault<UUmbrellaTuning>()->Hud;
	const FClockLayout Layout = ClockHudRules::ComputeLayout(FVector2D(1920.0, 1080.0), Tuning);
	const FClockDialPlan Drawn = ClockHudRules::BuildDialPlan(Layout, Tuning, false);
	TestTrue(TEXT("smoky translucent face"), ClockHudRules::IsSmokyTranslucent(Drawn.FaceColor));
	TestFalse(TEXT("an opaque face is not smoky"), ClockHudRules::IsSmokyTranslucent(FLinearColor(0.05f, 0.04f, 0.04f, 1.0f)));
	TestFalse(TEXT("a cold grey rim is not bronze"), ClockHudRules::IsAntiqueBronzeGold(FLinearColor(0.6f, 0.6f, 0.65f, 1.0f)));

	int32 Rings = 0;
	int32 EtchedRings = 0;
	int32 HourTicks = 0;
	int32 EtchMarks = 0;
	float RimThickness = 0.0f;
	for (const FClockDialStroke& Stroke : Drawn.Strokes)
	{
		TestTrue(TEXT("every stroke antique bronze/gold"), ClockHudRules::IsAntiqueBronzeGold(Stroke.Color));
		if (Stroke.bRing)
		{
			++Rings;
			if (FMath::IsNearlyEqual(Stroke.Radius, Layout.Radius))
			{
				RimThickness = Stroke.Thickness;
			}
			else if (Stroke.Radius < Layout.Radius && Stroke.Thickness <= Tuning.EtchThickness)
			{
				++EtchedRings;
			}
		}
		else if (Stroke.Thickness >= ClockHudConstants::TickThickness)
		{
			++HourTicks;
		}
		else
		{
			++EtchMarks;
		}
	}
	TestEqual(TEXT("one bronze rim plus one etched ring"), Rings, 2);
	TestEqual(TEXT("etched ring inside the rim"), EtchedRings, 1);
	TestTrue(TEXT("etched ring finer than the rim"), Tuning.EtchThickness < RimThickness);
	TestEqual(TEXT("twelve hour ticks"), HourTicks, 12);
	TestEqual(TEXT("fine etched marks between the hours"), EtchMarks, Tuning.EtchMarkCount - 12);

	const FClockDialPlan WithArt = ClockHudRules::BuildDialPlan(Layout, Tuning, true);
	TestTrue(TEXT("with art the face is still smoky and see-through"), ClockHudRules::IsSmokyTranslucent(WithArt.FaceColor));
	TestTrue(TEXT("with art the art carries the rim"), WithArt.bDrawArt && WithArt.Strokes.IsEmpty());
	return true;
}

// FLOW-32: absorbed energy visibly flows from Ella into the clock on a real heal (not on damage or a full capture).
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveEnergyFlowTest, "UmbrellaElla.Move.World.HealEnergyFlowsIntoClock", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveEnergyFlowTest::RunTest(const FString& Parameters)
{
	const FHudTuning& Tuning = GetDefault<UUmbrellaTuning>()->Hud;
	FClockEnergyMote Mote;
	Mote.From = FVector2D(900.0, 600.0);
	Mote.To = FVector2D(100.0, 100.0);
	TestTrue(TEXT("leaves from Ella"), ClockHudRules::EnergyPosition(Mote, 0.0f, Tuning).Equals(Mote.From, 0.01));
	TestTrue(TEXT("lands on the clock"), ClockHudRules::EnergyPosition(Mote, Tuning.EnergyFlowSeconds, Tuning).Equals(Mote.To, 0.01));
	const FVector2D Mid = ClockHudRules::EnergyPosition(Mote, Tuning.EnergyFlowSeconds * 0.5f, Tuning);
	TestTrue(TEXT("on its way between"), Mid.X < Mote.From.X && Mid.X > Mote.To.X);

	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	AUmbrellaHUD* Hud = Test.GetWorld()->SpawnActor<AUmbrellaHUD>();
	if (!TestNotNull(TEXT("Ella spawned"), Ella) || !TestNotNull(TEXT("HUD spawned"), Hud))
	{
		return false;
	}
	UUmbrellaHealthComponent* Health = Ella->GetHealth();
	Health->HealFromYellow(MoveClauseTest::OrdinarySource);
	TestEqual(TEXT("full-health capture sends no energy"), Hud->GetEnergyMotes().Num(), 0);
	Health->TakeHitAt(1.0f, MoveClauseTest::OrdinarySource, 0.0);
	TestEqual(TEXT("damage sends no energy"), Hud->GetEnergyMotes().Num(), 0);
	const FHealthHealOutcome Healed = Health->HealFromYellow(MoveClauseTest::OrdinarySource);
	TestFalse(TEXT("the yellow healed"), Healed.bNothingChanged);
	TestEqual(TEXT("a heal sends energy into the clock"), Hud->GetEnergyMotes().Num(), 1);
	MoveClauseTest::SendHealth(Test.GetWorld(), FName(TEXT("Heal")));
	TestEqual(TEXT("one mote per heal"), Hud->GetEnergyMotes().Num(), 2);

	Hud->StepEnergyFlow(Tuning.EnergyFlowSeconds * 0.5f);
	TestEqual(TEXT("still flowing halfway"), Hud->GetEnergyMotes().Num(), 2);
	Hud->StepEnergyFlow(Tuning.EnergyFlowSeconds);
	TestEqual(TEXT("arrived in the clock"), Hud->GetEnergyMotes().Num(), 0);
	TestEqual(TEXT("both reached the clock"), Hud->GetEnergyArrived(), 2);
	return true;
}

#endif
