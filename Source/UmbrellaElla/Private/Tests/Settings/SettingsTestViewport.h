#pragma once

#include "CoreMinimal.h"
#include "Engine/GameViewportClient.h"
#include "Widgets/SOverlay.h"
#include "SettingsTestViewport.generated.h"

/**
 * Tests only: a game viewport whose overlay content goes into an SOverlay the test reads, like the real viewport's
 * overlay (UGameViewportClient::AddViewportWidgetContent adds an overlay slot at ZOrder). Test worlds have no viewport.
 */
UCLASS(Transient)
class USettingsTestViewport final : public UGameViewportClient
{
	GENERATED_BODY()

public:
	virtual void AddViewportWidgetContent(TSharedRef<SWidget> ViewportContent, const int32 ZOrder = 0) override
	{
		Overlay->AddSlot(ZOrder)[ViewportContent];
	}

	virtual void RemoveViewportWidgetContent(TSharedRef<SWidget> ViewportContent) override
	{
		Overlay->RemoveSlot(ViewportContent);
	}

	TSharedRef<SOverlay> GetOverlay() const { return Overlay; }

private:
	TSharedRef<SOverlay> Overlay = SNew(SOverlay);
};
