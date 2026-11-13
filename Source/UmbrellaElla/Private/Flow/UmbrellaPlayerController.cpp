#include "Flow/UmbrellaPlayerController.h"
#include "Settings/UmbrellaAccessibility.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaGameMode.h"
#include "Level/UmbrellaLevelDirector.h"
#include "Core/UmbrellaTuning.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Engine/World.h"
#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Engine/GameViewportClient.h"
#include "Engine/LocalPlayer.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "InputAction.h"
#include "InputMappingContext.h"
#include "InputTriggers.h"
#include "Kismet/GameplayStatics.h"
#include "Kismet/KismetSystemLibrary.h"
#include "Flow/FlowMenuText.h"
#include "Flow/FlowTutorialText.h"
#include "Misc/ConfigCacheIni.h"
#include "Engine/GameInstance.h"
#include "Feedback/Audio/UmbrellaCueSubsystem.h"
#include "Progression/ProgressionSubsystem.h"
#include "Settings/SettingsMenuSubsystem.h"
#include "Story/StorySubsystem.h"
#include "UI/Story/StoryWidgets.h"
#include "UI/Progression/ProgressionPurchaseWidget.h"
#include "UI/Progression/XpRingWidget.h"
#include "Widgets/Input/SButton.h"
#include "Flow/FlowStoryText.h"
#include "UI/Menus/FlowMenuWidgets.h"
#include "UI/Style/UmbrellaUIStyle.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"
#include "Widgets/SCompoundWidget.h"
#include "Framework/Application/SlateApplication.h"

// Rule IDs built here: FLOW-02 (two routes), FLOW-04 (win: story, credits), FLOW-34 (Start screen), FLOW-35 (Pause),
// ART-04 (same moving background on Start and End), FLOW-03 (first-start tutorial, Pause then Skip), FLOW-41 (Start and
// Pause design retained), MOVE-08 (pause keys: Escape, F1, Menu), MOVE-09 (menu navigation, WASD included), NAR-04 (story
// Skip press routed to the story first and consumed), NAR-07 and FLOW-49 (one ending timeline: hold, story, credits, then
// Journey Complete in Director's Cut). Each is checked through IsFeatureEnabled below.

/** Bottom-centred holder of the purchase screen's Done button. Back keys (Escape, F1, B, Menu) pressed while it has focus call OnBack. */
class SFlowPurchaseDoneBox final : public SCompoundWidget
{
public:
	SLATE_BEGIN_ARGS(SFlowPurchaseDoneBox) {}
		SLATE_EVENT(FSimpleDelegate, OnBack)
		SLATE_ARGUMENT(FMargin, Padding)
		SLATE_DEFAULT_SLOT(FArguments, Content)
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs)
	{
		BackDelegate = InArgs._OnBack;
		ChildSlot.HAlign(HAlign_Center).VAlign(VAlign_Bottom).Padding(InArgs._Padding)
		[
			InArgs._Content.Widget
		];
	}

	virtual FReply OnKeyDown(const FGeometry& MyGeometry, const FKeyEvent& InKeyEvent) override
	{
		if (FFlowRules::MenuIntentForKey(InKeyEvent.GetKey()) == EFlowMenuIntent::Back)
		{
			return BackDelegate.ExecuteIfBound() ? FReply::Handled() : FReply::Unhandled();
		}
		return SCompoundWidget::OnKeyDown(MyGeometry, InKeyEvent);
	}

private:
	FSimpleDelegate BackDelegate;
};

namespace
{
	const TCHAR* const FlowSaveSection = TEXT("/Script/UmbrellaElla.FlowSave");
	const TCHAR* const FlowTutorialSeenKey = TEXT("TutorialSeen");

	/** Keys that must be released before control returns after Continue or Retry (neutral input). */
	TArray<FKey> GetNeutralKeys()
	{
		TArray<FKey> Keys;
		Keys.Add(EKeys::Enter);
		Keys.Add(EKeys::SpaceBar);
		Keys.Add(EKeys::LeftMouseButton);
		Keys.Add(EKeys::Escape);
		Keys.Add(EKeys::F1);
		Keys.Add(EKeys::Gamepad_FaceButton_Bottom);
		Keys.Add(EKeys::Gamepad_FaceButton_Right);
		Keys.Add(EKeys::Gamepad_Special_Right);
		return Keys;
	}
}

AUmbrellaPlayerController::AUmbrellaPlayerController()
{
	bShouldPerformFullTickWhenPaused = true;
}

void AUmbrellaPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	// IMC_Menu: pause keys, built in code. Not consumed, so a gameplay key it shares still reaches gameplay.
	PauseAction = NewObject<UInputAction>(this, TEXT("IA_Pause"));
	PauseAction->ValueType = EInputActionValueType::Boolean;
	PauseAction->bConsumeInput = false;
	PauseAction->Triggers.Add(NewObject<UInputTriggerPressed>(PauseAction));

	MenuContext = NewObject<UInputMappingContext>(this, TEXT("IMC_Menu"));
	MenuContext->MapKey(PauseAction, EKeys::Escape);
	if (IsFeatureEnabled(EFeatureId::MOVE_08))
	{
		MenuContext->MapKey(PauseAction, EKeys::F1);
		MenuContext->MapKey(PauseAction, EKeys::Gamepad_Special_Right);
	}

	// Story Skip: keys no gameplay action uses, so the press never leaks into play (NAR-04). Exact keys are OPEN.
	SkipAction = NewObject<UInputAction>(this, TEXT("IA_StorySkip"));
	SkipAction->ValueType = EInputActionValueType::Boolean;
	SkipAction->bConsumeInput = false;
	SkipAction->Triggers.Add(NewObject<UInputTriggerPressed>(SkipAction));
	for (const FKey& Key : FFlowRules::StorySkipKeys())
	{
		MenuContext->MapKey(SkipAction, Key);
	}

	if (UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(InputComponent))
	{
		Input->BindAction(PauseAction, ETriggerEvent::Triggered, this, &AUmbrellaPlayerController::OnPausePressed);
		Input->BindAction(SkipAction, ETriggerEvent::Triggered, this, &AUmbrellaPlayerController::OnSkipPressed);
	}
}

