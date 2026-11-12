#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Attack/AttackEmitterComponent.h"
#include "Attack/AttackTuning.h"
#include "Attack/SpellRules.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaTuning.h"
#include "EngineUtils.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Motor/EllaMotorComponent.h"
#include "Projectile/UmbrellaProjectile.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "Umbrella/UmbrellaStateComponent.h"

namespace
{
	const FAttackTuning& Attack()
	{
		return GetDefault<UUmbrellaTuning>()->Attack;
	}

	const float SpellDeltas[] = {1.0f / 30.0f, 1.0f / 60.0f, 1.0f / 120.0f};
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveSpellBaselineTest, "UmbrellaElla.Move.SpellBaseline", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveSpellBaselineTest::RunTest(const FString& Parameters)
{
	// Exactly four weapon families.
	static_assert(SpellRules::SpellCount == 4, "exactly four weapon families");
	TestEqual(TEXT("four spells"), SpellRules::SpellCount, 4);

	const FAttackTuning& A = Attack();
	TestEqual(TEXT("small rate"), A.SmallShotsPerSecond, 5.0f);
	TestEqual(TEXT("small damage"), A.SmallDamage, 10.0f);
	TestEqual(TEXT("small speed"), A.SmallSpeed, 700.0f);
	TestEqual(TEXT("small range"), A.SmallRange, 1500.0f);
	TestEqual(TEXT("stream ticks"), A.StreamTicksPerSecond, 10.0f);
	TestEqual(TEXT("stream damage"), A.StreamTickDamage, 4.0f);
	TestEqual(TEXT("stream growth"), A.StreamGrowthSpeed, 1200.0f);
	TestEqual(TEXT("stream range"), A.StreamMaxRange, 1400.0f);
	TestEqual(TEXT("stream width"), A.StreamWidth, 14.0f);
	TestEqual(TEXT("twin separation"), A.TwinSeparation, 44.0f);
	TestEqual(TEXT("twin rate"), A.TwinVolleysPerSecond, 5.0f);
	TestEqual(TEXT("twin damage"), A.TwinDamage, 7.0f);
	TestEqual(TEXT("twin speed"), A.TwinSpeed, 700.0f);
	TestEqual(TEXT("twin range"), A.TwinRange, 1500.0f);
	TestEqual(TEXT("needle rate"), A.NeedleShotsPerSecond, 3.0f);
	TestEqual(TEXT("needle damage"), A.NeedleDamage, 14.0f);
	TestEqual(TEXT("needle speed"), A.NeedleSpeed, 1000.0f);
	TestEqual(TEXT("needle range"), A.NeedleRange, 1700.0f);
	TestEqual(TEXT("needle size"), A.NeedleSizeMultiplier, 0.7f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveSpellAvailabilityTest, "UmbrellaElla.Move.SpellAvailability", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveSpellAvailabilityTest::RunTest(const FString& Parameters)
{
	// Start Game: only Small Blasts, at any level.
	for (int32 Level = 0; Level <= 62; Level += 31)
	{
		TestTrue(TEXT("start game small"), SpellRules::IsAvailable(EUmbrellaSpell::SmallBlasts, EUmbrellaPlayMode::StartGame, Level, Attack()));
		TestFalse(TEXT("start game stream"), SpellRules::IsAvailable(EUmbrellaSpell::StreamedBlast, EUmbrellaPlayMode::StartGame, Level, Attack()));
		TestFalse(TEXT("start game twin"), SpellRules::IsAvailable(EUmbrellaSpell::TwinStars, EUmbrellaPlayMode::StartGame, Level, Attack()));
		TestFalse(TEXT("start game needle"), SpellRules::IsAvailable(EUmbrellaSpell::Needle, EUmbrellaPlayMode::StartGame, Level, Attack()));
	}
	// Director's Cut unlocks at 1 / 10 / 20 / 30.
	const EUmbrellaPlayMode Mode = EUmbrellaPlayMode::DirectorsCut;
	TestTrue(TEXT("L1 small"), SpellRules::IsAvailable(EUmbrellaSpell::SmallBlasts, Mode, 1, Attack()));
	TestFalse(TEXT("L9 stream locked"), SpellRules::IsAvailable(EUmbrellaSpell::StreamedBlast, Mode, 9, Attack()));
	TestTrue(TEXT("L10 stream"), SpellRules::IsAvailable(EUmbrellaSpell::StreamedBlast, Mode, 10, Attack()));
	TestFalse(TEXT("L19 twin locked"), SpellRules::IsAvailable(EUmbrellaSpell::TwinStars, Mode, 19, Attack()));
	TestTrue(TEXT("L20 twin"), SpellRules::IsAvailable(EUmbrellaSpell::TwinStars, Mode, 20, Attack()));
	TestFalse(TEXT("L29 needle locked"), SpellRules::IsAvailable(EUmbrellaSpell::Needle, Mode, 29, Attack()));
	TestTrue(TEXT("L30 needle"), SpellRules::IsAvailable(EUmbrellaSpell::Needle, Mode, 30, Attack()));
	TestFalse(TEXT("no fifth spell"), SpellRules::IsAvailable(EUmbrellaSpell::Count, Mode, 62, Attack()));

	// Cycling skips locked spells and wraps.
	TestEqual(TEXT("L1 next stays"), SpellRules::Cycle(EUmbrellaSpell::SmallBlasts, 1, Mode, 1, Attack()), EUmbrellaSpell::SmallBlasts);
	TestEqual(TEXT("L10 next"), SpellRules::Cycle(EUmbrellaSpell::SmallBlasts, 1, Mode, 10, Attack()), EUmbrellaSpell::StreamedBlast);
	TestEqual(TEXT("L10 wrap"), SpellRules::Cycle(EUmbrellaSpell::StreamedBlast, 1, Mode, 10, Attack()), EUmbrellaSpell::SmallBlasts);
	TestEqual(TEXT("L20 skip to twin"), SpellRules::Cycle(EUmbrellaSpell::StreamedBlast, 1, Mode, 20, Attack()), EUmbrellaSpell::TwinStars);
	TestEqual(TEXT("L30 previous wraps to needle"), SpellRules::Cycle(EUmbrellaSpell::SmallBlasts, -1, Mode, 30, Attack()), EUmbrellaSpell::Needle);
	TestEqual(TEXT("start game cycle stays"), SpellRules::Cycle(EUmbrellaSpell::SmallBlasts, 1, EUmbrellaPlayMode::StartGame, 62, Attack()), EUmbrellaSpell::SmallBlasts);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveSpellVolleysTest, "UmbrellaElla.Move.SpellVolleys", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveSpellVolleysTest::RunTest(const FString& Parameters)
{
	const FVector Muzzle(100.0, 25.0, 10.0);
	for (int32 Index = 0; Index < SpellRules::SpellCount; ++Index)
	{
		const EUmbrellaSpell Spell = static_cast<EUmbrellaSpell>(Index);
		for (const FUmbrellaShotSpec& Shot : SpellRules::BuildVolley(Spell, Muzzle, Attack()))
		{
			TestTrue(TEXT("every shot goes right only"), Shot.Velocity.X > 0.0 && Shot.Velocity.Y == 0.0 && Shot.Velocity.Z == 0.0);
			TestEqual(TEXT("player kind"), Shot.Kind, EUmbrellaShotKind::PlayerBlast);
		}
	}
	const TArray<FUmbrellaShotSpec> Twin = SpellRules::BuildVolley(EUmbrellaSpell::TwinStars, Muzzle, Attack());
	if (TestEqual(TEXT("twin fires two"), Twin.Num(), 2))
	{
		TestEqual(TEXT("44 apart"), static_cast<float>(FMath::Abs(Twin[0].Origin.Z - Twin[1].Origin.Z)), 44.0f, 0.001f);
		TestEqual(TEXT("same X"), Twin[0].Origin.X, Twin[1].Origin.X);
		TestEqual(TEXT("damage 7 each"), Twin[0].Damage, 7.0f);
		TestEqual(TEXT("speed 700"), static_cast<float>(Twin[1].Velocity.X), 700.0f);
	}
	const TArray<FUmbrellaShotSpec> Needle = SpellRules::BuildVolley(EUmbrellaSpell::Needle, Muzzle, Attack());
	if (TestEqual(TEXT("needle fires one"), Needle.Num(), 1))
	{
		TestEqual(TEXT("needle damage 14"), Needle[0].Damage, 14.0f);
		TestEqual(TEXT("needle speed 1000"), static_cast<float>(Needle[0].Velocity.X), 1000.0f);
		TestEqual(TEXT("needle range 1700"), static_cast<float>(Needle[0].Velocity.X * Needle[0].LifetimeSeconds), 1700.0f, 0.01f);
		const TArray<FUmbrellaShotSpec> Small = SpellRules::BuildVolley(EUmbrellaSpell::SmallBlasts, Muzzle, Attack());
		TestEqual(TEXT("needle is 0.7 of a small blast"), Needle[0].Radius, Small[0].Radius * 0.7f, 0.001f);
	}
	const TArray<FUmbrellaShotSpec> Stream = SpellRules::BuildVolley(EUmbrellaSpell::StreamedBlast, Muzzle, Attack());
	if (TestEqual(TEXT("stream fires one pulse per tick"), Stream.Num(), 1))
	{
		TestEqual(TEXT("tick damage 4"), Stream[0].Damage, 4.0f);
		TestEqual(TEXT("pulse width 14"), Stream[0].Radius * 2.0f, 14.0f, 0.001f);
		TestEqual(TEXT("pulse range 1400"), static_cast<float>(Stream[0].Velocity.X * Stream[0].LifetimeSeconds), 1400.0f, 0.01f);
	}
	TestEqual(TEXT("beam starts at zero"), SpellRules::StreamLength(0.0f, Attack()), 0.0f);
	TestEqual(TEXT("beam grows 1200/s"), SpellRules::StreamLength(0.5f, Attack()), 600.0f, 0.001f);
	TestEqual(TEXT("beam caps at 1400"), SpellRules::StreamLength(5.0f, Attack()), 1400.0f);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldSpellTest, "UmbrellaElla.Move.World.SpellSelectionAndFire", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldSpellTest::RunTest(const FString& Parameters)
{
	for (const float Delta : SpellDeltas)
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		UAttackEmitterComponent* Emitter = Ella->GetAttack();
		UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();

		// Start Game: key 2 does nothing.
		Adapter->ApplyPress(EUmbrellaInputAction::Spell2);
		Adapter->ApplyRelease(EUmbrellaInputAction::Spell2);
		TestEqual(TEXT("Start Game keeps Small Blasts"), Emitter->GetEquippedSpell(), EUmbrellaSpell::SmallBlasts);

		// Director's Cut level 10: Stream unlocks but is not auto-equipped.
		Emitter->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
		Emitter->SetDirectorLevel(10);
		TestEqual(TEXT("unlock does not equip"), Emitter->GetEquippedSpell(), EUmbrellaSpell::SmallBlasts);
		Adapter->ApplyPress(EUmbrellaInputAction::Spell3);
		Adapter->ApplyRelease(EUmbrellaInputAction::Spell3);
		TestEqual(TEXT("locked twin cannot equip"), Emitter->GetEquippedSpell(), EUmbrellaSpell::SmallBlasts);
		Adapter->ApplyPress(EUmbrellaInputAction::SpellNext);
		TestEqual(TEXT("cycle to stream"), Emitter->GetEquippedSpell(), EUmbrellaSpell::StreamedBlast);

		// Stream: 10 pulses/s at damage 4 while dropping, beam grows.
		Adapter->ApplyPress(EUmbrellaInputAction::Shoot);
		Test.TickSeconds(0.5f, Delta);
		TestEqual(TEXT("beam length after 0.5 s"), Emitter->GetStreamLength(), 600.0f, 40.0f);
		Test.TickSeconds(0.5f, Delta);
		const int32 Pulses = Emitter->GetShotsFired();
		TestTrue(FString::Printf(TEXT("about 10 pulses in 1 s, got %d"), Pulses), Pulses >= 10 && Pulses <= 11);
		TestEqual(TEXT("pulse damage"), Emitter->GetLastShot().Damage, 4.0f);
		Adapter->ApplyRelease(EUmbrellaInputAction::Shoot);
		TestEqual(TEXT("beam ends on release"), Emitter->GetStreamLength(), 0.0f);

		// Twin Stars at level 20 fires two shots per volley.
		Emitter->SetDirectorLevel(20);
		Adapter->ApplyPress(EUmbrellaInputAction::Spell3);
		Adapter->ApplyRelease(EUmbrellaInputAction::Spell3);
		TestEqual(TEXT("twin equipped"), Emitter->GetEquippedSpell(), EUmbrellaSpell::TwinStars);
		const int32 Before = Emitter->GetShotsFired();
		Adapter->ApplyPress(EUmbrellaInputAction::Shoot);
		Test.TickSeconds(1.0f, Delta);
		const int32 TwinShots = Emitter->GetShotsFired() - Before;
		TestTrue(FString::Printf(TEXT("about 10 shots (5 volleys of 2) in 1 s, got %d"), TwinShots), TwinShots >= 10 && TwinShots <= 12 && TwinShots % 2 == 0);
		Adapter->ApplyRelease(EUmbrellaInputAction::Shoot);

		// Going back to Start Game drops the equipped spell to Small Blasts.
		Emitter->SetPlayMode(EUmbrellaPlayMode::StartGame);
		TestEqual(TEXT("Start Game resets to Small Blasts"), Emitter->GetEquippedSpell(), EUmbrellaSpell::SmallBlasts);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldWheelTest, "UmbrellaElla.Move.World.SpellWheelHoldAndConfirm", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldWheelTest::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	UAttackEmitterComponent* Emitter = Ella->GetAttack();
	UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();
	Emitter->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
	Emitter->SetDirectorLevel(30);

	// A flick equips at once and never opens the wheel.
	Adapter->ApplyPress(EUmbrellaInputAction::Spell4);
	TestEqual(TEXT("flick equips"), Emitter->GetEquippedSpell(), EUmbrellaSpell::Needle);
	Test.TickSeconds(0.1f, 1.0f / 60.0f);
	Adapter->ApplyRelease(EUmbrellaInputAction::Spell4);
	TestFalse(TEXT("no wheel on a flick"), Emitter->IsWheelOpen());

	// Hold past 0.3 s: the wheel opens, gameplay pauses, a direction previews, release confirms.
	Adapter->ApplyPress(EUmbrellaInputAction::Spell2);
	Test.TickSeconds(0.2f, 1.0f / 60.0f);
	TestFalse(TEXT("not yet"), Emitter->IsWheelOpen());
	Test.TickSeconds(0.2f, 1.0f / 60.0f);
	TestTrue(TEXT("wheel open after 0.3 s"), Emitter->IsWheelOpen());
	TestTrue(TEXT("wheel pauses gameplay"), Ella->GetUmbrellaState()->IsLocked());
	Adapter->ApplyPress(EUmbrellaInputAction::Spell3);
	TestEqual(TEXT("preview"), Emitter->GetWheelPreview(), EUmbrellaSpell::TwinStars);
	Adapter->ApplyRelease(EUmbrellaInputAction::Spell3);
	TestFalse(TEXT("wheel closed"), Emitter->IsWheelOpen());
	TestFalse(TEXT("gameplay resumes"), Ella->GetUmbrellaState()->IsLocked());
	TestEqual(TEXT("release confirms the preview"), Emitter->GetEquippedSpell(), EUmbrellaSpell::TwinStars);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldNoAmmoTest, "UmbrellaElla.Move.World.FireIsUnlimited", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldNoAmmoTest::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
	// 60 s of shoot-fall at the Small Blast rate: the rate never drops, nothing runs out.
	int32 FirstHalf = 0;
	for (int32 Chunk = 0; Chunk < 2; ++Chunk)
	{
		const int32 Start = Ella->GetAttack()->GetShotsFired();
		Test.TickSeconds(30.0f, 1.0f / 30.0f);
		const int32 Shots = Ella->GetAttack()->GetShotsFired() - Start;
		TestTrue(FString::Printf(TEXT("30 s fires about 150, got %d"), Shots), Shots >= 149 && Shots <= 151);
		if (Chunk == 0)
		{
			FirstHalf = Shots;
		}
		else
		{
			TestTrue(TEXT("second half fires as many as the first"), FMath::Abs(Shots - FirstHalf) <= 1);
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveWorldModeControlsTest, "UmbrellaElla.Move.World.ControlsSameInBothModes", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveWorldModeControlsTest::RunTest(const FString& Parameters)
{
	// The tutorial redesign changes presentation, not controls: movement is identical in both modes.
	const EUmbrellaPlayMode Modes[] = {EUmbrellaPlayMode::StartGame, EUmbrellaPlayMode::DirectorsCut};
	float Heights[2] = {0.0f, 0.0f};
	for (int32 Index = 0; Index < 2; ++Index)
	{
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		Ella->GetAttack()->SetPlayMode(Modes[Index]);
		Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Hop);
		Test.TickSeconds(1.0f, 1.0f / 60.0f);
		Heights[Index] = static_cast<float>(Ella->GetActorLocation().Z) + static_cast<float>(Ella->GetActorLocation().X);
	}
	TestEqual(TEXT("same movement in both modes"), Heights[0], Heights[1], 0.001f);
	return true;
}

#endif
