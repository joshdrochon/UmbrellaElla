// dcseamless (Josh, Nov 13 23:45): the Director's Cut route must read as one seamless painted world. These tests fail on
// the three seam sources found in the route captures: (1) every backdrop layer wrapped every 1200 units, so its picture
// jumped a quarter width in one frame; (2) the route start and end pictures ended in a hard vertical cut; (3) the arena's
// flat stand-in background planes showed as darkened 3840 x 1080 "screens" behind the layered backdrop.
#include "Arena/UmbrellaArena.h"
#include "Components/StaticMeshComponent.h"
#include "Core/UmbrellaTuning.h"
#include "Engine/Engine.h"
#include "Engine/Texture2D.h"
#include "Engine/World.h"
#include "Feedback/Background/SceneArtSubsystem.h"
#include "Feedback/Background/UmbrellaBackdropSubsystem.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

namespace
{
	/** Camera step for the continuity sweep: about one frame of a fast dash. */
	constexpr float DcSeamCameraStep = 25.0f;
	/** Largest layer move (world units) allowed for one DcSeamCameraStep: the layer may only slide at its parallax. */
	constexpr float DcSeamMaxLayerStep = DcSeamCameraStep;

	UWorld* DcSeamWorld()
	{
		UWorld* World = UWorld::CreateWorld(EWorldType::Game, false);
		if (World)
		{
			GEngine->CreateNewWorldContext(EWorldType::Game).SetCurrentWorld(World);
		}
		return World;
	}

