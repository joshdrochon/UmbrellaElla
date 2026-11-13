#include "Tests/UI/UIShotSubsystem.h"
#include "Core/UmbrellaLog.h"
#include "Engine/GameInstance.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Flow/UmbrellaPlayerController.h"
#include "Framework/Application/SlateApplication.h"
#include "ImageUtils.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Story/StorySubsystem.h"
#include "UI/Story/StoryWidgets.h"
#include "UObject/UObjectIterator.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Core/UmbrellaTuning.h"
#include "Flow/FlowMenuText.h"
#include "Styling/CoreStyle.h"
#include "UI/Menus/FlowMenuWidgets.h"
#include "UI/Style/UmbrellaUIStyle.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SViewport.h"
#include "Widgets/Text/STextBlock.h"

/**
 * The flat Defeated screen as it was before the shared UI style (navy fill, plain bold sans, lilac pills), rebuilt
 * from the same tuning colours: the art loop's known-bad. A critic that cannot pick the reference over this is broken.
 */
class SUIShotLegacyFlatMenu final : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SUIShotLegacyFlatMenu) {}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs)
	{
		const FFlowTuning& Tuning = GetDefault<UUmbrellaTuning>()->Flow;
		Pill = MakeShared<FSlateRoundedBoxBrush>(Tuning.ButtonColor, Tuning.ButtonCornerRadius);
		Style = FButtonStyle().SetNormal(*Pill).SetHovered(*Pill).SetPressed(*Pill);
		TSharedRef<SVerticalBox> Column = SNew(SVerticalBox);
		Column->AddSlot().AutoHeight().HAlign(HAlign_Center).Padding(0.0f, 0.0f, 0.0f, Tuning.MenuSpacing)
		[
			SNew(STextBlock).Text(FFlowMenuText::DefeatHeading()).Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), Tuning.TitleFontSize)).ColorAndOpacity(Tuning.TextColor)
		];
		for (const FText& Label : FFlowMenuText::DefeatLabels())
		{
			Column->AddSlot().AutoHeight().HAlign(HAlign_Center).Padding(0.0f, Tuning.MenuSpacing * 0.5f)
			[
				SNew(SButton).ButtonStyle(&Style).ContentPadding(FMargin(Tuning.ButtonPaddingX, Tuning.ButtonPaddingY)).HAlign(HAlign_Center)
				[
					SNew(STextBlock).Text(Label).Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), Tuning.MenuFontSize)).ColorAndOpacity(Tuning.TextColor)
				]
			];
		}
		ChildSlot
		[
			SNew(SBorder).BorderImage(FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"))).BorderBackgroundColor(Tuning.BackgroundColor)
				.HAlign(HAlign_Center).VAlign(VAlign_Center)
			[
				Column
			]
		];
	}

private:
	TSharedPtr<FSlateRoundedBoxBrush> Pill;
	FButtonStyle Style;
};

namespace
{
	const float UIShotStartDelay = 3.0f;
	const float UIShotReadyTimeout = 90.0f;
	const int32 LegacyZOrder = 1000;

	/** Sends the mouse to the middle of the open menu's row Label through Slate's real input path (no OS cursor). */
	bool UIShotMouseTo(const FText& Label, int32& OutIndex)
	{
		const TSharedPtr<SFlowMenu> Menu = SFlowMenu::GetLastOpened();
		OutIndex = Menu.IsValid() ? Menu->FindItem(Label) : INDEX_NONE;
		if (!FSlateApplication::IsInitialized() || OutIndex == INDEX_NONE)
		{
			return false;
		}
		const FGeometry Geometry = Menu->GetItemButton(OutIndex)->GetPaintSpaceGeometry();
		const FVector2f Center = FVector2f(Geometry.GetAbsolutePositionAtCoordinates(FVector2f(0.5f, 0.5f)));
		const FPointerEvent Move(FSlateApplication::CursorUserIndex, FSlateApplication::CursorPointerIndex, Center, Center,
			TSet<FKey>(), EKeys::Invalid, 0.0f, FModifierKeysState());
		FSlateApplication::Get().ProcessMouseMoveEvent(Move);
		return Menu->GetSelectedIndex() == OutIndex;
	}

