#include "UI/Style/UmbrellaUIStyle.h"
#include "UI/Style/UmbrellaUIStyleAssets.h"
#include "Brushes/SlateRoundedBoxBrush.h"
#include "Engine/Font.h"
#include "Engine/FontFace.h"
#include "Engine/Texture2D.h"
#include "Fonts/CompositeFont.h"
#include "Rendering/DrawElements.h"
#include "Styling/CoreStyle.h"
#include "UObject/ConstructorHelpers.h"
#include "Widgets/Text/STextBlock.h"

#include "UmbrellaStorybookFont.inl"

/** Brushes and widget styles, built once at first use. */
struct FUmbrellaUIStyleData
{
	TSharedPtr<FCompositeFont> DisplayComposite;
	FSlateBrush GroundBrush;
	bool bGroundValid = false;
	TUniquePtr<FSlateRoundedBoxBrush> Panel;
	TUniquePtr<FSlateRoundedBoxBrush> SliderBar;
	TUniquePtr<FSlateRoundedBoxBrush> SliderThumb;
	TUniquePtr<FSlateRoundedBoxBrush> SliderThumbLit;
	TUniquePtr<FSlateRoundedBoxBrush> CheckOff;
	TUniquePtr<FSlateRoundedBoxBrush> CheckOffLit;
	TUniquePtr<FSlateRoundedBoxBrush> CheckOn;
	TUniquePtr<FSlateRoundedBoxBrush> CheckOnLit;
	FButtonStyle TextButton;
	FSliderStyle Slider;
	FCheckBoxStyle CheckBox;
};

namespace
{
	UUmbrellaUIStyleAssets* UmbrellaUIAssets()
	{
		// Own rooted instance (the class default stays read-only); its constructor finds the same textures.
		static UUmbrellaUIStyleAssets* Instance = nullptr;
		if (Instance == nullptr)
		{
			Instance = NewObject<UUmbrellaUIStyleAssets>(GetTransientPackage(), TEXT("UmbrellaUIStyleAssetsInstance"), RF_Transient);
			Instance->AddToRoot();
		}
		return Instance;
	}

