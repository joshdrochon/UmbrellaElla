#include "UI/Progression/ProgressionPurchaseWidget.h"
#include "Core/UmbrellaPlayMode.h"
#include "Flow/FlowMenuText.h"
#include "Flow/FlowRules.h"
#include "Flow/UmbrellaPlayerController.h"
#include "GameFramework/PlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Progression/ProgressionSubsystem.h"
#include "UI/Style/UmbrellaUIStyle.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/Layout/SScaleBox.h"
#include "Widgets/SOverlay.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

#if UMBRELLAELLA_WORKBENCH && !UE_BUILD_SHIPPING
#include "Attack/AttackEmitterComponent.h"
#include "Core/EllaCharacter.h"
#include "Core/UmbrellaLog.h"
#include "Engine/Engine.h"
#include "Engine/GameViewportClient.h"
#include "Engine/World.h"
#include "Framework/Application/SlateApplication.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Story/StoryRules.h"
#include "Story/StorySubsystem.h"
#include "Widgets/SWindow.h"

// Workbench-only proof hooks for B9 (journey `console` lines; never in the packaged game):
//  Umbrella.Progression.ShadowLevel levelN  the developer level fixture on shadow progress (nothing saved), so a
//                                        Director's Cut start opens the purchase screen with points to spend.
//  Umbrella.Progression.ClickDone        a real mouse click (move, press, release through FSlateApplication) at the
//                                        centre of the purchase screen's Done button; logs PROGRESSION_DONE_CLICK with
//                                        Done's window rect, the widget Slate finds under that point and the screen
//                                        before and after.
//  Umbrella.Progression.LogRunStats      the Journey Complete run statistics as story counts them now, next to the
//                                        shots Ella's attack component emitted (lead order: "Shots fired 0" after J held).
namespace ProgressionPurchaseProof
{
	AUmbrellaPlayerController* FlowOf(UWorld* World)
	{
		return World ? Cast<AUmbrellaPlayerController>(UGameplayStatics::GetPlayerController(World, 0)) : nullptr;
	}

	FString ScreenName(const AUmbrellaPlayerController* Flow)
	{
		return Flow ? StaticEnum<EFlowScreen>()->GetNameStringByValue(static_cast<int64>(Flow->GetScreen())) : FString(TEXT("none"));
	}

	void ShadowLevel(const TArray<FString>& Args, UWorld* World)
	{
		UProgressionSubsystem* Subsystem = World ? UProgressionSubsystem::Get(World) : nullptr;
		// "level10" or "10": the journey parser keeps trailing numbers for itself, so a word with digits passes the level.
		FString Digits;
		for (const TCHAR Char : (Args.Num() > 0 ? Args[0] : FString()))
		{
			if (FChar::IsDigit(Char))
			{
				Digits.AppendChar(Char);
			}
		}
		const int32 Level = FCString::Atoi(*Digits);
		if (Subsystem != nullptr && Level > 0)
		{
			Subsystem->BeginShadowProgress(Level);
		}
		UE_LOG(LogUmbrellaElla, Display, TEXT("PROGRESSION_SHADOW_LEVEL want=%d level=%d unspent=%d"), Level,
			Subsystem ? Subsystem->GetLevel() : -1, Subsystem ? Subsystem->GetUnspentPoints() : -1);
	}