	void DcSeamEnd(UWorld* World)
	{
		GEngine->DestroyWorldContext(World);
		World->DestroyWorld(false);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackBackdropSeamless, "UmbrellaElla.Feedback.BackdropSeamless",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackBackdropSeamless::RunTest(const FString& Parameters)
{
	const float MinX = UUmbrellaBackdropSubsystem::RouteCameraMinX();
	const float MaxX = UUmbrellaBackdropSubsystem::RouteCameraMaxX();
	TestTrue(TEXT("camera range runs from the route start past the route end"), MaxX > MinX + GetDefault<UUmbrellaTuning>()->ArenaCamera.ArenaWidth);
	const float HalfPanel = UmbrellaBackdropConst::PanelWidth * 0.5f;
	TArray<FBackdropLayerSpec> Specs = UUmbrellaBackdropSubsystem::LayerSpecs();
	for (const FSceneArtSpec& Scene : USceneArtSubsystem::Specs())
	{
		if (Scene.Anchor == ESceneArtAnchor::Layer)
		{
			Specs.Add({ Scene.Visual, Scene.Depth, Scene.Parallax });
		}
	}
	for (const FBackdropLayerSpec& Spec : Specs)
	{
		float WorstJump = 0.0f;
		float WorstExposure = 0.0f;
		float Previous = UUmbrellaBackdropSubsystem::LayerXForCamera(MinX - DcSeamCameraStep, Spec.Parallax);
		for (float Camera = MinX; Camera <= MaxX; Camera += DcSeamCameraStep)
		{
			const float X = UUmbrellaBackdropSubsystem::LayerXForCamera(Camera, Spec.Parallax);
			// (1) No snap: the old wrap moved a layer by its 1200-unit period in one step.
			WorstJump = FMath::Max(WorstJump, FMath::Abs(X - Previous - DcSeamCameraStep));
			Previous = X;
			// The panel must cover the widest view on both sides: no picture edge in the frame.
			const float Left = (X - HalfPanel) - (Camera - UmbrellaBackdropConst::MaxViewHalfWidth);
			const float Right = (Camera + UmbrellaBackdropConst::MaxViewHalfWidth) - (X + HalfPanel);
			WorstExposure = FMath::Max(WorstExposure, FMath::Max(Left, Right));
		}
		TestTrue(*FString::Printf(TEXT("%s scrolls without a jump (worst %.1f units per %.0f-unit camera step)"), *Spec.Name.ToString(), WorstJump, DcSeamCameraStep),
			WorstJump <= DcSeamMaxLayerStep);
		TestTrue(*FString::Printf(TEXT("%s panel never shows its edge (worst %.1f units)"), *Spec.Name.ToString(), WorstExposure), WorstExposure <= 0.0f);
		// Depth order kept: a layer with more parallax still scrolls faster.
		for (const FBackdropLayerSpec& Other : Specs)
		{
			if (Other.Parallax > Spec.Parallax)
			{
				TestTrue(TEXT("depth order kept"), UUmbrellaBackdropSubsystem::EffectiveParallax(Other.Parallax) > UUmbrellaBackdropSubsystem::EffectiveParallax(Spec.Parallax));
			}
		}
	}
	// (2) The route start fades its right edge, the route end its left edge; nothing else fades.
	TestTrue(TEXT("start picture fades on the right"), USceneArtSubsystem::EdgeFades(ESceneArtAnchor::RouteStart).Y > 0.0f && USceneArtSubsystem::EdgeFades(ESceneArtAnchor::RouteStart).X == 0.0f);
	TestTrue(TEXT("end picture fades on the left"), USceneArtSubsystem::EdgeFades(ESceneArtAnchor::RouteEnd).X > 0.0f && USceneArtSubsystem::EdgeFades(ESceneArtAnchor::RouteEnd).Y == 0.0f);
	TestTrue(TEXT("layers and the frame do not fade"), USceneArtSubsystem::EdgeFades(ESceneArtAnchor::Layer).IsZero() && USceneArtSubsystem::EdgeFades(ESceneArtAnchor::View).IsZero());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFeedbackWorldBackdropSeamless, "UmbrellaElla.Feedback.World.BackdropSeamless",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ClientContext | EAutomationTestFlags::EngineFilter)

bool FFeedbackWorldBackdropSeamless::RunTest(const FString& Parameters)
{
	UWorld* World = DcSeamWorld();
	if (!TestNotNull(TEXT("world"), World))
	{
		return false;
	}
	UTexture2D* Picture = UTexture2D::CreateTransient(8, 8);
	Picture->AddToRoot();
	// (3) Arena stand-in planes hide once a backdrop layer draws art.
	AUmbrellaArena* Arena = World->SpawnActor<AUmbrellaArena>();
	UUmbrellaBackdropSubsystem* Backdrop = World->GetSubsystem<UUmbrellaBackdropSubsystem>();
	if (TestNotNull(TEXT("arena"), Arena) && TestNotNull(TEXT("backdrop"), Backdrop) && TestTrue(TEXT("layers built"), Backdrop->BuildLayers() > 0))
	{
		Arena->BuildPlaceholders();
		if (TestNotNull(TEXT("far plane"), Arena->GetBackgroundFar()) && TestNotNull(TEXT("near plane"), Arena->GetBackgroundNear()))
		{
			TestFalse(TEXT("far plane shows before"), Arena->GetBackgroundFar()->bHiddenInGame);
			Backdrop->ApplyLayerArt(0, Picture);
			TestEqual(TEXT("both arena planes hidden"), Backdrop->HideArenaStandIns(), 2);
			TestTrue(TEXT("far plane hidden"), Arena->GetBackgroundFar()->bHiddenInGame);
			TestTrue(TEXT("near plane hidden"), Arena->GetBackgroundNear()->bHiddenInGame);
		}
	}
	// (2) The route start and end panels draw with the edge-fade material and the right fade.
	USceneArtSubsystem* Scene = World->GetSubsystem<USceneArtSubsystem>();
	if (TestNotNull(TEXT("scene art"), Scene))
	{
		if (Scene->PanelCount(TEXT("bg:start-end")) == 0)
		{
			Scene->ShowArt(TEXT("bg:start-end"), Picture);
		}
		const UStaticMeshComponent* Start = Scene->FindPanel(TEXT("bg:start-end"), 0);
		const UStaticMeshComponent* End = Scene->FindPanel(TEXT("bg:start-end"), 1);
		if (TestNotNull(TEXT("start panel"), Start) && TestNotNull(TEXT("end panel"), End))
		{
			for (const UStaticMeshComponent* Panel : { Start, End })
			{
				const UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Panel->GetMaterial(0));
				TestTrue(TEXT("edge-fade material"), Dynamic && Dynamic->Parent && Dynamic->Parent->GetPathName() == UmbrellaSceneArtConst::EdgeFadeMaterialPath);
				TestEqual(TEXT("sorted behind other translucency"), Panel->TranslucencySortPriority, UmbrellaSceneArtConst::EdgeFadeSortPriority);
			}
			float StartRight = 0.0f, EndLeft = 0.0f;
			if (const UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Start->GetMaterial(0)))
			{
				Dynamic->GetScalarParameterValue(FName(TEXT("FadeRight")), StartRight);
			}
			if (const UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(End->GetMaterial(0)))
			{
				Dynamic->GetScalarParameterValue(FName(TEXT("FadeLeft")), EndLeft);
			}
			TestEqual(TEXT("start fades its right edge"), StartRight, UmbrellaSceneArtConst::RouteEndEdgeFade);
			TestEqual(TEXT("end fades its left edge"), EndLeft, UmbrellaSceneArtConst::RouteEndEdgeFade);
			// Josh, Nov 14: the 0.35 alpha ramp read as the barn picture dissolving into the void. The edge eases into the
			// picture's haze tone and only the outer haze goes see-through (old: share 1, colour none -> ramp 0.35 fails).
			for (const UStaticMeshComponent* Panel : { Start, End })
			{
				float Share = 1.0f;
				FLinearColor Haze = FLinearColor::Black;
				if (const UMaterialInstanceDynamic* Dynamic = Cast<UMaterialInstanceDynamic>(Panel->GetMaterial(0)))
				{
					Dynamic->GetScalarParameterValue(FName(TEXT("OpacityShare")), Share);
					Dynamic->GetVectorParameterValue(FName(TEXT("FadeColor")), Haze);
				}
				TestTrue(*FString::Printf(TEXT("alpha ramp %.3f of the width <= %.2f"), UmbrellaSceneArtConst::RouteEndEdgeFade * Share, UmbrellaSceneArtConst::RouteEndMaxAlphaRamp),
					UmbrellaSceneArtConst::RouteEndEdgeFade * Share <= UmbrellaSceneArtConst::RouteEndMaxAlphaRamp);
				TestTrue(TEXT("the edge eases into the haze tone, not black"), Haze.R > 0.0f && Haze.G > 0.0f && Haze.B > 0.0f);
			}
		}
	}
	Picture->RemoveFromRoot();
	DcSeamEnd(World);
	return true;
}

#endif
