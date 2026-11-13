#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Core/UmbrellaTuning.h"
#include "Flow/FlowMenuText.h"
#include "Framework/Application/SlateApplication.h"
#include "Input/Events.h"
#include "Layout/ArrangedChildren.h"
#include "UI/Menus/FlowMenuWidgets.h"
#include "UI/Style/UmbrellaUIStyle.h"
#include "Widgets/Text/STextBlock.h"

// menumouse: every flow menu (Start, Pause, Settings stub, Defeated) works with the mouse as well as keys and the pad.
namespace FlowMenuMouseTest
{
	/** One of the flow's menus as the player controller builds it: its labels, Back or not. */
	struct FMenuCase
	{
		const TCHAR* Name;
		TArray<FText> Labels;
		bool bHasBack;
	};

	TArray<FMenuCase> Menus()
	{
		return {
			{ TEXT("start"), FFlowMenuText::TitleLabels(), false },
			{ TEXT("pause"), FFlowMenuText::PauseLabels(), true },
			{ TEXT("settings"), { FFlowMenuText::BackLabel() }, true },
			{ TEXT("defeated"), FFlowMenuText::DefeatLabels(), false },
		};
	}

	/** Builds the menu; Chosen records which item ran (INDEX_NONE until one does). */
	TSharedRef<SFlowMenu> Build(const FMenuCase& Case, int32& Chosen, bool& bBack)
	{
		TArray<FFlowMenuItem> Items;
		for (int32 Index = 0; Index < Case.Labels.Num(); ++Index)
		{
			Items.Add({ Case.Labels[Index], FSimpleDelegate::CreateLambda([&Chosen, Index]() { Chosen = Index; }) });
		}
		FSimpleDelegate Back;
		if (Case.bHasBack)
		{
			Back = FSimpleDelegate::CreateLambda([&bBack]() { bBack = true; });
		}
		return SNew(SFlowMenu).Tuning(GetDefault<UUmbrellaTuning>()->Flow).Heading(FText::FromString(TEXT("Paused"))).Items(Items).OnBack(Back);
	}

