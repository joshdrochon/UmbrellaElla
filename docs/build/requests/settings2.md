# Requests from settings2 (FLOW-44, FLOW-45)

The settings API for readers outside Settings is `Settings/UmbrellaAccessibility.h` (namespace `UmbrellaAccessibility`).
Every function takes a world context and returns the shipped default when no settings subsystem exists:
`GetTextScalePercent` (100 to 200), `GetTextScale` (1.0 to 2.0), `IsReducedMotion`, `IsReducedFlash`, `GetShakeScale`
(0 under reduced motion, else 1), plus the pure `ScaledFontSize(Base, Percent)`. Values change only on Save;
`USettingsMenuSubsystem::OnSettingsSaved()` fires after every Save so a screen that caches them can re-read.
Callers guard their read with their own FLOW_45 check (module_check rule M).

## 1. Text scale in the shared UI style (artui lane)
The artui area's shared UI style multiplies every font size by `UmbrellaAccessibility::GetTextScale(WorldContext)`
(or `ScaledFontSize(Base, GetTextScalePercent(WorldContext))`) and rebuilds on `OnSettingsSaved()`. That covers the HUD
clock text, the flow menus and the story/tutorial text, which replaces item 6 (text-size half) of
`docs/build/requests/settings.md`. The settings menu itself already scales (`USettingsMenuWidget::ScaledFont`).

## 2. Screen shake (feel / Feedback lane, when a shake exists)
No camera or screen shake exists in `Source/` today (`grep -ri shake Source` finds only this API). Whoever adds the
`pipeline/feel/feel.json` shakes multiplies each amplitude by `UmbrellaAccessibility::GetShakeScale(WorldContext)`, so
reduced motion zeroes them (`pipeline/ui/accessibility.md` E8).

## 3. Gameplay backdrop motion (visuals lane, `Feedback/Background`)
Reduced motion reaches the XP ring (`UXpRingWidget::SetReducedMotion`, works in the shipping target). Menu backgrounds and the Keeper hover are not reached yet: see items 5 and 6.
The gameplay backdrop's parallax constants are not tuning, so Settings cannot reach them. Request: in
`UUmbrellaBackdropSubsystem::ScrollTo`, when `UmbrellaAccessibility::IsReducedMotion(this)` use parallax 0 for every
layer (fixed to the camera, no relative slide), and tag each layer actor `BackgroundMotion` (accessibility E8).

