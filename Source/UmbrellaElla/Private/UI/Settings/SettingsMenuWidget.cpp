#include "UI/Settings/SettingsMenuWidget.h"
#include "Framework/Application/SlateApplication.h"
#include "GameFramework/PlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Settings/DeveloperOptions.h"
#include "Settings/SettingsConstants.h"
#include "Settings/SettingsLiveTuning.h"
#include "Settings/SettingsMenuSubsystem.h"
#include "Settings/UmbrellaAccessibility.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/Input/SCheckBox.h"
#include "Widgets/Input/SSlider.h"
#include "Widgets/Layout/SBorder.h"
#include "Widgets/Layout/SBox.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/SNullWidget.h"
#include "Widgets/Text/STextBlock.h"

#define LOCTEXT_NAMESPACE "UmbrellaSettingsMenu"

namespace
{
	enum class ESliderId : uint8
	{
		Master,
		Sfx,
		Music,
		TextScale
	};

	FLinearColor Sepia()
	{
		return FLinearColor(SettingsLayout::TextSepia[0], SettingsLayout::TextSepia[1], SettingsLayout::TextSepia[2]);
	}

	FLinearColor Gold()
	{
		return FLinearColor(SettingsLayout::GoldAccent[0], SettingsLayout::GoldAccent[1], SettingsLayout::GoldAccent[2]);
	}

	FLinearColor Warn()
	{
		return FLinearColor(SettingsLayout::WarnRed[0], SettingsLayout::WarnRed[1], SettingsLayout::WarnRed[2]);
	}

	FSlateFontInfo Font(int32 Size)
	{
		return FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), Size);
	}

	int32 SliderValue(const FUmbrellaSettingsData& Data, ESliderId Id)
	{
		switch (Id)
		{
		case ESliderId::Master:
			return Data.MasterVolume;
		case ESliderId::Sfx:
			return Data.SfxVolume;
		case ESliderId::Music:
			return Data.MusicVolume;
		default:
			return Data.TextScalePercent;
		}
	}

	void SetSliderValue(FSettingsSession& Session, ESliderId Id, int32 Value)
	{
		switch (Id)
		{
		case ESliderId::Master:
			Session.SetMasterVolume(Value);
			break;
		case ESliderId::Sfx:
			Session.SetSfxVolume(Value);
			break;
		case ESliderId::Music:
			Session.SetMusicVolume(Value);
			break;
		default:
			Session.SetTextScalePercent(Value);
			break;
		}
	}

	int32 SliderLow(ESliderId Id)
	{
		return Id == ESliderId::TextScale ? SettingsConstants::TextScaleMin : SettingsConstants::SliderMin;
	}

	int32 SliderHigh(ESliderId Id)
	{
		return Id == ESliderId::TextScale ? SettingsConstants::TextScaleMax : SettingsConstants::SliderMax;
	}

	FText PageName(ESettingsPage Page)
	{
		switch (Page)
		{
		case ESettingsPage::Sound:
			return LOCTEXT("PageSound", "Sound");
		case ESettingsPage::Controller:
			return LOCTEXT("PageController", "Controller");
		case ESettingsPage::Credits:
			return LOCTEXT("PageCredits", "Credits");
		default:
			return LOCTEXT("PageGameOptions", "Game Options");
		}
	}

	TSharedRef<SWidget> Label(const FText& Text, int32 Size, const FLinearColor& Color)
	{
		return SNew(STextBlock).Text(Text).Font(Font(Size)).ColorAndOpacity(Color).AutoWrapText(true);
	}
}

void USettingsMenuWidget::Setup(USettingsMenuSubsystem* InOwner, EUmbrellaPlayMode InMode)
{
	Owner = InOwner;
	Mode = InMode;
	SetIsFocusable(true);
	const TArray<ESettingsPage> Pages = SettingsRules::GetPages(Mode);
	Page = Pages.Num() > 0 ? Pages[0] : ESettingsPage::Sound;
}