void AUmbrellaPlayerController::BeginPlay()
{
	Super::BeginPlay();

	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		DefeatHandle = Bus->On(EUmbrellaEventType::PlayerDefeated).AddUObject(this, &AUmbrellaPlayerController::HandlePlayerDefeated);
		CompletedHandle = Bus->On(EUmbrellaEventType::EncounterCompleted).AddUObject(this, &AUmbrellaPlayerController::HandleEncounterCompleted);
		LevelHandle = Bus->On(EUmbrellaEventType::LevelGained).AddUObject(this, &AUmbrellaPlayerController::HandleLevelGained);
	}
	if (UStorySubsystem* Story = GetStory())
	{
		// FLOW-49: Journey Complete's buttons.
		StoryTryAgainHandle = Story->GetTryAgainDelegate().AddUObject(this, &AUmbrellaPlayerController::TryAgain);
		StoryMainMenuHandle = Story->GetMainMenuDelegate().AddUObject(this, &AUmbrellaPlayerController::ReturnToTitleFromStatistics);
	}

	const UUmbrellaTuning* Tuning = GetDefault<UUmbrellaTuning>();
	ULocalPlayer* Local = GetLocalPlayer();
	if (UEnhancedInputLocalPlayerSubsystem* Input = Local ? Local->GetSubsystem<UEnhancedInputLocalPlayerSubsystem>() : nullptr)
	{
		if (MenuContext)
		{
			Input->AddMappingContext(MenuContext, Tuning->Flow.MenuContextPriority);
		}
	}

	if (GConfig && !bTutorialInMemoryOnly)
	{
		GConfig->GetBool(FlowSaveSection, FlowTutorialSeenKey, bTutorialSeen, GGameUserSettingsIni);
	}

	if (!IsFeatureEnabled(EFeatureId::FLOW_34))
	{
		StartGame();
		return;
	}
	SetInputBlocked(true);
	ShowScreenWidget();
	SetInputModeFor(Screen);
	// FLOW-34: the Start screen has music from the moment it opens; picking a mode carries the same track on.
	PlayFlowMusic(Screen);

	const AGameModeBase* GameMode = GetWorld() ? GetWorld()->GetAuthGameMode() : nullptr;
	if (GameMode && IsFeatureEnabled(EFeatureId::FLOW_49) && FFlowRules::IsTryAgainStart(GameMode->OptionsString))
	{
		// Try Again from Journey Complete: a fresh world, straight into a new Director's Cut run (purchase screen first
		// when there is something to spend). BeginRun broadcasts ModeSelected, so story starts the run's stats from zero.
		StartDirectorsCut();
	}
}

void AUmbrellaPlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		Bus->On(EUmbrellaEventType::PlayerDefeated).Remove(DefeatHandle);
		Bus->On(EUmbrellaEventType::EncounterCompleted).Remove(CompletedHandle);
		Bus->On(EUmbrellaEventType::LevelGained).Remove(LevelHandle);
	}
	if (UStorySubsystem* Story = GetStory())
	{
		Story->GetTryAgainDelegate().Remove(StoryTryAgainHandle);
		Story->GetMainMenuDelegate().Remove(StoryMainMenuHandle);
	}
	ClearScreenWidget();
	Super::EndPlay(EndPlayReason);
}

void AUmbrellaPlayerController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);
	TickFlow(DeltaTime);
}

bool AUmbrellaPlayerController::IsGameplayInputBlocked() const
{
	return FFlowRules::IsInputBlockedOn(Screen);
}

void AUmbrellaPlayerController::StartGame()
{
	StartMode(EUmbrellaPlayMode::StartGame);
}

void AUmbrellaPlayerController::StartDirectorsCut()
{
	StartMode(IsFeatureEnabled(EFeatureId::FLOW_02) ? EUmbrellaPlayMode::DirectorsCut : EUmbrellaPlayMode::StartGame);
}

void AUmbrellaPlayerController::RequestSmokeStart()
{
	KeepTutorialInMemoryOnly();
	MarkTutorialSeen();
	StartGame();
}

void AUmbrellaPlayerController::StartMode(EUmbrellaPlayMode Mode)
{
	if (Screen != EFlowScreen::Title)
	{
		return;
	}
	PlayMode = Mode;
	SyncProgressionMode(Mode);
	if (Mode == EUmbrellaPlayMode::DirectorsCut && !bPurchaseDone && ShouldOfferPurchase())
	{
		// Spend earned points first; Done returns to the title and repeats this Start press.
		ApplyCommand(EFlowCommand::OpenPurchase);
		return;
	}
	bPurchaseDone = false;
	TutorialPage = 0;
	bRunBegun = false;
	if (FFlowRules::ShouldShowTutorial(IsFeatureEnabled(EFeatureId::FLOW_03), bTutorialSeen))
	{
		// The fight (or Director's Cut level) starts when the tutorial ends or is skipped.
		ApplyCommand(EFlowCommand::StartTutorial);
		return;
	}
	ApplyCommand(EFlowCommand::StartMode);
	BeginRun();
}

