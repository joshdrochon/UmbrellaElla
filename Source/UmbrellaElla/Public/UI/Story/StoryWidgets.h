#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "StoryWidgets.generated.h"

struct FStoryRunStats;
class STextBlock;
class SVerticalBox;

DECLARE_MULTICAST_DELEGATE(FOnStoryChoice);

enum class EStoryCaptionPlace : uint8
{
	Bottom,
	Centre
};

/** Bottom-centre caption and centre narration text. Text only, never a modal page. */
UCLASS()
class UMBRELLAELLA_API UStoryCaptionWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	/** Empty text hides the caption. Centre = ending story text, else the bottom caption. */
	void SetCaption(const FString& Text, EStoryCaptionPlace Place);
	const FString& GetCaption() const { return Caption; }

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void ReleaseSlateResources(bool bReleaseChildren) override;

private:
	FString Caption;
	TSharedPtr<STextBlock> BottomText;
	TSharedPtr<STextBlock> CentreText;
};

/** Journey Complete: eight rows, Try Again and Main Menu. Editable text, no baked numbers. */
UCLASS()
class UMBRELLAELLA_API UJourneyCompleteWidget : public UUserWidget
{
	GENERATED_BODY()

public:
	void SetStats(const FStoryRunStats& InStats);
	const TArray<TPair<FString, FString>>& GetRows() const { return Rows; }

	FOnStoryChoice& GetTryAgainDelegate() const { return TryAgainDelegate; }
	FOnStoryChoice& GetMainMenuDelegate() const { return MainMenuDelegate; }

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void ReleaseSlateResources(bool bReleaseChildren) override;

private:
	FReply HandleTryAgain();
	FReply HandleMainMenu();
	void FillRows();

	mutable FOnStoryChoice TryAgainDelegate;
	mutable FOnStoryChoice MainMenuDelegate;
	TArray<TPair<FString, FString>> Rows;
	TSharedPtr<SVerticalBox> RowBox;
	TSharedPtr<class SUmbrellaButton> TryAgainButton;
	TSharedPtr<class SUmbrellaButton> MainMenuButton;
};