int32 USettingsMenuWidget::ScaledFont(int32 Size) const
{
	const USettingsMenuSubsystem* Subsystem = Owner.Get();
	if (!Subsystem || !IsFeatureEnabled(EFeatureId::FLOW_45))
	{
		return Size;
	}
	return UmbrellaAccessibility::ScaledFontSize(Size, Subsystem->GetSavedTextScalePercent());
}

TSharedRef<SWidget> USettingsMenuWidget::RebuildWidget()
{
	BodyBox = SNew(SVerticalBox);
	FooterBox = SNew(SVerticalBox);

	TSharedRef<SHorizontalBox> Tabs = SNew(SHorizontalBox);
	for (const ESettingsPage TabPage : SettingsRules::GetPages(Mode))
	{
		Tabs->AddSlot()
			.AutoWidth()
			.Padding(SettingsLayout::RowPadding)
			[
				SNew(SButton)
				.OnClicked(FOnClicked::CreateWeakLambda(this, [this, TabPage]()
				{
					ShowPage(TabPage);
					return FReply::Handled();
				}))
				[
					Label(PageName(TabPage), ScaledFont(SettingsLayout::BodyFontSize), Sepia())
				]
			];
	}

	RebuildBody();

	return SNew(SBox)
		.HAlign(HAlign_Center)
		.VAlign(VAlign_Center)
		[
			SNew(SBorder)
			.BorderImage(FCoreStyle::Get().GetBrush(TEXT("GenericWhiteBox")))
			.BorderBackgroundColor(FLinearColor(SettingsLayout::PanelDim, SettingsLayout::PanelDim, SettingsLayout::PanelDim, SettingsLayout::PanelAlpha))
			.Padding(SettingsLayout::Padding)
			[
				SNew(SBox)
				.WidthOverride(SettingsLayout::PanelWidth)
				[
					SNew(SVerticalBox)
					+ SVerticalBox::Slot().AutoHeight().Padding(SettingsLayout::RowPadding)
					[
						Label(LOCTEXT("Title", "Settings"), ScaledFont(SettingsLayout::TitleFontSize), Gold())
					]
					+ SVerticalBox::Slot().AutoHeight()
					[
						Tabs
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(SettingsLayout::RowPadding)
					[
						BodyBox.ToSharedRef()
					]
					+ SVerticalBox::Slot().AutoHeight().Padding(SettingsLayout::RowPadding)
					[
						FooterBox.ToSharedRef()
					]
				]
			]
		];
}

void USettingsMenuWidget::ReleaseSlateResources(bool bReleaseChildren)
{
	BodyBox.Reset();
	FooterBox.Reset();
	Super::ReleaseSlateResources(bReleaseChildren);
}

void USettingsMenuWidget::RebuildBody()
{
	if (!BodyBox.IsValid() || !FooterBox.IsValid())
	{
		return;
	}
	BodyBox->ClearChildren();
	FooterBox->ClearChildren();
	switch (Page)
	{
	case ESettingsPage::Sound:
		AddSoundBody();
		break;
	case ESettingsPage::Controller:
		AddControllerBody();
		break;
	case ESettingsPage::Credits:
		AddCreditsBody();
		break;
	default:
		AddGameOptionsBody();
		break;
	}

	const int32 Size = ScaledFont(SettingsLayout::BodyFontSize);
	TSharedRef<SHorizontalBox> Buttons = SNew(SHorizontalBox);
	if (bSaveFailed && IsFeatureEnabled(EFeatureId::FLOW_43))
	{
		Buttons->AddSlot().AutoWidth().Padding(SettingsLayout::RowPadding)
		[
			Label(LOCTEXT("SaveFailed", "Could not save your settings."), Size, Warn())
		];
	}
	if (bBackPrompt)
	{
		Buttons->AddSlot().AutoWidth().Padding(SettingsLayout::RowPadding)
		[
			Label(LOCTEXT("Unsaved", "Unsaved changes."), Size, Warn())
		];
		const struct { FText Text; ESettingsBackChoice Choice; } Choices[] = {
			{LOCTEXT("PromptSave", "Save"), ESettingsBackChoice::Save},
			{LOCTEXT("PromptDiscard", "Discard"), ESettingsBackChoice::Discard},
			{LOCTEXT("PromptKeep", "Keep Editing"), ESettingsBackChoice::KeepEditing}};
		for (const auto& Choice : Choices)
		{
			const ESettingsBackChoice Picked = Choice.Choice;
			Buttons->AddSlot().AutoWidth().Padding(SettingsLayout::RowPadding)
			[
				SNew(SButton)
				.OnClicked(FOnClicked::CreateWeakLambda(this, [this, Picked]()
				{
					ChooseBack(Picked);
					return FReply::Handled();
				}))
				[
					Label(Choice.Text, Size, Sepia())
				]
			];
		}
	}
	else
	{
		Buttons->AddSlot().AutoWidth().Padding(SettingsLayout::RowPadding)
		[
			SNew(SButton)
			.OnClicked(FOnClicked::CreateWeakLambda(this, [this]()
			{
				PressBack();
				return FReply::Handled();
			}))
			[
				Label(LOCTEXT("Back", "Back"), Size, Sepia())
			]
		];
		Buttons->AddSlot().AutoWidth().Padding(SettingsLayout::RowPadding)
		[
			SNew(SButton)
			.OnClicked(FOnClicked::CreateWeakLambda(this, [this]()
			{
				PressSave();
				return FReply::Handled();
			}))
			[
				Label(LOCTEXT("Save", "Save"), Size, Gold())
			]
		];
	}
	FooterBox->AddSlot().AutoHeight()[Buttons];
}

void USettingsMenuWidget::AddSoundBody()
{
	const int32 Size = ScaledFont(SettingsLayout::BodyFontSize);
	const struct { FText Text; ESliderId Id; } Rows[] = {
		{LOCTEXT("Master", "Master Volume"), ESliderId::Master},
		{LOCTEXT("Sfx", "Sound Effects"), ESliderId::Sfx},
		{LOCTEXT("Music", "Music"), ESliderId::Music},
		{LOCTEXT("TextSize", "Text Size %"), ESliderId::TextScale}};
	for (const auto& Row : Rows)
	{
		const ESliderId Id = Row.Id;
		if (Id == ESliderId::TextScale && !IsFeatureEnabled(EFeatureId::FLOW_45))
		{
			continue;
		}
		const int32 Low = SliderLow(Id);
		const int32 High = SliderHigh(Id);
		BodyBox->AddSlot().AutoHeight().Padding(SettingsLayout::RowPadding)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(SBox).WidthOverride(SettingsLayout::LabelWidth)[Label(Row.Text, Size, Sepia())]
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(SBox).WidthOverride(SettingsLayout::SliderWidth)
				[
					SNew(SSlider)
					.StepSize(SettingsLayout::SliderStep)
					.Value(TAttribute<float>::Create(TAttribute<float>::FGetter::CreateWeakLambda(this, [this, Id, Low, High]()
					{
						const USettingsMenuSubsystem* Subsystem = Owner.Get();
						const int32 Value = Subsystem ? SliderValue(Subsystem->GetSession().GetDraft(), Id) : Low;
						return static_cast<float>(Value - Low) / static_cast<float>(High - Low);
					})))
					.OnValueChanged(FOnFloatValueChanged::CreateWeakLambda(this, [this, Id, Low, High](float Fraction)
					{
						if (USettingsMenuSubsystem* Subsystem = Owner.Get())
						{
							SetSliderValue(Subsystem->EditSession(), Id, Low + FMath::RoundToInt(Fraction * static_cast<float>(High - Low)));
						}
					}))
				]
			]
			+ SHorizontalBox::Slot().AutoWidth().Padding(SettingsLayout::RowPadding)
			[
				SNew(SBox).WidthOverride(SettingsLayout::ValueWidth)
				[
					SNew(STextBlock)
					.Font(Font(Size))
					.ColorAndOpacity(Gold())
					.Text(TAttribute<FText>::Create(TAttribute<FText>::FGetter::CreateWeakLambda(this, [this, Id]()
					{
						const USettingsMenuSubsystem* Subsystem = Owner.Get();
						return FText::AsNumber(Subsystem ? SliderValue(Subsystem->GetSession().GetDraft(), Id) : 0);
					})))
				]
			]
		];
	}
	if (IsFeatureEnabled(EFeatureId::FLOW_45))
	{
		BodyBox->AddSlot().AutoHeight().Padding(SettingsLayout::RowPadding)
		[
			SNew(SCheckBox)
			.IsChecked(TAttribute<ECheckBoxState>::Create(TAttribute<ECheckBoxState>::FGetter::CreateWeakLambda(this, [this]()
			{
				const USettingsMenuSubsystem* Subsystem = Owner.Get();
				return Subsystem && Subsystem->GetSession().GetDraft().bReducedMotion ? ECheckBoxState::Checked : ECheckBoxState::Unchecked;
			})))
			.OnCheckStateChanged(FOnCheckStateChanged::CreateWeakLambda(this, [this](ECheckBoxState State)
			{
				if (USettingsMenuSubsystem* Subsystem = Owner.Get())
				{
					Subsystem->EditSession().SetReducedMotion(State == ECheckBoxState::Checked);
				}
			}))
			[
				Label(LOCTEXT("ReducedMotion", "Reduced motion"), Size, Sepia())
			]
		];
		BodyBox->AddSlot().AutoHeight().Padding(SettingsLayout::RowPadding)
		[
			SNew(SCheckBox)
			.IsChecked(TAttribute<ECheckBoxState>::Create(TAttribute<ECheckBoxState>::FGetter::CreateWeakLambda(this, [this]()
			{
				const USettingsMenuSubsystem* Subsystem = Owner.Get();
				return Subsystem && Subsystem->GetSession().GetDraft().bReducedFlash ? ECheckBoxState::Checked : ECheckBoxState::Unchecked;
			})))
			.OnCheckStateChanged(FOnCheckStateChanged::CreateWeakLambda(this, [this](ECheckBoxState State)
			{
				if (USettingsMenuSubsystem* Subsystem = Owner.Get())
				{
					Subsystem->EditSession().SetReducedFlash(State == ECheckBoxState::Checked);
				}
			}))
			[
				Label(LOCTEXT("ReducedFlash", "Reduced flash"), Size, Sepia())
			]
		];
	}
}