	void ClickDone(const TArray<FString>& Args, UWorld* World)
	{
		AUmbrellaPlayerController* Flow = FlowOf(World);
		const UProgressionPurchaseWidget* Screen = Flow ? Flow->GetPurchaseWidget() : nullptr;
		const TSharedPtr<SWidget> Done = Screen ? Screen->GetDoneButton() : nullptr;
		const TSharedPtr<SWindow> Window = GEngine && GEngine->GameViewport ? GEngine->GameViewport->GetWindow() : nullptr;
		if (!Done.IsValid() || !Window.IsValid() || !FSlateApplication::IsInitialized())
		{
			UE_LOG(LogUmbrellaElla, Display, TEXT("PROGRESSION_DONE_CLICK ok=0 reason=no_done_button screen=%s"), *ScreenName(Flow));
			return;
		}
		const FGeometry Geometry = Done->GetTickSpaceGeometry();
		const FVector2D Centre = Geometry.GetAbsolutePositionAtCoordinates(FVector2D(0.5, 0.5));
		const FVector2D TopLeft = Geometry.GetAbsolutePosition() - Window->GetPositionInScreen();
		const FVector2D Extent = Geometry.GetAbsoluteSize();
		const FVector2D Client = Window->GetClientSizeInScreen();
		FSlateApplication& Slate = FSlateApplication::Get();
		const FWidgetPath Under = Slate.LocateWindowUnderMouse(Centre, Slate.GetInteractiveTopLevelWindows());
		bool bOnDone = false;
		for (int32 Index = 0; Under.IsValid() && Index < Under.Widgets.Num(); ++Index)
		{
			bOnDone = bOnDone || Under.Widgets[Index].Widget == Done;
		}
		const FString UnderName = Under.IsValid() ? Under.GetLastWidget()->GetTypeAsString() : FString(TEXT("none"));
		const FString Before = ScreenName(Flow);
		const TSet<FKey> NoKeys;
		TSet<FKey> Left;
		Left.Add(EKeys::LeftMouseButton);
		Slate.ProcessMouseMoveEvent(FPointerEvent(0, Centre, Centre, NoKeys, FKey(), 0.0f, FModifierKeysState()));
		Slate.ProcessMouseButtonDownEvent(Window->GetNativeWindow(), FPointerEvent(0, Centre, Centre, Left, EKeys::LeftMouseButton, 0.0f, FModifierKeysState()));
		Slate.ProcessMouseButtonUpEvent(FPointerEvent(0, Centre, Centre, NoKeys, EKeys::LeftMouseButton, 0.0f, FModifierKeysState()));
		const FString After = ScreenName(Flow);
		const bool bInside = TopLeft.X >= 0.0 && TopLeft.Y >= 0.0 && TopLeft.X + Extent.X <= Client.X && TopLeft.Y + Extent.Y <= Client.Y;
		const bool bLeft = After != Before;
		UE_LOG(LogUmbrellaElla, Display, TEXT("PROGRESSION_DONE_CLICK ok=%d window=%.0fx%.0f done_rect=%.0f,%.0f,%.0fx%.0f inside=%d under=%s on_done=%d before=%s after=%s"),
			(bInside && bOnDone && bLeft) ? 1 : 0, Client.X, Client.Y, TopLeft.X, TopLeft.Y, Extent.X, Extent.Y, bInside ? 1 : 0, *UnderName, bOnDone ? 1 : 0, *Before, *After);
	}

	void LogRunStats(const TArray<FString>& Args, UWorld* World)
	{
		const UStorySubsystem* Story = World ? World->GetSubsystem<UStorySubsystem>() : nullptr;
		const AUmbrellaPlayerController* Flow = FlowOf(World);
		const AEllaCharacter* Ella = Flow ? Cast<AEllaCharacter>(Flow->GetPawn()) : nullptr;
		const int32 Emitted = Ella && Ella->GetAttack() ? Ella->GetAttack()->GetShotsFired() : -1;
		if (Story == nullptr)
		{
			UE_LOG(LogUmbrellaElla, Display, TEXT("PROGRESSION_RUN_STATS ok=0 reason=no_story emitted=%d"), Emitted);
			return;
		}
		const FStoryRunStats& Stats = Story->GetModel().GetStats();
		UE_LOG(LogUmbrellaElla, Display, TEXT("PROGRESSION_RUN_STATS ok=%d shots_fired=%d shots_fired_at_you=%d attack_emitted=%d screen=%s"),
			(Stats.ShotsFired > 0 && Stats.ShotsFired <= Emitted) ? 1 : 0, Stats.ShotsFired, Stats.ShotsFiredAtYou, Emitted, *ScreenName(Flow));
	}

	FAutoConsoleCommandWithWorldAndArgs RunStatsCommand(TEXT("Umbrella.Progression.LogRunStats"),
		TEXT("Workbench: log the Journey Complete run statistics next to Ella's emitted shots."), FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&LogRunStats));
	FAutoConsoleCommandWithWorldAndArgs ShadowLevelCommand(TEXT("Umbrella.Progression.ShadowLevel"),
		TEXT("Workbench: developer level fixture on shadow progress (B9 proof)."), FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&ShadowLevel));
	FAutoConsoleCommandWithWorldAndArgs ClickDoneCommand(TEXT("Umbrella.Progression.ClickDone"),
		TEXT("Workbench: a real mouse click on the purchase screen's Done button, measured (B9 proof)."), FConsoleCommandWithWorldAndArgsDelegate::CreateStatic(&ClickDone));
}
#endif

#define LOCTEXT_NAMESPACE "ProgressionPurchase"