	/**
	 * menumouse: hover then click the open menu's row Label like a player. Logs MENU_MOUSE with hover and click results;
	 * click=1 only when the click changed the screen. When it did not, Fallback runs so the capture walk goes on.
	 */
	void UIShotClick(AUmbrellaPlayerController* Controller, const TCHAR* Menu, const FText& Label, TFunction<void()> Fallback)
	{
		int32 Index = INDEX_NONE;
		const bool bHover = UIShotMouseTo(Label, Index);
		const EFlowScreen Before = Controller->GetScreen();
		const TSharedPtr<SFlowMenu> Open = SFlowMenu::GetLastOpened();
		if (Index != INDEX_NONE && Open.IsValid())
		{
			const FGeometry Geometry = Open->GetItemButton(Index)->GetPaintSpaceGeometry();
			const FVector2f Center = FVector2f(Geometry.GetAbsolutePositionAtCoordinates(FVector2f(0.5f, 0.5f)));
			TSet<FKey> Pressed;
			Pressed.Add(EKeys::LeftMouseButton);
			FSlateApplication::Get().ProcessMouseButtonDownEvent(nullptr, FPointerEvent(FSlateApplication::CursorUserIndex,
				FSlateApplication::CursorPointerIndex, Center, Center, Pressed, EKeys::LeftMouseButton, 0.0f, FModifierKeysState()));
			FSlateApplication::Get().ProcessMouseButtonUpEvent(FPointerEvent(FSlateApplication::CursorUserIndex,
				FSlateApplication::CursorPointerIndex, Center, Center, TSet<FKey>(), EKeys::LeftMouseButton, 0.0f, FModifierKeysState()));
		}
		const bool bClicked = Controller->GetScreen() != Before;
		UE_LOG(LogUmbrellaElla, Log, TEXT("MENU_MOUSE menu=%s item=%s hover=%d click=%d"), Menu, *Label.ToString(), bHover ? 1 : 0, bClicked ? 1 : 0);
		if (!bClicked && Fallback)
		{
			Fallback();
		}
	}

	bool UIShotJourneyShown()
	{
		for (TObjectIterator<UJourneyCompleteWidget> It; It; ++It)
		{
			if (It->IsInViewport())
			{
				return true;
			}
		}
		return false;
	}
}

bool UUIShotSubsystem::ShouldCreateSubsystem(UObject* Outer) const
{
#if UE_BUILD_SHIPPING
	return false;
#else
	FString Dir;
	return FParse::Value(FCommandLine::Get(), TEXT("-UIShots="), Dir) && !Dir.IsEmpty();
#endif
}

void UUIShotSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	FParse::Value(FCommandLine::Get(), TEXT("-UIShots="), OutDir);
	FParse::Value(FCommandLine::Get(), TEXT("-UIShotsMode="), Mode);
	OutDir = FPaths::ConvertRelativePathToFull(OutDir);
	BuildSteps();
	TickHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateWeakLambda(this, [this](float DeltaSeconds)
	{
		AdvanceShots(DeltaSeconds);
		return !bDone;
	}));
}

void UUIShotSubsystem::Deinitialize()
{
	FTSTicker::GetCoreTicker().RemoveTicker(TickHandle);
	Super::Deinitialize();
}

AUmbrellaPlayerController* UUIShotSubsystem::FindController() const
{
	const UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	return World ? Cast<AUmbrellaPlayerController>(World->GetFirstPlayerController()) : nullptr;
}