void USettingsMenuWidget::AddControllerBody()
{
	const USettingsMenuSubsystem* Subsystem = Owner.Get();
	if (!Subsystem)
	{
		return;
	}
	const int32 Size = ScaledFont(SettingsLayout::BodyFontSize);
	const FUmbrellaSettingsData& Draft = Subsystem->GetSession().GetDraft();
	for (int32 ActionIndex = 0; ActionIndex < static_cast<int32>(EUmbrellaInputAction::Count); ++ActionIndex)
	{
		const EUmbrellaInputAction Action = static_cast<EUmbrellaInputAction>(ActionIndex);
		const int32 Count = SettingsRules::CountBindings(Draft.Bindings, Action);
		if (Count == 0)
		{
			continue;
		}
		TSharedRef<SHorizontalBox> Row = SNew(SHorizontalBox);
		Row->AddSlot().AutoWidth()
		[
			SNew(SBox).WidthOverride(SettingsLayout::LabelWidth)[Label(SettingsRules::ActionDisplayName(Action), Size, Sepia())]
		];
		for (int32 Slot = 0; Slot < Count; ++Slot)
		{
			const FUmbrellaDefaultBinding& Binding = Draft.Bindings[SettingsRules::FindBindingIndex(Draft.Bindings, Action, Slot)];
			const bool bWaiting = bCapturing && CaptureAction == Action && CaptureSlot == Slot;
			FString Text = bWaiting ? FString(TEXT("...")) : SettingsRules::KeyLabel(Binding.Key);
			if (!bWaiting && Binding.Scale < 0.0f)
			{
				Text += TEXT(" (-)");
			}
			Row->AddSlot().AutoWidth().Padding(SettingsLayout::RowPadding)
			[
				SNew(SBox).WidthOverride(SettingsLayout::KeyButtonWidth)
				[
					SNew(SButton)
					.OnClicked(FOnClicked::CreateWeakLambda(this, [this, Action, Slot]()
					{
						BeginRemap(Action, Slot);
						return FReply::Handled();
					}))
					[
						Label(FText::FromString(Text), Size, bWaiting ? Gold() : Sepia())
					]
				]
			];
		}
		BodyBox->AddSlot().AutoHeight().Padding(SettingsLayout::RowPadding)[Row];
	}
	if (IsFeatureEnabled(EFeatureId::FLOW_45) && SettingsRules::HasShootAbsorbConflict(Draft.Bindings))
	{
		BodyBox->AddSlot().AutoHeight().Padding(SettingsLayout::RowPadding)
		[
			Label(LOCTEXT("Conflict", "Shoot and Absorb share a key. The four flight modes need them apart. Reset bindings to recover."), Size, Warn())
		];
	}
	BodyBox->AddSlot().AutoHeight().Padding(SettingsLayout::RowPadding)
	[
		SNew(SButton)
		.OnClicked(FOnClicked::CreateWeakLambda(this, [this]()
		{
			PressResetBindings();
			return FReply::Handled();
		}))
		[
			Label(LOCTEXT("ResetBindings", "Reset bindings"), Size, Sepia())
		]
	];
}