## 4. Tutorial developer toggle (flow lane)
Game Options "First-play tutorials" (Director's Cut, developer option `EDeveloperOption::Tutorial`) has no tuning
number. Where flow decides to show a first-play tutorial, skip it when
`Settings->GetDeveloperOption(EDeveloperOption::Tutorial) == DeveloperOptionLimits::ToggleOff`. The read returns the
default (on) outside Director's Cut, so Start Game is unchanged.

## 5. Play mode (flow lane, optional)
Settings now follows `AUmbrellaPlayerController::GetPlayMode()` itself (every frame, and on `OpenSettings`), so
developer options never reach a Start Game run. Calling `USettingsMenuSubsystem::SetPlayMode` from `StartMode` would
apply them one frame earlier; not required.

## 5. Menu background stillness (flow lane)
Nothing reads `UmbrellaAccessibility::IsReducedMotion` in Flow yet. Where the menu background applies `Flow.BackgroundDriftSpeed`,
`BackgroundSwayAmplitude` and `FallingShapeMinSpeed/MaxSpeed`, use 0 for each when `IsFeatureEnabled(FLOW_45)` and
`UmbrellaAccessibility::IsReducedMotion(this)` (local value, no tuning write; works in the submission build).
(`BackgroundDriftSpeed` has no reader at all today.)

## 6. Keeper hover (keeper lane)
Where the Keeper applies `Keeper.HoverAmplitude`, use 0 when `IsFeatureEnabled(FLOW_45)` and
`UmbrellaAccessibility::IsReducedMotion(this)`. `HoverAmplitude` has no reader today; read it locally, never write the tuning.

## 7. World-free accessibility readers (flow, artui, visuals lanes; moved out of settings2 on review, Nov 13)
The settings2 lane brief allows only camera-shake reader lines outside `Settings/**`, so these reader edits were
reverted from `area/settings2` and are requested here instead. Settings already publishes the saved values with no
world context (`UmbrellaAccessibility::PublishedFontSize`, `PublishedTextScale`, `IsPublishedReducedMotion`; flag
FLOW_45 checked inside; test `UmbrellaElla.Settings.World.AccessibilityReachesReaders`). Owners apply the lines in their
lane; the review fixes are already in this diff (own header first, one VFX_10 check inside `VfxCatalog::FrameAt`).
- visuals (`Feedback/Background`, `Feedback/Vfx`): backdrop parallax 0 and looping VFX hold frame 0 under reduced motion.
- flow/artui (`UI/Menus`, `UI/Story`, `UI/UmbrellaHUD.cpp`, `Flow/UmbrellaPlayerController.cpp`): fonts by the saved
  text scale, flow menu backdrop still under reduced motion. Item 1 (shared UI style) covers the same need if done there.

```diff
diff --git a/Source/UmbrellaElla/Private/Feedback/Background/UmbrellaBackdropSubsystem.cpp b/Source/UmbrellaElla/Private/Feedback/Background/UmbrellaBackdropSubsystem.cpp
index 69980ed6..d2c57696 100644
--- a/Source/UmbrellaElla/Private/Feedback/Background/UmbrellaBackdropSubsystem.cpp
+++ b/Source/UmbrellaElla/Private/Feedback/Background/UmbrellaBackdropSubsystem.cpp
@@ -1,4 +1,5 @@
 #include "Feedback/Background/UmbrellaBackdropSubsystem.h"
+#include "Settings/UmbrellaAccessibility.h"
 #include "Components/StaticMeshComponent.h"
 #include "Core/UmbrellaDrawOrder.h"
 #include "Engine/StaticMesh.h"
@@ -222,12 +223,14 @@ int32 UUmbrellaBackdropSubsystem::CountCoveredStages() const
 
 void UUmbrellaBackdropSubsystem::ScrollTo(float CameraX)
 {
+	// Reduced motion (accessibility): parallax 0, every layer fixed to the camera with no relative slide.
+	const bool bStill = UmbrellaAccessibility::IsPublishedReducedMotion();
 	for (int32 Index = 0; Index < Layers.Num(); ++Index)
 	{
 		if (IsValid(Layers[Index]))
 		{
 			FVector Location = Layers[Index]->GetActorLocation();
-			Location.X = LayerXForCamera(CameraX, BuiltSpecs[Index].Parallax);
+			Location.X = LayerXForCamera(CameraX, bStill ? 0.0f : BuiltSpecs[Index].Parallax);
 			Layers[Index]->SetActorLocation(Location);
 		}
 	}
diff --git a/Source/UmbrellaElla/Private/Feedback/Vfx/UmbrellaVfxDirectorSubsystem.cpp b/Source/UmbrellaElla/Private/Feedback/Vfx/UmbrellaVfxDirectorSubsystem.cpp
index 6c86a1dd..4d7aa5f3 100644
--- a/Source/UmbrellaElla/Private/Feedback/Vfx/UmbrellaVfxDirectorSubsystem.cpp
+++ b/Source/UmbrellaElla/Private/Feedback/Vfx/UmbrellaVfxDirectorSubsystem.cpp
@@ -24,6 +24,7 @@
 #include "Feedback/Vfx/VfxLightPolicy.h"
 #include "Feedback/Vfx/VfxSheetVisual.h"
 #include "GameFramework/Actor.h"
 #include "Harness/UmbrellaFeatureFlags.h"
 #include "Kismet/GameplayStatics.h"
+#include "Settings/UmbrellaAccessibility.h"
 #include "Camera/PlayerCameraManager.h"
@@ -821,7 +822,7 @@ void UUmbrellaVfxDirectorSubsystem::StepShaft(float DeltaSeconds)
 		Part->SetActorLocation(Location);
 		VfxSheetVisual::Resize(Visual, Sizes[Index]);
 		VfxSheetVisual::SetOpacity(Visual, Opacities[Index]);
-		VfxSheetVisual::SetFrame(Visual, VfxCatalog::FrameAt(*Row, Clock));
+		VfxSheetVisual::SetFrame(Visual, VfxCatalog::FrameAt(*Row, Clock, UmbrellaAccessibility::IsPublishedReducedMotion()));
 		Part->SetActorHiddenInGame(Opacities[Index] <= 0.0f);
 	}
 }
@@ -853,7 +854,7 @@ void UUmbrellaVfxDirectorSubsystem::StepLive()
 			At = FVector(Target.X, At.Y, Target.Z);
 		}
 		Actor->SetActorLocation(At);
-		int32 ShownFrame = VfxCatalog::FrameAt(*Effect.Row, Elapsed);
+		int32 ShownFrame = VfxCatalog::FrameAt(*Effect.Row, Elapsed, UmbrellaAccessibility::IsPublishedReducedMotion());
 #if !UE_BUILD_SHIPPING
 		if (!DemoKey.IsNone() && Effect.Key == DemoKey)
 		{
diff --git a/Source/UmbrellaElla/Private/Feedback/Vfx/VfxCatalog.cpp b/Source/UmbrellaElla/Private/Feedback/Vfx/VfxCatalog.cpp
index 0c8e8fde..7db2eead 100644
--- a/Source/UmbrellaElla/Private/Feedback/Vfx/VfxCatalog.cpp
+++ b/Source/UmbrellaElla/Private/Feedback/Vfx/VfxCatalog.cpp
@@ -1,6 +1,6 @@
 #include "Feedback/Vfx/VfxCatalog.h"
 #include "Core/UmbrellaDrawOrder.h"
+#include "Harness/UmbrellaFeatureFlags.h"
 
 TConstArrayView<FVfxArtRow> VfxCatalog::Rows()
 {
 	return MakeArrayView(VfxCatalogData::Rows);
@@ -49,6 +49,12 @@ int32 VfxCatalog::FrameAt(const FVfxArtRow& Row, float Elapsed)
 	return Row.bLoop ? Raw % Row.Frames : FMath::Min(Raw, Row.Frames - 1);
 }
 
+int32 VfxCatalog::FrameAt(const FVfxArtRow& Row, float Elapsed, bool bReducedMotion)
+{
+	// Reduced motion: a looping effect holds one still frame; one-shots still play, they are short feedback.
+	return (bReducedMotion && Row.bLoop && IsFeatureEnabled(EFeatureId::VFX_10)) ? 0 : FrameAt(Row, Elapsed);
+}
+
 bool VfxCatalog::IsFinished(const FVfxArtRow& Row, float Elapsed)
 {
 	return !Row.bLoop && Elapsed >= Duration(Row);
diff --git a/Source/UmbrellaElla/Private/Flow/UmbrellaPlayerController.cpp b/Source/UmbrellaElla/Private/Flow/UmbrellaPlayerController.cpp
index 8831433b..d085a0de 100644
--- a/Source/UmbrellaElla/Private/Flow/UmbrellaPlayerController.cpp
+++ b/Source/UmbrellaElla/Private/Flow/UmbrellaPlayerController.cpp
@@ -1,4 +1,5 @@
 #include "Flow/UmbrellaPlayerController.h"
+#include "Settings/UmbrellaAccessibility.h"
 #include "Core/UmbrellaEvent.h"
 #include "Core/UmbrellaEventBus.h"
 #include "Core/UmbrellaGameMode.h"
@@ -811,7 +812,7 @@ void AUmbrellaPlayerController::ShowScreenWidget()
 			ScreenWidget = SNew(SBox).HAlign(HAlign_Center).VAlign(VAlign_Top).Visibility(EVisibility::HitTestInvisible)
 			[
 				SNew(STextBlock).Text(FText::FromString(TEXT("Director's Cut")))
-					.Font(FUmbrellaUIStyle::DisplayFont(Tuning.MenuFontSize)).ColorAndOpacity(FUmbrellaUIStyle::Gold())
+					.Font(FUmbrellaUIStyle::DisplayFont(UmbrellaAccessibility::PublishedFontSize(Tuning.MenuFontSize))).ColorAndOpacity(FUmbrellaUIStyle::Gold())
 					.ShadowOffset(FVector2D(UmbrellaUIStyleConstants::ShadowOffset, UmbrellaUIStyleConstants::ShadowOffset))
 					.ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
 			];
diff --git a/Source/UmbrellaElla/Private/UI/Menus/FlowMenuWidgets.cpp b/Source/UmbrellaElla/Private/UI/Menus/FlowMenuWidgets.cpp
index 1cf443d1..bf002b13 100644
--- a/Source/UmbrellaElla/Private/UI/Menus/FlowMenuWidgets.cpp
+++ b/Source/UmbrellaElla/Private/UI/Menus/FlowMenuWidgets.cpp
@@ -1,3 +1,4 @@
 #include "UI/Menus/FlowMenuWidgets.h"
+#include "Settings/UmbrellaAccessibility.h"
 #include "Flow/FlowMenuText.h"
 #include "Flow/FlowRules.h"
@@ -45,7 +46,9 @@ int32 SFlowBackground::OnPaint(const FPaintArgs& Args, const FGeometry& Allotted
 	FSlateWindowElementList& OutDrawElements, int32 LayerId, const FWidgetStyle& InWidgetStyle, bool bParentEnabled) const
 {
 	const FVector2f Size = AllottedGeometry.GetLocalSize();
-	const float Time = static_cast<float>(Args.GetCurrentTime());
+	const bool bStill = UmbrellaAccessibility::IsPublishedReducedMotion();
+	// Reduced motion (accessibility): the backdrop holds still, no fall, sway or tick.
+	const float Time = bStill ? 0.0f : static_cast<float>(Args.GetCurrentTime());
 	const FSlateBrush* White = FCoreStyle::Get().GetBrush(TEXT("WhiteBrush"));
 	const FSlateRoundedBoxBrush Round(FLinearColor::White, Size.Y);
 	const FLinearColor Gold = FUmbrellaUIStyle::Gold();
@@ -138,14 +141,14 @@ void SFlowMenu::Construct(const FArguments& InArgs)
 		{
 			Column->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(TextInset, 0.0f, 0.0f, 0.0f)
 			[
-				SNew(STextBlock).Text(FText::FromString(Name)).Font(FUmbrellaUIStyle::DisplayFont(UmbrellaUI::LockupNameSize))
+				SNew(STextBlock).Text(FText::FromString(Name)).Font(FUmbrellaUIStyle::DisplayFont(UmbrellaAccessibility::PublishedFontSize(UmbrellaUI::LockupNameSize)))
 					.ColorAndOpacity(FUmbrellaUIStyle::Cream())
 					.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
 			];
 			Column->AddSlot().AutoHeight().HAlign(HAlign_Left).Padding(TextInset + UmbrellaUI::LockupSubtitleInset, 0.0f, 0.0f, 0.0f)
 			[
 				SNew(STextBlock).Text(FText::FromString(Subtitle.Replace(TEXT("\n"), TEXT(" "))))
-					.Font(FUmbrellaUIStyle::DisplayFontSpaced(UmbrellaUI::LockupSubtitleSize, UmbrellaUI::LockupSubtitleSpacing))
+					.Font(FUmbrellaUIStyle::DisplayFontSpaced(UmbrellaAccessibility::PublishedFontSize(UmbrellaUI::LockupSubtitleSize), UmbrellaUI::LockupSubtitleSpacing))
 					.ColorAndOpacity(FUmbrellaUIStyle::Gold())
 					.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
 			];
@@ -162,7 +165,7 @@ void SFlowMenu::Construct(const FArguments& InArgs)
 			const int32 HeadingSize = Heading.Len() > UmbrellaUI::LongHeadingLength ? FMath::Min(Tuning.TitleFontSize, UmbrellaUI::LongHeadingSize) : Tuning.TitleFontSize;
 			Column->AddSlot().AutoHeight().HAlign(HAlign_Fill).Padding(TextInset, 0.0f, 0.0f, 0.0f)
 			[
-				SNew(STextBlock).Text(InArgs._Heading).Font(FUmbrellaUIStyle::DisplayFont(HeadingSize))
+				SNew(STextBlock).Text(InArgs._Heading).Font(FUmbrellaUIStyle::DisplayFont(UmbrellaAccessibility::PublishedFontSize(HeadingSize)))
 					.ColorAndOpacity(InArgs._HeadingColor.Get(FUmbrellaUIStyle::Cream())).AutoWrapText(true)
 					.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
 			];
@@ -176,7 +179,7 @@ void SFlowMenu::Construct(const FArguments& InArgs)
 	{
 		Column->AddSlot().AutoHeight().HAlign(HAlign_Fill).Padding(TextInset, 0.0f, UmbrellaUI::HeadingWidth - UmbrellaUI::ColumnWidth, UmbrellaUI::SectionGap)
 		[
-			SNew(STextBlock).Text(InArgs._Body).Font(FUmbrellaUIStyle::BodyFont(Tuning.BodyFontSize)).ColorAndOpacity(FUmbrellaUIStyle::Cream())
+			SNew(STextBlock).Text(InArgs._Body).Font(FUmbrellaUIStyle::BodyFont(UmbrellaAccessibility::PublishedFontSize(Tuning.BodyFontSize))).ColorAndOpacity(FUmbrellaUIStyle::Cream())
 				.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
 				.AutoWrapText(true).Justification(ETextJustify::Left)
 		];
@@ -442,7 +445,7 @@ void SFlowTextScreen::Construct(const FArguments& InArgs)
 		[
 			SNew(SBox).WidthOverride(FMath::Min(Tuning.TextBlockWidth, UmbrellaUI::ColumnWidth))
 			[
-				SAssignNew(TextBlock, STextBlock).Font(FUmbrellaUIStyle::BodyFont(Tuning.BodyFontSize)).ColorAndOpacity(FUmbrellaUIStyle::Cream())
+				SAssignNew(TextBlock, STextBlock).Font(FUmbrellaUIStyle::BodyFont(UmbrellaAccessibility::PublishedFontSize(Tuning.BodyFontSize))).ColorAndOpacity(FUmbrellaUIStyle::Cream())
 					.ShadowOffset(FVector2D(UmbrellaUI::ShadowOffset, UmbrellaUI::ShadowOffset)).ShadowColorAndOpacity(FUmbrellaUIStyle::Shadow())
 					.AutoWrapText(true).Justification(ETextJustify::Left)
 					.RenderTransform(this, &SFlowTextScreen::GetScrollTransform)
diff --git a/Source/UmbrellaElla/Private/UI/Story/StoryWidgets.cpp b/Source/UmbrellaElla/Private/UI/Story/StoryWidgets.cpp
index 585ba791..c89351d8 100644
--- a/Source/UmbrellaElla/Private/UI/Story/StoryWidgets.cpp
+++ b/Source/UmbrellaElla/Private/UI/Story/StoryWidgets.cpp
@@ -1,3 +1,4 @@
 #include "UI/Story/StoryWidgets.h"
+#include "Settings/UmbrellaAccessibility.h"
 #include "Story/StoryRules.h"
 #include "Core/UmbrellaTuning.h"
@@ -15,12 +16,12 @@ namespace
 {
 	FSlateFontInfo StoryFont(int32 Extra)
 	{
-		return FUmbrellaUIStyle::BodyFont(GetDefault<UUmbrellaTuning>()->Story.MinFontSize + Extra);
+		return FUmbrellaUIStyle::BodyFont(UmbrellaAccessibility::PublishedFontSize(GetDefault<UUmbrellaTuning>()->Story.MinFontSize + Extra));
 	}
 
 	FSlateFontInfo StoryDisplayFont(int32 Extra)
 	{
-		return FUmbrellaUIStyle::DisplayFont(GetDefault<UUmbrellaTuning>()->Story.MinFontSize + Extra);
+		return FUmbrellaUIStyle::DisplayFont(UmbrellaAccessibility::PublishedFontSize(GetDefault<UUmbrellaTuning>()->Story.MinFontSize + Extra));
 	}
 
 	FVector2D StoryShadow()
diff --git a/Source/UmbrellaElla/Private/UI/UmbrellaHUD.cpp b/Source/UmbrellaElla/Private/UI/UmbrellaHUD.cpp
index 6018d22a..9daa2537 100644
--- a/Source/UmbrellaElla/Private/UI/UmbrellaHUD.cpp
+++ b/Source/UmbrellaElla/Private/UI/UmbrellaHUD.cpp
@@ -1,4 +1,5 @@
 #include "UI/UmbrellaHUD.h"
+#include "Settings/UmbrellaAccessibility.h"
 #include "Core/EllaCharacter.h"
 #include "Attack/AttackEmitterComponent.h"
 #include "Core/UmbrellaEvent.h"
@@ -56,7 +57,7 @@ void AUmbrellaHUD::DrawHUD()
 	if (Font)
 	{
 		const float ViewHeight = static_cast<float>(Layout.View.GetSize().Y);
-		const float Scale = ClockHudRules::TextScale(Font->GetMaxCharHeight(), ViewHeight, Tuning);
+		const float Scale = ClockHudRules::TextScale(Font->GetMaxCharHeight(), ViewHeight, Tuning) * UmbrellaAccessibility::PublishedTextScale();
 		for (int32 Quarter = 0; Quarter < ClockHudConstants::NumeralCount; ++Quarter)
 		{
 			const TCHAR* Text = NumeralText[Quarter];
diff --git a/Source/UmbrellaElla/Public/Feedback/Vfx/VfxCatalog.h b/Source/UmbrellaElla/Public/Feedback/Vfx/VfxCatalog.h
index c4d6c7f0..c2c09cfc 100644
--- a/Source/UmbrellaElla/Public/Feedback/Vfx/VfxCatalog.h
+++ b/Source/UmbrellaElla/Public/Feedback/Vfx/VfxCatalog.h
@@ -142,6 +142,8 @@ namespace VfxCatalog
 
 	/** Frame shown after Elapsed seconds of game time: wraps for a loop, holds the last frame for a one-shot. */
 	UMBRELLAELLA_API int32 FrameAt(const FVfxArtRow& Row, float Elapsed);
+	/** As above; a looping row holds frame 0 under reduced motion (VFX-10 flag checked here). */
+	UMBRELLAELLA_API int32 FrameAt(const FVfxArtRow& Row, float Elapsed, bool bReducedMotion);
 
 	/** True when a one-shot has shown its last frame. A loop never finishes by itself. */
 	UMBRELLAELLA_API bool IsFinished(const FVfxArtRow& Row, float Elapsed);
```
