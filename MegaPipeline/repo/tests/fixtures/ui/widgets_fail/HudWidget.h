#pragma once
#include "Blueprint/UserWidget.h"
#include "HudWidget.generated.h"

UCLASS()
class UMBRELLAELLA_API UHudWidget : public UUserWidget
{
	GENERATED_BODY()
protected:
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;
};