void USettingsMenuWidget::AddCreditsBody()
{
	const int32 Size = ScaledFont(SettingsLayout::BodyFontSize);
	for (const FSettingsCreditLine& Line : SettingsRules::GetCredits())
	{
		const FString Text = Line.Role.IsEmpty() ? Line.Name : FString::Printf(TEXT("%s - %s"), *Line.Name, *Line.Role);
		BodyBox->AddSlot().AutoHeight().Padding(SettingsLayout::RowPadding)[Label(FText::FromString(Text), Size, Sepia())];
	}
}

void USettingsMenuWidget::AddGameOptionsBody()
{
	const int32 Size = ScaledFont(SettingsLayout::BodyFontSize);
	const bool bEditable = DeveloperOptionRules::CanEdit(Mode, DeveloperOptionRules::IsWorkbenchBuild());
	BodyBox->AddSlot().AutoHeight().Padding(SettingsLayout::RowPadding)
	[
		Label(bEditable
			? LOCTEXT("DevNote", "Developer options (Director's Cut only). Save applies them to this session; 100% is as tuned.")
			: LOCTEXT("DevNoteLocked", "Developer options (Director's Cut only). They can be changed in the tester build."), Size, Gold())
	];
	const USettingsMenuSubsystem* Subsystem = Owner.Get();
	const FSettingsLiveTuning Baseline = Subsystem ? Subsystem->GetBaselineTuning() : FSettingsLiveTuning();
	if (SettingsRules::GetDeveloperOptionNames(Mode).Num() == 0)
	{
		return;
	}
	for (const FDeveloperOptionSpec& Spec : DeveloperOptionRules::AllSpecs())
	{
		const EDeveloperOption Option = Spec.Id;
		TSharedRef<SWidget> Control = SNullWidget::NullWidget;
		switch (Spec.Kind)
		{
		case EDeveloperOptionKind::Percent:
		case EDeveloperOptionKind::Offset:
		{
			const int32 Low = Spec.Low;
			const int32 High = Spec.High;
			Control = SNew(SSlider)
				.IsEnabled(bEditable)
				.StepSize(static_cast<float>(Spec.Step) / static_cast<float>(High - Low))
				.Value(TAttribute<float>::Create(TAttribute<float>::FGetter::CreateWeakLambda(this, [this, Option, Low, High]()
				{
					const USettingsMenuSubsystem* Current = Owner.Get();
					const int32 Value = Current ? DeveloperOptionRules::ValueOf(Current->GetSession().GetDraft().DeveloperValues, Option) : Low;
					return static_cast<float>(Value - Low) / static_cast<float>(High - Low);
				})))
				.OnValueChanged(FOnFloatValueChanged::CreateWeakLambda(this, [this, Option, Low, High](float Fraction)
				{
					SetDeveloperOption(Option, Low + FMath::RoundToInt(Fraction * static_cast<float>(High - Low)));
				}));
			break;
		}
		case EDeveloperOptionKind::Toggle:
			Control = SNew(SCheckBox)
				.IsEnabled(bEditable)
				.IsChecked(TAttribute<ECheckBoxState>::Create(TAttribute<ECheckBoxState>::FGetter::CreateWeakLambda(this, [this, Option]()
				{
					const USettingsMenuSubsystem* Current = Owner.Get();
					const int32 Value = Current ? DeveloperOptionRules::ValueOf(Current->GetSession().GetDraft().DeveloperValues, Option) : 0;
					return Value == DeveloperOptionLimits::ToggleOn ? ECheckBoxState::Checked : ECheckBoxState::Unchecked;
				})))
				.OnCheckStateChanged(FOnCheckStateChanged::CreateWeakLambda(this, [this, Option](ECheckBoxState State)
				{
					SetDeveloperOption(Option, State == ECheckBoxState::Checked ? DeveloperOptionLimits::ToggleOn : DeveloperOptionLimits::ToggleOff);
				}));
			break;
		case EDeveloperOptionKind::Link:
		default:
			Control = SNew(SButton)
				.IsEnabled(SettingsRules::IsPageAvailable(ESettingsPage::Controller, Mode))
				.OnClicked(FOnClicked::CreateWeakLambda(this, [this]()
				{
					ShowPage(ESettingsPage::Controller);
					return FReply::Handled();
				}))
				[
					Label(LOCTEXT("OpenController", "Open Controller page"), Size, Gold())
				];
			break;
		}
		BodyBox->AddSlot().AutoHeight().Padding(SettingsLayout::RowPadding)
		[
			SNew(SHorizontalBox)
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(SBox).WidthOverride(SettingsLayout::LabelWidth)[Label(Spec.Label, Size, Sepia())]
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(SBox).WidthOverride(SettingsLayout::SliderWidth)[Control]
			]
			+ SHorizontalBox::Slot().AutoWidth().Padding(SettingsLayout::RowPadding)
			[
				SNew(SBox).WidthOverride(SettingsLayout::ValueWidth)
				[
					SNew(STextBlock)
					.Font(Font(Size))
					.ColorAndOpacity(Gold())
					.Text(TAttribute<FText>::Create(TAttribute<FText>::FGetter::CreateWeakLambda(this, [this, Option, Baseline]()
					{
						const USettingsMenuSubsystem* Current = Owner.Get();
						const int32 Value = Current ? DeveloperOptionRules::ValueOf(Current->GetSession().GetDraft().DeveloperValues, Option)
							: DeveloperOptionRules::SpecFor(Option).Default;
						return DeveloperOptionRules::ValueText(Option, Value, Baseline);
					})))
				]
			]
		];
	}
	if (bEditable)
	{
		BodyBox->AddSlot().AutoHeight().Padding(SettingsLayout::RowPadding)
		[
			SNew(SButton)
			.OnClicked(FOnClicked::CreateWeakLambda(this, [this]()
			{
				PressResetDeveloperOptions();
				return FReply::Handled();
			}))
			[
				Label(LOCTEXT("ResetDev", "Reset to as tuned"), Size, Gold())
			]
		];
	}
}

