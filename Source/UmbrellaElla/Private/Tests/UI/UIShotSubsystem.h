#pragma once

#include "CoreMinimal.h"
#include "Containers/Ticker.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "UIShotSubsystem.generated.h"

class AUmbrellaPlayerController;
class SWidget;

/**
 * Art-loop capture driver (development only, never in Shipping): with -UIShots=<folder> on the command line it walks the
 * real flow through every screen and saves one PNG of each (title.png, defeated.png, ...), then quits.
 * -UIShotsMode=dc walks the Director's Cut screens (purchase, level-up, XP ring, Journey Complete).
 * Without the switch the subsystem is not created.
 */
UCLASS()
class UUIShotSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

public:
	virtual bool ShouldCreateSubsystem(UObject* Outer) const override;
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;
	virtual void Deinitialize() override;

private:
	struct FShotStep
	{
		/** Runs once when the step starts. */
		TFunction<void(AUmbrellaPlayerController*)> Do;
		/** Seconds to wait after Do before the shot (or before the next step when Name is empty). */
		float Wait = 1.0f;
		/** File name without extension; empty = no shot. */
		FString Name;
		/** When set, the step also waits until this is true (or UIShotReadyTimeout passes). */
		TFunction<bool()> Ready;
	};

	void AdvanceShots(float DeltaSeconds);
	void BuildSteps();
	void SaveShot(const FString& Name);
	AUmbrellaPlayerController* FindController() const;

	FTSTicker::FDelegateHandle TickHandle;
	TArray<FShotStep> Steps;
	FString OutDir;
	FString Mode;
	int32 StepIndex = -1;
	float StepSeconds = 0.0f;
	bool bStepStarted = false;
	TSharedPtr<SWidget> LegacyWidget;
	int32 Saved = 0;
	bool bDone = false;
};