UProgressionPurchaseWidget* UProgressionPurchaseWidget::Show(APlayerController* Owner)
{
	if (Owner == nullptr || !IsFeatureEnabled(EFeatureId::FLOW_42))
	{
		return nullptr;
	}
	const UProgressionSubsystem* Subsystem = UProgressionSubsystem::Get(Owner);
	if (Subsystem == nullptr || Subsystem->GetPlayMode() != EUmbrellaPlayMode::DirectorsCut)
	{
		return nullptr;
	}
	UProgressionPurchaseWidget* Screen = CreateWidget<UProgressionPurchaseWidget>(Owner);
	if (Screen != nullptr)
	{
		Screen->AddToViewport();
	}
	return Screen;
}

void UProgressionPurchaseWidget::NativeConstruct()
{
	Super::NativeConstruct();
	Progression = UProgressionSubsystem::Get(GetOwningPlayer());
	if (UProgressionSubsystem* Subsystem = Progression.Get())
	{
		ChangedHandle = Subsystem->OnChanged().AddUObject(this, &UProgressionPurchaseWidget::OnProgressionChanged);
		Draft = FProgressionDraft::Begin(Subsystem->GetEffectiveProfile());
		LastContext = Subsystem->GetPurchaseContext().Kind;
	}
	Rebuild();
}

void UProgressionPurchaseWidget::NativeDestruct()
{
	if (UProgressionSubsystem* Subsystem = Progression.Get())
	{
		Subsystem->OnChanged().Remove(ChangedHandle);
	}
	Super::NativeDestruct();
}

void UProgressionPurchaseWidget::OnProgressionChanged()
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	if (Subsystem == nullptr)
	{
		return;
	}
	if (Subsystem->GetPurchaseContext().Kind != LastContext || !Subsystem->CanPurchaseNow())
	{
		// A context change discards an unconfirmed draft.
		LastContext = Subsystem->GetPurchaseContext().Kind;
		Draft.Discard(Subsystem->GetEffectiveProfile());
	}
	else if (!IsDraftDirty())
	{
		Draft = FProgressionDraft::Begin(Subsystem->GetEffectiveProfile());
	}
	Rebuild();
}

FText UProgressionPurchaseWidget::TrackLabel(EProgressionTrack Track)
{
	switch (Track)
	{
	case EProgressionTrack::HitCapacity:
		return LOCTEXT("HitCapacity", "Hits per life");
	case EProgressionTrack::Lives:
		return LOCTEXT("Lives", "Lives");
	case EProgressionTrack::Recovery:
		return LOCTEXT("Recovery", "Recovery per yellow");
	case EProgressionTrack::DamageReduction:
		return LOCTEXT("DamageReduction", "Damage reduction");
	case EProgressionTrack::SuctionRange:
		return LOCTEXT("SuctionRange", "Suction range");
	case EProgressionTrack::SuctionCone:
		return LOCTEXT("SuctionCone", "Suction cone");
	case EProgressionTrack::DamageSmall:
		return LOCTEXT("DamageSmall", "Small Blasts damage");
	case EProgressionTrack::DamageStreamed:
		return LOCTEXT("DamageStreamed", "Streamed Blast damage");
	case EProgressionTrack::DamageTwin:
		return LOCTEXT("DamageTwin", "Twin Stars damage");
	default:
		return LOCTEXT("DamageNeedle", "Needle Spell damage");
	}
}

TSharedRef<SWidget> UProgressionPurchaseWidget::RebuildWidget()
{
	Rows = SNew(SVerticalBox);
	Rebuild();
	return SNew(SOverlay)
		+ SOverlay::Slot()
		[
			SNew(SUmbrellaGround)
		]
		// B9 (agentplay, 640x360): the panel grew past the screen's bottom edge and covered the Done button. It now fills
		// the screen's height at most (scaled down, never up), and Done lives in its own button row, so it is always on
		// screen and on top at every size.
		+ SOverlay::Slot().HAlign(HAlign_Fill).VAlign(VAlign_Fill)
			.Padding(UmbrellaUI::ColumnLeft - UmbrellaUI::PanelPadding, UmbrellaUI::SectionGap, 0.0f, UmbrellaUI::SectionGap)
		[
			SNew(SScaleBox)
			.HAlign(HAlign_Left)
			.VAlign(VAlign_Center)
			.Stretch(EStretch::ScaleToFit)
			.StretchDirection(EStretchDirection::DownOnly)
			[
				SNew(SBorder)
				.BorderImage(FUmbrellaUIStyle::PanelBrush())
				.Padding(UmbrellaUI::PanelPadding)
				[
					SNew(SBox).WidthOverride(UmbrellaUI::ColumnWidth)
					[
						Rows.ToSharedRef()
					]
				]
			]
		];
}

