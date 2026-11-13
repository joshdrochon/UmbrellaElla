#pragma once

#include "CoreMinimal.h"
#include "Fonts/SlateFontInfo.h"
#include "Styling/SlateTypes.h"
#include "Widgets/Input/SButton.h"
#include "Widgets/SLeafWidget.h"

class UTexture2D;

/** Every number of the shared UI look. Colours are sRGB bytes read off the title-screen reference. */
namespace UmbrellaUIStyleConstants
{
	/** Smallest text size any screen may use (accessibility U1: 18 px at 1080p). */
	static constexpr int32 MinTextSize = 18;
	/** Menu control hint: inset from the bottom-right corner, and the gap between the Confirm and Back hints. */
	static constexpr float PromptInsetX = 64.0f;
	static constexpr float PromptInsetY = 44.0f;
	static constexpr float PromptGap = 40.0f;

	static constexpr FColor Cream = FColor(233, 220, 195);
	static constexpr FColor Dim = FColor(168, 156, 136);
	static constexpr FColor Gold = FColor(217, 162, 87);
	static constexpr FColor GoldBright = FColor(246, 205, 128);
	static constexpr FColor Ink = FColor(20, 16, 14);
	static constexpr FColor Warn = FColor(226, 112, 78);

	/** Letter spacing of the display face, in 1/1000 em (the reference letters its menu wide). */
	static constexpr int32 DisplayLetterSpacing = 70;

	/** Letter spacing of body copy, also set in the storybook face. */
	static constexpr int32 BodyLetterSpacing = 40;

	/** Painted size of the ground texture. */
	static constexpr float GroundWidth = 1920.0f;
	static constexpr float GroundHeight = 1080.0f;

	/** The column every menu is set in: the dark left third of the ground, as on the title-screen reference. */
	static constexpr float ColumnLeft = 132.0f;
	static constexpr float ColumnWidth = 700.0f;
	/** The title lockup and headings may run wider than the body column, over the mist. */
	static constexpr float HeadingWidth = 860.0f;
	static constexpr float ColumnBottomLift = 60.0f;

	/** Panel behind dense screens (settings, purchase, statistics). */
	static constexpr float PanelFillAlpha = 0.9f;
	static constexpr float PanelBorderAlpha = 0.85f;
	static constexpr float PanelCornerRadius = 3.0f;
	static constexpr float PanelBorderWidth = 1.5f;
	static constexpr float PanelPadding = 44.0f;
	/** Painted panel card as a nine-slice: drawn size of the whole card image and the border share kept unstretched. */
	static constexpr float PanelArtWidth = 460.0f;
	static constexpr float PanelArtHeight = 253.0f;
	static constexpr float PanelArtMarginX = 0.078f;
	static constexpr float PanelArtMarginY = 0.14f;

	/** Menu button: the focus mark is a short gold rule with a diamond, left of the label, and a rule under it. */
	static constexpr float ButtonPadX = 10.0f;
	static constexpr float ButtonPadY = 7.0f;
	static constexpr float OrnamentWidth = 86.0f;
	static constexpr float OrnamentGap = 16.0f;
	static constexpr float DiamondSize = 11.0f;
	static constexpr float RuleThickness = 2.0f;
	static constexpr float UnderlineDrop = 3.0f;
	static constexpr float UnderlineFadeAlpha = 0.0f;
	static constexpr float DisabledAlpha = 0.45f;
	static constexpr float QuarterTurnRadians = 0.7853982f;

	/** Heading rule: drawn as a clock hand lying under the heading (pommel diamond, pivot ring, a long tapering needle). */
	static constexpr float RuleHeight = 26.0f;
	static constexpr float RuleDiamondInset = 2.0f;
	static constexpr float RuleLineAlpha = 0.9f;
	static constexpr float RulePivotAt = 64.0f;
	static constexpr float RulePivotRadius = 9.0f;
	static constexpr float RulePivotLine = 2.0f;
	static constexpr int32 RulePivotSegments = 20;
	static constexpr float RuleNeedleWidth = 7.0f;

	/** Slider and checkbox. */
	static constexpr float SliderBarThickness = 3.0f;
	static constexpr float SliderThumbSize = 18.0f;
	static constexpr float CheckSize = 22.0f;
	static constexpr float CheckBorderWidth = 2.0f;
	static constexpr float CheckInnerRadius = 2.0f;
	static constexpr float DimBarAlpha = 0.45f;

	/** Text over the scene keeps an ink shadow so it reads on any ground. */
	static constexpr float ShadowOffset = 2.0f;
	static constexpr float ShadowAlpha = 0.85f;