void USettingsMenuWidget::SetDeveloperOption(EDeveloperOption Option, int32 Value)
{
	USettingsMenuSubsystem* Subsystem = Owner.Get();
	if (Subsystem && DeveloperOptionRules::CanEdit(Mode, DeveloperOptionRules::IsWorkbenchBuild()))
	{
		Subsystem->EditSession().SetDeveloperOption(Option, Value);
	}
}

void USettingsMenuWidget::PressResetDeveloperOptions()
{
	USettingsMenuSubsystem* Subsystem = Owner.Get();
	if (Subsystem && DeveloperOptionRules::CanEdit(Mode, DeveloperOptionRules::IsWorkbenchBuild()))
	{
		Subsystem->EditSession().ResetDeveloperOptions();
		RebuildBody();
	}
}

void USettingsMenuWidget::ShowPage(ESettingsPage NewPage)
{
	if (!SettingsRules::IsPageAvailable(NewPage, Mode))
	{
		return;
	}
	Page = NewPage;
	bBackPrompt = false;
	bCapturing = false;
	RebuildBody();
}

void USettingsMenuWidget::CloseMenu()
{
	if (USettingsMenuSubsystem* Subsystem = Owner.Get())
	{
		Subsystem->CloseSettings();
	}
}

void USettingsMenuWidget::PressBack()
{
	USettingsMenuSubsystem* Subsystem = Owner.Get();
	if (!Subsystem)
	{
		return;
	}
	if (Subsystem->GetSession().RequestBack(Page) == ESettingsBackResult::AskSaveDiscardKeep)
	{
		bBackPrompt = true;
		RebuildBody();
		return;
	}
	CloseMenu();
}