bool AUmbrellaPlayerController::ShouldOfferPurchase() const
{
	const UProgressionSubsystem* Progression = UProgressionSubsystem::Get(this);
	if (!Progression)
	{
		return false;
	}
	FPurchaseContext Context;
	Context.Kind = bPurchaseAtRefuge ? EPurchaseContextKind::SafeRefuge : EPurchaseContextKind::RunStart;
	const FProgressionProfile Profile = Progression->GetEffectiveProfile();
	bool bAnythingRefundable = false;
	for (const int32 Rank : Profile.Ranks)
	{
		bAnythingRefundable |= Rank > 0;
	}
	return FFlowRules::ShouldOfferPurchase(IsFeatureEnabled(EFeatureId::FLOW_42), Progression->GetUnspentPoints(),
		Progression->GetPlayMode() == EUmbrellaPlayMode::DirectorsCut && FProgressionRules::CanReallocate(Context, Profile), bAnythingRefundable);
}

void AUmbrellaPlayerController::SyncProgressionMode(EUmbrellaPlayMode Mode)
{
	if (UProgressionSubsystem* Progression = UProgressionSubsystem::Get(this))
	{
		Progression->SetPlayMode(Mode);
	}
	if (UGameInstance* Instance = GetGameInstance())
	{
		if (USettingsMenuSubsystem* Settings = Instance->GetSubsystem<USettingsMenuSubsystem>())
		{
			Settings->SetPlayMode(Mode);
		}
	}
}

void AUmbrellaPlayerController::ShowPurchaseScreen()
{
	FPurchaseContext Context;
	Context.Kind = bPurchaseAtRefuge ? EPurchaseContextKind::SafeRefuge : EPurchaseContextKind::RunStart;
	if (UProgressionSubsystem* Progression = UProgressionSubsystem::Get(this))
	{
		Progression->SetPurchaseContext(Context);
	}
	ClearPurchaseScreen();
	const int32 Z = GetDefault<UUmbrellaTuning>()->Flow.MenuContextPriority;
	PurchaseWidget = UProgressionPurchaseWidget::Show(this);
	if (PurchaseWidget)
	{
		PurchaseWidget->RemoveFromParent();
		PurchaseWidget->AddToViewport(Z);
	}
	// Done sits above the purchase screen; Confirm and Cancel are the widget's own. Escape, F1, B and Menu go back too.
	TSharedPtr<SButton> DoneButton;
	PurchaseDoneButton = SNew(SFlowPurchaseDoneBox).OnBack(FSimpleDelegate::CreateWeakLambda(this, [this]() { ApplyCommand(EFlowCommand::Back); }))
		.Padding(FMargin(0.0f, 0.0f, 0.0f, GetDefault<UUmbrellaTuning>()->Flow.PurchaseDoneBottomMargin))
	[
		SAssignNew(DoneButton, SUmbrellaButton).Text(FFlowMenuText::DoneLabel()).FontSize(GetDefault<UUmbrellaTuning>()->Flow.MenuFontSize)
			.OnClicked_Lambda([this]() { ApplyCommand(EFlowCommand::Continue); return FReply::Handled(); })
	];
	if (UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr)
	{
		Viewport->AddViewportWidgetContent(PurchaseDoneButton.ToSharedRef(), Z + 1);
		if (DoneButton.IsValid() && FSlateApplication::IsInitialized())
		{
			FSlateApplication::Get().SetAllUserFocus(DoneButton, EFocusCause::SetDirectly);
		}
	}
}

void AUmbrellaPlayerController::ClearPurchaseScreen()
{
	if (PurchaseWidget)
	{
		// FLOW-42: closing or a context change discards an unconfirmed draft.
		PurchaseWidget->Cancel();
		PurchaseWidget->RemoveFromParent();
		PurchaseWidget = nullptr;
	}
	UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	if (Viewport && PurchaseDoneButton.IsValid())
	{
		Viewport->RemoveViewportWidgetContent(PurchaseDoneButton.ToSharedRef());
	}
	PurchaseDoneButton.Reset();
}

void AUmbrellaPlayerController::BeginRun()
{
	if (bRunBegun)
	{
		return;
	}
	bRunBegun = true;
	// The run-start screen already served the checkpoint Ella is placed at; the next window is the next refuge.
	LastRefugeOffered = 1;
	bPurchaseAtRefuge = false;
	if (UProgressionSubsystem* Progression = UProgressionSubsystem::Get(this))
	{
		// Nothing is bought during the fight; the next window is a refuge or the next start.
		Progression->SetPurchaseContext(FPurchaseContext());
	}
	if (AUmbrellaGameMode* Fight = GetWorld()->GetAuthGameMode<AUmbrellaGameMode>())
	{
		// Director's Cut walks the route first; the level director starts the Keeper at its end. If the route cannot be
		// built (level flags off), Director's Cut falls back to the Keeper fight as before.
		if (PlayMode == EUmbrellaPlayMode::DirectorsCut)
		{
			Fight->BeginRoute(this, GetDefault<UUmbrellaTuning>()->Flow.DirectorsCutRouteSeed);
		}
		if (!Fight->HasRoute())
		{
			Fight->BeginFight(this);
		}
	}
	// Broadcast once the world is up, so listeners can rely on the arena and Ella.
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		FUmbrellaEvent Event;
		Event.Type = EUmbrellaEventType::ModeSelected;
		Event.Detail = PlayMode == EUmbrellaPlayMode::StartGame ? FName(TEXT("StartGame")) : FName(TEXT("DirectorsCut"));
		Event.Amount = static_cast<int32>(PlayMode);
		Bus->Broadcast(Event);
	}
	if (PlayMode == EUmbrellaPlayMode::DirectorsCut && !XpRing)
	{
		XpRing = UXpRingWidget::Show(this);
	}
}

