#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Attack/StreamBeamActor.h"
#include "Components/PointLightComponent.h"
#include "Components/PrimitiveComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaDrawOrder.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaSourceIds.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Engine/World.h"
#include "Feedback/Vfx/KeeperVfxRules.h"
#include "Feedback/Vfx/LightShaftRules.h"
#include "Feedback/Vfx/UmbrellaVfxDirectorSubsystem.h"
#include "Feedback/Vfx/UmbrellaVfxSubsystem.h"
#include "Feedback/Vfx/VfxCatalog.h"
#include "Feedback/Vfx/VfxLightPolicy.h"
#include "Feedback/Vfx/VfxSheetVisual.h"
#include "Owl/KeeperOfTime.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "Umbrella/UmbrellaPlayerIds.h"

namespace
{
	constexpr EAutomationTestFlags VfxArtTestFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter;
	constexpr float VfxArtTestStep = 1.0f / 60.0f;

	bool VfxArtTestHasCue(const TArray<FKeeperVfxCue>& Cues, const TCHAR* Key, bool bStart)
	{
		return Cues.ContainsByPredicate([Key, bStart](const FKeeperVfxCue& Cue) { return Cue.Key == FName(Key) && Cue.bStart == bStart; });
	}

	int32 VfxArtTestStarts(const TArray<FKeeperVfxCue>& Cues)
	{
		int32 Count = 0;
		for (const FKeeperVfxCue& Cue : Cues)
		{
			Count += Cue.bStart ? 1 : 0;
		}
		return Count;
	}

	FKeeperVfxSnapshot VfxArtTestSnapshot(EKeeperPhysical Physical, EKeeperStage Stage)
	{
		FKeeperVfxSnapshot Snapshot;
		Snapshot.bFightActive = true;
		Snapshot.Physical = Physical;
		Snapshot.Stage = Stage;
		return Snapshot;
	}

	void VfxArtTestSend(UWorld* World, EUmbrellaEventType Type, FName Source, FName Detail, FName Target = NAME_None)
	{
		FUmbrellaEvent Event;
		Event.Type = Type;
		Event.SourceId = Source;
		Event.Detail = Detail;
		Event.TargetId = Target;
		UUmbrellaEventBus::Get(World)->Broadcast(Event);
	}

