#pragma once
#include "Blueprint/UserWidget.h"
#include "HudWidget.generated.h"

UCLASS()
class UMBRELLAELLA_API UHudWidget : public UUserWidget
{
	GENERATED_BODY()
public:
	void HandleHealthChanged(int32 NewHealth); // bound to the health component's delegate
	// NativeTick is banned here; this comment must not trip the check
};