void AUmbrellaPlayerController::MarkTutorialSeen()
{
	bTutorialSeen = true;
	if (!bTutorialInMemoryOnly && GConfig)
	{
		GConfig->SetBool(FlowSaveSection, FlowTutorialSeenKey, true, GGameUserSettingsIni);
		GConfig->Flush(false, GGameUserSettingsIni);
	}
}

void AUmbrellaPlayerController::ClearTutorialSeen()
{
	bTutorialSeen = false;
}

void AUmbrellaPlayerController::KeepTutorialInMemoryOnly()
{
	bTutorialInMemoryOnly = true;
}

void AUmbrellaPlayerController::AdvanceTutorial()
{
	if (Screen != EFlowScreen::Tutorial)
	{
		return;
	}
	const int32 PageCount = FFlowTutorialText::GetPages(PlayMode).Num();
	if (FFlowRules::HasTutorialPageAfter(TutorialPage, PageCount))
	{
		++TutorialPage;
		ShowScreenWidget();
		SetInputModeFor(Screen);
		return;
	}
	ApplyCommand(EFlowCommand::TimelineDone);
}

void AUmbrellaPlayerController::ApplyCommand(EFlowCommand Command)
{
	if (Command == EFlowCommand::Pause && !IsFeatureEnabled(EFeatureId::FLOW_35))
	{
		return;
	}
	if (Screen == EFlowScreen::Purchase && bPurchaseAtRefuge
		&& (Command == EFlowCommand::Continue || Command == EFlowCommand::Back || Command == EFlowCommand::Pause))
	{
		Command = EFlowCommand::LeaveRefuge;
	}
	const EFlowScreen From = Screen;
	const EFlowScreen To = FFlowRules::Next(Screen, Command);
	if (To != Screen)
	{
		EnterScreen(To, Command);
		if ((From == EFlowScreen::Tutorial || From == EFlowScreen::TutorialPaused) && To == EFlowScreen::Resuming)
		{
			// Finished or skipped: remember it, then start the run; the neutral wait consumes the confirm press.
			MarkTutorialSeen();
			BeginRun();
		}
	}
}

void AUmbrellaPlayerController::EnterScreen(EFlowScreen To, EFlowCommand Cause)
{
	const EFlowScreen From = Screen;
	Screen = To;

	SetPause(FFlowRules::IsWorldPausedOn(To));
	SetInputBlocked(FFlowRules::IsInputBlockedOn(To));

	if (From == EFlowScreen::Settings)
	{
		CloseSettingsMenu();
	}
	if (From == EFlowScreen::Purchase)
	{
		ClearPurchaseScreen();
		if (!bPurchaseAtRefuge)
		{
			bPurchaseDone = true;
		}
		bPurchaseAtRefuge = false;
		if (UProgressionSubsystem* Progression = UProgressionSubsystem::Get(this))
		{
			Progression->SetPurchaseContext(FPurchaseContext());
		}
	}
	if (To == EFlowScreen::Credits && PlayMode == EUmbrellaPlayMode::DirectorsCut)
	{
		FPurchaseContext Context;
		Context.Kind = EPurchaseContextKind::BetweenRuns;
		if (UProgressionSubsystem* Progression = UProgressionSubsystem::Get(this))
		{
			Progression->SetPurchaseContext(Context);
		}
	}

	NeutralSeconds = 0.0f;
	StoryElapsed = To == EFlowScreen::Story ? 0.0f : StoryElapsed;
	CreditsElapsed = To == EFlowScreen::Credits ? 0.0f : CreditsElapsed;
	bEndingTextShown = To == EFlowScreen::Story ? false : bEndingTextShown;

	// One ending timeline (NAR-07, FLOW-49): flow's clock, story follows it (stats frozen, first win saved at Statistics).
	if (UStorySubsystem* Story = PlayMode == EUmbrellaPlayMode::DirectorsCut ? GetStory() : nullptr)
	{
		if (To == EFlowScreen::Story)
		{
			Story->ShowDirectorsCutEnding();
		}
		else if (To == EFlowScreen::Credits)
		{
			Story->EnterEndingStage(EStoryEndingStage::Credits);
		}
		else if (To == EFlowScreen::Statistics)
		{
			Story->EnterEndingStage(EStoryEndingStage::Statistics);
		}
	}

	if (Cause == EFlowCommand::Retry)
	{
		++RetryCount;
		if (UEncounterDirectorSubsystem* Director = GetWorld()->GetSubsystem<UEncounterDirectorSubsystem>())
		{
			Director->ResetForRestart();
		}
		if (AUmbrellaGameMode* Mode = GetWorld()->GetAuthGameMode<AUmbrellaGameMode>())
		{
			Mode->EnsurePlayerPawn(this);
			if (PlayMode == EUmbrellaPlayMode::DirectorsCut)
			{
				Mode->PlaceAtLastCheckpoint(this);
			}
		}
	}

	ApplyPawnInputBlock();
	ShowScreenWidget();
	PlayFlowMusic(To);
	if (!(To == EFlowScreen::Settings && bSettingsOpened))
	{
		SetInputModeFor(To);
	}

	if (From == EFlowScreen::Credits && To == EFlowScreen::Title)
	{
		ReturnToTitle();
	}
}