void UProgressionPurchaseWidget::Rebuild()
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	if (!Rows.IsValid() || Subsystem == nullptr)
	{
		return;
	}
	Rows->ClearChildren();
	const FProgressionTuning& Tuning = Subsystem->GetTuning();
	const FProgressionProfile Real = Subsystem->GetEffectiveProfile();
	const int32 Spare = FProgressionRules::UnspentPoints(Tuning, Real) - GetDraftNetCost();
	const FSlateFontInfo Body = FUmbrellaUIStyle::BodyFont(UmbrellaUI::PurchaseRowTextSize);

	Rows->AddSlot().AutoHeight()
	[
		SNew(STextBlock).Font(FUmbrellaUIStyle::DisplayFont(UmbrellaUI::PurchaseHeadingTextSize)).ColorAndOpacity(FUmbrellaUIStyle::Cream())
			.Text(FText::Format(LOCTEXT("Header", "Level {0}   Points left {1}"), Subsystem->GetLevel(), Spare))
	];
	Rows->AddSlot().AutoHeight().Padding(0.0f, UmbrellaUI::HeadingGap, 0.0f, UmbrellaUI::HeadingGap)
	[
		SNew(SUmbrellaRule)
	];
	if (IsInspectionOnly())
	{
		Rows->AddSlot().AutoHeight().Padding(0.0f, 0.0f, 0.0f, UmbrellaUI::HeadingGap)
		[
			SNew(STextBlock).Font(Body).ColorAndOpacity(FUmbrellaUIStyle::Dim()).AutoWrapText(true)
				.Text(LOCTEXT("Inspect", "Inspection only. Spend points at a refuge or between runs."))
		];
	}
	for (int32 Index = 0; Index < static_cast<int32>(EProgressionTrack::Count); ++Index)
	{
		const EProgressionTrack Track = static_cast<EProgressionTrack>(Index);
		const int32 Rank = GetDraftRank(Track);
		const int32 Max = FProgressionRules::TrackMaxRank(Tuning, Track);
		Rows->AddSlot().AutoHeight()
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().FillWidth(1.0f).VAlign(VAlign_Center)
			[
				SNew(STextBlock).Font(Body).ColorAndOpacity(FUmbrellaUIStyle::Cream())
					.Text(FText::Format(LOCTEXT("Row", "{0}: {1} / {2}"), TrackLabel(Track), Rank, Max))
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(SUmbrellaButton).IsEnabled(!IsInspectionOnly()).Text(LOCTEXT("Minus", "-")).FontSize(UmbrellaUI::PurchaseStepTextSize).RestColor(FUmbrellaUIStyle::Gold())
					.OnClicked_Lambda([this, Track]() { StageRefund(Track); return FReply::Handled(); })
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(SUmbrellaButton).IsEnabled(!IsInspectionOnly()).Text(LOCTEXT("Plus", "+")).FontSize(UmbrellaUI::PurchaseStepTextSize).RestColor(FUmbrellaUIStyle::Gold())
					.OnClicked_Lambda([this, Track]() { StageBuy(Track); return FReply::Handled(); })
			]
		];
	}
	const TArray<FProgressionReviewLine> Review = GetReviewLines();
	if (Review.Num() > 0)
	{
		Rows->AddSlot().AutoHeight().Padding(0.0f, UmbrellaUI::HeadingGap, 0.0f, 0.0f)
		[
			SNew(STextBlock).Font(Body).ColorAndOpacity(FUmbrellaUIStyle::Gold())
				.Text(FText::Format(LOCTEXT("ReviewHead", "Review: {0} points in total"), GetDraftNetCost()))
		];
		for (const FProgressionReviewLine& Line : Review)
		{
			Rows->AddSlot().AutoHeight()
			[
				SNew(STextBlock).Font(Body).ColorAndOpacity(FUmbrellaUIStyle::Cream()).AutoWrapText(true).Text(ReviewLineText(Line))
			];
		}
	}
	Rows->AddSlot().AutoHeight().Padding(0.0f, UmbrellaUI::HeadingGap, 0.0f, 0.0f)
	[
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth().Padding(0.0f, 0.0f, UmbrellaUI::SectionGap, 0.0f)
		[
			SNew(SUmbrellaButton).IsEnabled(IsDraftDirty()).FontSize(UmbrellaUI::PurchaseRowTextSize)
				.Text(FText::Format(LOCTEXT("Confirm", "Confirm ({0} points)"), GetDraftNetCost()))
				.OnClicked_Lambda([this]() { Confirm(); return FReply::Handled(); })
		]
		+ SHorizontalBox::Slot().AutoWidth().Padding(0.0f, 0.0f, UmbrellaUI::SectionGap, 0.0f)
		[
			SNew(SUmbrellaButton).FontSize(UmbrellaUI::PurchaseRowTextSize).Text(LOCTEXT("Cancel", "Cancel"))
				.OnClicked_Lambda([this]() { Cancel(); return FReply::Handled(); })
		]
		+ SHorizontalBox::Slot().AutoWidth()
		[
			SAssignNew(DoneButton, SUmbrellaButton).FontSize(UmbrellaUI::PurchaseRowTextSize).Text(FFlowMenuText::DoneLabel())
				.OnClicked_Lambda([this]() { Done(); return FReply::Handled(); })
		]
	];
}

