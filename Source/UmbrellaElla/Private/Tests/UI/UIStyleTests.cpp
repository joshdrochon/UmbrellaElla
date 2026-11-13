#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Engine/Font.h"
#include "Framework/Application/SlateApplication.h"
#include "UI/Style/UmbrellaUIStyle.h"

namespace
{
	/** WCAG relative luminance of a linear colour. */
	float UIStyleTestLuminance(const FLinearColor& Color)
	{
		return 0.2126f * Color.R + 0.7152f * Color.G + 0.0722f * Color.B;
	}

	float UIStyleTestContrast(const FLinearColor& A, const FLinearColor& B)
	{
		const float Hi = FMath::Max(UIStyleTestLuminance(A), UIStyleTestLuminance(B));
		const float Lo = FMath::Min(UIStyleTestLuminance(A), UIStyleTestLuminance(B));
		return (Hi + 0.05f) / (Lo + 0.05f);
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FUIStyleDisplayFontTest, "UmbrellaElla.UI.Style.DisplayFaceLoadsFromEmbeddedBytes",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FUIStyleDisplayFontTest::RunTest(const FString& Parameters)
{
	TestTrue(TEXT("the embedded display face has data"), FUmbrellaUIStyle::HasDisplayFont());
	const FSlateFontInfo Font = FUmbrellaUIStyle::DisplayFont(40);
	TestTrue(TEXT("display font has a composite font"), Font.CompositeFont.IsValid());
	TestEqual(TEXT("one face in the display typeface"), Font.CompositeFont.IsValid() ? Font.CompositeFont->DefaultTypeface.Fonts.Num() : 0, 1);
	TestEqual(TEXT("size kept"), Font.Size, 40.0f);
	TestTrue(TEXT("the HUD canvas gets the same face"), FUmbrellaUIStyle::DisplayCanvasFont() != nullptr);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FUIStyleTextFloorTest, "UmbrellaElla.UI.Style.TextNeverUnderEighteen",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FUIStyleTextFloorTest::RunTest(const FString& Parameters)
{
	TestEqual(TEXT("floor"), UmbrellaUIStyleConstants::MinTextSize, 18);
	TestEqual(TEXT("small display size is raised"), FUmbrellaUIStyle::DisplayFont(9).Size, 18.0f);
	TestEqual(TEXT("small body size is raised"), FUmbrellaUIStyle::BodyFont(12).Size, 18.0f);
	TestEqual(TEXT("large size is kept"), FUmbrellaUIStyle::BodyFont(30).Size, 30.0f);
	TestEqual(TEXT("clamp"), FUmbrellaUIStyle::ClampTextSize(1), 18);
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FUIStyleContrastTest, "UmbrellaElla.UI.Style.LetteringReadsOnInk",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FUIStyleContrastTest::RunTest(const FString& Parameters)
{
	const FLinearColor Ink = FUmbrellaUIStyle::Ink();
	TestTrue(TEXT("cream on ink >= 4.5"), UIStyleTestContrast(FUmbrellaUIStyle::Cream(), Ink) >= 4.5f);
	TestTrue(TEXT("dim on ink >= 4.5"), UIStyleTestContrast(FUmbrellaUIStyle::Dim(), Ink) >= 4.5f);
	TestTrue(TEXT("gold on ink >= 4.5"), UIStyleTestContrast(FUmbrellaUIStyle::Gold(), Ink) >= 4.5f);
	TestTrue(TEXT("focus gold on ink >= 4.5"), UIStyleTestContrast(FUmbrellaUIStyle::GoldBright(), Ink) >= 4.5f);
	TestTrue(TEXT("warning on ink >= 4.5"), UIStyleTestContrast(FUmbrellaUIStyle::Warn(), Ink) >= 4.5f);
	// Focus is told by more than colour: the lit label is also brighter than the resting one.
	TestTrue(TEXT("focused label is brighter than gold"), UIStyleTestLuminance(FUmbrellaUIStyle::GoldBright()) > UIStyleTestLuminance(FUmbrellaUIStyle::Gold()));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FUIStyleButtonFocusTest, "UmbrellaElla.UI.Style.ButtonShowsItsOwnFocusMark",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FUIStyleButtonFocusTest::RunTest(const FString& Parameters)
{
	if (!FSlateApplication::IsInitialized())
	{
		return true;
	}
	bool bSelected = false;
	int32 Clicks = 0;
	TSharedRef<SUmbrellaButton> Button = SNew(SUmbrellaButton)
		.Text(FText::FromString(TEXT("Retry")))
		.FontSize(28)
		.Ornament(true)
		.Selected_Lambda([&bSelected]() { return bSelected; })
		.OnClicked_Lambda([&Clicks]() { ++Clicks; return FReply::Handled(); });
	TestTrue(TEXT("takes keyboard and gamepad focus"), Button->SupportsKeyboardFocus());
	TestFalse(TEXT("unlit at rest"), Button->IsLit());
	bSelected = true;
	TestTrue(TEXT("lit when it is the current choice"), Button->IsLit());
	Button->SetEnabled(false);
	TestFalse(TEXT("a disabled button is never lit"), Button->IsLit());
	TestTrue(TEXT("the default dashed focus box is replaced by the button's own mark"), Button->GetFocusBrush() == FStyleDefaults::GetNoBrush());
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FUIStyleBrushesTest, "UmbrellaElla.UI.Style.SharedBrushesExist",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FUIStyleBrushesTest::RunTest(const FString& Parameters)
{
	TestTrue(TEXT("panel brush"), FUmbrellaUIStyle::PanelBrush() != nullptr);
	TestEqual(TEXT("slider bar thickness"), FUmbrellaUIStyle::SliderStyle().BarThickness, UmbrellaUIStyleConstants::SliderBarThickness);
	TestEqual(TEXT("checkbox image size"), static_cast<float>(FUmbrellaUIStyle::CheckBoxStyle().CheckedImage.ImageSize.X), UmbrellaUIStyleConstants::CheckSize);
	// The painted ground is a tracked placeholder texture; when it is imported the brush carries its size.
	if (const FSlateBrush* Ground = FUmbrellaUIStyle::GroundBrush())
	{
		TestEqual(TEXT("ground width"), static_cast<float>(Ground->ImageSize.X), UmbrellaUIStyleConstants::GroundWidth);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FUIStyleHandBladeTest, "UmbrellaElla.UI.Style.ClockHandIsABladeToItsTip",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FUIStyleHandBladeTest::RunTest(const FString& Parameters)
{
	const FUmbrellaHandBlade Blade = FUmbrellaUIStyle::HandBlade(FVector2D(100.0, 100.0), FVector2D(100.0, 0.0), 10.0f);
	TestEqual(TEXT("the blade ends exactly at the tip (the value the hand shows)"), Blade.Tip, FVector2D(100.0, 0.0));
	TestEqual(TEXT("width at the widest point"), static_cast<float>(FVector2D::Distance(Blade.Left, Blade.Right)), 10.0f);
	TestTrue(TEXT("widest point sits between pivot and tip"), Blade.Left.Y < 100.0 && Blade.Left.Y > 0.0);
	TestTrue(TEXT("a short tail behind the pivot"), Blade.Tail.Y > 100.0 && Blade.Tail.Y < 120.0);
	return true;
}

#endif