void AUmbrellaPlayerController::PlayFlowMusic(EFlowScreen To)
{
	UUmbrellaCueSubsystem* Cues = GetWorld() ? GetWorld()->GetSubsystem<UUmbrellaCueSubsystem>() : nullptr;
	if (!Cues)
	{
		return;
	}
	const FName Music = FFlowRules::MusicFor(To);
	if (To == EFlowScreen::Story && IsFeatureEnabled(EFeatureId::FLOW_04))
	{
		// FLOW-04: the win sting and the story text play without the run's music; credits bring it back.
		Cues->StopMusic();
	}
	else if (!Music.IsNone() && IsFeatureEnabled(To == EFlowScreen::Title ? EFeatureId::FLOW_34 : EFeatureId::FLOW_04))
	{
		Cues->EnsureMusic(Music);
	}
}

void AUmbrellaPlayerController::TickFlow(float DeltaSeconds)
{
	const UUmbrellaTuning* Tuning = GetDefault<UUmbrellaTuning>();
	switch (Screen)
	{
	case EFlowScreen::Playing:
		OfferRefugePurchase();
		break;
	case EFlowScreen::Settings:
		// The settings area's menu owns this screen; it closes itself on Back and Save.
		if (bSettingsOpened && !IsSettingsMenuOpen())
		{
			ApplyCommand(EFlowCommand::Back);
		}
		break;
	case EFlowScreen::Resuming:
		NeutralSeconds = FFlowRules::AdvanceNeutral(NeutralSeconds, DeltaSeconds, IsAnyNeutralKeyHeld());
		if (NeutralSeconds >= Tuning->Flow.ResumeNeutralSeconds)
		{
			ApplyCommand(EFlowCommand::NeutralReached);
		}
		break;
	case EFlowScreen::Story:
		StoryElapsed += DeltaSeconds;
		if (IsInEndingHold())
		{
			// NAR-07: hold on Ella under her umbrella while the light still falls; no ending background yet.
			break;
		}
		if (!bEndingTextShown)
		{
			bEndingTextShown = true;
			if (UStorySubsystem* Story = PlayMode == EUmbrellaPlayMode::DirectorsCut ? GetStory() : nullptr)
			{
				Story->EnterEndingStage(EStoryEndingStage::StoryText);
			}
			ShowScreenWidget();
			SetInputModeFor(Screen);
		}
		if (FFlowRules::EndingPageAt(StoryElapsed, IsFeatureEnabled(EFeatureId::NAR_07) ? Tuning->Story.EndingHoldSeconds : 0.0f,
			GetEndingPageSeconds(), GetEndingPages().Num()) == INDEX_NONE)
		{
			ApplyCommand(EFlowCommand::TimelineDone);
		}
		else
		{
			RefreshTimedText();
		}
		break;
	case EFlowScreen::Credits:
		CreditsElapsed += DeltaSeconds;
		if (FFlowRules::IsTimelineDone(CreditsElapsed, Tuning->Flow.CreditsSeconds))
		{
			ApplyCommand(FFlowRules::AfterCredits(PlayMode, IsFeatureEnabled(EFeatureId::FLOW_49)));
		}
		else
		{
			RefreshTimedText();
		}
		break;
	default:
		break;
	}
}

void AUmbrellaPlayerController::OfferRefugePurchase()
{
	// FLOW-29 / FLOW-42: spending happens in a real refuge on the route, once per refuge, never in a fight.
	if (PlayMode != EUmbrellaPlayMode::DirectorsCut || !IsFeatureEnabled(EFeatureId::FLOW_29) || !GetWorld())
	{
		return;
	}
	const AUmbrellaGameMode* Mode = GetWorld()->GetAuthGameMode<AUmbrellaGameMode>();
	const AUmbrellaLevelDirector* Level = Mode ? Mode->GetLevelDirector() : nullptr;
	if (!Level || Level->HasHandedOff() || Level->GetCheckpointReached() <= LastRefugeOffered)
	{
		return;
	}
	LastRefugeOffered = Level->GetCheckpointReached();
	bPurchaseAtRefuge = true;
	if (ShouldOfferPurchase())
	{
		ApplyCommand(EFlowCommand::EnterRefuge);
	}
	if (Screen != EFlowScreen::Purchase)
	{
		bPurchaseAtRefuge = false;
	}
	else
	{
		SetPause(true);
	}
}

void AUmbrellaPlayerController::RefreshTimedText()
{
	if (!TextScreen.IsValid())
	{
		return;
	}
	const FFlowTuning& Tuning = GetDefault<UUmbrellaTuning>()->Flow;
	if (Screen == EFlowScreen::Story)
	{
		const TArray<FText> Pages = GetEndingPages();
		const float Hold = IsFeatureEnabled(EFeatureId::NAR_07) ? GetDefault<UUmbrellaTuning>()->Story.EndingHoldSeconds : 0.0f;
		const int32 Page = FFlowRules::EndingPageAt(StoryElapsed, Hold, GetEndingPageSeconds(), Pages.Num());
		if (Pages.IsValidIndex(Page))
		{
			TextScreen->SetText(Pages[Page], 0.0f);
		}
	}
	else if (Screen == EFlowScreen::Credits)
	{
		TArray<FString> Lines;
		for (const FText& Line : FFlowStoryText::GetCreditsLines())
		{
			Lines.Add(Line.ToString());
		}
		const float Progress = FMath::Clamp(CreditsElapsed / Tuning.CreditsSeconds, 0.0f, 1.0f);
		TextScreen->SetCredits(Lines, FMath::Lerp(-Tuning.CreditsTravel, Tuning.CreditsTravel, Progress));
	}
}