void USettingsMenuWidget::PressSave()
{
	USettingsMenuSubsystem* Subsystem = Owner.Get();
	if (!Subsystem)
	{
		return;
	}
	bSaveFailed = Subsystem->SaveSettings(Page) == ESettingsResult::Failed;
	Subsystem->ApplySavedBindings(GetOwningPlayer());
	RebuildBody();
}

void USettingsMenuWidget::ChooseBack(ESettingsBackChoice Choice)
{
	USettingsMenuSubsystem* Subsystem = Owner.Get();
	if (!Subsystem)
	{
		return;
	}
	bBackPrompt = false;
	switch (Choice)
	{
	case ESettingsBackChoice::Save:
		bSaveFailed = Subsystem->SaveSettings(Page) == ESettingsResult::Failed;
		Subsystem->ApplySavedBindings(GetOwningPlayer());
		if (bSaveFailed)
		{
			// The file could not be written: stay open and say so.
			RebuildBody();
			break;
		}
		CloseMenu();
		break;
	case ESettingsBackChoice::Discard:
		Subsystem->DiscardChanges(Page);
		CloseMenu();
		break;
	case ESettingsBackChoice::KeepEditing:
	default:
		RebuildBody();
		break;
	}
}

void USettingsMenuWidget::BeginRemap(EUmbrellaInputAction Action, int32 Slot)
{
	bCapturing = true;
	CaptureAction = Action;
	CaptureSlot = Slot;
	RebuildBody();
	if (IsInViewport())
	{
		SetKeyboardFocus();
	}
}