	FUmbrellaUIStyleData& UmbrellaUIStyleData()
	{
		UUmbrellaUIStyleAssets* Assets = UmbrellaUIAssets();
		if (Assets->GetStyleData().IsValid())
		{
			return *Assets->GetStyleData();
		}
		const TSharedPtr<FUmbrellaUIStyleData> Data = MakeShared<FUmbrellaUIStyleData>();
		Assets->SetStyleData(Data);

		// The display face from the embedded bytes: no loose file to stage, nothing to cook.
		UFontFace* Face = NewObject<UFontFace>(Assets, TEXT("UmbrellaStorybookFace"), RF_Transient);
		Face->LoadingPolicy = EFontLoadingPolicy::Inline;
		Face->Hinting = EFontHinting::None;
		TArray<uint8> Bytes;
		Bytes.Append(GUmbrellaStorybookFontData, GUmbrellaStorybookFontSize);
		Face->FontFaceData->SetData(MoveTemp(Bytes));
		Data->DisplayComposite = MakeShared<FCompositeFont>();
		FTypefaceEntry& Entry = Data->DisplayComposite->DefaultTypeface.Fonts.Emplace_GetRef(FName(TEXT("Regular")));
		Entry.Font = FFontData(Face);
		// Characters the face does not draw fall back to the engine's body face.
		const FSlateFontInfo Body = FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), UmbrellaUI::MinTextSize);
		if (Body.CompositeFont.IsValid() && Body.CompositeFont->DefaultTypeface.Fonts.Num() > 0)
		{
			Data->DisplayComposite->FallbackTypeface.Typeface.Fonts.Add(Body.CompositeFont->DefaultTypeface.Fonts[0]);
		}

		UFont* CanvasFont = NewObject<UFont>(Assets, TEXT("UmbrellaStorybookCanvasFont"), RF_Transient);
		CanvasFont->FontCacheType = EFontCacheType::Runtime;
		CanvasFont->LegacyFontSize = UmbrellaUI::CanvasFontSize;
		CanvasFont->GetMutableInternalCompositeFont() = *Data->DisplayComposite;
		Assets->SetDisplayFonts(Face, CanvasFont);

		if (UTexture2D* Ground = Assets->GetGround())
		{
			Data->GroundBrush.SetResourceObject(Ground);
			Data->GroundBrush.ImageSize = FVector2D(UmbrellaUI::GroundWidth, UmbrellaUI::GroundHeight);
			Data->GroundBrush.DrawAs = ESlateBrushDrawType::Image;
			Data->bGroundValid = true;
		}

		const FLinearColor Ink = FUmbrellaUIStyle::Ink();
		const FLinearColor Gold = FUmbrellaUIStyle::Gold();
		const FLinearColor Bright = FUmbrellaUIStyle::GoldBright();
		Data->Panel = MakeUnique<FSlateRoundedBoxBrush>(Ink.CopyWithNewOpacity(UmbrellaUI::PanelFillAlpha), UmbrellaUI::PanelCornerRadius, Gold.CopyWithNewOpacity(UmbrellaUI::PanelBorderAlpha), UmbrellaUI::PanelBorderWidth);

		const FSlateBrush* None = FStyleDefaults::GetNoBrush();
		Data->TextButton = FButtonStyle().SetNormal(*None).SetHovered(*None).SetPressed(*None).SetDisabled(*None)
			.SetNormalPadding(FMargin(0.0f)).SetPressedPadding(FMargin(0.0f));

		Data->SliderBar = MakeUnique<FSlateRoundedBoxBrush>(Gold.CopyWithNewOpacity(UmbrellaUI::DimBarAlpha), UmbrellaUI::SliderBarThickness * 0.5f);
		Data->SliderThumb = MakeUnique<FSlateRoundedBoxBrush>(Gold, UmbrellaUI::SliderThumbSize * 0.5f, Ink, UmbrellaUI::CheckBorderWidth, FVector2f(UmbrellaUI::SliderThumbSize, UmbrellaUI::SliderThumbSize));
		Data->SliderThumbLit = MakeUnique<FSlateRoundedBoxBrush>(Bright, UmbrellaUI::SliderThumbSize * 0.5f, Ink, UmbrellaUI::CheckBorderWidth, FVector2f(UmbrellaUI::SliderThumbSize, UmbrellaUI::SliderThumbSize));
		Data->Slider = FSliderStyle()
			.SetNormalBarImage(*Data->SliderBar).SetHoveredBarImage(*Data->SliderBar).SetDisabledBarImage(*Data->SliderBar)
			.SetNormalThumbImage(*Data->SliderThumb).SetHoveredThumbImage(*Data->SliderThumbLit).SetDisabledThumbImage(*Data->SliderThumb)
			.SetBarThickness(UmbrellaUI::SliderBarThickness);

		const FVector2f CheckImage(UmbrellaUI::CheckSize, UmbrellaUI::CheckSize);
		Data->CheckOff = MakeUnique<FSlateRoundedBoxBrush>(Ink.CopyWithNewOpacity(UmbrellaUI::PanelFillAlpha), UmbrellaUI::CheckInnerRadius, Gold, UmbrellaUI::CheckBorderWidth, CheckImage);
		Data->CheckOffLit = MakeUnique<FSlateRoundedBoxBrush>(Ink.CopyWithNewOpacity(UmbrellaUI::PanelFillAlpha), UmbrellaUI::CheckInnerRadius, Bright, UmbrellaUI::CheckBorderWidth, CheckImage);
		Data->CheckOn = MakeUnique<FSlateRoundedBoxBrush>(Gold, UmbrellaUI::CheckInnerRadius, Ink, UmbrellaUI::CheckBorderWidth * 2.0f, CheckImage);
		Data->CheckOnLit = MakeUnique<FSlateRoundedBoxBrush>(Bright, UmbrellaUI::CheckInnerRadius, Ink, UmbrellaUI::CheckBorderWidth * 2.0f, CheckImage);
		Data->CheckBox = FCheckBoxStyle()
			.SetCheckBoxType(ESlateCheckBoxType::CheckBox)
			.SetUncheckedImage(*Data->CheckOff).SetUncheckedHoveredImage(*Data->CheckOffLit).SetUncheckedPressedImage(*Data->CheckOffLit)
			.SetCheckedImage(*Data->CheckOn).SetCheckedHoveredImage(*Data->CheckOnLit).SetCheckedPressedImage(*Data->CheckOnLit)
			.SetUndeterminedImage(*Data->CheckOff).SetUndeterminedHoveredImage(*Data->CheckOffLit).SetUndeterminedPressedImage(*Data->CheckOffLit)
			.SetPadding(FMargin(UmbrellaUI::OrnamentGap, 0.0f, 0.0f, 0.0f));
		return *Data;
	}
}

