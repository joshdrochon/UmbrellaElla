#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Components/StaticMeshComponent.h"
#include "Attack/AttackEmitterComponent.h"
#include "Core/EllaCharacter.h"
#include "Input/EllaInputAdapterComponent.h"
#include "Feedback/Anim/EllaAnimPresenterComponent.h"
#include "Feedback/Art/ArtSlot.h"
#include "Materials/MaterialInterface.h"
#include "Tests/Shared/UmbrellaTestWorld.h"

/**
 * Josh, 14 Nov: Ella looked like a still sprite, not the approved 24-frame idle (ella-up-open, 6x4 grid). Nothing set the
 * art-slot Frame, and the material read only the top row. Now the presenter walks every cell at the sidecar fps.
 */
namespace
{
	constexpr EAutomationTestFlags GridTestFlags = EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter;

	float MaterialFrame(const UStaticMeshComponent* Mesh)
	{
		const UMaterialInterface* Material = IsValid(Mesh) && Mesh->GetNumMaterials() > 0 ? Mesh->GetMaterial(0) : nullptr;
		float Frame = -1.0f;
		if (Material)
		{
			Material->GetScalarParameterValue(FHashedMaterialParameterInfo(FName(TEXT("Frame"))), Frame);
		}
		return Frame;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEllaGridFrameRule, "UmbrellaElla.Feedback.EllaAnim.GridFrameAt", GridTestFlags)

bool FEllaGridFrameRule::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("starts on cell 0"), UEllaAnimPresenterComponent::GridFrameAt(0.0, 6.0f, 6, 4), 0);
	TestEqual(TEXT("one second at 6 fps is cell 6 (row 2, first cell)"), UEllaAnimPresenterComponent::GridFrameAt(1.0, 6.0f, 6, 4), 6);
	TestEqual(TEXT("reaches the last cell"), UEllaAnimPresenterComponent::GridFrameAt(23.0 / 6.0 + 0.01, 6.0f, 6, 4), 23);
	TestEqual(TEXT("loops after 24 cells"), UEllaAnimPresenterComponent::GridFrameAt(4.0 + 0.01, 6.0f, 6, 4), 0);
	TestEqual(TEXT("a single picture stays on 0"), UEllaAnimPresenterComponent::GridFrameAt(3.3, 6.0f, 1, 1), 0);
	TestEqual(TEXT("a play-once clip holds its last cell"), UEllaAnimPresenterComponent::GridFrameAt(9.0, 6.0f, 6, 4, false), 23);
	TestEqual(TEXT("a play-once clip starts on 0"), UEllaAnimPresenterComponent::GridFrameAt(0.0, 6.0f, 6, 4, false), 0);
	TestTrue(TEXT("Idle loops"), UEllaAnimPresenterComponent::IsLoopingState(EEllaVisualState::Idle));
	TestFalse(TEXT("Hurt plays once"), UEllaAnimPresenterComponent::IsLoopingState(EEllaVisualState::Hurt));
	TestFalse(TEXT("Down plays once"), UEllaAnimPresenterComponent::IsLoopingState(EEllaVisualState::Down));
	TestTrue(TEXT("Shoot loops while shooting"), UEllaAnimPresenterComponent::IsLoopingState(EEllaVisualState::Shoot));
	TestFalse(TEXT("AimShot plays once"), UEllaAnimPresenterComponent::IsLoopingState(EEllaVisualState::AimShot));
	TestEqual(TEXT("AimShot waits on cell 0 before the pose time"), UEllaAnimPresenterComponent::AimShotFrameAt(0.1f, 0.15f, 0.5f, false, 24), 0);
	TestEqual(TEXT("AimShot halfway through the charge"), UEllaAnimPresenterComponent::AimShotFrameAt(0.325f, 0.15f, 0.5f, false, 24), 11);
	TestEqual(TEXT("AimShot holds the last cell once the beam fired"), UEllaAnimPresenterComponent::AimShotFrameAt(0.0f, 0.15f, 0.5f, true, 24), 23);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEllaShootAnimates, "UmbrellaElla.Feedback.World.EllaShootAnimatesWhileShooting", GridTestFlags)