void USettingsMenuWidget::CaptureKey(const FKey& Key)
{
	USettingsMenuSubsystem* Subsystem = Owner.Get();
	if (!bCapturing || !Subsystem)
	{
		return;
	}
	bCapturing = false;
	if (Key != EKeys::Escape)
	{
		Subsystem->EditSession().Remap(CaptureAction, CaptureSlot, Key);
	}
	RebuildBody();
}

void USettingsMenuWidget::PressResetBindings()
{
	if (USettingsMenuSubsystem* Subsystem = Owner.Get())
	{
		Subsystem->EditSession().ResetBindings();
		bCapturing = false;
		RebuildBody();
	}
}

FReply USettingsMenuWidget::NativeOnKeyDown(const FGeometry& InGeometry, const FKeyEvent& InKeyEvent)
{
	if (IsCapturingKey())
	{
		CaptureKey(InKeyEvent.GetKey());
		return FReply::Handled();
	}
	return Super::NativeOnKeyDown(InGeometry, InKeyEvent);
}

FReply USettingsMenuWidget::NativeOnPreviewMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	// Preview runs before Slate buttons see the click, so a mouse button can be bound even over a button.
	if (IsCapturingKey())
	{
		CaptureKey(InMouseEvent.GetEffectingButton());
		return FReply::Handled();
	}
	return Super::NativeOnPreviewMouseButtonDown(InGeometry, InMouseEvent);
}

FReply USettingsMenuWidget::NativeOnMouseButtonDown(const FGeometry& InGeometry, const FPointerEvent& InMouseEvent)
{
	if (IsCapturingKey())
	{
		CaptureKey(InMouseEvent.GetEffectingButton());
		return FReply::Handled();
	}
	return Super::NativeOnMouseButtonDown(InGeometry, InMouseEvent);
}

#undef LOCTEXT_NAMESPACE
