#pragma once

#include "CoreMinimal.h"
#include "StoryTuning.generated.h"

/**
 * Every number of the Story module (lane story). Read with GetDefault<UUmbrellaTuning>()->Story. Values are story-lane choices where the
 * GDD says OPEN; the GDD value is named where there is one.
 */
USTRUCT()
struct UMBRELLAELLA_API FStoryTuning
{
	GENERATED_BODY()

	/** Mother caption on screen, seconds ("about four seconds"). */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0.5"))
	float OpeningCaptionSeconds = 4.0f;

	/** Hold on Ella under her umbrella after the Keeper has departed ("roughly 2.5 s"); flow's ending clock reads it. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float EndingHoldSeconds = 2.5f;

	/** How long flow shows each Director's Cut ending story line (script timing OPEN). Credits length is Flow.CreditsSeconds. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	float EndingLineSeconds = 5.0f;

	/** Smallest text size in px for every story widget (assignment: at least 18 px). */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "18"))
	int32 MinFontSize = 18;

	/** Distance steps larger than this many units in one tick are teleports (respawn, checkpoint) and not flown. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	float MaxFlownStepUnits = 2000.0f;

	/** Unreal units per metre shown on the statistics screen. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	float UnitsPerMetre = 100.0f;

	/** Screen margin so text stays inside the 16:9 view (px at 1920x1080). */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	FVector2D SafeMargin = FVector2D(96.0, 54.0);

	/** Font size added to MinFontSize: bottom caption, centre narration, statistics rows, title, buttons. */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	int32 CaptionFontExtra = 4;
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	int32 NarrationFontExtra = 10;
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	int32 RowFontExtra = 6;
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	int32 TitleFontExtra = 24;
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	int32 ButtonFontExtra = 4;

	/** Statistics layout: label column width, gap between rows, gap between blocks (px). */
	UPROPERTY(EditAnywhere, meta = (ClampMin = "1"))
	float RowLabelWidth = 420.0f;
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float RowGap = 6.0f;
	UPROPERTY(EditAnywhere, meta = (ClampMin = "0"))
	float BlockGap = 24.0f;

	/** Parchment text and charcoal panel (art bible: ink on aged paper, muted sepia). */
	UPROPERTY(EditAnywhere)
	FLinearColor TextColor = FLinearColor(0.93f, 0.88f, 0.76f, 1.0f);
	UPROPERTY(EditAnywhere)
	FLinearColor PanelColor = FLinearColor(0.09f, 0.08f, 0.07f, 1.0f);

	/** Viewport layers: captions below the statistics screen. */
	UPROPERTY(EditAnywhere)
	int32 CaptionZOrder = 80;
	UPROPERTY(EditAnywhere)
	int32 StatisticsZOrder = 90;
};