void UUIShotSubsystem::BuildSteps()
{
	auto Add = [this](const TCHAR* Name, float Wait, TFunction<void(AUmbrellaPlayerController*)> Do, TFunction<bool()> Ready = nullptr)
	{
		FShotStep Step;
		Step.Name = Name;
		Step.Wait = Wait;
		Step.Do = MoveTemp(Do);
		Step.Ready = MoveTemp(Ready);
		Steps.Add(MoveTemp(Step));
	};
	auto Command = [](EFlowCommand Value)
	{
		return [Value](AUmbrellaPlayerController* Controller) { Controller->ApplyCommand(Value); };
	};

	if (Mode == TEXT("dc"))
	{
		Add(TEXT(""), 1.0f, [](AUmbrellaPlayerController* Controller)
		{
			Controller->KeepTutorialInMemoryOnly();
			Controller->MarkTutorialSeen();
			Controller->StartDirectorsCut();
		});
		Add(TEXT(""), 2.5f, [](AUmbrellaPlayerController* Controller)
		{
			// Start may already have offered the purchase screen; otherwise open it the way a refuge does.
			if (Controller->GetScreen() == EFlowScreen::Playing)
			{
				Controller->ApplyCommand(EFlowCommand::EnterRefuge);
			}
		});
		Add(TEXT("purchase"), 0.5f, [](AUmbrellaPlayerController*) {});
		Add(TEXT(""), 1.5f, [](AUmbrellaPlayerController* Controller)
		{
			Controller->ApplyCommand(Controller->IsPurchaseAtRefuge() ? EFlowCommand::LeaveRefuge : EFlowCommand::Continue);
		});
		Add(TEXT("xp-ring"), 3.0f, [](AUmbrellaPlayerController*) {});
		Add(TEXT("level-up"), 1.5f, Command(EFlowCommand::OpenLevelUp));
		Add(TEXT(""), 1.5f, Command(EFlowCommand::Continue));
		Add(TEXT("story-caption"), 4.5f, [](AUmbrellaPlayerController* Controller)
		{
			if (UStorySubsystem* Story = Controller->GetWorld()->GetSubsystem<UStorySubsystem>())
			{
				Story->ShowDirectorsCutEnding();
			}
		});
		Add(TEXT("journey-complete"), 1.0f, [](AUmbrellaPlayerController*) {}, []() { return UIShotJourneyShown(); });
		return;
	}

	// The known-bad for the critic sanity check: the old flat screen laid over the title, shot, then taken away.
	Add(TEXT("known-bad-defeated"), 1.0f, [this](AUmbrellaPlayerController* Controller)
	{
		LegacyWidget = SNew(SUIShotLegacyFlatMenu);
		if (UGameViewportClient* Client = Controller->GetWorld()->GetGameViewport())
		{
			Client->AddViewportWidgetContent(LegacyWidget.ToSharedRef(), LegacyZOrder);
		}
	});
	Add(TEXT("title"), 1.0f, [this](AUmbrellaPlayerController* Controller)
	{
		if (UGameViewportClient* Client = Controller->GetWorld()->GetGameViewport())
		{
			Client->RemoveViewportWidgetContent(LegacyWidget.ToSharedRef());
		}
		LegacyWidget.Reset();
	});
	Add(TEXT(""), 0.5f, [](AUmbrellaPlayerController* Controller)
	{
		// menumouse: hovering a row moves the mark there; then back to Start Game.
		int32 Index = INDEX_NONE;
		const bool bDirectors = UIShotMouseTo(FFlowMenuText::DirectorsCutLabel(), Index);
		const bool bStart = UIShotMouseTo(FFlowMenuText::StartGameLabel(), Index);
		UE_LOG(LogUmbrellaElla, Log, TEXT("MENU_MOUSE menu=start hover-directors-cut=%d hover-start-game=%d"), bDirectors ? 1 : 0, bStart ? 1 : 0);
	});
	Add(TEXT("tutorial"), 1.5f, [](AUmbrellaPlayerController* Controller)
	{
		Controller->KeepTutorialInMemoryOnly();
		Controller->ClearTutorialSeen();
		UIShotClick(Controller, TEXT("start"), FFlowMenuText::StartGameLabel(), [Controller]() { Controller->StartGame(); });
	});
	Add(TEXT("hud"), 4.0f, Command(EFlowCommand::SkipTutorial));
	Add(TEXT("pause"), 1.5f, Command(EFlowCommand::Pause));
	Add(TEXT("settings"), 1.5f, Command(EFlowCommand::OpenSettings));
	Add(TEXT(""), 1.0f, Command(EFlowCommand::Back));
	Add(TEXT(""), 1.5f, [](AUmbrellaPlayerController* Controller)
	{
		UIShotClick(Controller, TEXT("pause"), FFlowMenuText::ContinueLabel(), [Controller]() { Controller->ApplyCommand(EFlowCommand::Continue); });
	});
	Add(TEXT("defeated"), 1.5f, Command(EFlowCommand::PlayerDefeated));
	Add(TEXT(""), 1.5f, [](AUmbrellaPlayerController* Controller)
	{
		UIShotClick(Controller, TEXT("defeated"), FFlowMenuText::RetryLabel(), [Controller]() { Controller->ApplyCommand(EFlowCommand::Retry); });
	});
	Add(TEXT("story"), 2.5f, Command(EFlowCommand::EncounterCompleted));
	Add(TEXT("credits"), 12.0f, Command(EFlowCommand::TimelineDone));
}

