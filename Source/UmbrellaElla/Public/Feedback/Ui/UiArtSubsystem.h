#pragma once

#include "CoreMinimal.h"
#include "Core/UmbrellaPlayMode.h"
#include "Flow/FlowRules.h"
#include "Subsystems/WorldSubsystem.h"
#include "UObject/StrongObjectPtr.h"
#include "UiArtSubsystem.generated.h"

class SWidget;
class UTexture2D;
enum class EArtSlotDraw : uint8;
struct FSlateBrush;

namespace UmbrellaUiArtConst
{
	/** The overlay sits this far above the flow menus (which use Flow.MenuContextPriority) and never takes a click. */
	static constexpr int32 ZOrderAboveMenu = 1;
}

/** Screens as a bit mask for the piece table. */
static constexpr uint32 UiScreenBit(EFlowScreen Screen) { return 1u << static_cast<uint32>(Screen); }

namespace UmbrellaUiPieceConst
{
	/** Menu screens that sit on the ground picture. */
	static constexpr uint32 MenuScreens = UiScreenBit(EFlowScreen::Title) | UiScreenBit(EFlowScreen::Paused) | UiScreenBit(EFlowScreen::Settings)
		| UiScreenBit(EFlowScreen::Defeat) | UiScreenBit(EFlowScreen::Story) | UiScreenBit(EFlowScreen::Credits)
		| UiScreenBit(EFlowScreen::TutorialPaused) | UiScreenBit(EFlowScreen::Purchase) | UiScreenBit(EFlowScreen::LevelUp)
		| UiScreenBit(EFlowScreen::Statistics);
	static constexpr uint32 DriftScreens = UiScreenBit(EFlowScreen::Title) | UiScreenBit(EFlowScreen::Credits) | UiScreenBit(EFlowScreen::Statistics);
	static constexpr uint32 PauseScreens = UiScreenBit(EFlowScreen::Paused) | UiScreenBit(EFlowScreen::TutorialPaused);
	static constexpr uint32 HudScreens = UiScreenBit(EFlowScreen::Playing) | UiScreenBit(EFlowScreen::Tutorial);

	/** One piece: which screens show it, whether it fills the frame, where it sits otherwise, and whether it sits below the menus (grounds) or above. */
	struct FUiPiece
	{
		const TCHAR* Visual;
		uint32 Screens;
		bool bFill;
		EHorizontalAlignment Horizontal;
		EVerticalAlignment Vertical;
		bool bBelowMenu;
		/** Shown only in Director's Cut (ART-08, FLOW-48: Start Game has no XP ring). */
		bool bDirectorOnly = false;
	};
	/** Back to front. Pieces without a screen of their own sit at their native size, aligned to the frame. */
	static const FUiPiece Pieces[] = {
		{ TEXT("menu-backdrop:Drift"), DriftScreens, true, HAlign_Fill, VAlign_Fill, true },
		{ TEXT("menu-backdrop:Clocks"), PauseScreens, true, HAlign_Fill, VAlign_Fill, true },
		{ TEXT("ui:ground-Ground"), MenuScreens, true, HAlign_Fill, VAlign_Fill, true },
		{ TEXT("ui:ground-Grain"), MenuScreens, true, HAlign_Fill, VAlign_Fill, true },
		{ TEXT("ui:panel"), UiScreenBit(EFlowScreen::Paused) | UiScreenBit(EFlowScreen::Settings) | UiScreenBit(EFlowScreen::Defeat), false, HAlign_Center, VAlign_Center, false },
		{ TEXT("ui:title-lockup"), UiScreenBit(EFlowScreen::Title), false, HAlign_Center, VAlign_Top, false },
		{ TEXT("ui:head-Paused"), PauseScreens, false, HAlign_Center, VAlign_Top, false },
		{ TEXT("ui:head-Settings"), UiScreenBit(EFlowScreen::Settings), false, HAlign_Center, VAlign_Top, false },
		{ TEXT("ui:device-and-remap-prompts"), UiScreenBit(EFlowScreen::Settings), false, HAlign_Center, VAlign_Bottom, false },
		{ TEXT("ui:clock-face"), HudScreens, false, HAlign_Left, VAlign_Top, false },
		{ TEXT("ui:xp-ring"), HudScreens, false, HAlign_Left, VAlign_Top, false, true },
		{ TEXT("ui:spell-wheel"), UiScreenBit(EFlowScreen::Purchase) | UiScreenBit(EFlowScreen::LevelUp), false, HAlign_Center, VAlign_Center, false },
	};
}

/**
 * Draws the art slot "screen:<Screen>" over the current flow screen when its asset exists. The picture is a
 * click-through full-frame overlay; the flow menus and buttons underneath keep working and stay the fallback.
 * Reads the screen through the player controller's public getter. Never gameplay authority. Visuals lane.
 */
UCLASS()
class UMBRELLAELLA_API UUiArtSubsystem final : public UTickableWorldSubsystem
{
	GENERATED_BODY()

public:
	virtual void Tick(float DeltaTime) override;
	virtual TStatId GetStatId() const override;
	virtual void Deinitialize() override;

	/** Art slot id for a screen, e.g. "screen:Title". Pure. */
	static FString VisualIdFor(EFlowScreen Screen);

	/** Show a picture for a screen (null removes it). Tests pass a transient texture. */
	void ShowScreenArt(EFlowScreen Screen, UTexture2D* Texture);
	void ClearScreenArt();

	/** Draw one table piece for a screen (null removes it). Tests pass a transient texture. Refused (not Drawn) when the piece is not on that screen. */
	EArtSlotDraw DrawPiece(const FString& Visual, EFlowScreen Screen, UTexture2D* Texture, EUmbrellaPlayMode Mode = EUmbrellaPlayMode::DirectorsCut);
	void ClearPieces();
	int32 PieceCount() const { return PieceWidgets.Num(); }
	bool IsShowingPiece(const FString& Visual) const { return ShownPieces.Contains(Visual); }
	/** The table row of a visual, or null. Pure. */
	static const UmbrellaUiPieceConst::FUiPiece* FindPiece(const FString& Visual);

	bool IsShowingArt() const { return Widget.IsValid(); }
	EFlowScreen GetShownScreen() const { return ShownScreen; }
	const UTexture2D* GetShownTexture() const { return ShownTexture.Get(); }
	/** True when the overlay lets clicks through. */
	bool IsClickThrough() const;

private:
	bool bHasTarget = false;
	EFlowScreen ShownScreen = EFlowScreen::Title;
	EFlowScreen TargetScreen = EFlowScreen::Title;
	TStrongObjectPtr<UTexture2D> ShownTexture;
	TSharedPtr<FSlateBrush> Brush;
	TSharedPtr<SWidget> Widget;
	TArray<TSharedPtr<SWidget>> PieceWidgets;
	TArray<TSharedPtr<FSlateBrush>> PieceBrushes;
	TArray<TStrongObjectPtr<UTexture2D>> PieceTextures;
	TSet<FString> ShownPieces;
	void ShowPiecesFor(EFlowScreen Screen, EUmbrellaPlayMode Mode);
};