UUmbrellaUIStyleAssets::UUmbrellaUIStyleAssets()
{
	static ConstructorHelpers::FObjectFinderOptional<UTexture2D> GroundFinder(TEXT("/Game/UmbrellaElla/UI/T_UI_Ground_PH.T_UI_Ground_PH"));
	static ConstructorHelpers::FObjectFinderOptional<UTexture2D> ClockFinder(TEXT("/Game/UmbrellaElla/UI/T_UI_ClockFace_PH.T_UI_ClockFace_PH"));
	Ground = GroundFinder.Get();
	ClockFace = ClockFinder.Get();
}

void UUmbrellaUIStyleAssets::SetDisplayFonts(UFontFace* InFace, UFont* InCanvasFont)
{
	DisplayFace = InFace;
	DisplayCanvasFont = InCanvasFont;
}

FSlateFontInfo FUmbrellaUIStyle::DisplayFont(int32 Size)
{
	FSlateFontInfo Info(UmbrellaUIStyleData().DisplayComposite, static_cast<float>(ClampTextSize(Size)), FName(TEXT("Regular")));
	Info.LetterSpacing = UmbrellaUI::DisplayLetterSpacing;
	return Info;
}

FSlateFontInfo FUmbrellaUIStyle::DisplayFontSpaced(int32 Size, int32 LetterSpacing)
{
	FSlateFontInfo Info = DisplayFont(Size);
	Info.LetterSpacing = LetterSpacing;
	return Info;
}

FUmbrellaHandBlade FUmbrellaUIStyle::HandBlade(const FVector2D& Center, const FVector2D& Tip, float Width)
{
	const FVector2D Along = Tip - Center;
	const FVector2D Side = FVector2D(-Along.Y, Along.X).GetSafeNormal() * (Width * 0.5);
	const FVector2D Widest = Center + Along * UmbrellaUI::HandBladeWidest;
	FUmbrellaHandBlade Blade;
	Blade.Tail = Center - Along * UmbrellaUI::HandBladeTail;
	Blade.Left = Widest + Side;
	Blade.Right = Widest - Side;
	Blade.Tip = Tip;
	return Blade;
}

FSlateFontInfo FUmbrellaUIStyle::BodyFont(int32 Size)
{
	return FCoreStyle::GetDefaultFontStyle(TEXT("Regular"), ClampTextSize(Size));
}

int32 FUmbrellaUIStyle::ClampTextSize(int32 Size)
{
	return FMath::Max(Size, UmbrellaUI::MinTextSize);
}

FLinearColor FUmbrellaUIStyle::Cream() { return FLinearColor::FromSRGBColor(UmbrellaUI::Cream); }
FLinearColor FUmbrellaUIStyle::Dim() { return FLinearColor::FromSRGBColor(UmbrellaUI::Dim); }
FLinearColor FUmbrellaUIStyle::Gold() { return FLinearColor::FromSRGBColor(UmbrellaUI::Gold); }
FLinearColor FUmbrellaUIStyle::GoldBright() { return FLinearColor::FromSRGBColor(UmbrellaUI::GoldBright); }
FLinearColor FUmbrellaUIStyle::Ink() { return FLinearColor::FromSRGBColor(UmbrellaUI::Ink); }
FLinearColor FUmbrellaUIStyle::Warn() { return FLinearColor::FromSRGBColor(UmbrellaUI::Warn); }
FLinearColor FUmbrellaUIStyle::Shadow() { return Ink().CopyWithNewOpacity(UmbrellaUI::ShadowAlpha); }

const FSlateBrush* FUmbrellaUIStyle::GroundBrush()
{
	FUmbrellaUIStyleData& Data = UmbrellaUIStyleData();
	return Data.bGroundValid ? &Data.GroundBrush : nullptr;
}

UTexture2D* FUmbrellaUIStyle::ClockFaceTexture()
{
	return UmbrellaUIAssets()->GetClockFace();
}