	AUmbrellaProjectile* VfxArtTestFire(UWorld* World, const FVector& Origin)
	{
		FUmbrellaShotSpec Spec;
		Spec.Kind = EUmbrellaShotKind::PlayerBlast;
		Spec.Origin = Origin;
		Spec.Velocity = FVector(600.0, 0.0, 0.0);
		Spec.Radius = 8.0f;
		Spec.Damage = 1.0f;
		Spec.LifetimeSeconds = 0.5f;
		Spec.SourceId = UmbrellaPlayerIds::Ella;
		return AUmbrellaProjectile::Fire(World, Spec);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVfxArtCatalogRules, "UmbrellaElla.Feedback.VfxCatalogRules", VfxArtTestFlags)

bool FVfxArtCatalogRules::RunTest(const FString& Parameters)
{
	TArray<FName> Keys;
	for (const FVfxArtRow& Row : VfxCatalog::Rows())
	{
		TestFalse(TEXT("effect key is unique"), Keys.Contains(FName(Row.Key)));
		Keys.Add(FName(Row.Key));
		TestTrue(TEXT("sheet has frames"), Row.Frames > 0 && Row.Fps > 0.0f && Row.Size > 0.0f);
		const float LayerY = VfxCatalog::LayerY(Row.Layer);
		TestTrue(TEXT("effect layer is not a sprite layer"), LayerY != UmbrellaDrawOrder::EllaY && LayerY != UmbrellaDrawOrder::KeeperY
			&& LayerY != UmbrellaDrawOrder::ArenaY);
		TestTrue(TEXT("an effect without light has no light colour"), Row.bLit || Row.LightHex == VfxCatalogData::None);
		TestTrue(TEXT("a flashing effect is a one-shot"), !Row.bFlashing || !Row.bLoop);
		TestEqual(TEXT("placeholder sheet is the fallback path"), VfxCatalog::TexturePaths(Row).Num(), 2);
	}
	// Four weapons, each with its own stages.
	const EVfxWeaponStage Common[] = { EVfxWeaponStage::Release, EVfxWeaponStage::Impact, EVfxWeaponStage::Fade };
	TArray<FName> Releases;
	for (int32 Index = 0; Index < SpellRules::SpellCount; ++Index)
	{
		const EUmbrellaSpell Spell = static_cast<EUmbrellaSpell>(Index);
		for (const EVfxWeaponStage Stage : Common)
		{
			TestNotNull(TEXT("spell stage has an effect"), VfxCatalog::Find(VfxCatalog::WeaponKey(Spell, Stage)));
		}
		Releases.AddUnique(VfxCatalog::WeaponKey(Spell, EVfxWeaponStage::Release));
	}
	TestEqual(TEXT("each weapon has its own release effect"), Releases.Num(), SpellRules::SpellCount);
	TestNotNull(TEXT("small blasts travel"), VfxCatalog::Find(VfxCatalog::WeaponKey(EUmbrellaSpell::SmallBlasts, EVfxWeaponStage::Travel)));
	TestNotNull(TEXT("stream sustains"), VfxCatalog::Find(VfxCatalog::WeaponKey(EUmbrellaSpell::StreamedBlast, EVfxWeaponStage::Sustain)));
	TestTrue(TEXT("stream has no travelling head"), VfxCatalog::WeaponKey(EUmbrellaSpell::StreamedBlast, EVfxWeaponStage::Travel).IsNone());
	TestNotNull(TEXT("twin stars have a head"), VfxCatalog::Find(VfxCatalog::WeaponKey(EUmbrellaSpell::TwinStars, EVfxWeaponStage::Travel)));
	TestNotNull(TEXT("needle channels"), VfxCatalog::Find(VfxCatalog::WeaponKey(EUmbrellaSpell::Needle, EVfxWeaponStage::Channel)));
	TestNotNull(TEXT("needle pierces"), VfxCatalog::Find(VfxCatalog::WeaponKey(EUmbrellaSpell::Needle, EVfxWeaponStage::Pierce)));
	TestTrue(TEXT("only the needle pierces"), VfxCatalog::WeaponKey(EUmbrellaSpell::SmallBlasts, EVfxWeaponStage::Pierce).IsNone()
		&& VfxCatalog::WeaponKey(EUmbrellaSpell::TwinStars, EVfxWeaponStage::Pierce).IsNone());
	const FVfxArtRow* Protected = VfxCatalog::Find(VfxCatalog::ProtectedContactKey());
	if (TestNotNull(TEXT("protected contact effect"), Protected))
	{
		TestTrue(TEXT("protected contact never looks like damage"), !Protected->bFlashing && !Protected->bLit);
	}
	// Frames follow game time.
	const FVfxArtRow* Loop = VfxCatalog::Find(TEXT("SmallBlastTravel"));
	const FVfxArtRow* Once = VfxCatalog::Find(TEXT("SmallBlastImpact"));
	if (TestNotNull(TEXT("loop row"), Loop) && TestNotNull(TEXT("one-shot row"), Once))
	{
		TestEqual(TEXT("first frame"), VfxCatalog::FrameAt(*Once, 0.0f), 0);
		TestEqual(TEXT("one-shot holds its last frame"), VfxCatalog::FrameAt(*Once, 99.0f), Once->Frames - 1);
		TestEqual(TEXT("loop wraps"), VfxCatalog::FrameAt(*Loop, VfxCatalog::Duration(*Loop) + 0.5f / Loop->Fps), 0);
		TestTrue(TEXT("one-shot finishes"), VfxCatalog::IsFinished(*Once, VfxCatalog::Duration(*Once)));
		TestFalse(TEXT("loop never finishes alone"), VfxCatalog::IsFinished(*Loop, 99.0f));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVfxArtKeeperRules, "UmbrellaElla.Feedback.VfxKeeperRules", VfxArtTestFlags)

bool FVfxArtKeeperRules::RunTest(const FString& Parameters)
{
	const EKeeperPhysical Physicals[] = { EKeeperPhysical::Gust, EKeeperPhysical::Talon, EKeeperPhysical::FrontCast, EKeeperPhysical::MiddleCurve,
		EKeeperPhysical::RearTwoStage };
	const FName Attacks[] = { UmbrellaSourceIds::GustBand(), UmbrellaSourceIds::TalonRake(), UmbrellaSourceIds::MechFrontCast(),
		UmbrellaSourceIds::MechMiddleCurve(), UmbrellaSourceIds::MechRearTwoStage() };
	TArray<FName> Warnings;
	for (int32 Index = 0; Index < UE_ARRAY_COUNT(Physicals); ++Index)
	{
		TestEqual(TEXT("attack name maps to its move"), KeeperVfxRules::PhysicalForAttack(Attacks[Index]), Physicals[Index]);
		TestNotNull(TEXT("warning effect"), VfxCatalog::Find(KeeperVfxRules::WarningKey(Physicals[Index])));
		TestNotNull(TEXT("strike effect"), VfxCatalog::Find(KeeperVfxRules::StrikeKey(Physicals[Index])));
		TestNotNull(TEXT("recovery effect"), VfxCatalog::Find(KeeperVfxRules::RecoveryKey(Physicals[Index])));
		const FVfxArtRow* Recovery = VfxCatalog::Find(KeeperVfxRules::RecoveryKey(Physicals[Index]));
		TestTrue(TEXT("recovery never looks like damage"), Recovery && !Recovery->bFlashing && !Recovery->bLit);
		Warnings.AddUnique(KeeperVfxRules::WarningKey(Physicals[Index]));
	}
	TestEqual(TEXT("each move has its own warning"), Warnings.Num(), static_cast<int32>(UE_ARRAY_COUNT(Physicals)));
	TestEqual(TEXT("a shot name is not a physical move"), KeeperVfxRules::PhysicalForAttack(UmbrellaSourceIds::RedFan()), EKeeperPhysical::None);
	for (const FName Key : KeeperVfxRules::HeldKeys())
	{
		const FVfxArtRow* Row = VfxCatalog::Find(Key);
		TestTrue(TEXT("held effect is a loop in the catalog"), Row && Row->bLoop);
	}

	TArray<FKeeperVfxCue> Cues;
	// Warning to strike: the warning ends, the strike starts once.
	KeeperVfxRules::Diff(VfxArtTestSnapshot(EKeeperPhysical::Talon, EKeeperStage::Warning), VfxArtTestSnapshot(EKeeperPhysical::Talon, EKeeperStage::Stroke), Cues);
	TestTrue(TEXT("talon warning stops"), VfxArtTestHasCue(Cues, TEXT("TalonWarning"), false));
	TestTrue(TEXT("talon strike starts"), VfxArtTestHasCue(Cues, TEXT("TalonStrike"), true));
	TestEqual(TEXT("one start"), VfxArtTestStarts(Cues), 1);
	// The rear cast's safe pause adds nothing that could read as damage.
	Cues.Reset();
	KeeperVfxRules::Diff(VfxArtTestSnapshot(EKeeperPhysical::RearTwoStage, EKeeperStage::Stroke), VfxArtTestSnapshot(EKeeperPhysical::RearTwoStage, EKeeperStage::Pause), Cues);
	TestEqual(TEXT("safe pause starts no effect"), VfxArtTestStarts(Cues), 0);
	Cues.Reset();
	KeeperVfxRules::Diff(VfxArtTestSnapshot(EKeeperPhysical::RearTwoStage, EKeeperStage::Pause), VfxArtTestSnapshot(EKeeperPhysical::RearTwoStage, EKeeperStage::SecondStroke), Cues);
	TestTrue(TEXT("second stroke strikes again"), VfxArtTestHasCue(Cues, TEXT("MechRearStrike"), true));
	// Recovery (the harmless return) shows only the recovery cue.
	Cues.Reset();
	KeeperVfxRules::Diff(VfxArtTestSnapshot(EKeeperPhysical::FrontCast, EKeeperStage::Stroke), VfxArtTestSnapshot(EKeeperPhysical::FrontCast, EKeeperStage::Recovery), Cues);
	TestTrue(TEXT("recovery cue"), VfxArtTestHasCue(Cues, TEXT("MechFrontRecovery"), true));
	TestEqual(TEXT("recovery starts nothing else"), VfxArtTestStarts(Cues), 1);
	// Gust: release and travel, then expiry.
	Cues.Reset();
	KeeperVfxRules::Diff(VfxArtTestSnapshot(EKeeperPhysical::Gust, EKeeperStage::Warning), VfxArtTestSnapshot(EKeeperPhysical::Gust, EKeeperStage::Stroke), Cues);
	TestTrue(TEXT("gust release"), VfxArtTestHasCue(Cues, TEXT("GustRelease"), true));
	TestTrue(TEXT("gust travel"), VfxArtTestHasCue(Cues, TEXT("GustTravel"), true));
	Cues.Reset();
	KeeperVfxRules::Diff(VfxArtTestSnapshot(EKeeperPhysical::Gust, EKeeperStage::Stroke), VfxArtTestSnapshot(EKeeperPhysical::None, EKeeperStage::Idle), Cues);
	TestTrue(TEXT("gust travel stops"), VfxArtTestHasCue(Cues, TEXT("GustTravel"), false));
	TestTrue(TEXT("gust expiry"), VfxArtTestHasCue(Cues, TEXT("GustExpiry"), true));
	// Clock, eye, slow, stun, blackout and restoration, departure.
	FKeeperVfxSnapshot Before = VfxArtTestSnapshot(EKeeperPhysical::None, EKeeperStage::Idle);
	FKeeperVfxSnapshot After = Before;
	After.bClockOpen = true;
	After.bEyeExposed = true;
	After.bSlowed = true;
	After.bStunned = true;
	After.bBlackedOut = true;
	Cues.Reset();
	KeeperVfxRules::Diff(Before, After, Cues);
	TestTrue(TEXT("clock opening"), VfxArtTestHasCue(Cues, TEXT("ClockOpening"), true));
	TestTrue(TEXT("eye exposed"), VfxArtTestHasCue(Cues, TEXT("KeeperEyeExposed"), true));
	TestTrue(TEXT("slow"), VfxArtTestHasCue(Cues, TEXT("KeeperSlow"), true));
	TestTrue(TEXT("stun"), VfxArtTestHasCue(Cues, TEXT("KeeperStun"), true));
	TestTrue(TEXT("blackout"), VfxArtTestHasCue(Cues, TEXT("KeeperBlackout"), true));
	Cues.Reset();
	KeeperVfxRules::Diff(After, Before, Cues);
	TestTrue(TEXT("clock cover"), VfxArtTestHasCue(Cues, TEXT("ClockCover"), true));
	TestTrue(TEXT("blackout ends"), VfxArtTestHasCue(Cues, TEXT("KeeperBlackout"), false));
	TestTrue(TEXT("restoration"), VfxArtTestHasCue(Cues, TEXT("KeeperRestoration"), true));
	TestTrue(TEXT("stun ends"), VfxArtTestHasCue(Cues, TEXT("KeeperStun"), false));
	Cues.Reset();
	KeeperVfxRules::Diff(After, After, Cues);
	TestEqual(TEXT("no change, no cue"), Cues.Num(), 0);
	// Reset: everything held stops, nothing starts.
	Cues.Reset();
	KeeperVfxRules::Diff(After, FKeeperVfxSnapshot(), Cues);
	TestEqual(TEXT("reset starts nothing"), VfxArtTestStarts(Cues), 0);
	TestEqual(TEXT("reset stops every held effect"), Cues.Num(), KeeperVfxRules::HeldKeys().Num());
	// Living departure.
	FKeeperVfxSnapshot Leaving;
	Leaving.bDeparting = true;
	Cues.Reset();
	KeeperVfxRules::Diff(Before, Leaving, Cues);
	TestTrue(TEXT("departure"), VfxArtTestHasCue(Cues, TEXT("KeeperDeparture"), true));
	// Double beat: one effect per beat.
	TestTrue(TEXT("first shot of a beat"), KeeperVfxRules::IsNewBeat(0.6f, 0.09f, 0.6f));
	TestFalse(TEXT("next shot of the same beat"), KeeperVfxRules::IsNewBeat(0.09f, 0.09f, 0.6f));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVfxArtLightRules, "UmbrellaElla.Feedback.VfxLightAndShaftRules", VfxArtTestFlags)

bool FVfxArtLightRules::RunTest(const FString& Parameters)
{
	const FVfxArtRow* Impact = VfxCatalog::Find(TEXT("SmallBlastImpact"));
	const FVfxArtRow* Fade = VfxCatalog::Find(TEXT("SmallBlastFade"));
	const FVfxArtRow* Travel = VfxCatalog::Find(TEXT("SmallBlastTravel"));
	if (!TestNotNull(TEXT("impact row"), Impact) || !TestNotNull(TEXT("fade row"), Fade) || !TestNotNull(TEXT("travel row"), Travel))
	{
		return false;
	}
	const FVfxLightPlan On = VfxLightPolicy::PlanFor(*Impact, true, false);
	TestTrue(TEXT("lit effect: point light and overlay"), On.bPointLight && On.bSpillOverlay);
	TestTrue(TEXT("light stays local"), On.Radius > 0.0f && On.Radius <= VfxLightPolicy::MaxRadius);
	TestEqual(TEXT("light has the effect's colour"), On.Colour, VfxCatalog::LightColour(*Impact));
	const FVfxLightPlan Off = VfxLightPolicy::PlanFor(*Impact, false, false);
	TestTrue(TEXT("switched off: nothing"), !Off.bPointLight && !Off.bSpillOverlay && Off.Intensity == 0.0f);
	const FVfxLightPlan Unlit = VfxLightPolicy::PlanFor(*Fade, true, false);
	TestTrue(TEXT("an unlit effect throws no light"), !Unlit.bPointLight && !Unlit.bSpillOverlay);
	const FVfxLightPlan Reduced = VfxLightPolicy::PlanFor(*Impact, true, true);
	TestEqual(TEXT("reduced flash dims a flashing light"), Reduced.Intensity, On.Intensity * VfxLightPolicy::ReducedFraction);
	TestTrue(TEXT("reduced flash keeps the light"), Reduced.bPointLight);
	TestEqual(TEXT("reduced flash leaves a steady light alone"), VfxLightPolicy::PlanFor(*Travel, true, true).Intensity, VfxLightPolicy::PointIntensity);
	TestEqual(TEXT("light starts full"), VfxLightPolicy::FadeAt(*Impact, 0.0f), 1.0f);
	TestEqual(TEXT("light is gone at the end"), VfxLightPolicy::FadeAt(*Impact, VfxCatalog::Duration(*Impact)), 0.0f);
	TestTrue(TEXT("overlay is above the characters and below the shots"), VfxLightPolicy::SpillLayerY() > UmbrellaDrawOrder::EllaY
		&& VfxLightPolicy::SpillLayerY() < UmbrellaDrawOrder::ProjectileY);

	// The quad faces the camera (+Y) with its X on world X.
	const FRotator Facing = VfxSheetVisual::FacingCamera();
	TestTrue(TEXT("quad normal faces the camera"), Facing.RotateVector(FVector::ZAxisVector).Equals(FVector::YAxisVector, 0.001));
	TestTrue(TEXT("quad X is screen right"), Facing.RotateVector(FVector::XAxisVector).Equals(FVector::XAxisVector, 0.001));

	// Light and umbra.
	TestTrue(TEXT("open while rising"), LightShaftRules::IsUmbrellaOpen(EUmbrellaAction::Rise));
	TestFalse(TEXT("folded while shooting"), LightShaftRules::IsUmbrellaOpen(EUmbrellaAction::ShootFall));
	TestFalse(TEXT("folded while absorbing"), LightShaftRules::IsUmbrellaOpen(EUmbrellaAction::AbsorbFall));
	TestFalse(TEXT("folded in free fall"), LightShaftRules::IsUmbrellaOpen(EUmbrellaAction::FreeFall));
	TestEqual(TEXT("folding closes the gap in the close time"), LightShaftRules::StepOpenness(1.0f, false, LightShaftRules::CloseSeconds), 0.0f);
	TestEqual(TEXT("opening takes the open time"), LightShaftRules::StepOpenness(0.0f, true, LightShaftRules::OpenSeconds), 1.0f);
	TestTrue(TEXT("half way is half open"), FMath::IsNearlyEqual(LightShaftRules::StepOpenness(1.0f, false, LightShaftRules::CloseSeconds * 0.5f), 0.5f, 0.001f));
	TestEqual(TEXT("no umbra when folded"), LightShaftRules::UmbraWidthAt(0.0f), 0.0f);
	TestEqual(TEXT("full umbra when open"), LightShaftRules::UmbraWidthAt(1.0f), LightShaftRules::UmbraWidth);
	TestEqual(TEXT("light passes when folded"), LightShaftRules::LightBelowAt(0.0f), 1.0f);
	TestEqual(TEXT("no light under the open canopy"), LightShaftRules::LightBelowAt(1.0f), 0.0f);
	const FVector Ella(320.0, 0.0, 500.0);
	TestEqual(TEXT("shaft is on Ella's X"), LightShaftRules::ShaftAboveCentre(Ella).X, Ella.X);
	TestEqual(TEXT("umbra is on Ella's X"), LightShaftRules::UmbraCentre(Ella).X, Ella.X);
	TestTrue(TEXT("umbra hangs below the canopy"), LightShaftRules::UmbraCentre(Ella).Z < Ella.Z + LightShaftRules::CanopyHeight);
	TestTrue(TEXT("shaft comes from above"), LightShaftRules::ShaftAboveCentre(Ella).Z > Ella.Z);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVfxArtWeaponWorld, "UmbrellaElla.Feedback.World.VfxWeaponWiring", VfxArtTestFlags)

bool FVfxArtWeaponWorld::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Harness;
	UWorld* World = Harness.GetWorld();
	UUmbrellaVfxDirectorSubsystem* Director = World ? World->GetSubsystem<UUmbrellaVfxDirectorSubsystem>() : nullptr;
	UUmbrellaVfxSubsystem* Shared = World ? World->GetSubsystem<UUmbrellaVfxSubsystem>() : nullptr;
	if (!TestNotNull(TEXT("effect director"), Director) || !TestNotNull(TEXT("shared effects"), Shared))
	{
		return false;
	}
	// Small Blasts: release once at the muzzle, a head that travels with the shot, a fade when it runs out.
	const FVector Muzzle(100.0, 0.0, 300.0);
	AUmbrellaProjectile* Shot = VfxArtTestFire(World, Muzzle);
	if (!TestNotNull(TEXT("shot"), Shot))
	{
		return false;
	}
	TestEqual(TEXT("release once"), Director->GetPlayCount(TEXT("SmallBlastRelease")), 1);
	TestEqual(TEXT("release at the muzzle X"), static_cast<float>(Director->GetLastLocation(TEXT("SmallBlastRelease")).X), static_cast<float>(Muzzle.X));
	TestEqual(TEXT("release at the muzzle Z"), static_cast<float>(Director->GetLastLocation(TEXT("SmallBlastRelease")).Z), static_cast<float>(Muzzle.Z));
	TestEqual(TEXT("one travelling head"), Director->GetLiveCount(TEXT("SmallBlastTravel")), 1);
	TestEqual(TEXT("the shared subsystem does not double the player shot"), Shared->GetEffectCount(), 0);
	if (AActor* Head = Director->GetLiveActor(TEXT("SmallBlastTravel")))
	{
		const UPrimitiveComponent* Visual = Cast<UPrimitiveComponent>(Head->GetRootComponent());
		TestTrue(TEXT("effect has no collision"), Visual && Visual->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
		TestEqual(TEXT("effect is on the effect layer"), static_cast<float>(Head->GetActorLocation().Y), UmbrellaDrawOrder::VfxY);
		Shot->AdvanceShot(0.1f);
		Director->StepEffects(0.1f);
		TestEqual(TEXT("head stays on the shot"), static_cast<float>(Head->GetActorLocation().X), static_cast<float>(Shot->GetActorLocation().X));
	}
	const FVector Before = Shot->GetActorLocation();
	const FVector Velocity = Shot->GetSpec().Velocity;
	TestEqual(TEXT("effects never change the shot"), Velocity, FVector(600.0, 0.0, 0.0));
	Shot->AdvanceShot(1.0f);
	Director->StepEffects(VfxArtTestStep);
	TestEqual(TEXT("head stops with the shot"), Director->GetLiveCount(TEXT("SmallBlastTravel")), 0);
	TestEqual(TEXT("fade once when it runs out"), Director->GetPlayCount(TEXT("SmallBlastFade")), 1);
	TestEqual(TEXT("no impact without a contact"), Director->GetPlayCount(TEXT("SmallBlastImpact")), 0);
	TestTrue(TEXT("fade where the shot ended"), Director->GetLastLocation(TEXT("SmallBlastFade")).X >= Before.X);

	// Twin Stars: two shots, two release anchors, two heads.
	VfxArtTestSend(World, EUmbrellaEventType::UmbrellaConfigChanged, UmbrellaPlayerIds::Ella, SpellRules::SpellName(EUmbrellaSpell::TwinStars));
	TestEqual(TEXT("equip follows the bus"), Director->GetEquippedSpell(), EUmbrellaSpell::TwinStars);
	AUmbrellaProjectile* Upper = VfxArtTestFire(World, Muzzle + FVector(0.0, 0.0, 20.0));
	const FVector UpperRelease = Director->GetLastLocation(TEXT("TwinStarRelease"));
	AUmbrellaProjectile* Lower = VfxArtTestFire(World, Muzzle - FVector(0.0, 0.0, 20.0));
	const FVector LowerRelease = Director->GetLastLocation(TEXT("TwinStarRelease"));
	TestEqual(TEXT("two releases"), Director->GetPlayCount(TEXT("TwinStarRelease")), 2);
	TestTrue(TEXT("two distinct release anchors"), !FMath::IsNearlyEqual(UpperRelease.Z, LowerRelease.Z));
	TestEqual(TEXT("two travelling heads"), Director->GetLiveCount(TEXT("TwinStarHead")), 2);
	// A consumed contact: one impact, at the shot, and no fade for that shot afterwards.
	if (TestNotNull(TEXT("upper shot"), Upper) && TestNotNull(TEXT("lower shot"), Lower))
	{
		VfxArtTestSend(World, EUmbrellaEventType::ProjectileContact, UmbrellaPlayerIds::Ella, TEXT("Consumed"));
		TestEqual(TEXT("one impact"), Director->GetPlayCount(TEXT("TwinStarImpact")), 1);
		Upper->Destroy();
		Lower->Destroy();
		Director->StepEffects(VfxArtTestStep);
		TestEqual(TEXT("the consumed shot does not also fade"), Director->GetPlayCount(TEXT("TwinStarFade")), 1);
		TestEqual(TEXT("heads cleared"), Director->GetLiveCount(TEXT("TwinStarHead")), 0);
	}

	// Needle: channel while shooting, pulse per shot, pierce on a pass, protected-contact kept apart.
	AEllaCharacter* Ella = Harness.SpawnElla(FVector(0.0, 0.0, 400.0));
	VfxArtTestSend(World, EUmbrellaEventType::UmbrellaConfigChanged, UmbrellaPlayerIds::Ella, SpellRules::SpellName(EUmbrellaSpell::Needle));
	VfxArtTestSend(World, EUmbrellaEventType::UmbrellaConfigChanged, UmbrellaPlayerIds::Ella, UmbrellaActionRules::ActionName(EUmbrellaAction::ShootFall));
	Director->StepEffects(VfxArtTestStep);
	if (TestNotNull(TEXT("ella"), Ella))
	{
		TestEqual(TEXT("needle channel while shooting"), Director->GetLiveCount(TEXT("NeedleChannel")), 1);
	}
	AUmbrellaProjectile* Sliver = VfxArtTestFire(World, Muzzle);
	TestEqual(TEXT("needle pulse"), Director->GetPlayCount(TEXT("NeedlePulse")), 1);
	TestEqual(TEXT("needle sliver travels"), Director->GetLiveCount(TEXT("NeedleSliver")), 1);
	VfxArtTestSend(World, EUmbrellaEventType::ProjectileContact, UmbrellaPlayerIds::Ella, TEXT("Passed"));
	TestEqual(TEXT("valid penetration shows a pierce"), Director->GetPlayCount(TEXT("NeedlePierce")), 1);
	TestEqual(TEXT("a pass is not an impact"), Director->GetPlayCount(TEXT("NeedleImpact")), 0);
	TestEqual(TEXT("the sliver flies on"), Director->GetLiveCount(TEXT("NeedleSliver")), 1);
	VfxArtTestSend(World, EUmbrellaEventType::UmbrellaConfigChanged, UmbrellaPlayerIds::Ella, UmbrellaActionRules::ActionName(EUmbrellaAction::Rise));
	Director->StepEffects(VfxArtTestStep);
	TestEqual(TEXT("channel stops on release"), Director->GetLiveCount(TEXT("NeedleChannel")), 0);
	if (Sliver)
	{
		Sliver->Destroy();
	}
	// Equipping cancels: a pass with Small Blasts shows nothing.
	VfxArtTestSend(World, EUmbrellaEventType::UmbrellaConfigChanged, UmbrellaPlayerIds::Ella, SpellRules::SpellName(EUmbrellaSpell::SmallBlasts));
	Director->StepEffects(VfxArtTestStep);
	const int32 PierceBefore = Director->GetPlayCount(TEXT("NeedlePierce"));
	VfxArtTestSend(World, EUmbrellaEventType::ProjectileContact, UmbrellaPlayerIds::Ella, TEXT("Passed"));
	TestEqual(TEXT("small blasts do not pierce"), Director->GetPlayCount(TEXT("NeedlePierce")), PierceBefore);

	// Streamed Blast: startup, a sustain that covers the beam, contact at the beam, stop.
	AStreamBeamActor* Beam = World->SpawnActor<AStreamBeamActor>(AStreamBeamActor::StaticClass(), FTransform(Muzzle));
	if (TestNotNull(TEXT("beam"), Beam))
	{
		Beam->SetBeam(Muzzle, 200.0f, 14.0f);
		Director->StepEffects(VfxArtTestStep);
		TestEqual(TEXT("stream startup once"), Director->GetPlayCount(TEXT("StreamStartup")), 1);
		TestEqual(TEXT("stream sustain held"), Director->GetLiveCount(TEXT("StreamSustain")), 1);
		Director->StepEffects(VfxArtTestStep);
		TestEqual(TEXT("startup is not repeated"), Director->GetPlayCount(TEXT("StreamStartup")), 1);
		if (const AActor* Sustain = Director->GetLiveActor(TEXT("StreamSustain")))
		{
			TestEqual(TEXT("sustain is centred on the beam"), static_cast<float>(Sustain->GetActorLocation().X),
				static_cast<float>(Muzzle.X) + Beam->GetEffectiveLength() * 0.5f);
		}
		VfxArtTestSend(World, EUmbrellaEventType::ProjectileContact, UmbrellaPlayerIds::Ella, TEXT("Consumed"));
		TestEqual(TEXT("stream contact"), Director->GetPlayCount(TEXT("StreamContact")), 1);
		TestEqual(TEXT("contact at the beam end"), static_cast<float>(Director->GetLastLocation(TEXT("StreamContact")).X),
			static_cast<float>(Muzzle.X) + Beam->GetEffectiveLength());
		Beam->Destroy();
		Director->StepEffects(VfxArtTestStep);
		TestEqual(TEXT("stream stop once"), Director->GetPlayCount(TEXT("StreamStop")), 1);
		TestEqual(TEXT("sustain cleared"), Director->GetLiveCount(TEXT("StreamSustain")), 0);
	}
	// Retry clears everything.
	VfxArtTestFire(World, Muzzle);
	VfxArtTestSend(World, EUmbrellaEventType::CheckpointRetried, TEXT("KeeperOfTime"), NAME_None);
	TestEqual(TEXT("retry clears every effect"), Director->GetLiveTotal(), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVfxArtKeeperWorld, "UmbrellaElla.Feedback.World.VfxKeeperWiring", VfxArtTestFlags)

bool FVfxArtKeeperWorld::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Harness;
	UWorld* World = Harness.GetWorld();
	UUmbrellaVfxDirectorSubsystem* Director = World ? World->GetSubsystem<UUmbrellaVfxDirectorSubsystem>() : nullptr;
	UUmbrellaVfxSubsystem* Shared = World ? World->GetSubsystem<UUmbrellaVfxSubsystem>() : nullptr;
	UEncounterDirectorSubsystem* Encounter = World ? World->GetSubsystem<UEncounterDirectorSubsystem>() : nullptr;
	if (!TestNotNull(TEXT("effect director"), Director) || !TestNotNull(TEXT("shared effects"), Shared) || !TestNotNull(TEXT("encounter"), Encounter))
	{
		return false;
	}
	const FName KeeperSource(TEXT("KeeperOfTime"));
	Encounter->SetManualStepping(true);
	Encounter->BeginKeeperFight();
	const AKeeperOfTime* Keeper = Encounter->GetKeeper();
	if (!TestNotNull(TEXT("keeper"), Keeper))
	{
		return false;
	}
	Director->StepEffects(VfxArtTestStep);
	// Telegraph: the move's own warning, once, held, and not doubled by the shared subsystem.
	VfxArtTestSend(World, EUmbrellaEventType::BossAttackTelegraphed, KeeperSource, UmbrellaSourceIds::TalonRake());
	VfxArtTestSend(World, EUmbrellaEventType::BossAttackTelegraphed, KeeperSource, UmbrellaSourceIds::TalonRake());
	TestEqual(TEXT("one talon warning"), Director->GetLiveCount(TEXT("TalonWarning")), 1);
	TestEqual(TEXT("played once"), Director->GetPlayCount(TEXT("TalonWarning")), 1);
	TestEqual(TEXT("no doubled telegraph"), Shared->GetEffectCount(), 0);
	if (const AActor* Warning = Director->GetLiveActor(TEXT("TalonWarning")))
	{
		TestEqual(TEXT("warning is on the hazard layer"), static_cast<float>(Warning->GetActorLocation().Y), UmbrellaDrawOrder::HazardY);
	}
	VfxArtTestSend(World, EUmbrellaEventType::BossAttackTelegraphed, KeeperSource, UmbrellaSourceIds::MechRearTwoStage());
	TestEqual(TEXT("rear cast has its own warning"), Director->GetLiveCount(TEXT("MechRearWarning")), 1);
	// The model is idle, so the next step ends warnings that have no move behind them: effects follow the model.
	const FVector KeeperAt = Keeper->GetActorLocation();
	// A protected contact and a damaging hit look different, one effect each.
	VfxArtTestSend(World, EUmbrellaEventType::ProjectileContact, UmbrellaPlayerIds::Ella, TEXT("Consumed"), Keeper->GetFName());
	TestEqual(TEXT("protected contact"), Director->GetPlayCount(TEXT("ProtectedContact")), 1);
	TestEqual(TEXT("protected contact is not a hit"), Director->GetPlayCount(TEXT("KeeperPartHit")), 0);
	VfxArtTestSend(World, EUmbrellaEventType::BossTargetHit, KeeperSource, TEXT("Wings"));
	VfxArtTestSend(World, EUmbrellaEventType::ProjectileContact, UmbrellaPlayerIds::Ella, TEXT("Consumed"), Keeper->GetFName());
	TestEqual(TEXT("component hit"), Director->GetPlayCount(TEXT("KeeperPartHit")), 1);
	TestEqual(TEXT("still one protected contact"), Director->GetPlayCount(TEXT("ProtectedContact")), 1);
	TestEqual(TEXT("no weapon impact on top"), Director->GetPlayCount(TEXT("SmallBlastImpact")), 0);
	VfxArtTestSend(World, EUmbrellaEventType::BossPartDestroyed, KeeperSource, TEXT("Wings"));
	TestEqual(TEXT("component break"), Director->GetPlayCount(TEXT("KeeperPartBroken")), 1);
	// Clock double beat: two beats, one effect each, however many shots a beat has.
	FUmbrellaShotSpec Red;
	Red.Kind = EUmbrellaShotKind::EnemyRed;
	Red.Origin = KeeperAt;
	Red.Velocity = FVector(-300.0, 0.0, 0.0);
	Red.Radius = 8.0f;
	Red.LifetimeSeconds = 1.0f;
	Red.SourceId = UmbrellaSourceIds::ClockDoubleBeat();
	AUmbrellaProjectile::Fire(World, Red);
	AUmbrellaProjectile::Fire(World, Red);
	TestEqual(TEXT("first beat"), Director->GetPlayCount(TEXT("ClockBeat")), 1);
	Director->StepEffects(1.0f);
	AUmbrellaProjectile::Fire(World, Red);
	AUmbrellaProjectile::Fire(World, Red);
	TestEqual(TEXT("second beat"), Director->GetPlayCount(TEXT("ClockBeat")), 2);
	// Effects never move the Keeper.
	TestEqual(TEXT("keeper untouched"), Keeper->GetActorLocation(), KeeperAt);
	// Retry: everything stops and nothing is left behind.
	VfxArtTestSend(World, EUmbrellaEventType::BossAttackTelegraphed, KeeperSource, UmbrellaSourceIds::GustBand());
	VfxArtTestSend(World, EUmbrellaEventType::CheckpointRetried, KeeperSource, NAME_None);
	TestEqual(TEXT("retry clears every effect"), Director->GetLiveTotal(), 0);
	Encounter->ResetForRestart();
	Director->StepEffects(VfxArtTestStep);
	TestEqual(TEXT("nothing restarts after the reset"), Director->GetLiveTotal(), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVfxArtIlluminationWorld, "UmbrellaElla.Feedback.World.VfxIlluminationOnOff", VfxArtTestFlags)

bool FVfxArtIlluminationWorld::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Harness;
	UWorld* World = Harness.GetWorld();
	UUmbrellaVfxDirectorSubsystem* Director = World ? World->GetSubsystem<UUmbrellaVfxDirectorSubsystem>() : nullptr;
	if (!TestNotNull(TEXT("effect director"), Director))
	{
		return false;
	}
	const FVector At(200.0, 0.0, 300.0);
	const FVfxArtRow* Row = VfxCatalog::Find(TEXT("SmallBlastImpact"));
	// On: the effect carries a local light of its own colour at its own place.
	TestTrue(TEXT("illumination defaults on"), Director->IsIlluminationEnabled());
	Director->Play(TEXT("SmallBlastImpact"), At, nullptr);
	AActor* Lit = Director->GetLiveActor(TEXT("SmallBlastImpact"));
	if (!TestNotNull(TEXT("lit effect"), Lit) || !TestNotNull(TEXT("row"), Row))
	{
		return false;
	}
	UPointLightComponent* Light = Lit->FindComponentByClass<UPointLightComponent>();
	if (TestNotNull(TEXT("effect lights nearby surfaces"), Light))
	{
		TestEqual(TEXT("light is at the effect X"), static_cast<float>(Light->GetComponentLocation().X), static_cast<float>(At.X));
		TestEqual(TEXT("light is at the effect Z"), static_cast<float>(Light->GetComponentLocation().Z), static_cast<float>(At.Z));
		TestTrue(TEXT("light is local"), Light->AttenuationRadius <= VfxLightPolicy::MaxRadius);
		TestTrue(TEXT("light has the effect colour"), Light->GetLightColor().Equals(VfxCatalog::LightColour(*Row), 0.01f));
		TestFalse(TEXT("light casts no shadow"), Light->CastShadows);
		const float Full = Light->Intensity;
		Director->StepEffects(VfxCatalog::Duration(*Row) * 0.5f);
		TestTrue(TEXT("light fades with the effect"), Light->Intensity < Full);
		// Off: the same live effect stops lighting; the effect itself stays.
		Director->SetIlluminationEnabled(false);
		TestFalse(TEXT("switched off: light hidden"), Light->IsVisible());
		TestEqual(TEXT("the effect stays"), Director->GetLiveCount(TEXT("SmallBlastImpact")), 1);
		Director->SetIlluminationEnabled(true);
		TestTrue(TEXT("switched on again"), Light->IsVisible());
	}
	const UStaticMeshComponent* Visual = Cast<UStaticMeshComponent>(Lit->GetRootComponent());
	const UStaticMeshComponent* Spill = nullptr;
	for (const UActorComponent* Component : Lit->GetComponents())
	{
		if (Component && Component->GetFName() == FName(TEXT("VfxSpill")))
		{
			Spill = Cast<UStaticMeshComponent>(Component);
		}
	}
	if (VfxSheetVisual::HasArt(Visual))
	{
		// With the sheets imported the overlay exists too, on its own layer, at the effect.
		if (TestNotNull(TEXT("light overlay"), Spill))
		{
			TestEqual(TEXT("overlay layer"), static_cast<float>(Spill->GetComponentLocation().Y), VfxLightPolicy::SpillLayerY());
			TestEqual(TEXT("overlay at the effect"), static_cast<float>(Spill->GetComponentLocation().X), static_cast<float>(At.X));
			TestTrue(TEXT("overlay has no collision"), Spill->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
		}
	}
	// The effect ends: its light leaves with it and the scene is as before.
	Director->StepEffects(VfxCatalog::Duration(*Row));
	TestEqual(TEXT("effect ended"), Director->GetLiveTotal(), 0);
	TestFalse(TEXT("light left with the effect"), IsValid(Lit) && !Lit->IsActorBeingDestroyed());
	// Off before spawning: no light at all.
	Director->SetIlluminationEnabled(false);
	Director->StepEffects(1.0f);
	Director->Play(TEXT("SmallBlastImpact"), At, nullptr);
	if (const AActor* Dark = Director->GetLiveActor(TEXT("SmallBlastImpact")))
	{
		TestNull(TEXT("off: no light"), Dark->FindComponentByClass<UPointLightComponent>());
	}
	Director->SetIlluminationEnabled(true);
	// An unlit effect never lights.
	Director->Play(TEXT("ProtectedContact"), At, nullptr);
	if (const AActor* Plain = Director->GetLiveActor(TEXT("ProtectedContact")))
	{
		TestNull(TEXT("unlit effect has no light"), Plain->FindComponentByClass<UPointLightComponent>());
	}
	// Flash limit: a second flash inside the gap is shown but throws no light.
	Director->StopAll();
	Director->StepEffects(1.0f);
	Director->Play(TEXT("TwinStarImpact"), At, nullptr);
	Director->Play(TEXT("NeedleImpact"), At, nullptr);
	TestEqual(TEXT("second flash still shown"), Director->GetLiveCount(TEXT("NeedleImpact")), 1);
	TestEqual(TEXT("second flash dimmed"), Director->GetFlashDimmedCount(), 1);
	if (const AActor* Second = Director->GetLiveActor(TEXT("NeedleImpact")))
	{
		TestNull(TEXT("dimmed flash has no light"), Second->FindComponentByClass<UPointLightComponent>());
	}
	// Concurrency cap: one-shots beyond the cap are dropped, a held warning never is.
	Director->StopAll();
	for (int32 Index = 0; Index < UmbrellaVfxDirectorConst::MaxLive + 5; ++Index)
	{
		Director->Play(TEXT("SmallBlastFade"), At, nullptr);
	}
	TestEqual(TEXT("live effects are capped"), Director->GetLiveTotal(), UmbrellaVfxDirectorConst::MaxLive);
	TestEqual(TEXT("extra one-shots are dropped"), Director->GetDroppedCount(), 5);
	TestTrue(TEXT("a warning is never dropped"), Director->Play(TEXT("TalonWarning"), At, nullptr) != 0);
	// A held effect cannot stay up forever.
	Director->StepEffects(UmbrellaVfxDirectorConst::MaxHeldSeconds);
	TestEqual(TEXT("held effects are bounded"), Director->GetLiveTotal(), 0);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FVfxArtShaftWorld, "UmbrellaElla.Feedback.World.VfxLightShaftAndUmbra", VfxArtTestFlags)

bool FVfxArtShaftWorld::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Harness;
	UWorld* World = Harness.GetWorld();
	UUmbrellaVfxDirectorSubsystem* Director = World ? World->GetSubsystem<UUmbrellaVfxDirectorSubsystem>() : nullptr;
	AEllaCharacter* Ella = Harness.SpawnElla(FVector(250.0, 0.0, 600.0));
	if (!TestNotNull(TEXT("effect director"), Director) || !TestNotNull(TEXT("ella"), Ella))
	{
		return false;
	}
	const FVector EllaAt = Ella->GetActorLocation();
	Director->StepEffects(VfxArtTestStep);
	const AActor* Above = Director->GetShaftPart(0);
	const AActor* Below = Director->GetShaftPart(1);
	const AActor* Umbra = Director->GetShaftPart(2);
	if (!TestNotNull(TEXT("shaft above"), Above) || !TestNotNull(TEXT("shaft below"), Below) || !TestNotNull(TEXT("umbra"), Umbra))
	{
		return false;
	}
	// Open umbrella: light from above stops at the canopy, the umbra hangs below Ella and follows her.
	TestEqual(TEXT("open: full umbra"), Director->GetUmbraOpenness(), 1.0f);
	TestEqual(TEXT("shaft falls through Ella's X"), static_cast<float>(Above->GetActorLocation().X), static_cast<float>(EllaAt.X));
	TestTrue(TEXT("shaft comes from above"), Above->GetActorLocation().Z > EllaAt.Z);
	TestFalse(TEXT("shaft above is shown"), Above->IsHidden());
	TestTrue(TEXT("no light under the open canopy"), Below->IsHidden());
	TestFalse(TEXT("umbra is shown"), Umbra->IsHidden());
	TestTrue(TEXT("umbra is below Ella"), Umbra->GetActorLocation().Z < EllaAt.Z);
	TestTrue(TEXT("shaft is behind the play layer"), Above->GetActorLocation().Y < UmbrellaDrawOrder::EllaY);
	const AActor* Parts[] = { Above, Below, Umbra };
	for (const AActor* Part : Parts)
	{
		const UPrimitiveComponent* Visual = Cast<UPrimitiveComponent>(Part->GetRootComponent());
		TestTrue(TEXT("part has no collision"), Visual && Visual->GetCollisionEnabled() == ECollisionEnabled::NoCollision);
	}
	Ella->SetActorLocation(EllaAt + FVector(80.0, 0.0, -40.0));
	Director->StepEffects(VfxArtTestStep);
	TestEqual(TEXT("umbra follows Ella"), static_cast<float>(Umbra->GetActorLocation().X), static_cast<float>(EllaAt.X + 80.0));
	TestEqual(TEXT("shaft follows Ella"), static_cast<float>(Above->GetActorLocation().X), static_cast<float>(EllaAt.X + 80.0));
	// Folding to descend closes the gap: the light passes through her position.
	VfxArtTestSend(World, EUmbrellaEventType::UmbrellaConfigChanged, UmbrellaPlayerIds::Ella, UmbrellaActionRules::ActionName(EUmbrellaAction::AbsorbFall));
	Director->StepEffects(LightShaftRules::CloseSeconds * 0.5f);
	TestTrue(TEXT("gap is closing"), Director->GetUmbraOpenness() > 0.0f && Director->GetUmbraOpenness() < 1.0f);
	TestFalse(TEXT("light starts to pass"), Below->IsHidden());
	Director->StepEffects(LightShaftRules::CloseSeconds);
	TestEqual(TEXT("gap closed"), Director->GetUmbraOpenness(), 0.0f);
	TestTrue(TEXT("umbra gone"), Umbra->IsHidden());
	TestFalse(TEXT("light passes below Ella"), Below->IsHidden());
	// Opening again brings the umbra back.
	VfxArtTestSend(World, EUmbrellaEventType::UmbrellaConfigChanged, UmbrellaPlayerIds::Ella, UmbrellaActionRules::ActionName(EUmbrellaAction::Rise));
	Director->StepEffects(LightShaftRules::OpenSeconds);
	TestEqual(TEXT("open again"), Director->GetUmbraOpenness(), 1.0f);
	TestFalse(TEXT("umbra back"), Umbra->IsHidden());
	// Looks only: Ella is exactly where the test put her.
	TestEqual(TEXT("ella untouched"), Ella->GetActorLocation(), EllaAt + FVector(80.0, 0.0, -40.0));
	return true;
}

#endif