	/** Lays the widget tree out at Size and finds Target's geometry (no window, no paint). */
	bool FindGeometry(const TSharedRef<SWidget>& Widget, const FGeometry& Geometry, const SWidget* Target, FGeometry& Out)
	{
		if (&Widget.Get() == Target)
		{
			Out = Geometry;
			return true;
		}
		FArrangedChildren Arranged(EVisibility::Visible);
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

	/** The first text block under Widget (a button's label). */
	bool FindText(const TSharedRef<SWidget>& Widget, const FGeometry& Geometry, FGeometry& Out)
	{
		if (Widget->GetType() == FName(TEXT("STextBlock")))
		{
			Out = Geometry;
			return true;
		}
		FArrangedChildren Arranged(EVisibility::Visible);
		Widget->ArrangeChildren(Geometry, Arranged);
		for (int32 Index = 0; Index < Arranged.Num(); ++Index)
		{
			if (FindText(Arranged[Index].Widget, Arranged[Index].Geometry, Out))
			{
				return true;
			}
		}
		return false;
	}

	int32 LitCount(const TSharedRef<SFlowMenu>& Menu)
	{
		int32 Lit = 0;
		for (int32 Index = 0; Index < Menu->GetItemCount(); ++Index)
		{
			Lit += Menu->GetItemButton(Index)->IsLit() ? 1 : 0;
		}
		return Lit;
	}

	FPointerEvent MouseAt(const FVector2f& Position)
	{
		return FPointerEvent(0, Position, Position, TSet<FKey>(), EKeys::Invalid, 0.0f, FModifierKeysState());
	}
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowMenuMouseSelectedOnOpen, "UmbrellaElla.Flow.MenuMouse.FirstItemSelectedOnOpen",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowMenuMouseSelectedOnOpen::RunTest(const FString& Parameters)
{
	if (!FSlateApplication::IsInitialized())
	{
		AddError(TEXT("needs Slate"));
		return false;
	}
	for (const FlowMenuMouseTest::FMenuCase& Case : FlowMenuMouseTest::Menus())
	{
		int32 Chosen = INDEX_NONE;
		bool bBack = false;
		// No focus is ever given here: the mark must show without it (Josh saw nothing selected when focus was elsewhere).
		const TSharedRef<SFlowMenu> Menu = FlowMenuMouseTest::Build(Case, Chosen, bBack);
		TestEqual(FString::Printf(TEXT("%s: first item selected on open"), Case.Name), Menu->GetSelectedIndex(), 0);
		TestTrue(FString::Printf(TEXT("%s: the first item shows the mark"), Case.Name), Menu->GetItemButton(0)->IsLit());
		TestEqual(FString::Printf(TEXT("%s: exactly one item shows the mark"), Case.Name), FlowMenuMouseTest::LitCount(Menu), 1);
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowMenuMouseHoverSelects, "UmbrellaElla.Flow.MenuMouse.HoverSelects",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowMenuMouseHoverSelects::RunTest(const FString& Parameters)
{
	if (!FSlateApplication::IsInitialized())
	{
		AddError(TEXT("needs Slate"));
		return false;
	}
	for (const FlowMenuMouseTest::FMenuCase& Case : FlowMenuMouseTest::Menus())
	{
		int32 Chosen = INDEX_NONE;
		bool bBack = false;
		const TSharedRef<SFlowMenu> Menu = FlowMenuMouseTest::Build(Case, Chosen, bBack);
		const int32 Last = Menu->GetItemCount() - 1;
		const TSharedPtr<SUmbrellaButton> Button = Menu->GetItemButton(Last);
		const FGeometry Geometry = FGeometry::MakeRoot(FVector2D(300.0, 60.0), FSlateLayoutTransform());
		Button->OnMouseEnter(Geometry, FlowMenuMouseTest::MouseAt(FVector2f(10.0f, 10.0f)));
		TestEqual(FString::Printf(TEXT("%s: hovering the last item selects it"), Case.Name), Menu->GetSelectedIndex(), Last);
		TestTrue(FString::Printf(TEXT("%s: the hovered item shows the mark"), Case.Name), Button->IsLit());
		TestEqual(FString::Printf(TEXT("%s: only the hovered item shows the mark"), Case.Name), FlowMenuMouseTest::LitCount(Menu), 1);
		Button->OnMouseLeave(FlowMenuMouseTest::MouseAt(FVector2f(-10.0f, -10.0f)));
		TestEqual(FString::Printf(TEXT("%s: the selection stays when the mouse leaves"), Case.Name), Menu->GetSelectedIndex(), Last);
		TestEqual(FString::Printf(TEXT("%s: nothing chosen by a hover"), Case.Name), Chosen, static_cast<int32>(INDEX_NONE));
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowMenuMouseClickChooses, "UmbrellaElla.Flow.MenuMouse.ClickChoosesEachItem",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowMenuMouseClickChooses::RunTest(const FString& Parameters)
{
	if (!FSlateApplication::IsInitialized())
	{
		AddError(TEXT("needs Slate"));
		return false;
	}
	// The press-and-release path needs a live window's mouse capture; the dev capture driver proves it in the running
	// game (MENU_MOUSE lines, -UIShots). Here every item's click runs that item and no other.
	for (const FlowMenuMouseTest::FMenuCase& Case : FlowMenuMouseTest::Menus())
	{
		for (int32 Index = 0; Index < Case.Labels.Num(); ++Index)
		{
			int32 Chosen = INDEX_NONE;
			bool bBack = false;
			const TSharedRef<SFlowMenu> Menu = FlowMenuMouseTest::Build(Case, Chosen, bBack);
			Menu->GetItemButton(Index)->SimulateClick();
			TestEqual(FString::Printf(TEXT("%s: clicking '%s' runs it"), Case.Name, *Case.Labels[Index].ToString()), Chosen, Index);
			TestEqual(FString::Printf(TEXT("%s: the clicked item is the selection"), Case.Name), Menu->GetSelectedIndex(), Index);
			TestFalse(FString::Printf(TEXT("%s: a click is not Back"), Case.Name), bBack);
		}
	}
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowMenuMouseKeysStillWork, "UmbrellaElla.Flow.MenuMouse.KeysAndPadStillChoose",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowMenuMouseKeysStillWork::RunTest(const FString& Parameters)
{
	if (!FSlateApplication::IsInitialized())
	{
		AddError(TEXT("needs Slate"));
		return false;
	}
	const FGeometry Geometry = FGeometry::MakeRoot(FVector2D(1920.0, 1080.0), FSlateLayoutTransform());
	for (const FKey& Key : { EKeys::Enter, EKeys::Gamepad_FaceButton_Bottom })
	{
		int32 Chosen = INDEX_NONE;
		bool bBack = false;
		const FlowMenuMouseTest::FMenuCase Pause = FlowMenuMouseTest::Menus()[1];
		const TSharedRef<SFlowMenu> Menu = FlowMenuMouseTest::Build(Pause, Chosen, bBack);
		Menu->GetItemButton(1)->OnMouseEnter(Geometry, FlowMenuMouseTest::MouseAt(FVector2f(1.0f, 1.0f)));
		// Confirm reaching the menu (no row focused) chooses the row the mark is on.
		const FKeyEvent Event(Key, FModifierKeysState(), 0, false, 0, 0);
		Menu->OnPreviewKeyDown(Geometry, Event);
		TestTrue(FString::Printf(TEXT("%s: Confirm is handled"), *Key.ToString()), Menu->OnKeyDown(Geometry, Event).IsEventHandled());
		TestEqual(FString::Printf(TEXT("%s: Confirm chooses the hovered row"), *Key.ToString()), Chosen, 1);
		TestEqual(FString::Printf(TEXT("%s: the hint follows the device"), *Key.ToString()), Menu->IsShowingGamepadPrompts(), Key.IsGamepadKey());
		const FKeyEvent Back(Key.IsGamepadKey() ? EKeys::Gamepad_FaceButton_Right : EKeys::Escape, FModifierKeysState(), 0, false, 0, 0);
		Menu->OnKeyDown(Geometry, Back);
		TestTrue(FString::Printf(TEXT("%s: Back still goes back"), *Key.ToString()), bBack);
	}
	TestEqual(TEXT("keyboard hint"), FFlowMenuText::ConfirmPrompt(false).ToString(), FString(TEXT("Click or Enter to choose")));
	TestEqual(TEXT("pad hint"), FFlowMenuText::BackPrompt(true).ToString(), FString(TEXT("B to go back")));
	return true;
}

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FFlowMenuMouseMarkerOnRow, "UmbrellaElla.Flow.MenuMouse.MarkerLinesUpWithSelectedRow",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FFlowMenuMouseMarkerOnRow::RunTest(const FString& Parameters)
{
	if (!FSlateApplication::IsInitialized())
	{
		AddError(TEXT("needs Slate"));
		return false;
	}
	constexpr float Tolerance = 2.0f;
	int32 Chosen = INDEX_NONE;
	bool bBack = false;
	FlowMenuMouseTest::FMenuCase Start = FlowMenuMouseTest::Menus()[0];
	TArray<FFlowMenuItem> Items;
	for (const FText& Label : Start.Labels)
	{
		Items.Add({ Label, FSimpleDelegate() });
	}
	// The real Start screen: the title lockup and its gold rule above the rows (1600 x 900, as Josh saw it).
	const TSharedRef<SFlowMenu> Menu = SNew(SFlowMenu).Tuning(GetDefault<UUmbrellaTuning>()->Flow).Heading(FFlowMenuText::TitleHeading()).Items(Items);
	Menu->SlatePrepass(1.0f);
	const FGeometry Root = FGeometry::MakeRoot(FVector2D(1600.0, 900.0), FSlateLayoutTransform());
	for (int32 Selected = 0; Selected < Menu->GetItemCount(); ++Selected)
	{
		Menu->SelectItem(Selected);
		const TSharedPtr<SUmbrellaButton> Button = Menu->GetItemButton(Selected);
		FGeometry ButtonGeometry;
		FGeometry LabelGeometry;
		if (!TestTrue(TEXT("the selected row is laid out"), FlowMenuMouseTest::FindGeometry(Menu, Root, Button.Get(), ButtonGeometry))
			|| !TestTrue(TEXT("the row has a label"), FlowMenuMouseTest::FindText(Button.ToSharedRef(), ButtonGeometry, LabelGeometry)))
		{
			return false;
		}
		const float ButtonTop = ButtonGeometry.GetAbsolutePosition().Y;
		const float MarkerY = ButtonTop + SUmbrellaButton::OrnamentCenterY(ButtonGeometry.GetAbsoluteSize().Y);
		const float LabelY = LabelGeometry.GetAbsolutePosition().Y + LabelGeometry.GetAbsoluteSize().Y * 0.5f;
		AddInfo(FString::Printf(TEXT("row %d: marker y=%.1f label middle y=%.1f row %.1f..%.1f"), Selected, MarkerY, LabelY, ButtonTop, ButtonTop + ButtonGeometry.GetAbsoluteSize().Y));
		TestTrue(FString::Printf(TEXT("row %d: the marker is level with the label (within %.0f px)"), Selected, Tolerance), FMath::Abs(MarkerY - LabelY) <= Tolerance);
		TestTrue(FString::Printf(TEXT("row %d: only the selected row shows the mark"), Selected), Button->IsLit() && FlowMenuMouseTest::LitCount(Menu) == 1);
		for (int32 Other = 0; Other < Menu->GetItemCount(); ++Other)
		{
			FGeometry OtherGeometry;
			if (Other != Selected && FlowMenuMouseTest::FindGeometry(Menu, Root, Menu->GetItemButton(Other).Get(), OtherGeometry))
			{
				const float OtherTop = OtherGeometry.GetAbsolutePosition().Y;
				const bool bOutside = MarkerY < OtherTop || MarkerY > OtherTop + OtherGeometry.GetAbsoluteSize().Y;
				TestTrue(FString::Printf(TEXT("row %d: the marker is not on row %d"), Selected, Other), bOutside);
			}
		}
	}
	return true;
}

#endif