UFont* FUmbrellaUIStyle::DisplayCanvasFont()
{
	UmbrellaUIStyleData();
	return HasDisplayFont() ? UmbrellaUIAssets()->GetDisplayCanvasFont() : nullptr;
}

const FSlateBrush* FUmbrellaUIStyle::PanelBrush() { return UmbrellaUIStyleData().Panel.Get(); }
const FButtonStyle& FUmbrellaUIStyle::TextButtonStyle() { return UmbrellaUIStyleData().TextButton; }
const FSliderStyle& FUmbrellaUIStyle::SliderStyle() { return UmbrellaUIStyleData().Slider; }
const FCheckBoxStyle& FUmbrellaUIStyle::CheckBoxStyle() { return UmbrellaUIStyleData().CheckBox; }

bool FUmbrellaUIStyle::HasDisplayFont()
{
	const FUmbrellaUIStyleData& Data = UmbrellaUIStyleData();
	const UFontFace* Face = UmbrellaUIAssets()->GetDisplayFace();
	return Data.DisplayComposite.IsValid() && Face != nullptr && Face->GetFontFaceData()->HasData();
}

int32 FUmbrellaUIStyle::PaintGround(const FGeometry& Geometry, FSlateWindowElementList& Elements, int32 Layer)
{
	const FSlateBrush* White = FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"));
	FSlateDrawElement::MakeBox(Elements, Layer, Geometry.ToPaintGeometry(), White, ESlateDrawEffect::None, Ink());
	if (const FSlateBrush* Ground = GroundBrush())
	{
		FSlateDrawElement::MakeBox(Elements, Layer + 1, Geometry.ToPaintGeometry(), Ground, ESlateDrawEffect::None, FLinearColor::White);
	}
	return Layer + 1;
}

void FUmbrellaUIStyle::PaintDiamond(const FGeometry& Geometry, FSlateWindowElementList& Elements, int32 Layer, const FVector2f& Center, float Size, const FLinearColor& Color)
{
	const FSlateBrush* White = FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"));
	const FVector2f Box(Size, Size);
	FSlateDrawElement::MakeRotatedBox(Elements, Layer, Geometry.ToPaintGeometry(Box, FSlateLayoutTransform(Center - Box * 0.5f)), White,
		ESlateDrawEffect::None, UmbrellaUI::QuarterTurnRadians, FVector2D(Box.X * 0.5, Box.Y * 0.5), FSlateDrawElement::RelativeToElement, Color);
}

void FUmbrellaUIStyle::PaintRule(const FGeometry& Geometry, FSlateWindowElementList& Elements, int32 Layer, const FVector2f& From, const FVector2f& To, const FLinearColor& Color, float EndAlpha)
{
	const float Thickness = UmbrellaUI::RuleThickness;
	const FVector2f Size(FMath::Max(1.0f, To.X - From.X), Thickness);
	TArray<FSlateGradientStop> Stops;
	Stops.Emplace(FVector2f(0.0f, 0.0f), Color);
	Stops.Emplace(FVector2f(Size.X, 0.0f), Color.CopyWithNewOpacity(Color.A * EndAlpha));
	FSlateDrawElement::MakeGradient(Elements, Layer, Geometry.ToPaintGeometry(Size, FSlateLayoutTransform(FVector2f(From.X, From.Y - Thickness * 0.5f))), Stops, Orient_Vertical);
}

void SUmbrellaGround::Construct(const FArguments& InArgs)
{
}

FVector2D SUmbrellaGround::ComputeDesiredSize(float LayoutScaleMultiplier) const
{
	return FVector2D(1.0, 1.0);
}

int32 SUmbrellaGround::OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	return FUmbrellaUIStyle::PaintGround(AllottedGeometry, OutDrawElements, LayerId);
}

void SUmbrellaRule::Construct(const FArguments& InArgs)
{
}

FVector2D SUmbrellaRule::ComputeDesiredSize(float LayoutScaleMultiplier) const
{
	return FVector2D(UmbrellaUI::OrnamentWidth, UmbrellaUI::RuleHeight);
}

