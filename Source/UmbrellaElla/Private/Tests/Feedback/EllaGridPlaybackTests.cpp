#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Components/StaticMeshComponent.h"
#include "Core/EllaCharacter.h"
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

#endif
