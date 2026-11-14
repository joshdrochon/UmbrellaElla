#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Core/UmbrellaPlayMode.h"
#include "Engine/Engine.h"
#include "Engine/LocalPlayer.h"
#include "Engine/UserInterfaceSettings.h"
#include "Engine/World.h"
#include "Flow/FlowRules.h"
#include "Core/UmbrellaGameMode.h"
#include "Flow/UmbrellaPlayerController.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerState.h"
#include "GameFramework/WorldSettings.h"
#include "Layout/ArrangedChildren.h"
#include "Progression/ProgressionSubsystem.h"
#include "UI/Progression/ProgressionPurchaseWidget.h"
#include "Widgets/Input/SButton.h"

// B9 (agentplay playthrough, Nov 13): at 640x360 the purchase screen's Done button drew under the purchase panel and a
// mouse click on it landed on the panel's SBorder. Done now sits in the panel's own button row and the panel scales down
// to fit. This lays the real screen out at each window size with the game's own DPI scale, hit-tests Done's centre the
// way Slate does (front-most visible, hit-testable widget under the point) and clicks it.
namespace ProgressionDoneHitTest
{
	struct FPurchaseTestWorld
	{
		UWorld* World = nullptr;
		UGameInstance* Instance = nullptr;
		AUmbrellaPlayerController* Controller = nullptr;

		FPurchaseTestWorld()
		{
			World = UWorld::CreateWorld(EWorldType::Game, false);
			FWorldContext& Context = GEngine->CreateNewWorldContext(EWorldType::Game);
			Context.SetCurrentWorld(World);
			Instance = NewObject<UGameInstance>(GEngine);
			Instance->AddToRoot();
			Context.OwningGameInstance = Instance;
			World->SetGameInstance(Instance);
			World->GetWorldSettings()->DefaultGameMode = AUmbrellaGameMode::StaticClass();
			World->SetGameMode(FURL());
			World->InitializeActorsForPlay(FURL());
			World->BeginPlay();
			Controller = World->SpawnActor<AUmbrellaPlayerController>();
			Controller->PlayerState = World->SpawnActor<APlayerState>();
			Controller->KeepTutorialInMemoryOnly();
			Controller->MarkTutorialSeen();
			Instance->Init();
			Controller->SetPlayer(NewObject<ULocalPlayer>(GEngine, GEngine->LocalPlayerClass));
		}

		~FPurchaseTestWorld()
		{
			GEngine->DestroyWorldContext(World);
			World->DestroyWorld(false);
			Instance->RemoveFromRoot();
		}
	};

	/**
	 * The widget path Slate's hit test would pick at Point: the front-most (last arranged) visible child first, and a
	 * widget counts only if its visibility takes hits. Empty when nothing under Point takes hits.
	 */
	bool HitPath(const TSharedRef<SWidget>& Widget, const FGeometry& Geometry, const FVector2f& Point, TArray<const SWidget*>& OutPath)
	{
		const EVisibility Visibility = Widget->GetVisibility();
		if (!Visibility.IsVisible() || !Geometry.IsUnderLocation(FVector2D(Point)))
		{
			return false;
		}
		OutPath.Add(&Widget.Get());
		if (Visibility.AreChildrenHitTestVisible())
		{
			FArrangedChildren Arranged(EVisibility::All);
			Widget->ArrangeChildren(Geometry, Arranged);
			for (int32 Index = Arranged.Num() - 1; Index >= 0; --Index)
			{
				if (HitPath(Arranged[Index].Widget, Arranged[Index].Geometry, Point, OutPath))
				{
					return true;
				}
			}
		}
		if (Visibility.IsHitTestVisible())
		{
			return true;
		}
		OutPath.Pop();
		return false;
	}