int32 SUmbrellaRule::OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	const FVector2f Size = AllottedGeometry.GetLocalSize();
	const float Mid = Size.Y * 0.5f;
	const FLinearColor Gold = FUmbrellaUIStyle::Gold();
	const FLinearColor Line = Gold.CopyWithNewOpacity(UmbrellaUI::RuleLineAlpha);
	const float PommelX = UmbrellaUI::DiamondSize + UmbrellaUI::RuleDiamondInset;
	const FVector2f Pivot(UmbrellaUI::RulePivotAt, Mid);

	// Pommel, then the short tail to the pivot ring.
	FUmbrellaUIStyle::PaintDiamond(AllottedGeometry, OutDrawElements, LayerId + 1, FVector2f(PommelX, Mid), UmbrellaUI::DiamondSize, Gold);
	TArray<FVector2f> Tail;
	Tail.Add(FVector2f(PommelX + UmbrellaUI::DiamondSize * 0.5f, Mid));
	Tail.Add(FVector2f(Pivot.X - UmbrellaUI::RulePivotRadius, Mid));
	FSlateDrawElement::MakeLines(OutDrawElements, LayerId, AllottedGeometry.ToPaintGeometry(), MoveTemp(Tail), ESlateDrawEffect::None, Line, true, UmbrellaUI::RulePivotLine);

	TArray<FVector2f> Ring;
	for (int32 Segment = 0; Segment <= UmbrellaUI::RulePivotSegments; ++Segment)
	{
		const float Angle = UE_TWO_PI * static_cast<float>(Segment) / static_cast<float>(UmbrellaUI::RulePivotSegments);
		Ring.Add(Pivot + FVector2f(FMath::Cos(Angle), FMath::Sin(Angle)) * UmbrellaUI::RulePivotRadius);
	}
	FSlateDrawElement::MakeLines(OutDrawElements, LayerId, AllottedGeometry.ToPaintGeometry(), MoveTemp(Ring), ESlateDrawEffect::None, Line, true, UmbrellaUI::RulePivotLine);
	FUmbrellaUIStyle::PaintDiamond(AllottedGeometry, OutDrawElements, LayerId + 1, Pivot, UmbrellaUI::DiamondSize * 0.5f, Gold);

	// The needle: widest just past the pivot, tapering to a point and fading at the far end.
	const float NeedleFrom = Pivot.X + UmbrellaUI::RulePivotRadius;
	const float Swell = NeedleFrom + (Size.X - NeedleFrom) * UmbrellaUI::HandBladeTail;
	TArray<FVector2f> Upper;
	Upper.Add(FVector2f(NeedleFrom, Mid));
	Upper.Add(FVector2f(Swell, Mid - UmbrellaUI::RuleNeedleWidth * 0.5f));
	Upper.Add(FVector2f(Size.X, Mid));
	TArray<FVector2f> Lower;
	Lower.Add(FVector2f(NeedleFrom, Mid));
	Lower.Add(FVector2f(Swell, Mid + UmbrellaUI::RuleNeedleWidth * 0.5f));
	Lower.Add(FVector2f(Size.X, Mid));
	FSlateDrawElement::MakeLines(OutDrawElements, LayerId, AllottedGeometry.ToPaintGeometry(), MoveTemp(Upper), ESlateDrawEffect::None, Line, true, UmbrellaUI::RulePivotLine);
	FSlateDrawElement::MakeLines(OutDrawElements, LayerId, AllottedGeometry.ToPaintGeometry(), MoveTemp(Lower), ESlateDrawEffect::None, Line, true, UmbrellaUI::RulePivotLine);
	FUmbrellaUIStyle::PaintRule(AllottedGeometry, OutDrawElements, LayerId, FVector2f(NeedleFrom, Mid), FVector2f(Size.X, Mid), Line, UmbrellaUI::UnderlineFadeAlpha);
	return LayerId + 1;
}