	/** Drifting embers and the pause clocks painted over the ground. */
	static constexpr float EmberSizeShare = 0.2f;
	static constexpr float EmberAlpha = 0.75f;
	static constexpr float ClockLineAlpha = 0.2f;
	static constexpr float ClockLineShare = 0.5f;
	static constexpr int32 ClockTickCount = 12;
	static constexpr float ClockTickInner = 0.86f;

	/** HUD clock: the dial texture's rim sits at this share of its half size; the canvas face is built at this size. */
	static constexpr float ClockFaceRimShare = 0.96875f;
	static constexpr int32 CanvasFontSize = 24;
	/** A clock hand is a blade: widest at this share of its length, with a short tail behind the pivot. */
	static constexpr float HandBladeWidest = 0.3f;
	static constexpr float HandBladeTail = 0.12f;
	static constexpr float HandBladeWidthShare = 2.4f;

	/** Purchase screen text sizes (points). */
	static constexpr int32 PurchaseHeadingTextSize = 30;
	static constexpr int32 PurchaseRowTextSize = 20;
	static constexpr int32 PurchaseStepTextSize = 24;

	/** The title lockup: its first line is the name, lettered large; the lines under it are the subtitle. */
	/** The grain tile is drawn at its painted size, over the whole ground, at this strength. */
	static constexpr float GrainTileSize = 512.0f;
	static constexpr float GrainOpacity = 0.6f;
	/** The painted lockup is drawn this wide (it is 1584 x 672 painted, 21:9). */
	static constexpr float LockupImageWidth = 820.0f;
	static constexpr float LockupImageHeight = 820.0f * 672.0f / 1584.0f;
	static constexpr float LockupImagePixelWidth = 1584.0f;
	static constexpr float LockupImagePixelHeight = 672.0f;
	/** Painted screen headings, drawn at 0.3 of their pixel size (1085x272 and 1086x323). */
	static constexpr float HeadPausedWidth = 1085.0f * 0.3f;
	static constexpr float HeadPausedHeight = 272.0f * 0.3f;
	static constexpr float HeadSettingsWidth = 1086.0f * 0.3f;
	static constexpr float HeadSettingsHeight = 323.0f * 0.3f;
	static constexpr float HeadSettingsWidgetHeight = 60.0f;
	static constexpr int32 LockupNameSize = 74;
	static constexpr int32 LockupSubtitleSize = 38;
	static constexpr int32 LockupSubtitleSpacing = 260;
	static constexpr float LockupSubtitleInset = 6.0f;
	/** A heading longer than this many characters is lettered at the smaller size so it stays on the paper's dark side. */
	static constexpr int32 LongHeadingLength = 14;
	static constexpr int32 LongHeadingSize = 44;
	static constexpr int32 ClockRingSegments = 48;
	static constexpr float HeadingGap = 10.0f;
	static constexpr float SectionGap = 26.0f;
	static constexpr float ItemGap = 4.0f;
}

/** Short name for the constants where they are used. */
namespace UmbrellaUI = UmbrellaUIStyleConstants;

/** The four corners of a clock hand drawn as a blade. */
struct FUmbrellaHandBlade
{
	/** Short end behind the pivot. */
	FVector2D Tail = FVector2D::ZeroVector;
	/** Widest point, to either side of the hand's line. */
	FVector2D Left = FVector2D::ZeroVector;
	FVector2D Right = FVector2D::ZeroVector;
	FVector2D Tip = FVector2D::ZeroVector;
};

/** The one shared UI look: paper ground, ink-and-gold lettering, focus marks. Every screen builds with it. */
class UMBRELLAELLA_API FUmbrellaUIStyle
{
public:
	/** The game's own display face (Umbrella Storybook, small capitals). Titles, headings and buttons. */
	static FSlateFontInfo DisplayFont(int32 Size);

	/** The display face with its own letter spacing (1/1000 em), for a widely spaced subtitle. */
	static FSlateFontInfo DisplayFontSpaced(int32 Size, int32 LetterSpacing);

	/** A hand of a clock as a tapered blade from Center to Tip (canvas or Slate space). */
	static FUmbrellaHandBlade HandBlade(const FVector2D& Center, const FVector2D& Tip, float Width);

	/** Plain sans-serif body text (accessibility U14). */
	static FSlateFontInfo BodyFont(int32 Size);

	/** Size raised to the smallest allowed text size. */
	static int32 ClampTextSize(int32 Size);

