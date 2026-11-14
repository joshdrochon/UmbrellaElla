#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Flow/FlowRules.h"
#include "Feedback/Ui/UiArtSubsystem.h"
#include "UI/Menus/FlowMenuWidgets.h"

// Josh, Nov 13: the death screen shows the in-game backdrop, never the title picture; the title screen keeps it.
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FDeathScreenBackdropTest, "UmbrellaElla.UI.DeathScreenNotTitlePicture",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FDeathScreenBackdropTest::RunTest(const FString& Parameters)
{
	TestTrue(TEXT("Defeated shows the game scene, not the title picture"), ShouldFlowMenuShowGameScene(EFlowScreen::Defeat));
	TestFalse(TEXT("the title screen keeps its picture"), ShouldFlowMenuShowGameScene(EFlowScreen::Title));
	TestFalse(TEXT("credits keep their picture"), ShouldFlowMenuShowGameScene(EFlowScreen::Credits));
	TestFalse(TEXT("pause keeps its picture"), ShouldFlowMenuShowGameScene(EFlowScreen::Paused));
	TestEqual(TEXT("pause keeps its clocks"), FlowBackdropFor(EFlowScreen::Paused), EFlowBackdrop::Clocks);

	// The UI art layer: no full-frame picture (the title ground, its grain, or the screen:Defeat capture) on Defeated.
	TestFalse(TEXT("no full-frame screen art on Defeated"), UUiArtSubsystem::IsScreenArtAllowedOn(EFlowScreen::Defeat));
	TestTrue(TEXT("the title keeps its screen art"), UUiArtSubsystem::IsScreenArtAllowedOn(EFlowScreen::Title));
	bool bTitleHasGround = false;
	for (const UmbrellaUiPieceConst::FUiPiece& Piece : UmbrellaUiPieceConst::Pieces)
	{
		if (Piece.bFill)
		{
			TestFalse(FString::Printf(TEXT("%s does not fill the Defeated screen"), Piece.Visual), (Piece.Screens & UiScreenBit(EFlowScreen::Defeat)) != 0);
		}
		bTitleHasGround |= FString(Piece.Visual) == TEXT("ui:ground-Ground") && (Piece.Screens & UiScreenBit(EFlowScreen::Title)) != 0;
	}
	TestTrue(TEXT("the title keeps the ground picture"), bTitleHasGround);
	return true;
}

#endif