void AUmbrellaPlayerController::ClearScreenWidget()
{
	UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	if (Viewport && ScreenWidget.IsValid())
	{
		Viewport->RemoveViewportWidgetContent(ScreenWidget.ToSharedRef());
	}
	ScreenWidget.Reset();
	TextScreen.Reset();
}

void AUmbrellaPlayerController::AddViewportWidget(const TSharedRef<SWidget>& Widget)
{
	UGameViewportClient* Viewport = GetWorld() ? GetWorld()->GetGameViewport() : nullptr;
	if (Viewport)
	{
		const int32 MenuZOrder = GetDefault<UUmbrellaTuning>()->Flow.MenuContextPriority;
		Viewport->AddViewportWidgetContent(Widget, MenuZOrder);
	}
}

void AUmbrellaPlayerController::ShowScreenWidget()
{
	ClearScreenWidget();

	FFlowTuning Tuning = GetDefault<UUmbrellaTuning>()->Flow;
	if (!IsFeatureEnabled(EFeatureId::ART_04))
	{
		Tuning.FallingShapeCount = 0;
		Tuning.PauseClockCount = 0;
	}

	const FSimpleDelegate Resume = FSimpleDelegate::CreateWeakLambda(this, [this]() { ApplyCommand(EFlowCommand::Continue); });
	const FSimpleDelegate Back = FSimpleDelegate::CreateWeakLambda(this, [this]() { ApplyCommand(EFlowCommand::Back); });

	TSharedPtr<SFlowMenu> Menu;
	switch (Screen)
	{
	case EFlowScreen::Title:
	{
		TArray<FFlowMenuItem> Items;
		Items.Add({ FFlowMenuText::StartGameLabel(), FSimpleDelegate::CreateUObject(this, &AUmbrellaPlayerController::StartGame) });
		Items.Add({ FFlowMenuText::DirectorsCutLabel(), FSimpleDelegate::CreateUObject(this, &AUmbrellaPlayerController::StartDirectorsCut) });
		Menu = SNew(SFlowMenu).WasdNavigation(IsFeatureEnabled(EFeatureId::MOVE_09)).Tuning(Tuning).Heading(FFlowMenuText::TitleHeading()).Items(Items);
		break;
	}
	case EFlowScreen::Paused:
	{
		TArray<FFlowMenuItem> Items;
		Items.Add({ FFlowMenuText::ContinueLabel(), Resume });
		if (IsFeatureEnabled(EFeatureId::FLOW_41))
		{
			Items.Add({ FFlowMenuText::SettingsLabel(), FSimpleDelegate::CreateWeakLambda(this, [this]() { ApplyCommand(EFlowCommand::OpenSettings); }) });
		}
		Items.Add({ FFlowMenuText::QuitLabel(), FSimpleDelegate::CreateUObject(this, &AUmbrellaPlayerController::QuitGame) });
		Menu = SNew(SFlowMenu).WasdNavigation(IsFeatureEnabled(EFeatureId::MOVE_09)).Backdrop(EFlowBackdrop::Clocks).Tuning(Tuning).Heading(FFlowMenuText::PausedHeading()).Items(Items).OnBack(Resume);
		break;
	}
	case EFlowScreen::Purchase:
		ShowPurchaseScreen();
		return;
	case EFlowScreen::Settings:
	{
		OpenSettingsMenu();
		if (bSettingsOpened)
		{
			return;
		}
		TArray<FFlowMenuItem> Items;
		Items.Add({ FFlowMenuText::BackLabel(), Back });
		Menu = SNew(SFlowMenu).WasdNavigation(IsFeatureEnabled(EFeatureId::MOVE_09)).Backdrop(EFlowBackdrop::Clocks).Tuning(Tuning).Heading(FFlowMenuText::SettingsHeading())
			.Body(FFlowMenuText::SettingsStubBody()).Items(Items).OnBack(Back);
		break;
	}
	case EFlowScreen::Tutorial:
	{
		const TArray<FText> Pages = FFlowTutorialText::GetPages(PlayMode);
		TArray<FFlowMenuItem> Items;
		Items.Add({ FText::FromString(FFlowRules::HasTutorialPageAfter(TutorialPage, Pages.Num()) ? TEXT("Next") : TEXT("Begin")),
			FSimpleDelegate::CreateUObject(this, &AUmbrellaPlayerController::AdvanceTutorial) });
		Menu = SNew(SFlowMenu).WasdNavigation(IsFeatureEnabled(EFeatureId::MOVE_09)).Tuning(Tuning).Heading(FFlowTutorialText::GetHeading(PlayMode))
			.Body(Pages.IsValidIndex(TutorialPage) ? Pages[TutorialPage] : FText::GetEmpty()).Items(Items);
		break;
	}
	case EFlowScreen::TutorialPaused:
	{
		TArray<FFlowMenuItem> Items;
		const FSimpleDelegate Skip = FSimpleDelegate::CreateWeakLambda(this, [this]() { ApplyCommand(EFlowCommand::SkipTutorial); });
		Items.Add({ FFlowMenuText::ContinueLabel(), Resume });
		Items.Add({ FFlowMenuText::SkipLabel(), Skip });
		Menu = SNew(SFlowMenu).WasdNavigation(IsFeatureEnabled(EFeatureId::MOVE_09)).Backdrop(EFlowBackdrop::Clocks).Tuning(Tuning).Heading(FFlowMenuText::PausedHeading()).Items(Items).OnBack(Resume);
		break;
	}
	case EFlowScreen::LevelUp:
	{
		TArray<FFlowMenuItem> Items;
		Items.Add({ FFlowMenuText::ContinueLabel(), Resume });
		Menu = SNew(SFlowMenu).WasdNavigation(IsFeatureEnabled(EFeatureId::MOVE_09)).Tuning(Tuning).Heading(FFlowMenuText::LevelUpHeading(LevelUpShown))
			.Body(FFlowMenuText::LevelUpBody()).Items(Items).OnBack(Back);
		break;
	}
	case EFlowScreen::Defeat:
	{
		TArray<FFlowMenuItem> Items;
		Items.Add({ FFlowMenuText::RetryLabel(), FSimpleDelegate::CreateWeakLambda(this, [this]() { ApplyCommand(EFlowCommand::Retry); }) });
		Items.Add({ FFlowMenuText::QuitToTitleLabel(), FSimpleDelegate::CreateUObject(this, &AUmbrellaPlayerController::ReturnToTitle) });
		Menu = SNew(SFlowMenu).WasdNavigation(IsFeatureEnabled(EFeatureId::MOVE_09)).Tuning(Tuning).Heading(FFlowMenuText::DefeatHeading()).HeadingColor(FUmbrellaUIStyle::Warn()).Items(Items);
		break;
	}
	case EFlowScreen::Statistics:
		// Story's Journey Complete widget is the screen; flow only gives it focus (SetInputModeFor).
		return;
	case EFlowScreen::Story:
	case EFlowScreen::Credits:
	{
		if (Screen == EFlowScreen::Story && IsInEndingHold())
		{
			return;
		}
		TextScreen = SNew(SFlowTextScreen).Tuning(Tuning);
		ScreenWidget = TextScreen;
		RefreshTimedText();
		AddViewportWidget(TextScreen.ToSharedRef());
		return;
	}
	case EFlowScreen::Playing:
		if (PlayMode == EUmbrellaPlayMode::DirectorsCut)
		{
			ScreenWidget = SNew(SBox).HAlign(HAlign_Center).VAlign(VAlign_Top).Visibility(EVisibility::HitTestInvisible)
			[
				SNew(STextBlock).Text(FText::FromString(TEXT("Director's Cut")))
					.Font(FUmbrellaUIStyle::DisplayFont(UmbrellaAccessibility::PublishedFontSize(Tuning.MenuFontSize))).ColorAndOpacity(FUmbrellaUIStyle::Gold())
					.ShadowOffset(FVector2D(UmbrellaUIStyleConstants::ShadowOffset, UmbrellaUIStyleConstants::ShadowOffset))
					.ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
			];
			AddViewportWidget(ScreenWidget.ToSharedRef());
		}
		return;
	default:
		return;
	}

	ScreenWidget = Menu;
	AddViewportWidget(Menu.ToSharedRef());
	Menu->FocusFirstItem();
}

