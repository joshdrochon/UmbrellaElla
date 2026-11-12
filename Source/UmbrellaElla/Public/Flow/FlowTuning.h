#pragma once

#include "CoreMinimal.h"
#include "FlowTuning.generated.h"

/** Every number of the Flow module: default, units and clamps (lane d). End a shipped default with // bake: <feature ID>.<param>. */
USTRUCT()
struct UMBRELLAELLA_API FFlowTuning
{
	GENERATED_BODY()

	/** Seconds each ending story page stays up before the next (timing is OPEN in the GDD; adjustable). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0", Units = "s"))
	float StoryPageSeconds = 8.0f;

	/** Seconds the credits roll over the background. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0", Units = "s"))
	float CreditsSeconds = 24.0f;

	/** Seconds with the confirm and pause keys released before Resume or Retry hands control back. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0", Units = "s"))
	float ResumeNeutralSeconds = 0.25f;

	/** Priority of the menu input mapping context (above gameplay at 0). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1"))
	int32 MenuContextPriority = 10;

	/** Background drift speed in Slate units per second (slow on purpose). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float BackgroundDriftSpeed = 14.0f;

	/** Background sway in Slate units. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float BackgroundSwayAmplitude = 24.0f;

	/** Sway angular speed in radians per second. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float BackgroundSwaySpeed = 0.4f;

	/** Golden-ratio step that spreads the background shapes without a random stream. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0", ClampMax = "1.0"))
	float BackgroundSpreadStep = 0.618034f;

	/** Falling shapes drawn behind every menu. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0"))
	int32 FallingShapeCount = 16;

	/** Smallest and largest falling shape, Slate units. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0"))
	float FallingShapeMinSize = 10.0f;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0"))
	float FallingShapeMaxSize = 34.0f;

	/** Fall speed range, Slate units per second. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float FallingShapeMinSpeed = 14.0f;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float FallingShapeMaxSpeed = 46.0f;

	/** Ticking clocks drawn behind the pause menu. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0"))
	int32 PauseClockCount = 5;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "8.0"))
	float PauseClockRadius = 72.0f;

	/** Clock-hand length as a share of the clock radius. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.1", ClampMax = "1.0"))
	float ClockHandLengthShare = 0.8f;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0"))
	float ClockHandThickness = 4.0f;

	/** Seconds per full minute-hand turn of a background clock (a tick every second). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "1.0", Units = "s"))
	float ClockTurnSeconds = 60.0f;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "8"))
	int32 TitleFontSize = 64;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "8"))
	int32 MenuFontSize = 28;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "8"))
	int32 BodyFontSize = 30;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float ButtonCornerRadius = 30.0f;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float ButtonPaddingX = 48.0f;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float ButtonPaddingY = 14.0f;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float MenuSpacing = 18.0f;

	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float TextBlockWidth = 900.0f;

	/** Credits scroll start offset below the screen, Slate units. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float CreditsTravel = 1400.0f;

	UPROPERTY(Config, EditAnywhere)
	FLinearColor BackgroundColor = FLinearColor(0.02f, 0.025f, 0.07f, 1.0f);

	UPROPERTY(Config, EditAnywhere)
	FLinearColor ShapeColor = FLinearColor(0.55f, 0.5f, 0.75f, 0.35f);

	UPROPERTY(Config, EditAnywhere)
	FLinearColor ClockColor = FLinearColor(0.85f, 0.65f, 0.25f, 0.6f);

	UPROPERTY(Config, EditAnywhere)
	FLinearColor ButtonColor = FLinearColor(0.12f, 0.1f, 0.22f, 0.9f);

	UPROPERTY(Config, EditAnywhere)
	FLinearColor ButtonHoverColor = FLinearColor(0.3f, 0.22f, 0.45f, 1.0f);

	UPROPERTY(Config, EditAnywhere)
	FLinearColor ButtonPressedColor = FLinearColor(0.5f, 0.35f, 0.15f, 1.0f);

	UPROPERTY(Config, EditAnywhere)
	FLinearColor TextColor = FLinearColor(0.95f, 0.92f, 0.85f, 1.0f);

	/** Seconds after the first gameplay frame at which the smoke hook takes its screenshot. */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0", Units = "s"))
	float SmokeShotDelaySeconds = 5.0f;

	/** Share of the slowest frames the smoke fps reads (0.01 = the 1% low). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.001", ClampMax = "1.0"))
	float SmokeLowShare = 0.01f;

	/** Gap under the purchase screen's Done button (pixels; no GDD value, layout only). */
	UPROPERTY(Config, EditAnywhere, meta = (ClampMin = "0.0"))
	float PurchaseDoneBottomMargin = 32.0f;
};
