#pragma once

#include "CoreMinimal.h"
#include "Blueprint/UserWidget.h"
#include "FinalHourIntroWidget.generated.h"

class APlayerController;

/**
 * The Final Hour intro, shown before an Extreme (all stats maxed) Director's Cut run. Full-screen story card with
 * the approved exact text; it removes itself after the tuning's seconds (duration, skip and repeat policy are OPEN in the
 * GDD, so this is the provisional default). Built in Slate from C++.
 */
UCLASS()
class UMBRELLAELLA_API UFinalHourIntroWidget final : public UUserWidget
{
	GENERATED_BODY()

public:
	static UFinalHourIntroWidget* Show(APlayerController* Owner, float Seconds);

	/** The approved exact text (GDD). */
	static FText IntroText();

	float GetSecondsLeft() const { return SecondsLeft; }

protected:
	virtual TSharedRef<SWidget> RebuildWidget() override;
	virtual void NativeTick(const FGeometry& MyGeometry, float InDeltaTime) override;

private:
	float SecondsLeft = 0.0f;
};