void AUmbrellaPlayerController::SetInputModeFor(EFlowScreen To)
{
	if (!GetLocalPlayer() || !GetWorld() || !GetWorld()->GetGameViewport())
	{
		return;
	}
	if (To == EFlowScreen::Playing)
	{
		SetShowMouseCursor(false);
		SetInputMode(FInputModeGameOnly());
		return;
	}
	SetShowMouseCursor(true);
	FInputModeGameAndUI Mode;
	Mode.SetLockMouseToViewportBehavior(EMouseLockMode::DoNotLock);
	Mode.SetHideCursorDuringCapture(false);
	if (ScreenWidget.IsValid())
	{
		Mode.SetWidgetToFocus(ScreenWidget);
	}
	else if (UJourneyCompleteWidget* Statistics = To == EFlowScreen::Statistics && GetStory() ? GetStory()->GetStatisticsWidget() : nullptr)
	{
		Mode.SetWidgetToFocus(Statistics->TakeWidget());
	}
	SetInputMode(Mode);
}

void AUmbrellaPlayerController::SetInputBlocked(bool bBlocked)
{
	bInputBlocked = bBlocked;
	ApplyPawnInputBlock();
}

void AUmbrellaPlayerController::ApplyPawnInputBlock()
{
	// IMC_Menu stays on the stack at menu priority; the pawn's gameplay bindings leave the input stack while a menu is up.
	if (APawn* Controlled = GetPawn())
	{
		if (bInputBlocked)
		{
			Controlled->DisableInput(this);
		}
		else
		{
			Controlled->EnableInput(this);
		}
	}
}

void AUmbrellaPlayerController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);
	ApplyPawnInputBlock();
}

bool AUmbrellaPlayerController::IsAnyNeutralKeyHeld() const
{
	if (!PlayerInput)
	{
		return false;
	}
	for (const FKey& Key : GetNeutralKeys())
	{
		if (PlayerInput->IsPressed(Key))
		{
			return true;
		}
	}
	return false;
}

void AUmbrellaPlayerController::OnPausePressed()
{
	ApplyCommand(EFlowCommand::Pause);
}

void AUmbrellaPlayerController::HandlePlayerDefeated(const FUmbrellaEvent& Event)
{
	ApplyCommand(EFlowCommand::PlayerDefeated);
}

void AUmbrellaPlayerController::HandleEncounterCompleted(const FUmbrellaEvent& Event)
{
	if (IsFeatureEnabled(EFeatureId::FLOW_04))
	{
		ApplyCommand(EFlowCommand::EncounterCompleted);
	}
}

