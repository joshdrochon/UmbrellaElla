#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Attack/AttackEmitterComponent.h"
#include "Attack/SpellRules.h"
#include "Core/EllaCharacter.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Input/UmbrellaInputBindings.h"
#include "InputCoreTypes.h"
#include "Tests/Shared/UmbrellaTestWorld.h"

namespace
{
	bool MoveProofHasBinding(const TArray<FUmbrellaDefaultBinding>& Bindings, EUmbrellaInputAction Action, const FKey& Key, float Scale)
	{
		for (const FUmbrellaDefaultBinding& Binding : Bindings)
		{
			if (Binding.Action == Action && Binding.Key == Key && FMath::IsNearlyEqual(Binding.Scale, Scale))
			{
				return true;
			}
		}
		return false;
	}
}

// MOVE-07 arrow-key trim aliases; MOVE-07 / MOVE-19 right stick selects spells.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveProofArrowsAndStickTest, "UmbrellaElla.Move.ArrowTrimAndRightStickSpells", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveProofArrowsAndStickTest::RunTest(const FString& Parameters)
{
	const TArray<FUmbrellaDefaultBinding> Bindings = UmbrellaInputBindings::BuildDefaults();
	TestTrue(TEXT("Up arrow trims up"), MoveProofHasBinding(Bindings, EUmbrellaInputAction::Trim, EKeys::Up, 1.0f));
	TestTrue(TEXT("Down arrow trims down"), MoveProofHasBinding(Bindings, EUmbrellaInputAction::Trim, EKeys::Down, -1.0f));
	TestTrue(TEXT("stick up = Small"), MoveProofHasBinding(Bindings, EUmbrellaInputAction::Spell1, EKeys::Gamepad_RightStick_Up, 1.0f));
	TestTrue(TEXT("stick right = Stream"), MoveProofHasBinding(Bindings, EUmbrellaInputAction::Spell2, EKeys::Gamepad_RightStick_Right, 1.0f));
	TestTrue(TEXT("stick down = Twin"), MoveProofHasBinding(Bindings, EUmbrellaInputAction::Spell3, EKeys::Gamepad_RightStick_Down, 1.0f));
	TestTrue(TEXT("stick left = Needle"), MoveProofHasBinding(Bindings, EUmbrellaInputAction::Spell4, EKeys::Gamepad_RightStick_Left, 1.0f));
	return true;
}

// MOVE-12 / COM-05: Stream, Twin and Needle never run out either: the second half of a long shoot-fall fires as many as the first.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveProofAllSpellsUnlimitedTest, "UmbrellaElla.Move.World.AllSpellsNeverRunOut", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveProofAllSpellsUnlimitedTest::RunTest(const FString& Parameters)
{
	for (int32 Index = 0; Index < SpellRules::SpellCount; ++Index)
	{
		const EUmbrellaSpell Spell = static_cast<EUmbrellaSpell>(Index);
		FUmbrellaTestWorld Test;
		AEllaCharacter* Ella = Test.SpawnElla();
		if (!TestNotNull(TEXT("Ella spawned"), Ella))
		{
			return false;
		}
		UAttackEmitterComponent* Emitter = Ella->GetAttack();
		Emitter->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
		Emitter->SetDirectorLevel(30);
		Emitter->SelectSpell(Spell);
		Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
		int32 Counts[2] = {0, 0};
		for (int32 Half = 0; Half < 2; ++Half)
		{
			const int32 Start = Emitter->GetShotsFired();
			Test.TickSeconds(20.0f, 1.0f / 30.0f);
			Counts[Half] = Emitter->GetShotsFired() - Start;
		}
		const FString Name = SpellRules::SpellName(Spell).ToString();
		TestTrue(*FString::Printf(TEXT("%s fires in the first half (%d)"), *Name, Counts[0]), Counts[0] > 0);
		TestTrue(*FString::Printf(TEXT("%s second half %d matches first %d"), *Name, Counts[1], Counts[0]), FMath::Abs(Counts[1] - Counts[0]) <= 2);
	}
	return true;
}

// MOVE-07: fire goes right while the player travels left.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FMoveProofFireRightWhileLeftTest, "UmbrellaElla.Move.World.FireGoesRightWhileTravelingLeft", EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FMoveProofFireRightWhileLeftTest::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla();
	if (!TestNotNull(TEXT("Ella spawned"), Ella))
	{
		return false;
	}
	UEllaInputAdapterComponent* Adapter = Ella->GetInputAdapter();
	Adapter->ApplyAxis(EUmbrellaInputAction::MoveX, -1.0f);
	Adapter->ApplyPress(EUmbrellaInputAction::DashBack);
	Adapter->ApplyPress(EUmbrellaInputAction::Shoot);
	Test.TickSeconds(0.5f, 1.0f / 60.0f);
	TestTrue(TEXT("shots fired"), Ella->GetAttack()->GetShotsFired() > 0);
	TestTrue(TEXT("shot goes to +X"), Ella->GetAttack()->GetLastShot().Velocity.X > 0.0f);
	return true;
}

#endif
