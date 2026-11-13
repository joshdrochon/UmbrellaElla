#include "Misc/AutomationTest.h"

#if WITH_AUTOMATION_TESTS

#include "Core/UmbrellaTuning.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/LocalPlayer.h"
#include "Engine/World.h"
#include "Feedback/Ui/UiArtSubsystem.h"
#include "GameFramework/PlayerController.h"
#include "Settings/SettingsMenuSubsystem.h"
#include "Settings/SettingsStore.h"
#include "Tests/Settings/SettingsTestViewport.h"
#include "Tests/Shared/UmbrellaTestWorld.h"
#include "UI/Settings/SettingsMenuWidget.h"
#include "Misc/Paths.h"
#include "Widgets/SOverlay.h"
#include "Widgets/Text/STextBlock.h"

namespace SettingsLayerTest
{
	/** The widget the viewport paints last (on top): the last overlay slot. */
	TSharedPtr<SWidget> TopOf(const TSharedRef<SOverlay>& Overlay)
	{
		FChildren* Children = Overlay->GetChildren();
		return Children->Num() > 0 ? TSharedPtr<SWidget>(Children->GetChildAt(Children->Num() - 1)) : TSharedPtr<SWidget>();
	}

	bool Holds(const TSharedRef<SOverlay>& Overlay, const TSharedRef<SWidget>& Widget)
	{
		FChildren* Children = Overlay->GetChildren();
		for (int32 SettingsLayerIndex = 0; SettingsLayerIndex < Children->Num(); ++SettingsLayerIndex)
		{
			if (Children->GetChildAt(SettingsLayerIndex) == Widget)
			{
				return true;
			}
		}
		return false;
	}

	FReply PressKey(USettingsMenuWidget* Widget, const FKey& Key)
	{
		const FKeyEvent Event(Key, FModifierKeysState(), 0, false, 0, 0);
		return Widget->NativeOnKeyDown(FGeometry(), Event);
	}
}

/**
 * Handoff B3: Pause -> Settings drew under the Paused menu (player layer vs viewport overlay). Settings now goes into
 * the same viewport overlay as the flow menus, above them and their art, and leaves it on close.
 */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsLayerAboveMenusTest, "UmbrellaElla.Settings.World.DrawsAboveFlowMenus",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSettingsLayerAboveMenusTest::RunTest(const FString& Parameters)
{
	const FString Path = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("UmbrellaEllaTests"), TEXT("Settings"), TEXT("layer.ini"));
	SettingsStore::Delete(Path);
	FUmbrellaTestWorld TestWorld;
	UWorld* World = TestWorld.GetWorld();
	APlayerController* Controller = World ? World->SpawnActor<APlayerController>() : nullptr;
	UGameInstance* GameInstance = NewObject<UGameInstance>(GEngine);
	GameInstance->InitializeStandalone();
	USettingsMenuSubsystem* Settings = GameInstance->GetSubsystem<USettingsMenuSubsystem>();
	if (!TestNotNull(TEXT("controller"), Controller) || !TestNotNull(TEXT("settings subsystem"), Settings))
	{
		return false;
	}
	// Widgets take only a local player's controller.
	Controller->SetPlayer(NewObject<ULocalPlayer>(GEngine, GEngine->LocalPlayerClass));
	Settings->SetStorePath(Path);
	Settings->ReloadFromStore();

	// A game viewport with the overlay the flow menus draw into.
	USettingsTestViewport* Viewport = NewObject<USettingsTestViewport>(GEngine);
	const TSharedRef<SOverlay> Overlay = Viewport->GetOverlay();
	Settings->SetViewportForTests(Viewport);

	// The Paused menu and its art, at the Z orders the flow controller and the UI art subsystem use.
	const int32 MenuZ = GetDefault<UUmbrellaTuning>()->Flow.MenuContextPriority;
	const TSharedRef<SWidget> PausedMenu = SNew(STextBlock).Text(FText::FromString(TEXT("Paused")));
	const TSharedRef<SWidget> MenuArt = SNew(STextBlock).Text(FText::FromString(TEXT("menu art")));
	Viewport->AddViewportWidgetContent(PausedMenu, MenuZ);
	Viewport->AddViewportWidgetContent(MenuArt, MenuZ + UmbrellaUiArtConst::ZOrderAboveMenu);

	Settings->OpenSettings(Controller);
	USettingsMenuWidget* Open = Settings->GetOpenWidget();
	if (!TestNotNull(TEXT("Settings opened"), Open))
	{
		return false;
	}
	const TSharedRef<SWidget> SettingsSlate = Open->TakeWidget();
	TestTrue(TEXT("Settings is in the flow menus' viewport overlay"), SettingsLayerTest::Holds(Overlay, SettingsSlate));
	TestTrue(TEXT("the top visible widget is Settings, not the Paused menu"), SettingsLayerTest::TopOf(Overlay) == SettingsSlate);

	// The flow re-shows its screen widget (same Z) while Settings is open: Settings stays on top.
	const TSharedRef<SWidget> PausedAgain = SNew(STextBlock).Text(FText::FromString(TEXT("Paused again")));
	Viewport->AddViewportWidgetContent(PausedAgain, MenuZ);
	Viewport->AddViewportWidgetContent(SNew(STextBlock), MenuZ + UmbrellaUiArtConst::ZOrderAboveMenu);
	TestTrue(TEXT("a re-shown flow menu or its art does not cover Settings"), SettingsLayerTest::TopOf(Overlay) == SettingsSlate);

	Settings->CloseSettings();
	TestFalse(TEXT("closing removes Settings from the overlay"), SettingsLayerTest::Holds(Overlay, SettingsSlate));
	TestTrue(TEXT("the Paused menu is still there to return to"), SettingsLayerTest::Holds(Overlay, PausedMenu));
	SettingsStore::Delete(Path);
	return true;
}