void UProgressionPurchaseWidget::Done()
{
	// Leaves the screen the way the flow's own Done does (an unconfirmed draft is discarded when the screen closes).
	if (AUmbrellaPlayerController* Flow = Cast<AUmbrellaPlayerController>(GetOwningPlayer()))
	{
		Flow->ApplyCommand(EFlowCommand::Continue);
	}
}

void UProgressionPurchaseWidget::StageBuy(EProgressionTrack Track)
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	if (Subsystem != nullptr && Subsystem->CanPurchaseNow())
	{
		Draft.Stage(Subsystem->GetTuning(), Subsystem->GetEffectiveProfile(), Subsystem->GetPurchaseContext(), Track, 1);
		Rebuild();
	}
}

void UProgressionPurchaseWidget::StageRefund(EProgressionTrack Track)
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	if (Subsystem != nullptr && Subsystem->CanPurchaseNow())
	{
		Draft.Stage(Subsystem->GetTuning(), Subsystem->GetEffectiveProfile(), Subsystem->GetPurchaseContext(), Track, -1);
		Rebuild();
	}
}

EProgressionCommit UProgressionPurchaseWidget::Confirm()
{
	UProgressionSubsystem* Subsystem = Progression.Get();
	if (Subsystem == nullptr)
	{
		return EProgressionCommit::InvalidRanks;
	}
	const EProgressionCommit Result = Subsystem->CommitRanks(Draft.Ranks);
	if (Result == EProgressionCommit::Ok)
	{
		Draft = FProgressionDraft::Begin(Subsystem->GetEffectiveProfile());
	}
	Rebuild();
	return Result;
}

void UProgressionPurchaseWidget::Cancel()
{
	if (const UProgressionSubsystem* Subsystem = Progression.Get())
	{
		Draft.Discard(Subsystem->GetEffectiveProfile());
	}
	Rebuild();
}

bool UProgressionPurchaseWidget::IsDraftDirty() const
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	return Subsystem != nullptr && Draft.IsDirty(Subsystem->GetEffectiveProfile());
}

int32 UProgressionPurchaseWidget::GetDraftNetCost() const
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	return Subsystem != nullptr ? Draft.NetCost(Subsystem->GetTuning(), Subsystem->GetEffectiveProfile()) : 0;
}

int32 UProgressionPurchaseWidget::GetDraftRank(EProgressionTrack Track) const
{
	return FProgressionRules::RankOf(Draft.Ranks, Track);
}

bool UProgressionPurchaseWidget::IsInspectionOnly() const
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	return Subsystem == nullptr || !Subsystem->CanPurchaseNow();
}

TArray<FProgressionReviewLine> UProgressionPurchaseWidget::GetReviewLines() const
{
	const UProgressionSubsystem* Subsystem = Progression.Get();
	return Subsystem != nullptr ? Draft.Review(Subsystem->GetTuning(), Subsystem->GetEffectiveProfile()) : TArray<FProgressionReviewLine>();
}

FText UProgressionPurchaseWidget::ReviewLineText(const FProgressionReviewLine& Line)
{
	FNumberFormattingOptions Format;
	Format.MaximumFractionalDigits = 2;
	const FText Points = FMath::Abs(Line.Cost) == 1 ? LOCTEXT("Point", "point") : LOCTEXT("Points", "points");
	const FText Verb = Line.Cost >= 0 ? LOCTEXT("Costs", "Cost") : LOCTEXT("Reallocates", "Reallocation");
	return FText::Format(LOCTEXT("ReviewLine", "{0} {1} to {2}: {3} to {4}, {5}: {6} {7}"), TrackLabel(Line.Track), Line.FromRank, Line.ToRank,
		FText::AsNumber(Line.ValueBefore, &Format), FText::AsNumber(Line.ValueAfter, &Format), Verb, FMath::Abs(Line.Cost), Points);
}

#undef LOCTEXT_NAMESPACE