bool FEllaShootAnimates::RunTest(const FString& Parameters)
{
	// Josh, 14 Nov: the hip-fire picture (ella-state:Shoot, T_Ella_Shoot 6x4) loops while Shoot is held. Twin Stars here:
	// Small Blasts would start charging the aimed beam (D-new-aimed-shot) after AimedPoseShowSeconds and show AimShot.
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla(FVector(0.0, 0.0, 2000.0));
	UEllaAnimPresenterComponent* Look = Ella ? Ella->GetAnimPresenter() : nullptr;
	const UStaticMeshComponent* Mesh = Ella ? FindObjectFast<UStaticMeshComponent>(Ella, FName(TEXT("EllaStandIn"))) : nullptr;
	const FArtSlotRow* Shoot = ArtSlot::Find(TEXT("ella-state:Shoot"));
	if (!TestNotNull(TEXT("ella"), Ella) || !TestNotNull(TEXT("presenter"), Look) || !TestNotNull(TEXT("Ella's picture"), Mesh)
		|| !TestNotNull(TEXT("shoot row"), Shoot) || !TestTrue(TEXT("Shoot is a 6x4 grid sheet"), Shoot->Cols == 6 && Shoot->Rows == 4))
	{
		return false;
	}
	Ella->GetAttack()->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
	Ella->GetAttack()->SetDirectorLevel(20);
	Ella->GetAttack()->SelectSpell(EUmbrellaSpell::TwinStars);
	Ella->GetInputAdapter()->ApplyPress(EUmbrellaInputAction::Shoot);
	TSet<int32> Seen;
	int32 ShootTicks = 0;
	constexpr int32 Steps = 30;
	for (int32 Step = 0; Step < Steps; ++Step)
	{
		Test.TickSeconds(1.0f / Steps, 1.0f / Steps);
		if (Look->GetVisualState() == EEllaVisualState::Shoot)
		{
			++ShootTicks;
			Seen.Add(Look->GetDrawnFrame());
			TestEqual(TEXT("the material draws the presenter's cell"), FMath::RoundToInt(MaterialFrame(Mesh)), Look->GetDrawnFrame());
		}
	}
	Ella->GetInputAdapter()->ApplyRelease(EUmbrellaInputAction::Shoot);
	AddInfo(FString::Printf(TEXT("1 s shooting: %d ticks in Shoot, %d distinct cells"), ShootTicks, Seen.Num()));
	TestTrue(TEXT("Ella shows Shoot while shooting"), ShootTicks >= Steps - 3);
	TestTrue(TEXT("Ella draws the Shoot picture"), ArtSlot::HasArt(Mesh));
	TestTrue(FString::Printf(TEXT("the hip-fire frames advance while shooting (%d distinct cells, want >= 5)"), Seen.Num()), Seen.Num() >= 5);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEllaIdleAnimates, "UmbrellaElla.Feedback.World.EllaIdleAnimatesInFlight", GridTestFlags)

