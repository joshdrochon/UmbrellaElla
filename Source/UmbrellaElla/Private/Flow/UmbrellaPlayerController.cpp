#include "Flow/UmbrellaPlayerController.h"
#include "Core/UmbrellaEvent.h"
#include "Core/UmbrellaEventBus.h"
#include "Core/UmbrellaGameMode.h"
#include "Core/UmbrellaTuning.h"
#include "Encounter/EncounterDirectorSubsystem.h"
#include "Engine/World.h"
#include "Engine/World.h"
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
#include "Flow/FlowTutorialText.h"
#include "Misc/ConfigCacheIni.h"
#include "Story/FlowStoryText.h"
#include "UI/Menus/FlowMenuWidgets.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Text/STextBlock.h"

// Rule IDs built here: FLOW-02 (two routes), FLOW-04 (win: story, credits), FLOW-34 (Start screen), FLOW-35 (Pause),
// ART-04 (same moving background on Start and End), FLOW-03 (first-start tutorial, Pause then Skip). Each is checked through IsFeatureEnabled below.

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
	MenuContext->MapKey(PauseAction, EKeys::F1);
	MenuContext->MapKey(PauseAction, EKeys::Gamepad_Special_Right);

	if (UEnhancedInputComponent* Input = Cast<UEnhancedInputComponent>(InputComponent))
	{
		Input->BindAction(PauseAction, ETriggerEvent::Triggered, this, &AUmbrellaPlayerController::OnPausePressed);
	}
}

void AUmbrellaPlayerController::BeginPlay()
{
	Super::BeginPlay();

	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		DefeatHandle = Bus->On(EUmbrellaEventType::PlayerDefeated).AddUObject(this, &AUmbrellaPlayerController::HandlePlayerDefeated);
		CompletedHandle = Bus->On(EUmbrellaEventType::EncounterCompleted).AddUObject(this, &AUmbrellaPlayerController::HandleEncounterCompleted);
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
}

void AUmbrellaPlayerController::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
	if (UUmbrellaEventBus* Bus = UUmbrellaEventBus::Get(this))
	{
		Bus->On(EUmbrellaEventType::PlayerDefeated).Remove(DefeatHandle);
		Bus->On(EUmbrellaEventType::EncounterCompleted).Remove(CompletedHandle);
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

void AUmbrellaPlayerController::BeginRun()
{
	if (bRunBegun)
	{
		return;
	}
	bRunBegun = true;
	if (AUmbrellaGameMode* Fight = GetWorld()->GetAuthGameMode<AUmbrellaGameMode>())
	{
		Fight->BeginFight(this);
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

	NeutralSeconds = 0.0f;
	StoryElapsed = To == EFlowScreen::Story ? 0.0f : StoryElapsed;
	CreditsElapsed = To == EFlowScreen::Credits ? 0.0f : CreditsElapsed;

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
		}
	}

	ApplyPawnInputBlock();
	ShowScreenWidget();
	SetInputModeFor(To);

	if (From == EFlowScreen::Credits && To == EFlowScreen::Title)
	{
		ReturnToTitle();
	}
}