void UUIShotSubsystem::SaveShot(const FString& Name)
{
	const UWorld* World = GetGameInstance() ? GetGameInstance()->GetWorld() : nullptr;
	UGameViewportClient* Client = World ? World->GetGameViewport() : nullptr;
	TSharedPtr<SViewport> Widget = Client ? Client->GetGameViewportWidget() : nullptr;
	if (!Widget.IsValid() || !FSlateApplication::IsInitialized())
	{
		return;
	}
	TArray<FColor> Pixels;
	FIntVector Size;
	if (!FSlateApplication::Get().TakeScreenshot(Widget.ToSharedRef(), Pixels, Size) || Pixels.Num() == 0)
	{
		return;
	}
	for (FColor& Pixel : Pixels)
	{
		Pixel.A = 255;
	}
	TArray64<uint8> Png;
	FImageUtils::PNGCompressImageArray(Size.X, Size.Y, TArrayView64<const FColor>(Pixels.GetData(), Pixels.Num()), Png);
	const FString Path = OutDir / (Name + TEXT(".png"));
	const bool bSaved = FFileHelper::SaveArrayToFile(Png, *Path);
	UE_LOG(LogUmbrellaElla, Log, TEXT("UI_SHOT name=%s w=%d h=%d saved=%d path=%s"), *Name, Size.X, Size.Y, bSaved ? 1 : 0, *Path);
	Saved += bSaved ? 1 : 0;
}

void UUIShotSubsystem::AdvanceShots(float DeltaSeconds)
{
	AUmbrellaPlayerController* Controller = FindController();
	if (!Controller || !Controller->HasActorBegunPlay())
	{
		return;
	}
	StepSeconds += DeltaSeconds;
	if (StepIndex < 0)
	{
		if (StepSeconds < UIShotStartDelay)
		{
			return;
		}
		StepIndex = 0;
		StepSeconds = 0.0f;
		bStepStarted = false;
	}
	if (!Steps.IsValidIndex(StepIndex))
	{
		UE_LOG(LogUmbrellaElla, Log, TEXT("UI_SHOTS_DONE saved=%d mode=%s"), Saved, Mode.IsEmpty() ? TEXT("start") : *Mode);
		bDone = true;
		FPlatformMisc::RequestExit(false);
		return;
	}
	const FShotStep& Step = Steps[StepIndex];
	if (!bStepStarted)
	{
		bStepStarted = true;
		StepSeconds = 0.0f;
		Step.Do(Controller);
		return;
	}
	const bool bReady = !Step.Ready || Step.Ready() || StepSeconds > UIShotReadyTimeout;
	if (StepSeconds < Step.Wait || !bReady)
	{
		return;
	}
	if (!Step.Name.IsEmpty())
	{
		SaveShot(Step.Name);
	}
	++StepIndex;
	bStepStarted = false;
	StepSeconds = 0.0f;
}