void AUmbrellaPlayerController::OpenSettingsMenu()
{
	bSettingsOpened = false;
	if (UGameInstance* Instance = GetGameInstance())
	{
		if (USettingsMenuSubsystem* Settings = Instance->GetSubsystem<USettingsMenuSubsystem>())
		{
			Settings->OpenSettings(this);
			bSettingsOpened = Settings->IsSettingsOpen();
		}
	}
}

void AUmbrellaPlayerController::CloseSettingsMenu()
{
	if (UGameInstance* Instance = GetGameInstance())
	{
		if (USettingsMenuSubsystem* Settings = Instance->GetSubsystem<USettingsMenuSubsystem>())
		{
			Settings->CloseSettings();
		}
	}
	bSettingsOpened = false;
}

bool AUmbrellaPlayerController::IsSettingsMenuOpen() const
{
	const UGameInstance* Instance = GetGameInstance();
	const USettingsMenuSubsystem* Settings = Instance ? Instance->GetSubsystem<USettingsMenuSubsystem>() : nullptr;
	return Settings && Settings->IsSettingsOpen();
}

void AUmbrellaPlayerController::ReturnToTitle()
{
	bTitleReturnRequested = true;
	if (GetWorld() && GetWorld()->GetGameViewport())
	{
		SetPause(false);
		UGameplayStatics::OpenLevel(this, FName(*UGameplayStatics::GetCurrentLevelName(this)));
	}
}

void AUmbrellaPlayerController::QuitGame()
{
	UKismetSystemLibrary::QuitGame(this, this, EQuitPreference::Quit, false);
}

void AUmbrellaPlayerController::HandleLevelGained(const FUmbrellaEvent& Event)
{
	// Director's Cut only; a level reached while another screen holds the game is not shown late.
	if (IsFeatureEnabled(EFeatureId::FLOW_48) && PlayMode == EUmbrellaPlayMode::DirectorsCut && Screen == EFlowScreen::Playing)
	{
		LevelUpShown = Event.Amount;
		ApplyCommand(EFlowCommand::OpenLevelUp);
	}
}

UStorySubsystem* AUmbrellaPlayerController::GetStory() const
{
	return GetWorld() ? GetWorld()->GetSubsystem<UStorySubsystem>() : nullptr;
}

TArray<FText> AUmbrellaPlayerController::GetEndingPages() const
{
	// Director's Cut shows the story's ending lines (story lane text); Start Game keeps flow's ending pages.
	const UStorySubsystem* Story = PlayMode == EUmbrellaPlayMode::DirectorsCut && IsFeatureEnabled(EFeatureId::NAR_07) ? GetStory() : nullptr;
	const TArray<FString> Lines = Story ? Story->GetEndingLines() : TArray<FString>();
	if (Lines.Num() == 0)
	{
		return FFlowStoryText::GetEndingPages();
	}
	TArray<FText> Pages;
	for (const FString& Line : Lines)
	{
		Pages.Add(FText::FromString(Line));
	}
	return Pages;
}

float AUmbrellaPlayerController::GetEndingPageSeconds() const
{
	const UUmbrellaTuning* Tuning = GetDefault<UUmbrellaTuning>();
	const bool bStoryLines = PlayMode == EUmbrellaPlayMode::DirectorsCut && IsFeatureEnabled(EFeatureId::NAR_07) && GetStory()
		&& GetStory()->GetEndingLines().Num() > 0;
	return bStoryLines ? Tuning->Story.EndingLineSeconds : Tuning->Flow.StoryPageSeconds;
}

bool AUmbrellaPlayerController::IsInEndingHold() const
{
	return Screen == EFlowScreen::Story && IsFeatureEnabled(EFeatureId::NAR_07)
		&& FFlowRules::IsEndingHoldAt(StoryElapsed, GetDefault<UUmbrellaTuning>()->Story.EndingHoldSeconds);
}

void AUmbrellaPlayerController::OnSkipPressed()
{
	PressSkip();
}

void AUmbrellaPlayerController::PressSkip()
{
	UStorySubsystem* Story = GetStory();
	if (!Story)
	{
		return;
	}
	const bool bOpening = Screen == EFlowScreen::Playing && IsFeatureEnabled(EFeatureId::NAR_04);
	const bool bEnding = (Screen == EFlowScreen::Story || Screen == EFlowScreen::Credits) && IsFeatureEnabled(EFeatureId::NAR_07);
	if ((bOpening || bEnding) && Story->IsSkipPressForStory())
	{
		// The press is the story's: the opening clears (once seen before) or the ending skips; nothing reaches play.
		Story->HandleSkipPressed();
	}
	if (bEnding && Story->GetModel().ShouldShowStatistics())
	{
		ApplyCommand(EFlowCommand::ShowStatistics);
	}
}

void AUmbrellaPlayerController::TryAgain()
{
	if (Screen != EFlowScreen::Statistics || !IsFeatureEnabled(EFeatureId::FLOW_49))
	{
		return;
	}
	bTryAgainRequested = true;
	if (GetWorld() && GetWorld()->GetGameViewport())
	{
		SetPause(false);
		UGameplayStatics::OpenLevel(this, FName(*UGameplayStatics::GetCurrentLevelName(this)), true, FFlowRules::TryAgainOption());
	}
}

void AUmbrellaPlayerController::ReturnToTitleFromStatistics()
{
	if (Screen == EFlowScreen::Statistics)
	{
		ReturnToTitle();
	}
}