/** Pause step 5: Escape (and the other menu Back keys) inside Settings backs out like the Back button. */
IMPLEMENT_SIMPLE_AUTOMATION_TEST(FSettingsEscapeBacksOutTest, "UmbrellaElla.Settings.World.EscapeBacksOut",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::EngineFilter)
bool FSettingsEscapeBacksOutTest::RunTest(const FString& Parameters)
{
	const FString Path = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("UmbrellaEllaTests"), TEXT("Settings"), TEXT("escape.ini"));
	SettingsStore::Delete(Path);
	FUmbrellaTestWorld TestWorld;
	UWorld* World = TestWorld.GetWorld();
	APlayerController* Controller = World ? World->SpawnActor<APlayerController>() : nullptr;
	UGameInstance* GameInstance = NewObject<UGameInstance>(GEngine);
	GameInstance->InitializeStandalone();
	USettingsMenuSubsystem* Settings = GameInstance->GetSubsystem<USettingsMenuSubsystem>();
	if (!TestNotNull(TEXT("controller"), Controller) || !TestNotNull(TEXT("settings subsystem"), Settings))
	{
		return false;
	}
	// Widgets take only a local player's controller.
	Controller->SetPlayer(NewObject<ULocalPlayer>(GEngine, GEngine->LocalPlayerClass));
	Settings->SetStorePath(Path);
	Settings->ReloadFromStore();

	// Clean: Escape closes, as Back does.
	Settings->OpenSettings(Controller);
	USettingsMenuWidget* Open = Settings->GetOpenWidget();
	if (!TestNotNull(TEXT("Settings opened"), Open))
	{
		return false;
	}
	TestTrue(TEXT("Escape is handled"), SettingsLayerTest::PressKey(Open, EKeys::Escape).IsEventHandled());
	TestFalse(TEXT("Escape on a clean page closes Settings"), Settings->IsSettingsOpen());

	// The gamepad Back button does the same.
	Settings->OpenSettings(Controller);
	Open = Settings->GetOpenWidget();
	SettingsLayerTest::PressKey(Open, EKeys::Gamepad_FaceButton_Right);
	TestFalse(TEXT("the gamepad B button closes a clean Settings"), Settings->IsSettingsOpen());

	// Dirty: Escape asks Save / Discard / Keep Editing; Escape again keeps editing.
	Settings->OpenSettings(Controller);
	Open = Settings->GetOpenWidget();
	Open->ShowPage(ESettingsPage::Controller);
	Open->BeginRemap(EUmbrellaInputAction::Shoot, 0);
	SettingsLayerTest::PressKey(Open, EKeys::G);
	TestTrue(TEXT("the remap made the page dirty"), Settings->GetSession().IsPageDirty(ESettingsPage::Controller));
	SettingsLayerTest::PressKey(Open, EKeys::Escape);
	TestTrue(TEXT("Escape on a dirty page shows the Back prompt"), Open->IsBackPromptShown());
	TestTrue(TEXT("Settings stays open behind the prompt"), Settings->IsSettingsOpen());
	SettingsLayerTest::PressKey(Open, EKeys::Escape);
	TestFalse(TEXT("Escape at the prompt keeps editing"), Open->IsBackPromptShown());
	TestTrue(TEXT("Keep Editing keeps the draft"), Settings->GetSession().IsPageDirty(ESettingsPage::Controller));

	// While a remap waits for a key, Escape cancels the remap and leaves Settings open.
	Open->BeginRemap(EUmbrellaInputAction::Shoot, 0);
	SettingsLayerTest::PressKey(Open, EKeys::Escape);
	TestFalse(TEXT("Escape cancels a pending remap"), Open->IsCapturingKey());
	TestTrue(TEXT("Settings stays open after cancelling a remap"), Settings->IsSettingsOpen());

	Settings->CloseSettings();
	SettingsStore::Delete(Path);
	return true;
}

#endif