void AUmbrellaPlayerController::TickFlow(float DeltaSeconds)
{
	const UUmbrellaTuning* Tuning = GetDefault<UUmbrellaTuning>();
	switch (Screen)
	{
	case EFlowScreen::Resuming:
		NeutralSeconds = FFlowRules::AdvanceNeutral(NeutralSeconds, DeltaSeconds, IsAnyNeutralKeyHeld());
		if (NeutralSeconds >= Tuning->Flow.ResumeNeutralSeconds)
		{
			ApplyCommand(EFlowCommand::NeutralReached);
		}
		break;
	case EFlowScreen::Story:
		StoryElapsed += DeltaSeconds;
		if (FFlowRules::StoryPageAt(StoryElapsed, Tuning->Flow.StoryPageSeconds, FFlowStoryText::GetEndingPages().Num()) == INDEX_NONE)
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
			ApplyCommand(EFlowCommand::TimelineDone);
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

void AUmbrellaPlayerController::RefreshTimedText()
{
	if (!TextScreen.IsValid())
	{
		return;
	}
	const FFlowTuning& Tuning = GetDefault<UUmbrellaTuning>()->Flow;
	if (Screen == EFlowScreen::Story)
	{
		const TArray<FText> Pages = FFlowStoryText::GetEndingPages();
		const int32 Page = FFlowRules::StoryPageAt(StoryElapsed, Tuning.StoryPageSeconds, Pages.Num());
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
		TextScreen->SetText(FText::FromString(FString::Join(Lines, TEXT("\n\n"))), FMath::Lerp(-Tuning.CreditsTravel, Tuning.CreditsTravel, Progress));
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
		Items.Add({ FText::FromString(TEXT("Start Game")), FSimpleDelegate::CreateUObject(this, &AUmbrellaPlayerController::StartGame) });
		Items.Add({ FText::FromString(TEXT("Start Director's Cut")), FSimpleDelegate::CreateUObject(this, &AUmbrellaPlayerController::StartDirectorsCut) });
		Menu = SNew(SFlowMenu).Tuning(Tuning).Heading(FText::FromString(TEXT("Umbrella Ella"))).Items(Items);
		break;
	}
	case EFlowScreen::Paused:
	{
		TArray<FFlowMenuItem> Items;
		Items.Add({ FText::FromString(TEXT("Continue")), Resume });
		Items.Add({ FText::FromString(TEXT("Settings")), FSimpleDelegate::CreateWeakLambda(this, [this]() { ApplyCommand(EFlowCommand::OpenSettings); }) });
		Items.Add({ FText::FromString(TEXT("Quit")), FSimpleDelegate::CreateUObject(this, &AUmbrellaPlayerController::QuitGame) });
		Menu = SNew(SFlowMenu).Backdrop(EFlowBackdrop::Clocks).Tuning(Tuning).Heading(FText::FromString(TEXT("Paused"))).Items(Items).OnBack(Resume);
		break;
	}
	case EFlowScreen::Settings:
	{
		TArray<FFlowMenuItem> Items;
		Items.Add({ FText::FromString(TEXT("Back")), Back });
		Menu = SNew(SFlowMenu).Backdrop(EFlowBackdrop::Clocks).Tuning(Tuning).Heading(FText::FromString(TEXT("Settings")))
			.Body(FText::FromString(TEXT("Sound, Controller and Credits arrive in the next slice."))).Items(Items).OnBack(Back);
		break;
	}
	case EFlowScreen::Tutorial:
	{
		const TArray<FText> Pages = FFlowTutorialText::GetPages(PlayMode);
		TArray<FFlowMenuItem> Items;
		Items.Add({ FText::FromString(FFlowRules::HasTutorialPageAfter(TutorialPage, Pages.Num()) ? TEXT("Next") : TEXT("Begin")),
			FSimpleDelegate::CreateUObject(this, &AUmbrellaPlayerController::AdvanceTutorial) });
		Menu = SNew(SFlowMenu).Tuning(Tuning).Heading(FFlowTutorialText::GetHeading(PlayMode))
			.Body(Pages.IsValidIndex(TutorialPage) ? Pages[TutorialPage] : FText::GetEmpty()).Items(Items);
		break;
	}
	case EFlowScreen::TutorialPaused:
	{
		TArray<FFlowMenuItem> Items;
		const FSimpleDelegate Skip = FSimpleDelegate::CreateWeakLambda(this, [this]() { ApplyCommand(EFlowCommand::SkipTutorial); });
		Items.Add({ FText::FromString(TEXT("Continue")), Resume });
		Items.Add({ FText::FromString(TEXT("Skip")), Skip });
		Menu = SNew(SFlowMenu).Backdrop(EFlowBackdrop::Clocks).Tuning(Tuning).Heading(FText::FromString(TEXT("Paused"))).Items(Items).OnBack(Resume);
		break;
	}
	case EFlowScreen::Defeat:
	{
		TArray<FFlowMenuItem> Items;
		Items.Add({ FText::FromString(TEXT("Retry")), FSimpleDelegate::CreateWeakLambda(this, [this]() { ApplyCommand(EFlowCommand::Retry); }) });
		Items.Add({ FText::FromString(TEXT("Quit to Title")), FSimpleDelegate::CreateUObject(this, &AUmbrellaPlayerController::ReturnToTitle) });
		Menu = SNew(SFlowMenu).Tuning(Tuning).Heading(FText::FromString(TEXT("Defeated"))).Items(Items);
		break;
	}
	case EFlowScreen::Story:
	case EFlowScreen::Credits:
	{
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
					.Font(FCoreStyle::GetDefaultFontStyle(TEXT("Bold"), Tuning.MenuFontSize)).ColorAndOpacity(Tuning.TextColor)
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