void SUmbrellaButton::Construct(const FArguments& InArgs)
{
	bOrnament = InArgs._Ornament;
	SelectedAttribute = InArgs._Selected;
	RestColorAttribute = InArgs._RestColor;
	const float Left = UmbrellaUI::ButtonPadX + (bOrnament ? UmbrellaUI::OrnamentWidth + UmbrellaUI::OrnamentGap : 0.0f);
	SButton::Construct(SButton::FArguments()
		.ButtonStyle(&FUmbrellaUIStyle::TextButtonStyle())
		.ContentPadding(FMargin(Left, UmbrellaUI::ButtonPadY, UmbrellaUI::ButtonPadX, UmbrellaUI::ButtonPadY + UmbrellaUI::UnderlineDrop))
		.HAlign(HAlign_Left)
		.VAlign(VAlign_Center)
		.OnClicked(InArgs._OnClicked)
		[
			SNew(STextBlock)
			.Text(InArgs._Text)
			.Font(InArgs._BodyFace ? FUmbrellaUIStyle::BodyFont(InArgs._FontSize) : FUmbrellaUIStyle::DisplayFont(InArgs._FontSize))
			.ColorAndOpacity(this, &SUmbrellaButton::GetLabelColor)
			.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset))
			.ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
		]);
}

bool SUmbrellaButton::IsLit() const
{
	return IsEnabled() && (HasKeyboardFocus() || HasAnyUserFocus().IsSet() || IsHovered() || SelectedAttribute.Get(false));
}

FSlateColor SUmbrellaButton::GetLabelColor() const
{
	if (!IsEnabled())
	{
		return FUmbrellaUIStyle::Dim().CopyWithNewOpacity(UmbrellaUI::DisabledAlpha);
	}
	if (IsPressed() || HasKeyboardFocus() || HasAnyUserFocus().IsSet() || IsHovered())
	{
		return FUmbrellaUIStyle::GoldBright();
	}
	return RestColorAttribute.IsSet() ? RestColorAttribute.Get() : FUmbrellaUIStyle::Cream();
}

const FSlateBrush* SUmbrellaButton::GetFocusBrush() const
{
	// The button draws its own focus mark; the default dashed rectangle would sit on top of it.
	return FStyleDefaults::GetNoBrush();
}

int32 SUmbrellaButton::OnPaint(const FPaintArgs& Args, const FGeometry& AllottedGeometry, const FSlateRect& MyCullingRect,
	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
{
	int32 Layer = SButton::OnPaint(Args, AllottedGeometry, MyCullingRect, OutDrawElements, LayerId, InWidgetStyle, bParentEnabled);
	if (!IsLit())
	{
		return Layer;
	}
	++Layer;
	const FVector2f Size = AllottedGeometry.GetLocalSize();
	const FLinearColor Gold = FUmbrellaUIStyle::Gold();
	const float TextLeft = UmbrellaUI::ButtonPadX + (bOrnament ? UmbrellaUI::OrnamentWidth + UmbrellaUI::OrnamentGap : 0.0f);
	const float Under = Size.Y - UmbrellaUI::UnderlineDrop;
	FUmbrellaUIStyle::PaintRule(AllottedGeometry, OutDrawElements, Layer, FVector2f(TextLeft, Under), FVector2f(Size.X, Under), Gold, UmbrellaUI::UnderlineFadeAlpha);
	if (bOrnament)
	{
		const float Mid = (Size.Y - UmbrellaUI::UnderlineDrop) * 0.5f;
		const float DiamondX = UmbrellaUI::ButtonPadX + UmbrellaUI::OrnamentWidth - UmbrellaUI::DiamondSize;
		// The rule fades in from the left and ends in the diamond that points at the label.
		TArray<FSlateGradientStop> Stops;
		Stops.Emplace(FVector2f(0.0f, 0.0f), Gold.CopyWithNewOpacity(UmbrellaUI::UnderlineFadeAlpha));
		Stops.Emplace(FVector2f(UmbrellaUI::OrnamentWidth - UmbrellaUI::DiamondSize * 2.0f, 0.0f), Gold);
		FSlateDrawElement::MakeGradient(OutDrawElements, Layer,
			AllottedGeometry.ToPaintGeometry(FVector2f(UmbrellaUI::OrnamentWidth - UmbrellaUI::DiamondSize * 2.0f, UmbrellaUI::RuleThickness), FSlateLayoutTransform(FVector2f(UmbrellaUI::ButtonPadX, Mid - UmbrellaUI::RuleThickness * 0.5f))),
			Stops, Orient_Vertical);
		FUmbrellaUIStyle::PaintDiamond(AllottedGeometry, OutDrawElements, Layer + 1, FVector2f(DiamondX, Mid), UmbrellaUI::DiamondSize, FUmbrellaUIStyle::GoldBright());
	}
	return Layer + 1;
}
