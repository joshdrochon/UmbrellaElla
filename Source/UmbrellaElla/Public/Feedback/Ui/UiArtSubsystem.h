#pragma once

#include "CoreMinimal.h"
#include "Flow/FlowRules.h"
#include "Subsystems/WorldSubsystem.h"
#include "UObject/StrongObjectPtr.h"
#include "UiArtSubsystem.generated.h"

class SWidget;
class UTexture2D;
struct FSlateBrush;

namespace UmbrellaUiArtConst
{
	/** The overlay sits this far above the flow menus (which use Flow.MenuContextPriority) and never takes a click. */
	static constexpr int32 ZOrderAboveMenu = 1;
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
};