bool FEllaIdleAnimates::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	// Spawned in the air with nothing under her: she is in flight, umbrella open, as in normal play.
	AEllaCharacter* Ella = Test.SpawnElla(FVector(0.0, 0.0, 2000.0));
	UEllaAnimPresenterComponent* Look = Ella ? Ella->GetAnimPresenter() : nullptr;
	const UStaticMeshComponent* Mesh = Ella ? FindObjectFast<UStaticMeshComponent>(Ella, FName(TEXT("EllaStandIn"))) : nullptr;
	if (!TestNotNull(TEXT("ella"), Ella) || !TestNotNull(TEXT("presenter"), Look) || !TestNotNull(TEXT("Ella's picture"), Mesh)
		|| !TestTrue(TEXT("Ella draws art"), ArtSlot::HasArt(Mesh)))
	{
		return false;
	}
	const FArtSlotRow* Idle = ArtSlot::Find(TEXT("ella-state:Idle"));
	if (!TestNotNull(TEXT("idle row"), Idle) || !TestTrue(TEXT("idle is a grid sheet"), Idle->Cols * Idle->Rows > 1))
	{
		return false;
	}
	TSet<int32> Seen;
	int32 MaxFrame = -1;
	constexpr int32 Steps = 30;
	for (int32 Step = 0; Step < Steps; ++Step)
	{
		Test.TickSeconds(1.0f / Steps, 1.0f / Steps);
		const int32 Frame = FMath::RoundToInt(MaterialFrame(Mesh));
		Seen.Add(Frame);
		MaxFrame = FMath::Max(MaxFrame, Frame);
		TestEqual(TEXT("the material draws the presenter's cell"), Frame, Look->GetDrawnFrame());
	}
	AddInfo(FString::Printf(TEXT("1 s in flight: %d distinct cells, highest %d, state %d"), Seen.Num(), MaxFrame, static_cast<int32>(Look->GetVisualState())));
	TestTrue(FString::Printf(TEXT("the idle advances over 1 s (%d distinct cells, want >= 5)"), Seen.Num()), Seen.Num() >= 5);
	// Past the first row: the material must walk rows, not only frames 0-5. 1 s at 6.13 fps from t=0 reaches cell 6.
	TestTrue(FString::Printf(TEXT("reaches the second row (highest cell %d >= %d)"), MaxFrame, Idle->Cols), MaxFrame >= Idle->Cols);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FEllaHurtStartsOnCellZero, "UmbrellaElla.Feedback.World.EllaHurtStartsOnCellZero", GridTestFlags)

bool FEllaHurtStartsOnCellZero::RunTest(const FString& Parameters)
{
	FUmbrellaTestWorld Test;
	AEllaCharacter* Ella = Test.SpawnElla(FVector(0.0, 0.0, 2000.0));
	UEllaAnimPresenterComponent* Look = Ella ? Ella->GetAnimPresenter() : nullptr;
	const UStaticMeshComponent* Mesh = Ella ? FindObjectFast<UStaticMeshComponent>(Ella, FName(TEXT("EllaStandIn"))) : nullptr;
	if (!TestNotNull(TEXT("ella"), Ella) || !TestNotNull(TEXT("presenter"), Look) || !TestNotNull(TEXT("Ella's picture"), Mesh))
	{
		return false;
	}
	// Mid idle cycle (world clock past cell 0), then hit: the hurt clip starts on its own cell 0.
	Test.TickSeconds(1.3f, 1.0f / 30.0f);
	TestTrue(FString::Printf(TEXT("idle is mid-cycle before the hit (cell %d)"), Look->GetDrawnFrame()), Look->GetDrawnFrame() > 0);
	Look->SetVisualState(EEllaVisualState::Hurt);
	TestEqual(TEXT("Hurt starts on cell 0 (presenter)"), Look->GetDrawnFrame(), 0);
	TestEqual(TEXT("Hurt starts on cell 0 (material)"), FMath::RoundToInt(MaterialFrame(Mesh)), 0);
	Test.TickSeconds(0.2f, 1.0f / 30.0f);
	TestTrue(FString::Printf(TEXT("Hurt advances from 0 (cell %d after 0.2 s)"), Look->GetDrawnFrame()), Look->GetDrawnFrame() >= 1 && Look->GetDrawnFrame() <= 2);
	// Down plays once and holds its last cell.
	Look->SetVisualState(EEllaVisualState::Down);
	TestEqual(TEXT("Down starts on cell 0"), Look->GetDrawnFrame(), 0);
	Test.TickSeconds(6.0f, 1.0f / 30.0f);
	const FArtSlotRow* Down = ArtSlot::Find(TEXT("ella-state:Down"));
	if (Down && Look->GetVisualState() == EEllaVisualState::Down)
	{
		TestEqual(TEXT("Down holds its last cell, no loop"), Look->GetDrawnFrame(), Down->Cols * Down->Rows - 1);
	}
	return true;
}

#endif