	/** Target's laid-out geometry under Widget. */
	bool FindGeometry(const TSharedRef<SWidget>& Widget, const FGeometry& Geometry, const SWidget* Target, FGeometry& Out)
	{
		if (&Widget.Get() == Target)
		{
			Out = Geometry;
			return true;
		}
		FArrangedChildren Arranged(EVisibility::All);
		Widget->ArrangeChildren(Geometry, Arranged);
		for (int32 Index = 0; Index < Arranged.Num(); ++Index)
		{
			if (FindGeometry(Arranged[Index].Widget, Arranged[Index].Geometry, Target, Out))
			{
				return true;
			}
		}
		return false;
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FProgressionPurchaseDoneHit, "UmbrellaElla.Progression.World.PurchaseDoneVisibleAndClickable",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FProgressionPurchaseDoneHit::RunTest(const FString& Parameters)
{
	if (!FSlateApplication::IsInitialized())
	{
		AddError(TEXT("needs Slate"));
		return false;
	}
	const TArray<FIntPoint> Sizes = { FIntPoint(640, 360), FIntPoint(1280, 720), FIntPoint(1920, 1080) };
	// Level 10 with 9 points left: the state of the agentplay capture (d00_purchase.png).
	const int32 CaptureLevel = 10;
	for (const FIntPoint& Size : Sizes)
	{
		const FString At = FString::Printf(TEXT(" at %dx%d"), Size.X, Size.Y);
		// A fresh world per size: Done returns to the title and the flow then repeats the Start press.
		ProgressionDoneHitTest::FPurchaseTestWorld Test;
		UProgressionSubsystem* Progression = UProgressionSubsystem::Get(Test.World);
		if (!TestNotNull(TEXT("progression subsystem") + At, Progression))
		{
			break;
		}
		Progression->UseSaveSlot(FString());
		Progression->SetPlayMode(EUmbrellaPlayMode::DirectorsCut);
		Progression->BeginShadowProgress(CaptureLevel);
		Test.Controller->ApplyCommand(EFlowCommand::OpenPurchase);
		UProgressionPurchaseWidget* Widget = Test.Controller->GetPurchaseWidget();
		if (!TestNotNull(TEXT("purchase widget") + At, Widget))
		{
			break;
		}
		// The tallest panel: every review line showing (one staged rank on each track it can buy).
		for (int32 Track = 0; Track < static_cast<int32>(EProgressionTrack::Count); ++Track)
		{
			Widget->StageBuy(static_cast<EProgressionTrack>(Track));
		}
		const TSharedRef<SWidget> Root = Widget->TakeWidget();
		const float Scale = GetDefault<UUserInterfaceSettings>()->GetDPIScaleBasedOnSize(Size);
		Root->SlatePrepass(Scale);
		const FGeometry Screen = FGeometry::MakeRoot(FVector2D(Size) / Scale, FSlateLayoutTransform(Scale));
		const TSharedPtr<SWidget> Done = Widget->GetDoneButton();
		FGeometry DoneGeometry;
		if (!TestTrue(TEXT("Done is laid out on the purchase screen") + At,
			Done.IsValid() && ProgressionDoneHitTest::FindGeometry(Root, Screen, Done.Get(), DoneGeometry)))
		{
			break;
		}
		const FSlateRect DoneRect = DoneGeometry.GetLayoutBoundingRect();
		AddInfo(FString::Printf(TEXT("%dx%d: DPI scale %.3f, Done at %s, panel content desired %s"), Size.X, Size.Y, Scale, *DoneRect.ToString(), *Root->GetDesiredSize().ToString()));
		TestTrue(FString::Printf(TEXT("Done (%s) lies fully inside the %dx%d window"), *DoneRect.ToString(), Size.X, Size.Y),
			DoneRect.Left >= 0.0f && DoneRect.Top >= 0.0f && DoneRect.Right <= Size.X && DoneRect.Bottom <= Size.Y && DoneRect.GetArea() > 0.0f);
		const FVector2f Centre = FVector2f(DoneGeometry.GetAbsolutePositionAtCoordinates(FVector2D(0.5, 0.5)));
		TArray<const SWidget*> Path;
		const bool bHit = ProgressionDoneHitTest::HitPath(Root, Screen, Centre, Path);
		const FString Front = Path.Num() > 0 ? Path.Last()->GetTypeAsString() : TEXT("nothing");
		TestTrue(FString::Printf(TEXT("a click at Done's centre (%.0f,%.0f) lands on Done, not on %s"), Centre.X, Centre.Y, *Front) + At,
			bHit && Path.Contains(Done.Get()));
		StaticCastSharedPtr<SButton>(Done)->SimulateClick();
		TestNotEqual(TEXT("clicking Done leaves the purchase screen") + At, Test.Controller->GetScreen(), EFlowScreen::Purchase);
		TestNull(TEXT("the purchase widget is released") + At, Test.Controller->GetPurchaseWidget());
		TestFalse(TEXT("leaving discards the unconfirmed draft") + At, Widget->IsDraftDirty());
		Progression->EndShadowProgress();
	}
	return true;
}

#endif
