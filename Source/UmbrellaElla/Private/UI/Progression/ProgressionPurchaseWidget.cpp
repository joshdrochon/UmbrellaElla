#include "UI/Progression/ProgressionPurchaseWidget.h"
#include "Core/UmbrellaPlayMode.h"
#include "GameFramework/PlayerController.h"
#include "Harness/UmbrellaFeatureFlags.h"
#include "Progression/ProgressionSubsystem.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/SBoxPanel.h"
#include "Widgets/Text/STextBlock.h"

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
	return Rows.ToSharedRef();
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

	Rows->AddSlot().AutoHeight()
	[
		SNew(STextBlock).Text(FText::Format(LOCTEXT("Header", "Level {0}   Points left {1}"), Subsystem->GetLevel(), Spare))
	];
	if (IsInspectionOnly())
	{
		Rows->AddSlot().AutoHeight()
		[
			SNew(STextBlock).Text(LOCTEXT("Inspect", "Inspection only. Spend points at a refuge or between runs."))
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
			+ SHorizontalBox::Slot().FillWidth(1.0f)
			[
				SNew(STextBlock).Text(FText::Format(LOCTEXT("Row", "{0}: {1} / {2}"), TrackLabel(Track), Rank, Max))
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(SButton).IsEnabled(!IsInspectionOnly()).OnClicked_Lambda([this, Track]() { StageRefund(Track); return FReply::Handled(); })
				[
					SNew(STextBlock).Text(LOCTEXT("Minus", "-"))
				]
			]
			+ SHorizontalBox::Slot().AutoWidth()
			[
				SNew(SButton).IsEnabled(!IsInspectionOnly()).OnClicked_Lambda([this, Track]() { StageBuy(Track); return FReply::Handled(); })
				[
					SNew(STextBlock).Text(LOCTEXT("Plus", "+"))
				]
			]
		];
	}
	Rows->AddSlot().AutoHeight()
	[
		SNew(SHorizontalBox)
		+ SHorizontalBox::Slot().AutoWidth()
		[
			SNew(SButton).IsEnabled(IsDraftDirty()).OnClicked_Lambda([this]() { Confirm(); return FReply::Handled(); })
			[
				SNew(STextBlock).Text(FText::Format(LOCTEXT("Confirm", "Confirm ({0} points)"), GetDraftNetCost()))
			]
		]
		+ SHorizontalBox::Slot().AutoWidth()
		[
			SNew(SButton).OnClicked_Lambda([this]() { Cancel(); return FReply::Handled(); })
			[
				SNew(STextBlock).Text(LOCTEXT("Cancel", "Cancel"))
			]
		]
	];
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

#undef LOCTEXT_NAMESPACE
