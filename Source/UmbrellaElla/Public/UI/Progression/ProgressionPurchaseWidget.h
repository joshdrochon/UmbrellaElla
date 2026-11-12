#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "Progression/ProgressionDraft.h"
#include "ProgressionPurchaseWidget.generated.h"

class SVerticalBox;
class UProgressionSubsystem;

/**
 * The Ella and Spells purchase screen at refuges and between runs: stage purchases, review the complete cost, then confirm
 * (atomic) or cancel. Outside a purchase context it is inspection-only: the buttons are disabled and nothing is staged.
 * Browsing never changes live values; closing or a context change discards the draft. Built in Slate from C++.
 */
UCLASS()
class UMBRELLAELLA_API UProgressionPurchaseWidget final : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Opens the screen for a player; null when Start Game is active. */
	static UProgressionPurchaseWidget* Show(APlayerController* Owner);

	void StageBuy(EProgressionTrack Track);
	void StageRefund(EProgressionTrack Track);
	/** Applies the whole draft atomically. */
	EProgressionCommit Confirm();
	void Cancel();

	bool IsDraftDirty() const;
	int32 GetDraftNetCost() const;
	int32 GetDraftRank(EProgressionTrack Track) const;
	bool IsInspectionOnly() const;

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeConstruct() override;
	virtual void NativeDestruct() override;

private:
	void OnProgressionChanged();
	void Rebuild();
	static FText TrackLabel(EProgressionTrack Track);

	TWeakObjectPtr<UProgressionSubsystem> Progression;
	TSharedPtr<SVerticalBox> Rows;
	FProgressionDraft Draft;
	FDelegateHandle ChangedHandle;
	EPurchaseContextKind LastContext = EPurchaseContextKind::None;
};