	static FLinearColor Cream();
	static FLinearColor Dim();
	static FLinearColor Gold();
	static FLinearColor GoldBright();
	static FLinearColor Ink();
	static FLinearColor Warn();
	static FLinearColor Shadow();

	/** The painted ground; null when the texture is not imported (PaintGround then fills ink). */
	static const FSlateBrush* GroundBrush();
	static UTexture2D* ClockFaceTexture();
	/** The painted title lockup; null when the texture is not imported (the menu then letters the title in the display face). */
	static const FSlateBrush* TitleLockupBrush();
	/** The painted heading for a screen name ("Paused", "Settings"); null when none is painted or imported. */
	static const FSlateBrush* HeadingBrush(const FString& Heading);

	/** The display face as a font the HUD canvas can draw with; null when the face is missing. */
	static class UFont* DisplayCanvasFont();
	static const FSlateBrush* PanelBrush();
	static const FButtonStyle& TextButtonStyle();
	static const FSliderStyle& SliderStyle();
	static const FCheckBoxStyle& CheckBoxStyle();

	/** True when the embedded display face was built (false only if the bytes are missing). */
	static bool HasDisplayFont();

	/** Fills the geometry with the ground. Returns the layer used. */
	static int32 PaintGround(const FGeometry& Geometry, FSlateWindowElementList& Elements, int32 Layer);

	/** A filled diamond centred on Center (local space). */
	static void PaintDiamond(const FGeometry& Geometry, FSlateWindowElementList& Elements, int32 Layer, const FVector2f& Center, float Size, const FLinearColor& Color);

	/** A rule from From to To (local space) that fades out toward To. */
	static void PaintRule(const FGeometry& Geometry, FSlateWindowElementList& Elements, int32 Layer, const FVector2f& From, const FVector2f& To, const FLinearColor& Color, float EndAlpha);
};

/** The paper ground as a widget, for screens that are not built on SFlowBackground. */
class UMBRELLAELLA_API SUmbrellaGround : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SUmbrellaGround)
	{
	}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
	virtual FVector2D ComputeDesiredSize(float LayoutScaleMultiplier) const override;
};

/** A gold rule with a diamond at its head, set under headings. */
class UMBRELLAELLA_API SUmbrellaRule : public SLeafWidget
{
public:
	SLATE_BEGIN_ARGS(SUmbrellaRule)
	{
	}
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);
	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
	virtual FVector2D ComputeDesiredSize(float LayoutScaleMultiplier) const override;
};

/**
 * A lettered button with no plate. Keyboard or gamepad focus and mouse hover both light it: the label turns bright gold,
 * a rule runs under it, and (with Ornament) a rule and diamond point at it from the left, as on the title-screen reference.
 */
class UMBRELLAELLA_API SUmbrellaButton : public SButton
{
public:
	SLATE_BEGIN_ARGS(SUmbrellaButton)
	{
	}
	SLATE_ATTRIBUTE(FText, Text)
	SLATE_EVENT(FOnClicked, OnClicked)
	SLATE_ARGUMENT_DEFAULT(int32, FontSize) = UmbrellaUIStyleConstants::MinTextSize;
	/** Leave room at the left for the focus ornament (menu columns). */
	SLATE_ARGUMENT_DEFAULT(bool, Ornament) = false;
	/** Letter the label in the body face (key names, symbols). */
	SLATE_ARGUMENT_DEFAULT(bool, BodyFace) = false;
	/** True while this button stands for the current choice (a selected tab): it keeps its rule. */
	SLATE_ATTRIBUTE(bool, Selected)
	/** Label colour at rest; cream when unset. */
	SLATE_ATTRIBUTE(FLinearColor, RestColor)
	/**
	 * Lit only by Selected, never by its own focus or hover: for a menu that owns one selection, so exactly one row shows
	 * the mark whether the player last used the mouse, keys or a pad (SFlowMenu).
	 */
	SLATE_ARGUMENT_DEFAULT(bool, LitOnlyWhenSelected) = false;
	SLATE_END_ARGS()

	void Construct(const FArguments& InArgs);

	virtual int32 OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
		FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const override;
	virtual const FSlateBrush* GetFocusBrush() const override;

	/** True when the button shows its focus mark (focus, hover or selected). */
	bool IsLit() const;

	/** Height (local, from the button's top) of the focus diamond and its rule: the middle of the label's line. */
	static float OrnamentCenterY(float ButtonHeight);

private:
	FSlateColor GetLabelColor() const;

	bool bOrnament = false;
	bool bLitOnlyWhenSelected = false;
	TAttribute<bool> SelectedAttribute;
	TAttribute<FLinearColor> RestColorAttribute;
};
